# Short-horizon lane, study 2: hourly trend rules on BTC/ETH (run 2026-10-21)

**Pre-registration:** written before any data was downloaded, in the research agent's working folder (`pre_registration.txt`); the rules are restated below.

## Setup

- **Data:** Alpaca 1-hour bars, 2021-01-01 to 2026-10-21 (BTC 14 missing hours, ETH 16, filled flat).
- **Decision basis:** the 50/50 BTC+ETH book, long or cash.
- **Costs:** taker 0.25% + 0.05% slippage = 0.30% per side.
- **Splits:** development 2021-04-09 to 2023-12-31; confirmation 2024; holdout 2025 onward.

**Candidates:**

| id | Rule |
|---|---|
| H0 | Buy and hold |
| H1 | Daily close above its 50-day average |
| H2 | Hourly Donchian breakout: enter on a 20-day high, exit on a 10-day low |
| H3 | EMA 24h above EMA 168h |
| H4 | H3 plus a volatility filter |
| H5 | 7-day momentum, checked daily |

**Rule:** a candidate passes if its development Sharpe beats both H0 and H1 by at least 0.20 and its drawdown is smaller than H0's.

## Development (2021-04 to 2023), book, 0.30% per side

| | CAGR | Sharpe | Max drawdown | Trades/yr | Cost drag/yr |
|---|---|---|---|---|---|
| H0 buy and hold | −3.4% | 0.32 | −78.9% | 0.7 | 0.1% |
| H1 daily 50-day | 9.2% | 0.42 | −59.3% | 21 | 6.3% |
| H2 Donchian | 16.5% | 0.61 | −36.7% | 16.5 | 4.9% |
| H3 EMA | −18.0% | −0.28 | −65.3% | 87 | 26.1% |
| H4 EMA + vol | −18.1% | −0.59 | −60.9% | 82 | 24.7% |
| H5 7-day momentum | −6.4% | 0.04 | −59.7% | 69 | 20.8% |

**Decision: nothing passed.** H2 needed 0.62 and scored 0.605.

## Later periods (book)

| Rule | 2024 Sharpe | 2025+ Sharpe | 2025+ CAGR | 2025+ max drawdown |
|---|---|---|---|---|
| H0 buy and hold | 1.37 | 0.04 | −10.8% | −60.8% |
| H1 daily 50-day | 0.98 | 1.08 | +31.9% | −29.6% |
| H2 (not used for the decision) | 0.89 | 0.40 | | |

**Longer daily check** (Coinbase closes from FRED, 0.30% per side, BTC 2015+ / ETH 2016+), H1 against buy and hold:

| | Sharpe | Max drawdown |
|---|---|---|
| BTC | 1.35 vs 1.07 | −60% vs −84% |
| ETH | 1.28 vs 1.02 | −63% vs −94% |

H1 also won before 2021.

## Verdict

- **No hourly rule is adopted.** The fast rules trade 60–100 times a year and lose 20–30% a year to Alpaca fees.
- **The evidence supports only the once-a-day 50-day-average filter (H1).**
  - It roughly halves drawdowns.
  - It beat buy and hold in the falling 2025–26 period and over 2015–2026 daily data.
  - It trailed buy and hold in the 2024 bull year.
- **Caveat:** about 5.5 years of hourly data, two coins and mostly one market cycle.
- **The crypto lane, if used:** H1 on BTC and ETH, sized as a capped slice of capital.
