"""Performance page for the round 7 paper desks: each desk's $10,000 account against SPY.

Reads each desk's own paper account (daily equity history, current value, positions) and SPY's closes from the
main store, and writes one self-contained HTML file (no scripts, no external files). Read-only: no orders, and no
keys are written anywhere.
"""

from __future__ import annotations

import html
from datetime import date, datetime, timezone
from pathlib import Path

from .contracts import AssetClass
from .timeframes import NEW_YORK

START_CAPITAL = 10_000.0
DESK_NAMES = {"sector": "Sector rotation", "stockbook": "Stock book"}
TESTED = {"sector": "17.1% a year (2017–2026 test)", "stockbook": "13.5% a year (2017–2026 test; passed all 3 checks)"}
COLORS = {"sector": "var(--c-sector)", "stockbook": "var(--c-stock)", "SPY": "var(--c-spy)"}


def desk_snapshot(key: str, secret: str) -> dict:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import GetPortfolioHistoryRequest

    client = TradingClient(key, secret, paper=True, raw_data=True)
    account = client.get_account()
    history = client.get_portfolio_history(GetPortfolioHistoryRequest(period="1A", timeframe="1D"))
    points = [(datetime.fromtimestamp(t, timezone.utc).astimezone(NEW_YORK).date(), float(e))
              for t, e in zip(history["timestamp"], history["equity"]) if e and float(e) > 0]
    today = datetime.now(NEW_YORK).date()
    equity = float(account["equity"])
    points = [p for p in points if p[0] < today] + [(today, equity)]
    positions = client.get_all_positions()
    holdings = sorted(((p["symbol"], float(p["market_value"]), float(p["unrealized_pl"])) for p in positions),
                      key=lambda x: -x[1])
    return {"equity": equity, "cash": float(account["cash"]), "points": points, "holdings": holdings,
            "count": len(positions)}


def first_order_time(desk_home: Path) -> datetime | None:
    """When the desk sent its first order (from its own journal)."""
    from .contracts import parse_utc
    from .storage import LocalStorage

    with LocalStorage(desk_home, writer=False) as store:
        times = [parse_utc(r["event"]["payload"]["decided_at"]) for r in store.read_events()
                 if r["event"]["event_type"] == "ORDER_INTENT" and r["event"]["payload"].get("decided_at")]
    return min(times) if times else None


def spy_price_at(key: str, secret: str, moment: datetime) -> float | None:
    """SPY's 1-minute close at the given moment (free IEX feed), or None."""
    from datetime import timedelta

    from alpaca.data import StockHistoricalDataClient
    from alpaca.data.enums import DataFeed
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    client = StockHistoricalDataClient(key, secret, raw_data=True)
    bars = client.get_stock_bars(StockBarsRequest(symbol_or_symbols="SPY", timeframe=TimeFrame.Minute,
                                                  start=moment - timedelta(minutes=15), end=moment,
                                                  feed=DataFeed.IEX)).get("SPY", [])
    return float(bars[-1]["c"]) if bars else None


def spy_series(store, start: date, base: float, now_price: float | None) -> list[tuple[date, float]]:
    """$10,000 in SPY bought at ``base`` on ``start``: then daily closes, and the current price for today."""
    closes = {b.start_at.astimezone(NEW_YORK).date(): b.close
              for b in store.load_bars("SPY", AssetClass.EQUITY, dataset="1Day-adjusted")}
    today = datetime.now(NEW_YORK).date()
    out = [(start, START_CAPITAL)] + [(d, START_CAPITAL * closes[d] / base) for d in sorted(closes) if start < d < today]
    if now_price:
        out.append((today, START_CAPITAL * now_price / base))
    return out


def _money(x: float) -> str:
    return f"${x:,.2f}"


def _signed(x: float) -> str:
    return f"{'+' if x >= 0 else '−'}${abs(x):,.2f}"


def _chart(series: dict[str, list[tuple[date, float]]]) -> str:
    """Inline SVG line chart of the equity curves (all start at $10,000)."""
    width, height, pad_l, pad_r, pad_t, pad_b = 760, 300, 64, 16, 16, 34
    all_points = [p for s in series.values() for p in s]
    if len(all_points) < 2:
        return "<p class='muted'>The chart fills in as days pass.</p>"
    days = sorted({p[0] for p in all_points})
    lo = min(min(v for _, v in all_points), START_CAPITAL * 0.99)
    hi = max(max(v for _, v in all_points), START_CAPITAL * 1.01)
    span = max(1, (days[-1] - days[0]).days)

    def x(d):
        return pad_l + (width - pad_l - pad_r) * ((d - days[0]).days / span if len(days) > 1 else 0.5)

    def y(v):
        return pad_t + (height - pad_t - pad_b) * (1 - (v - lo) / (hi - lo))

    parts = [f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='Account values since start'>"]
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        parts.append(f"<line x1='{pad_l}' x2='{width - pad_r}' y1='{y(v):.1f}' y2='{y(v):.1f}' class='grid'/>"
                     f"<text x='{pad_l - 8}' y='{y(v) + 4:.1f}' class='axis' text-anchor='end'>${v:,.0f}</text>")
    parts.append(f"<line x1='{pad_l}' x2='{width - pad_r}' y1='{y(START_CAPITAL):.1f}' y2='{y(START_CAPITAL):.1f}' class='base'/>")
    for d in (days[0], days[-1]):
        parts.append(f"<text x='{x(d):.1f}' y='{height - 10}' class='axis' text-anchor='middle'>{d:%b %d}</text>")
    for name, pts in series.items():
        if len(pts) == 1:
            px, py = x(pts[0][0]), y(pts[0][1])
            parts.append(f"<circle cx='{px:.1f}' cy='{py:.1f}' r='4' fill='{COLORS[name]}'/>")
        else:
            path = " ".join(f"{'M' if i == 0 else 'L'}{x(d):.1f},{y(v):.1f}" for i, (d, v) in enumerate(pts))
            parts.append(f"<path d='{path}' fill='none' stroke='{COLORS[name]}' stroke-width='2.5'/>")
    parts.append("</svg>")
    return "".join(parts)


def render(desks: dict[str, dict], spy: list[tuple[date, float]], generated: datetime) -> str:
    cards, tables = [], []
    for name, d in desks.items():
        change = d["equity"] - START_CAPITAL
        invested = d["equity"] - d["cash"]
        cards.append(f"""
<section class='card'>
  <h2><span class='dot' style='background:{COLORS[name]}'></span>{DESK_NAMES[name]}</h2>
  <div class='big'>{_money(d['equity'])}</div>
  <div class='{'up' if change >= 0 else 'down'}'>{_signed(change)} ({change / START_CAPITAL:+.2%}) since start</div>
  <dl>
    <dt>Invested</dt><dd>{_money(invested)} in {d['count']} positions</dd>
    <dt>Cash</dt><dd>{_money(d['cash'])}</dd>
    <dt>Tested</dt><dd>{TESTED[name]}</dd>
  </dl>
</section>""")
        rows = "".join(f"<tr><td>{html.escape(sym)}</td><td>{_money(mv)}</td><td class='{'up' if pl >= 0 else 'down'}'>{_signed(pl)}</td></tr>"
                       for sym, mv, pl in d["holdings"][:10])
        more = f"<p class='muted'>…and {d['count'] - 10} more positions.</p>" if d["count"] > 10 else ""
        tables.append(f"""
<section class='card'>
  <h3>{DESK_NAMES[name]}: largest holdings</h3>
  <table><thead><tr><th>Holding</th><th>Value</th><th>Gain / loss</th></tr></thead><tbody>{rows}</tbody></table>{more}
</section>""")
    spy_now = spy[-1][1] if spy else None
    spy_line = (f"<section class='card'><h2><span class='dot' style='background:{COLORS['SPY']}'></span>S&amp;P 500 (SPY)</h2>"
                f"<div class='big'>{_money(spy_now)}</div><div class='{'up' if spy_now >= START_CAPITAL else 'down'}'>"
                f"{_signed(spy_now - START_CAPITAL)} ({spy_now / START_CAPITAL - 1:+.2%}) since start</div>"
                f"<dl><dt>What it is</dt><dd>$10,000 in SPY bought when the desks placed their first orders</dd></dl></section>"
                if spy_now else "")
    series = {name: d["points"] for name, d in desks.items()}
    if spy:
        series["SPY"] = spy
    legend = "".join(f"<span><span class='dot' style='background:{COLORS[n]}'></span>{DESK_NAMES.get(n, 'S&amp;P 500')}</span>"
                     for n in series)
    return f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Jarvis Paper Desks</title>
<style>
:root {{ --bg:#f7f7f5; --panel:#ffffff; --text:#1d1d1b; --muted:#6b6b66; --line:#e3e2dd; --up:#1a7f4b; --down:#b3261e;
  --c-sector:#2f6fdf; --c-stock:#c2410c; --c-spy:#7a7a72; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme='light']) {{ --bg:#161615; --panel:#1f1f1d; --text:#ecebe6;
  --muted:#a3a29b; --line:#33332f; --up:#4cc38a; --down:#f2726b; --c-sector:#6d9eff; --c-stock:#f08a4b; --c-spy:#a3a29b; }} }}
:root[data-theme='dark'] {{ --bg:#161615; --panel:#1f1f1d; --text:#ecebe6; --muted:#a3a29b; --line:#33332f; --up:#4cc38a;
  --down:#f2726b; --c-sector:#6d9eff; --c-stock:#f08a4b; --c-spy:#a3a29b; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font:15px/1.5 system-ui,-apple-system,'Segoe UI',sans-serif; }}
main {{ max-width:980px; margin:0 auto; padding:24px 16px 48px; }}
h1 {{ font-size:24px; margin:0 0 4px; }} h2 {{ font-size:16px; margin:0 0 8px; }} h3 {{ font-size:15px; margin:0 0 8px; }}
.muted {{ color:var(--muted); }}
.grid3 {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:12px; margin:16px 0; }}
.grid2 {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:12px; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px; }}
.big {{ font-size:28px; font-weight:650; font-variant-numeric:tabular-nums; }}
.up {{ color:var(--up); }} .down {{ color:var(--down); }}
dl {{ display:grid; grid-template-columns:auto 1fr; gap:4px 12px; margin:12px 0 0; font-size:14px; }}
dt {{ color:var(--muted); }} dd {{ margin:0; }}
.dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:8px; }}
.legend {{ display:flex; gap:16px; flex-wrap:wrap; font-size:14px; margin-bottom:8px; }}
svg {{ width:100%; height:auto; display:block; }}
svg .grid {{ stroke:var(--line); }} svg .base {{ stroke:var(--muted); stroke-dasharray:4 4; }}
svg .axis {{ fill:var(--muted); font-size:12px; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; font-variant-numeric:tabular-nums; }}
th, td {{ text-align:left; padding:6px 4px; border-bottom:1px solid var(--line); }} th {{ color:var(--muted); font-weight:500; }}
td:nth-child(n+2), th:nth-child(n+2) {{ text-align:right; }}
.note {{ font-size:14px; }}
</style></head>
<body><main>
<h1>Jarvis paper desks</h1>
<p class='muted'>Two strategies, $10,000 each, on separate Alpaca paper accounts. Updated {generated.astimezone(NEW_YORK):%A %d %B %Y, %I:%M %p} New York time.</p>
<div class='grid3'>{''.join(cards)}{spy_line}</div>
<section class='card'>
  <h2>Account value since start</h2>
  <div class='legend'>{legend}</div>
  {_chart(series)}
</section>
<div class='grid2' style='margin-top:12px'>{''.join(tables)}</div>
<section class='card note' style='margin-top:12px'>
  <h3>How to read this</h3>
  <p>A good year for these strategies is about <b>$1,300–1,700</b> on $10,000, roughly $6 a day <i>on average</i>. Real days swing much more: quiet days ±$10–50, normal days ±$50–150, big market days ±$200–400. Judge them over months against the S&amp;P 500 line, not day by day.</p>
  <p class='muted'>The sector rotation changes holdings on the first trading day of each month. The stock book rebalances weekly and keeps 20% in the strongest bonds and commodities. Paper accounts only, no leverage, daily loss stop $300, drawdown stop 25%.</p>
</section>
</main></body></html>
"""


def build(main_home: Path, out: Path) -> dict:
    from .desks import desk_keys
    from .storage import LocalStorage

    desks = {}
    for name in ("sector", "stockbook"):
        key, secret = desk_keys(name)
        if key and secret:
            desks[name] = desk_snapshot(key, secret)
    if not desks:
        raise RuntimeError("no desk credentials in the environment")
    from .desks import desk_home

    start = min(d["points"][0][0] for d in desks.values())
    key, secret = desk_keys(next(iter(desks)))
    firsts = [t for t in (first_order_time(desk_home(main_home, n)) for n in desks) if t]
    spy = []
    try:
        from .market_data import AlpacaMarketData

        q = AlpacaMarketData(key, secret).latest_quote("SPY", AssetClass.EQUITY)
        now_price = (q.bid + q.ask) / 2
        base = spy_price_at(key, secret, min(firsts)) if firsts else None
        if base:
            with LocalStorage(Path(main_home), writer=False) as store:
                spy = spy_series(store, start, base, now_price)
    except Exception:
        spy = []  # the page still shows the desks if the benchmark cannot be priced
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(desks, spy, datetime.now(timezone.utc)), encoding="utf-8")
    return {"file": str(out), **{n: round(d["equity"], 2) for n, d in desks.items()},
            "spy": round(spy[-1][1], 2) if spy else None}
