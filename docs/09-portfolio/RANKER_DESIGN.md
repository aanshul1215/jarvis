# Ranker v3: design (revised after red-team review; awaiting owner approval, not implemented)

Written 2026-10-20. History: the round 2 learning ranker lost money; three research reviews (academic ML asset pricing;
open-source practice such as Qlib, Numerai and Jansen; cost-aware portfolio construction); a first v3 draft; an
adversarial red-team review of that draft; a read-only development diagnostic (step 0). Evidence tags as elsewhere:
**FETCHED** (opened) and **RECALLED**.

## 1. Why round 2 failed (development diagnostic, weekly decisions 2017–2021, Spearman IC vs next 21 days, all 40 assets)

| Signal | Mean IC |
|---|---|
| Round 2 model (GBT on about 40 raw features, 5-day target) | +0.017 |
| Forecast volatility | +0.146 (mostly asset class: stocks beat bonds in 2017–21) |
| Earnings-drift sleeve | +0.095 |
| Relative strength / 12-1 momentum | +0.075 / +0.069 |
| 1-month return | −0.014 |

Causes:
- It ranked across asset classes, so it learned beta, not selection.
- It used raw features plus date-like regime inputs.
- It had a noisy 5-day target and weak regularisation.
- Its trading rule was a weekly long-short rebuild that churned (Avramov, Cheng & Metzker 2023, FETCHED: ML short legs in large caps fail after costs).

## 2. What the red team found wrong with the first v3 draft

1. **Survivorship built into the features.**
   - The 10 single stocks were chosen in 2026: NVDA, TSLA and META are in because they won.
   - Group, earnings and volatility features let a model learn "these names go up".
   - Point-in-time, NVDA and TSLA were not top-10 US stocks in 2016.
2. **No statistical power.**
   - 2017–2021 holds about 59 non-overlapping months. A "learned model beats simple rule by 1 standard error" gate on that is close to a coin flip.
   - Detecting a realistic IC improvement of about 0.01 would need far more history than exists.
3. **Double dipping.** The composite's ingredients were picked from the same development data they would be judged on. The real trial count is at least 25, not 9.
4. **The earlier diagnostic was measured on all 40 assets**, so it mostly measured asset class.
5. **Overlap.** The existing relative-strength sleeve is the same signal; adding a ranker next to it doubles one bet and concentrates in tech.
6. **Date fingerprinting.** Regime/conditioning features let trees memorise periods.
7. **Leakage traps** in earnings and news timing, and an unregistered ridge alpha.
8. **Hidden turnover** from re-weighting holdings every week.
9. **Small payoff.** At the ranker's weight in the portfolio, a working ranker adds roughly 0.1–0.3% a year. Turnover and the gap between the 15% risk target and the risk actually taken are much larger levers.

## 3. Step 0 result (read-only, development decisions only; 59 monthly decisions 2017-01 to 2021-11; IC vs next 21 trading days, open t+1 to open t+22)

| Universe | 12-1 mom | dist 52w high | 6-month | 3-month | 1-month |
|---|---|---|---|---|---|
| All 27 equity-risk | +0.056 (t 1.2) | −0.040 (t −1.0) | +0.082 (t 1.7) | +0.109 (t 2.3) | +0.069 (t 1.5) |
| 17 ETFs only | +0.053 (t 1.0) | +0.018 (t 0.4) | +0.069 (t 1.3) | +0.072 (t 1.3) | +0.037 (t 0.8) |
| 27 minus NVDA, TSLA | +0.066 (t 1.4) | −0.020 (t −0.5) | +0.075 (t 1.5) | +0.092 (t 1.8) | +0.055 (t 1.1) |
| 11 sector ETFs | +0.030 (t 0.5) | +0.012 (t 0.2) | +0.079 (t 1.4) | +0.053 (t 0.9) | +0.045 (t 0.9) |

Reading:
- **Not a survivorship artefact.** Momentum keeps its sign and roughly its size with only ETFs, and without NVDA/TSLA. The stop rule (ETF-only IC < 0.02) is not triggered.
- **Not proven.** No t-stat clears 2 except one cell out of 20, which multiple testing explains. The sizes (0.05–0.08) match the published range for industry momentum.
- **Distance from the 52-week high fails here** and is dropped, against the red team's suggestion.
- Choosing 3- and 6-month momentum from this table is itself double dipping, so section 4 requires an independent-history check before use.

## 4. Revised plan

**Step 1: independent validation (owner approved the download and the plan 2026-10-20; registered here before the
file was downloaded).**
- **Data:** Kenneth French's 49-industry portfolios, value-weighted monthly returns (the first table of
  `49_Industry_Portfolios_CSV.zip`), stored under `JARVIS_HOME/external/french/`, never committed. Only months up to
  2015-12 are used (no overlap with our 2016+ data, and no 2026-chosen names).
- **Signals at month-end t**, from compounded monthly returns: 3-month (months t-2..t), 6-month (t-5..t) and 12-1
  (t-11..t-1). **Composite:** the average of the three cross-sectional ranks (scaled to 0..1). Missing returns
  (−99.99) exclude an industry that month; a month needs at least 20 industries with all three signals and the next
  return.
- **Outcome:** the industry's month t+1 return. **IC:** the Spearman correlation across industries, one per month.
- **Pass (all three):**
  - mean IC > 0.02;
  - t-stat of the monthly ICs > 3 (the bar for at least 25 trials);
  - mean IC positive in at least 6 of 9 consecutive, equal-length blocks of months.
- **Also reported, not used to decide:** each single signal's IC, and a 1931–1970 / 1971–2015 split.
- **If it fails,** no ranker; the plan stops here.

**Step 2: the ranker sleeve (only if step 1 passes). It replaces relative_strength; no ML.**
- **Scope:** the 17 ETFs, plus single stocks only if the US top-10 by market cap held them at that date (point-in-time membership, built from the SEC data we already have). This removes the 2026 hindsight list.
- **Score:** the composite above. No learned weights, so no fitting on development data.
- **Hold-or-sell rule:**
  - Enter in the top 4.
  - Keep while in the top 9 (Novy-Marx & Velikov buy/hold band, FETCHED).
  - At most 2 swaps a month.
  - Weights are set at entry and not re-weighted weekly.
  - The tech cluster (XLK, SMH, NVDA, MSFT, AAPL, …) is capped at 40% of the sleeve.
  - Never uses entry price or unrealised P&L (Odean 1998, FETCHED).
- **Long only.**

**Step 3: ML only later.**
- A learned model is reconsidered only once it beats the composite by 2 standard errors on the French history.
- That needs more data than our 5 years can provide.

**Trial accounting.** Deflated Sharpe uses N = 25 from now on, counting every look so far.

## 5. Bigger levers (proposed for the same round 3, separately registered)

- **Risk actually taken vs target.** Round 2 ran at about 12% annual volatility (estimated from return / Sharpe) against a 15% target, because sleeve vol targets, caps and drawdown cuts compound. Closing that gap raises return at about the same Sharpe.
- **Turnover.** Round 2 traded about 27× a year. Banded rebalancing for all sleeves (not only the ranker) is the cheapest return available.
- **Leverage.** The gross cap is 1.5× by owner decision; 2.0× is an open question.
