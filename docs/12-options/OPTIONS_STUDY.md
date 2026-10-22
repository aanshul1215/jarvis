# Options study 1: single-stock and commodity-ETF options. Registered 2026-10-22 before any option data was analysed

## Owner direction (2026-10-22)

- Trade options on stocks and commodities, not XSP.
- Find a real edge using long calls, long puts, short calls and short puts.
- Use Black-Scholes, Itô's lemma "and many more things".
- Integrate open-source AI models such as Kronos.

## What the preceding research established

**Stage 1a, literature** (notes in `JARVIS_TEMP/opt2/`):
- **Black-Scholes and Itô's lemma price options without the stock's drift, so they make no directional forecast.** An edge must come from one of three sources:
  1. forecasting realised volatility better than implied volatility;
  2. forecasting direction better than the market;
  3. a risk premium.
- **The single-stock variance premium is about zero.**
- **Cross-sectional option anomalies** (Goyal-Saretto, Zhan et al., Bali et al.) **mostly disappear at 25–100% of the quoted spread.**
- **Buying options on predicted moves** pays a break-even of about 0.35–0.7% of the stock price per trade, through the spread.
- **Commodity ETFs** (GLD, USO) show a modest variance premium.

**Stage 1b, live liquidity survey** (`opt2/liquidity_survey.csv`):
- The median ATM spread on monthly options is about 10% of mid across the top-300 stocks.
- Spreads of 5% or less: 24 stocks (tier A); 10% or less: 40 more (tier B).
- Among the commodity ETFs, GLD and USO qualify, while SLV, GDX and UNG are marginal.
- A $5 put spread's natural credit is about half its mid credit.

**AI repositories** (`ai_repos/`):
- **Kronos** (MIT, pretrained to June 2024) has only author-reported gains over GARCH. Independent tests rank it behind HAR-RV.
- **The other foundation models and the LLM traders** show no independent out-of-sample edge.

## Data and its limits (stated in advance)

- **Option prices:** Alpaca daily option bars, from 2024-01-18. These are **trade prints only; there are no historical quotes.** A bar's close is its last trade.
  - A leg is usable on a date only if its bar exists, has volume of at least 1, and its last trade falls in the final 30 minutes, when that can be checked. Otherwise the leg is missing and the trade is skipped.
- **Underlyings:**
  - stocks: daily SIP bars (`JARVIS_HOME/shortterm/daily_adjusted.parquet`, `daily_raw.parquet`; raw prices for strikes and moneyness);
  - ETFs: the main store's 1Day bars;
  - the T-bill rate: DTB3, known the day before.
- **Implied volatility:** computed by us from option closes with Black-Scholes (European, no dividends; it is an approximation for American options near the money). The underlying is taken at its close, which is the strike reference. Brent root-finding is used; a leg is dropped if no root exists.
- **Costs:** there are no historical quotes, so each leg pays **half of today's measured spread for that name** (from the stage 1b survey):
  - **Which spread:** the ATM spread for ATM legs and the 25-delta spread for wings.
  - **When:** on entry and on exit, as a percentage of the leg's price at that time. This is the fill a marketable paper order gets.
  - **Missing measurement:** if a name has no measured spread for a leg, 1.5 times its ATM spread is used.
  - **Also reported:** results at double costs and at zero costs (mid).
- **Known bias:** today's liquidity chooses the universe (survivorship and popularity). Results for C2–C4 are therefore an upper bound.

## Calendar

- **Cycles:** for every standard monthly expiry E (the third Friday) from 2024-03 to 2026-10:
  - **entry:** the close of the first trading day on or after E minus 30 calendar days;
  - **exit:** the close of the trading day two sessions before E. This avoids expiry pinning and assignment, which are not modelled.
- **Development:** entries from 2024-02 to 2025-06. **Holdout:** entries from 2025-07 to 2026-09, run once, only for families that pass development.
- **The Kronos challenger** (C2-K) uses only entries from 2024-07 on (after its pretraining), with the same development/holdout boundary.

## Universe

- **Stocks:** the 24 tier-A and 40 tier-B stocks from the survey (`opt2/tradable_universe.csv`). A stock is eligible in a cycle only if it was in that month's point-in-time top 300, and has usable legs.
- **Commodity ETFs:** GLD and USO.

## Families and variants (8 trials in total; every result is reported)

| id | Rule | Measured as | Benchmark |
|---|---|---|---|
| **C1a** | **GLD and USO put credit spread, every cycle:** short the listed put nearest 25 delta (delta from ATM IV), long the next listed put at least 3% of spot lower | Return on max loss per trade | T-bills over the same days |
| **C1b** | C1a only when ATM IV is above the HAR forecast of 21-day realised vol | Same | T-bills |
| **C2-sell** | **Liquid stocks, "options rich":** rank by ATM IV divided by the HAR forecast of 21-day realised vol; the top 20% get an **iron butterfly** (short ATM call and put, long call and put at the listed strikes nearest ATM ± one IV-implied move, IV × S × √(T/365)) | Return on max loss | C2-sell-all: the same structure on every eligible name |
| **C2-buy** | **The bottom 20%** of the same ranking get a **long ATM straddle** | Return on premium | C2-buy-all: a straddle on every eligible name |
| **C2-K** *(conditional)* | C2-sell and C2-buy with **Kronos-small's** 21-day volatility forecast in place of HAR (median of the sampled paths' realised vol). Runs only if the owner approves downloading Kronos (code and weights), under the same rules | Same | C2 with HAR, on the same dates |
| **C3** | **Directional calls on events:** when a universe stock has an E1 event (day return of at least +4%, at least 3% above SPY, volume at least 3× its 20-day average), buy the ATM call of the first standard monthly at least 30 days out at the next day's close. Hold 20 trading days, or to that expiry minus 5 sessions. | Return on premium; and dollar P&L per trade compared with buying delta × 100 shares at the same close and holding the same days | The stock-equivalent position |
| **C4a** | **Cash-secured puts on cheaper stocks:** names with an ATM strike of $100 or less at entry sell the listed put nearest 25 delta | Return on collateral (strike × 100) | Holding $strike×100 of the stock over the same days (return and drawdown) |
| **C4b** | C4a only while the stock is above its 200-day average | Same | Same |

**HAR forecast** (Corsi 2009): realised variance from daily Parkinson ranges, regressed on the previous 1, 5 and 22-day averages with a rolling 500-day fit. It uses only data up to the entry close and forecasts the variance over the holding period.

## C2-K settings (owner approved the download 2026-10-22; fixed here before any Kronos forecast was made)

- **Code:** `shiyu-coder/Kronos` at commit `67b630e`, MIT licence, unmodified.
- **Weights:** `NeoQuasar/Kronos-small` and `NeoQuasar/Kronos-Tokenizer-base`, MIT, safetensors only. CPU.
- **Input:** the stock's last 400 daily bars up to and including the entry close, with columns open, high, low, close, volume and amount (volume × the mean of open, high, low and close). Timestamps are the session dates. `max_context` is 512.
- **Forecast horizon:** the number of trading sessions from entry to exit.
- **Paths:**
  - Kronos's `predict` averages its sampled paths, which would understate volatility. So the study draws **20 independent paths**, passing the same series 20 times to `predict_batch` with `sample_count = 1`.
  - Settings: `T = 1.0`, `top_p = 0.9`, `top_k = 0` (the repository's defaults), and `torch.manual_seed` equal to the entry date as YYYYMMDD.
- **Forecast volatility:** for each path, the standard deviation of daily log returns of the forecast closes (the first return is measured from the entry close), annualised with √252. The forecast is the **median across the 20 paths**.
- **Ranking:** IV divided by this forecast, in place of IV divided by the HAR forecast. The rest of the C2 rules are unchanged.

## Pass rules

- **Development:** a family passes if all three hold:
  - its mean net return per trade at base costs is positive;
  - the t-statistic is at least 2, with standard errors clustered by entry month;
  - it beats its benchmark by a positive margin with t at least 1.5. For C1 the benchmark is T-bills; for C4, the stock on a risk-adjusted basis (return per unit of drawdown).
- **Holdout (once):** the mean net return is positive at base costs and the sign versus the benchmark is unchanged.
- **C2-K:** adopted only if it beats C2 with HAR in **both** periods.
- **Not part of this study:** anything that passes still needs a separate pre-registered design (sizing, limits, execution) and paper trading before any real money. Families that fail are reported and not tuned.
