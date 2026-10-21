# Portfolio system register (pre-registration)

Written 2026-10-20, **before the portfolio system was run on real market data.** It implements the owner's
decisions of 2026-10-20:
- improve the existing system rather than start over;
- add proven strategy families, including pairs trading;
- make it regime- and situation-aware, with a big-picture layer after Aschenbrenner, *Situational Awareness*, 2024;
- let it choose and blend strategies by situation;
- maximise profit within a 25% worst-drawdown limit;
- allow short selling with tight caps;
- add 11 ETFs;
- test with a three-way split.

Code: `src/jarvis/portfolio/`. Runs are logged in `JARVIS_HOME/research/portfolio_studies.jsonl`. Evidence tags:
**FETCHED** (opened by a research agent; see `docs/01-research`) and **RECALLED** (from memory, not re-opened).

## Architecture

Every strategy ("sleeve") outputs target weights for every asset, every day. An allocator decides how much of each
sleeve to run in the current situation. A risk overlay sizes and caps the result, and an executor trades the
difference from current holdings. Weights decided after a close trade at the next open. Nothing in a decision uses
a later price: tests truncate the data and require identical past decisions.

## Universe

38 stocks and ETFs (2016 onward) plus BTC and ETH (Alpaca history from 2021), in fixed groups:
- **Equity indexes:** SPY, QQQ, IWM, DIA, EFA, EEM.
- **Sectors and themes:** XLF, XLK, XLE, XLV, XLY, XLP, XLI, XLU, XLB, SMH, VNQ.
- **Single stocks:** AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, JPM, XOM, UNH.
- **Bonds:** TLT, IEF, SHY, TIP, HYG, LQD.
- **Commodities:** GLD, SLV, DBC, USO, CPER.

**Known bias:** the single stocks were chosen in 2026, which flatters any strategy that holds them. The benchmarks
hold them too.

**Costs:**
- Trading costs per side: 5 bps for stocks and ETFs, 15 bps for CPER (thinly traded), 30 bps for crypto.
- Shorts pay a 1% a year borrow fee.
- Crypto is never shorted.

## Sleeves (all included; the allocator decides how much of each to run)

Each sleeve is scaled to 10% annual volatility on its own, with gross exposure capped at 2.

| Sleeve | Rule | Evidence |
|---|---|---|
| `trend_xasset` | Average sign of the 3-, 6- and 12-month returns; inverse-volatility weighted; long or short | Moskowitz, Ooi & Pedersen 2012 (FETCHED, S01); Hurst, Ooi & Pedersen, *A Century of Evidence on Trend-Following* (RECALLED) |
| `xs_momentum` | Stocks and equity ETFs: long the top fifth by 12-1 month momentum, short the bottom fifth | Jegadeesh & Titman 1993 (RECALLED) |
| `low_volatility` | Long the least volatile third of stocks and equity ETFs | Ang, Hodrick, Xing & Zhang 2006; Frazzini & Pedersen 2014 (RECALLED) |
| `pairs` | 20 economically linked pairs (listed in `sleeves.PAIRS`). 252-day hedge ratio; enter at a 2-standard-deviation spread with a 1–30 day half-life; exit at 0.5, stop at 4 or after 20 days; market-neutral | Gatev, Goetzmann & Rouwenhorst 2006, profits declining after the early 2000s (RECALLED) |
| `news_sentiment` | FinBERT headline sentiment z ≥ 2 from 3+ headlines; hold 5 days | Tetlock 2007 (RECALLED) |
| `theme_ai_power` | Hold SMH, NVDA, XLU, XLB, CPER in proportion to the four hyperscalers' capital-spending growth (full at ≥ 40%), only while the basket leads SPY over 6 months | Owner's thesis (Aschenbrenner 2024). Untested |
| `trend_sma200`, `meanrev_rsi2`, `volatility_breakout`, `breakout_volume`, `relative_strength`, `earnings_drift` | The earlier library (`docs/06-strategies`) as weight sleeves | See that register |

## Situational awareness

Twelve features, each standardised with its own past only.
- **Market state:**
  - S&P trend and volatility shift;
  - VIX level and term structure;
  - high-yield vs Treasury performance and the Baa spread change;
  - 10-year yield change;
  - breadth;
  - dispersion;
  - crypto trend.
- **Big picture:**
  - the AI/power basket's 6-month lead over SPY;
  - the hyperscalers' capital-spending growth, from SEC filings and dated when public.

## Allocator (blend methods: the logged development trials)

`equal`, `recent` (6-month return per unit of variance), `regime` (by plain-language regime), and `situational`
(a ridge regression per sleeve, with α = the number of samples, predicting the next month's return from the
features).
- All but `equal` keep 50% on equal shares and may hold cash.
- Monthly refits use only completed sleeve returns.
- Two years of history are needed first.

## Risk overlay

- Target 15% annual volatility.
- Caps:
  - gross exposure 1.5;
  - 30% per asset;
  - 20% crypto;
  - 30% shorts.
- Drawdown control: full size below 10%, falling to a quarter of size at 20%.
- Live: the Governor's own limits (allocated capital $10,000; per-order and per-asset caps; daily loss stop).

## Testing protocol

| Split | Period | Rule |
|---|---|---|
| Development | Decisions from 2017-01-01 to 2021-12-31 (2016 is warm-up) | All 4 blend methods run as trials. **Chosen:** the highest Sharpe after costs whose worst drawdown is within 25%. Also reported: the deflated Sharpe ratio (Bailey & López de Prado 2014, RECALLED) across the trials, and results with doubled costs |
| Confirmation | 2022-01-01 to 2023-12-31 (includes the 2022 bear market) | Once, for the chosen configuration. **Passes if:** Sharpe ≥ SPY's, worst drawdown within 25%, and total return above T-bills |
| Holdout | 2024-01-01 onward | Once, after the confirmation, with the same pass rule |

- Benchmarks: SPY, the equal-weight universe and 60/40 (SPY/IEF), all with the same execution model.
- **Development may iterate:** any change to a sleeve, feature or rule is logged as a new version and counted in the deflated Sharpe.
- **Confirmation and holdout cannot be re-run** for a configuration once used.

**Honest expectation:**
- The universe's single stocks and the 2017–2021 bull market make SPY a strong benchmark.
- The most likely benefit is a smoother path (diversification, trend's crisis protection, risk control) rather than a large return edge.
- Paper trading then provides out-of-sample evidence with real fills.
