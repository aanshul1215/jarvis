"""Market regime detection (Phase 5): point-in-time labels and a test of whether they tell us anything.

A regime detector labels each forecast origin using only information available then. It is useful only if the
label helps predict what happens next, so the comparison asks: with the next 21 observations' log return modelled
as normal, with a mean and variance estimated per regime from past data, which detector gives the higher
out-of-sample log score? Detectors (pre-registered in docs/07-awareness/MODEL_REGISTER.md):

- ``none`` (reference): no regime at all, the window's overall mean and variance. A detector must beat this too,
  otherwise a noisy baseline could make a useless detector look good.
- ``sma200`` (baseline): close above or below its 200-observation average.
- ``trend_vol``: the same trend label crossed with a volatility state (20-observation variance above or below its
  median of the last 252 observations): four regimes.
- ``hmm2``: a two-state Gaussian hidden Markov model of daily returns (Hamilton 1989), fitted by EM on the rolling
  window and read through the forward filter only. Smoothed probabilities use later data and are never used.
- ``trend_vol_stress``: ``trend_vol`` plus a market-stress state from FRED (VIX at or above 25, or VIX at or above
  its 3-month counterpart VXV). Tested separately as an ablation: the stress signal is kept only if it improves on
  ``trend_vol`` where VIX history exists.

Label statistics use the same rolling window and month-start refits as the volatility models, and the training
targets of a refit all end before the first origin it is used for.
"""

from __future__ import annotations

import hashlib
import math
from datetime import date, datetime, time, timedelta, timezone
from typing import Callable

import numpy as np

from .metrics import diebold_mariano
from .volatility import ALPHA, DEVELOPMENT_END, HOLDOUT_START, WINDOW, PriceSeries, month_starts

HORIZON = 21
MIN_LABEL_COUNT = 30           # fewer training targets than this: the label falls back to the window's statistics
WARMUP = 300                   # observations needed before the first labelled training origin (SMA 200, 252 median)
VIX_STRESS, TERM_STRESS = 25.0, 1.0
REGIME_NAMES = {0: "down_calm", 1: "down_volatile", 2: "up_calm", 3: "up_volatile", 4: "stress"}
BASELINE, NULL, CANDIDATES, ABLATION = "sma200", "none", ("trend_vol", "hmm2"), ("trend_vol", "trend_vol_stress")


# --- labels ---------------------------------------------------------------------------------------------------------

def trend_labels(closes: np.ndarray, n_returns: int) -> np.ndarray:
    """1 = close above its 200-observation average at return origin t (close index t + 1), 0 = below, -1 = unknown."""
    cumulative = np.concatenate([[0.0], np.cumsum(closes)])
    labels = np.full(n_returns, -1, dtype=int)
    t = np.arange(198, n_returns)
    sma = (cumulative[t + 2] - cumulative[t + 2 - 200]) / 200
    labels[t] = (closes[t + 1] > sma).astype(int)
    return labels


def vol_state(r: np.ndarray) -> np.ndarray:
    """1 = 20-observation variance above its median over the last 252 observations, 0 = below, -1 = unknown."""
    cumulative = np.concatenate([[0.0], np.cumsum(r ** 2)])
    v20 = np.full(len(r), np.nan)
    t = np.arange(19, len(r))
    v20[t] = (cumulative[t + 1] - cumulative[t - 19]) / 20
    state = np.full(len(r), -1, dtype=int)
    for i in range(19 + 251, len(r)):
        state[i] = int(v20[i] > np.median(v20[i - 251:i + 1]))
    return state


def is_stressed(vix: float | None, vxv: float | None) -> bool | None:
    """The pre-registered stress rule; None when VIX is unknown."""
    if vix is None:
        return None
    return bool(vix >= VIX_STRESS or (vxv is not None and vxv > 0 and vix / vxv >= TERM_STRESS))


def stress_flags(dates: tuple[date, ...], group: str, vix_at: Callable[[datetime], float | None],
                 vxv_at: Callable[[datetime], float | None]) -> np.ndarray:
    """1 = stressed, 0 = calm, -1 = no VIX known at the decision time.

    ``vix_at`` / ``vxv_at`` return the value known at a moment (``macro.AsOfSeries.at``: newest observation
    published by then, latest revision). Decision times: stocks 21:15 UTC on the close date (after the 16:00 New York
    close and the bar's 15-minute availability delay); crypto 01:15 UTC the next day (FRED's Coinbase price is taken
    at 17:00 Pacific).
    """
    flags = np.full(len(dates), -1, dtype=int)
    for i, day in enumerate(dates):
        moment = datetime.combine(day, time(21, 15), tzinfo=timezone.utc) if group == "EQUITY" else \
            datetime.combine(day + timedelta(days=1), time(1, 15), tzinfo=timezone.utc)
        stressed = is_stressed(vix_at(moment), vxv_at(moment))
        if stressed is not None:
            flags[i] = int(stressed)
    return flags


class GaussianHmm2:
    """Two-state Gaussian HMM fitted by EM on a window; states ordered so state 1 has the larger variance."""

    def __init__(self, iterations: int = 50, tolerance: float = 1e-6):
        self.iterations, self.tolerance = iterations, tolerance

    @staticmethod
    def _densities(x: np.ndarray, mean: np.ndarray, var: np.ndarray) -> np.ndarray:
        return np.exp(-0.5 * (x[:, None] - mean) ** 2 / var) / np.sqrt(2 * math.pi * var)

    @staticmethod
    def _forward(dens: np.ndarray, trans: np.ndarray, initial: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Filtered state probabilities P(state_t | x_1..x_t) and the scaling constants (likelihood factors)."""
        n = len(dens)
        alpha, scale = np.empty((n, 2)), np.empty(n)
        a00, a01, a10, a11 = trans[0, 0], trans[0, 1], trans[1, 0], trans[1, 1]
        p0, p1 = initial
        for i in range(n):
            q0, q1 = p0 * dens[i, 0], p1 * dens[i, 1]
            c = q0 + q1
            if c <= 0:
                q0, q1, c = 0.5, 0.5, 1e-300
            q0, q1 = q0 / c, q1 / c
            alpha[i, 0], alpha[i, 1], scale[i] = q0, q1, c
            p0, p1 = q0 * a00 + q1 * a10, q0 * a01 + q1 * a11
        return alpha, scale

    def fit(self, x: np.ndarray, start: dict | None = None) -> dict:
        """EM from a fixed start, so a fit depends only on its window (the live path can reproduce it)."""
        variance = float(np.var(x))
        if start is None:
            start = {"mean": np.array([0.0, 0.0]), "var": np.array([0.5, 2.0]) * variance,
                     "trans": np.array([[0.98, 0.02], [0.05, 0.95]]), "initial": np.array([0.5, 0.5])}
        mean, var, trans, initial = (np.array(start[k], dtype=float) for k in ("mean", "var", "trans", "initial"))
        previous = loglik = -np.inf
        floor = 1e-4 * variance
        for _ in range(self.iterations):
            dens = self._densities(x, mean, var)
            alpha, scale = self._forward(dens, trans, initial)
            loglik = float(np.sum(np.log(scale)))
            if loglik - previous < self.tolerance:
                break
            beta = np.empty_like(alpha)
            beta[-1] = 1.0
            for i in range(len(x) - 2, -1, -1):  # backward pass: only for fitting on past data, never for labels
                b = trans @ (dens[i + 1] * beta[i + 1])
                beta[i] = b / scale[i + 1]
            gamma = alpha * beta
            gamma /= gamma.sum(axis=1, keepdims=True)
            xi = (alpha[:-1, :, None] * trans[None] * (dens[1:] * beta[1:])[:, None, :]) / scale[1:, None, None]
            weights = gamma.sum(axis=0)
            if np.any(weights < 1e-6 * len(x)):
                break  # a state has collapsed: keep the last valid parameters
            new_mean = (gamma * x[:, None]).sum(axis=0) / weights
            new_var = np.maximum((gamma * (x[:, None] - new_mean) ** 2).sum(axis=0) / weights, floor)
            new_trans = xi.sum(axis=0) / xi.sum(axis=(0, 2))[:, None]
            if not (np.all(np.isfinite(new_mean)) and np.all(np.isfinite(new_var)) and np.all(np.isfinite(new_trans))):
                break
            mean, var, trans, initial = new_mean, new_var, new_trans, gamma[0]
            previous = loglik
        order = np.argsort(var)
        return {"mean": mean[order], "var": var[order], "trans": trans[np.ix_(order, order)],
                "initial": initial[order], "loglik": loglik}

    def filtered(self, x: np.ndarray, params: dict) -> np.ndarray:
        alpha, _ = self._forward(self._densities(x, params["mean"], params["var"]), params["trans"], params["initial"])
        return alpha


# --- comparison -----------------------------------------------------------------------------------------------------

def _targets(r: np.ndarray, horizon: int) -> np.ndarray:
    cumulative = np.concatenate([[0.0], np.cumsum(r)])
    out = np.full(len(r), np.nan)
    t = np.arange(0, len(r) - horizon)
    out[t] = cumulative[t + 1 + horizon] - cumulative[t + 1]
    return out


def _log_normal(y: np.ndarray, mean: np.ndarray, var: np.ndarray) -> np.ndarray:
    return -0.5 * (np.log(2 * math.pi * var) + (y - mean) ** 2 / var)


def _block_scores(labels_train: np.ndarray, y_train: np.ndarray, labels_test: np.ndarray, y_test: np.ndarray) -> np.ndarray:
    ok = (labels_train >= 0) & np.isfinite(y_train)
    if ok.sum() < MIN_LABEL_COUNT:  # e.g. no stress history yet: fall back to the whole window
        ok = np.isfinite(y_train)
    base_mean, base_var = float(np.mean(y_train[ok])), float(np.var(y_train[ok]))
    means, variances = np.full(len(y_test), base_mean), np.full(len(y_test), base_var)
    for label in np.unique(labels_test):
        rows = ok & (labels_train == label)
        if label >= 0 and rows.sum() >= MIN_LABEL_COUNT:
            means[labels_test == label] = float(np.mean(y_train[rows]))
            variances[labels_test == label] = float(np.var(y_train[rows]))
    return _log_normal(y_test, means, variances)


def static_labels(name: str, r: np.ndarray, closes: np.ndarray, stress: np.ndarray | None) -> np.ndarray:
    trend = trend_labels(closes, len(r))
    if name == "none":
        return np.where(trend >= 0, 0, -1)
    if name == "sma200":
        return trend
    vol = vol_state(r)
    combined = np.where((trend >= 0) & (vol >= 0), trend * 2 + vol, -1)  # 0 down-calm 1 down-volatile 2 up-calm 3 up-volatile
    if name == "trend_vol":
        return combined
    if name == "trend_vol_stress":
        if stress is None:
            raise ValueError("trend_vol_stress needs stress flags")
        return np.where(stress == 1, 4, np.where(stress == 0, combined, -1))
    raise ValueError(f"unknown detector {name}")


def detector_scores(name: str, r: np.ndarray, closes: np.ndarray, dates: tuple[date, ...],
                    stress: np.ndarray | None = None, horizon: int = HORIZON,
                    window: int = WINDOW) -> tuple[int, np.ndarray, np.ndarray]:
    """(first origin, out-of-sample log scores, labels) for every origin from the first refit to the end."""
    y = _targets(r, horizon)
    refits = [i for i in month_starts(dates) if i >= window + WARMUP]
    if not refits:
        return len(r), np.asarray([]), np.asarray([], dtype=int)
    bounds = refits + [len(r)]
    scores, labels_out = [], []
    hmm = GaussianHmm2()
    labels_all = None if name == "hmm2" else static_labels(name, r, closes, stress)
    for a, b in zip(bounds[:-1], bounds[1:]):
        train = np.arange(a - window, a - horizon)  # every training target ends before origin a
        if name == "hmm2":
            params = hmm.fit(r[a - window:a])  # cold start each month: deterministic, reproducible live
            probs = hmm.filtered(r[a - window:b], params)
            block_labels = (probs[:, 1] > 0.5).astype(int)
            lab_train, lab_test = block_labels[:window - horizon], block_labels[window:]
        else:
            lab_train, lab_test = labels_all[train], labels_all[a:b]
        scores.append(_block_scores(lab_train, y[train], lab_test, y[a:b]))
        labels_out.append(lab_test)
    return refits[0], np.concatenate(scores), np.concatenate(labels_out)


def _in_split(dates: tuple[date, ...], origin: int, horizon: int, split: str) -> bool:
    if split == "DEVELOPMENT":
        return origin + horizon < len(dates) and dates[origin + horizon] <= DEVELOPMENT_END
    if split == "HOLDOUT":
        return origin + horizon < len(dates) and dates[origin] >= HOLDOUT_START
    raise ValueError(f"unknown split {split}")


def compare(series: list[PriceSeries], *, stress_for: Callable[[PriceSeries, tuple[date, ...]], np.ndarray] | None = None,
            split: str = "DEVELOPMENT", horizon: int = HORIZON, window: int = WINDOW) -> dict:
    """Pre-registered pass rule (same shape as the volatility study):

    - main test: a candidate passes if, against both ``sma200`` and ``none``, in every asset group, the one-sided
      Diebold-Mariano p-value of its log-score gain (averaged across that group's assets per date) is below 0.05 / 2
      and the mean gain is positive. Groups are tested separately because stock and crypto calendars differ;
    - ablation: the stress signal is kept if ``trend_vol_stress`` beats ``trend_vol`` the same way at p < 0.05, on
      origins where VIX was known;
    - ``sma200_vs_none`` (is the baseline itself informative?) uses the main threshold, 0.05 / 2.
    """
    names = (NULL, BASELINE, *CANDIDATES) + (("trend_vol_stress",) if stress_for else ())
    per_asset, pooled = {}, {}
    for item in series:
        r, dates = item.returns()
        closes = np.asarray(item.closes, dtype=float)
        stress = stress_for(item, dates) if stress_for else None
        computed = {n: detector_scores(n, r, closes, dates, stress, horizon, window) for n in names}
        first = computed[BASELINE][0]
        if first >= len(r) - horizon:
            per_asset[item.asset] = {"group": item.group, "origins": 0, "note": "not enough history"}
            continue
        origins = np.arange(first, len(r))
        keep = np.array([_in_split(dates, t, horizon, split) for t in origins], dtype=bool)
        if not keep.any():
            per_asset[item.asset] = {"group": item.group, "origins": 0, "note": "no origins in this split"}
            continue
        scores = {n: computed[n][1] for n in names}
        row = {"group": item.group, "origins": int(keep.sum()),
               "first_origin": dates[origins[keep][0]].isoformat(), "last_origin": dates[origins[keep][-1]].isoformat(),
               "mean_log_score": {n: float(np.mean(scores[n][keep])) for n in names}, "tests": {},
               "regimes": _regime_table(computed["trend_vol"][2][keep], _targets(r, horizon)[origins][keep], horizon)}
        pairs = [(c, b) for c in CANDIDATES for b in (BASELINE, NULL)] + [(BASELINE, NULL)] + ([ABLATION[::-1]] if stress_for else [])
        for cand, base in pairs:
            mask = keep & (stress >= 0)[origins] if cand == "trend_vol_stress" else keep
            d = scores[cand][mask] - scores[base][mask]
            key = f"{cand}_vs_{base}"
            row["tests"][key] = diebold_mariano(d, horizon)
            for day, value in zip([dates[t] for t in origins[mask]], d):
                pooled.setdefault(key, {}).setdefault(item.group, {}).setdefault(day, []).append(float(value))
        per_asset[item.asset] = row
    results = {}
    for key, by_group in pooled.items():
        threshold = ALPHA if key.startswith("trend_vol_stress") else ALPHA / len(CANDIDATES)
        tests = {g: diebold_mariano(np.asarray([np.mean(v[d]) for d in sorted(v)]), horizon) for g, v in by_group.items()}
        results[key] = {"by_group": tests, "p_threshold": threshold,
                        "mean_gain": float(np.mean([t["mean"] for t in tests.values()])),
                        "passed": bool(tests and all(t["p_value"] < threshold and t["mean"] > 0 for t in tests.values()))}
    passing = [(results[f"{c}_vs_{BASELINE}"]["mean_gain"], c) for c in CANDIDATES
               if all(results.get(f"{c}_vs_{b}", {}).get("passed") for b in (BASELINE, NULL))]
    # Without a passing candidate, keep the baseline only if it is itself better than knowing no regime at all.
    fallback = BASELINE if results.get(f"{BASELINE}_vs_{NULL}", {}).get("passed") else NULL
    winner = max(passing)[1] if passing else fallback
    stress_kept = bool(results.get("trend_vol_stress_vs_trend_vol", {}).get("passed"))
    return {"split": split, "horizon": horizon, "window": window, "per_asset": per_asset, "tests": results,
            "winner": winner, "stress_signal_kept": stress_kept}


def _regime_table(labels: np.ndarray, y: np.ndarray, horizon: int) -> dict:
    """What followed each trend/volatility regime: share of time, annualised mean and volatility of returns."""
    names = {0: "down_calm", 1: "down_volatile", 2: "up_calm", 3: "up_volatile"}
    table = {}
    for code, name in names.items():
        rows = (labels == code) & np.isfinite(y)
        if rows.sum() < 2:
            continue
        table[name] = {"share": float(rows.mean()), "annual_mean": float(np.mean(y[rows]) * 252 / horizon),
                       "annual_vol": float(np.std(y[rows]) * math.sqrt(252 / horizon))}
    return table


def current_label(name: str, r: np.ndarray, closes: np.ndarray, stressed: bool | None = None) -> int | None:
    """The live label at the latest return for a rule-based detector, computed exactly as ``static_labels`` does at
    its last index but without recomputing the whole history. None while the history is too short."""
    if len(closes) != len(r) + 1:
        raise ValueError("closes must have one more value than returns")
    if len(closes) < 200:
        return None
    trend = int(closes[-1] > np.mean(closes[-200:]))
    if name == "none":
        return 0
    if name == "sma200":
        return trend
    if len(r) < 19 + 252:
        return None
    window = r[-(252 + 19):] ** 2
    cumulative = np.concatenate([[0.0], np.cumsum(window)])
    v20 = (cumulative[20:] - cumulative[:-20]) / 20                     # the last 252 twenty-observation variances
    combined = trend * 2 + int(v20[-1] > np.median(v20))
    if name == "trend_vol":
        return combined
    if name == "trend_vol_stress":
        return None if stressed is None else (4 if stressed else combined)
    raise ValueError(f"current_label covers the rule-based detectors, not {name}; use live_label")


def live_label(name: str, r: np.ndarray, dates: tuple[date, ...], closes: np.ndarray, *, stressed: bool | None = None,
               window: int = WINDOW, cache: dict | None = None) -> int | None:
    """Live label for any detector, matching the study: ``hmm2`` uses parameters fitted at the start of the current
    month on the ``window`` returns before it, then the forward filter up to the latest return."""
    if name != "hmm2":
        return current_label(name, r, closes, stressed)
    starts = [i for i in month_starts(dates) if i <= len(r) - 1]
    if not starts or starts[-1] < window:
        return None
    refit = starts[-1]
    key = ("hmm2", window, dates[refit], hashlib.sha256(r[refit - window:refit].tobytes()).hexdigest())
    params = cache.get(key) if cache is not None else None
    if params is None:
        params = GaussianHmm2().fit(r[refit - window:refit])
        if cache is not None:
            cache[key] = params
    return int(GaussianHmm2().filtered(r[refit - window:], params)[-1, 1] > 0.5)
