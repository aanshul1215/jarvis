# Adjusted-price cleaning for the short-horizon lane. Adopted 2026-10-22

**Problem (research screen, 2026-10-22).** The daily adjusted bars contain jumps that the raw bars do not show.
- Example: NVS −82.4% adjusted against −12.1% raw on 2019-04-09, the Alcon spin-off day.
- Cause: Alpaca adjusted these events as if they were reverse splits. For NVS it multiplied every earlier price by 5 and every earlier volume by 0.2, which matches Alcon's distribution ratio of 1 share per 5.
- Effect: the jump inflates 63-day volatility and drags 6- and 12-month momentum to the bottom of the ranks for up to a year. In a backtest it is booked as a loss or gain.

**Where the rule applies.** In `Market.from_frames` (`shortterm/reversal.py`), the one loader that both the research studies and the live stock-book desk (`desks.StockBookBuilder`) use. It cleans by default.
- The Parquet files stay as the vendor sent them.
- `clean=False` gives the uncleaned arrays that the studies registered before 2026-10-22 were run on.

## The check (`data.adjustment_flags`; `jarvis shortterm-check [--csv FILE]`)

A symbol-day is **flagged** when, compared with the symbol's previous bar, both of these hold:
- |adjusted close-to-close return − raw return| > 15%;
- the raw close ratio is **not** within ±3% of 1/2, 1/3, 2/3, 1/4, 1/5, 1/10, 2, 3, 4, 5 or 10.

## The rule (`data.clean_adjusted`)

1. A flagged day is **spurious** when the adjusted move is the larger one: |ln(1 + r_adj)| > |ln(1 + r_raw)|. On those days the vendor's adjustment made the jump.
2. **On a spurious day, the vendor's factor change is undone.**
   - The symbol's earlier adjusted open, high, low, close and VWAP are multiplied by (1 + r_adj) / (1 + r_raw).
   - Its earlier volumes are multiplied by the change in the vendor's volume factor on that day.
   - The day's adjusted return then equals the raw return. Dividends and real splits before and after the day keep their adjustment.
3. **Every other flagged day keeps the vendor's adjustment.**

**Why not use the raw return on every flagged day.** 142 of the 155 flagged research days are real splits that the vendor adjusted correctly:
- split ratios outside the list: AMZN and GOOGL 20:1, CMG 50:1, BKNG 25:1, ORLY 15:1, and reverse splits such as 1:20 or 1:60;
- listed ratios on days when the stock also moved more than 3%: AAPL 4:1 on a +3.4% day, TSLA 5:1 on a +12.6% day;
- large distributions adjusted correctly, such as IAC's Angi spin-off (+3.7% adjusted, −14.5% raw).

Using raw returns there would add jumps of up to −98% (CMG).

**Why not mark the day missing.** The 6- and 12-month momentum ratios compare prices on either side of the day. A missing day would leave the earlier history on the wrong scale.

## Result on the 2026-10-22 files

Every flagged symbol-day, with both returns: [adjustment_flags_2026-10-22.csv](adjustment_flags_2026-10-22.csv).

| File | Flagged | Spurious (cleaned) |
|---|---|---|
| `daily_*` (research: 1,044 symbols, 2016-01-04 to 2026-10-19) | 155 (125 symbols) | 13 |
| `live_daily_*` (live stock book: 331 symbols, 2025-07-21 to 2026-10-20) | 3: BKNG 25:1 split, KLAC 10:1 split, FDX 2026-06-01 distribution | 0 |

The 13 cleaned days:

| Symbol | Day | Adjusted | Raw | Event |
|---|---|---|---|---|
| AA | 2016-11-01 | −73.3% | −19.9% | Alcoa split into Arconic and the new Alcoa, which took the ticker |
| AMC | 2023-08-23 | +38.3% | −23.1% | The day before its 1:10 reverse split |
| APTV | 2017-12-05 | −71.6% | −14.9% | Delphi Technologies spin-off; Delphi Automotive renamed Aptiv |
| CIVI | 2017-05-01 | −99.1% | −0.3% | — |
| DB | 2017-03-21 | −53.5% | −7.1% | Rights issue |
| DLPH | 2017-12-05 | −81.9% | −45.8% | The ticker passed to the spun-off Delphi Technologies |
| GSK | 2022-07-19 | −20.0% | 0.0% (zero-volume bar) | Haleon demerger and 4-for-5 share consolidation |
| ITUB | 2025-03-19 | +10.6% | −8.8% | — |
| MAC | 2020-04-21 | +34.6% | −3.8% | — |
| NVS | 2019-04-09 | −82.4% | −12.1% | Alcon spin-off (1 per 5) |
| RTX | 2020-04-03 | −71.0% | −41.9% | Raytheon merger; Carrier and Otis spin-offs |
| STLA | 2021-01-14 | +19.5% | −10.1% | — |
| SW | 2016-05-16 | −84.5% | −6.9% | — |

After cleaning, the check finds the same 142 kept days and no spurious ones. The 1,031 symbols without a spurious day are unchanged.

## Limits (stated, not hidden)

- **Spin-off value.** On a spin-off day, the raw return still includes the value of the distributed shares, which a holder did not lose: NVS −12%, RTX −42%.
- **Ticker passed to another company.** When the ticker moved to a different company that day, the raw move compares two companies: DLPH −46%, AA −20%.
- These residual moves are smaller than the vendor's errors (−82%, −71%, −82%, −73%), but they are not true returns.
- **Kept days can also be wrong.** A day the rule keeps can still be wrong in the vendor's data. DD on 2019-06-03 shows +17.8% adjusted and +149% raw (the Corteva spin-off with a 1:3 reverse split). The adjusted move is the smaller one, so it is kept.
- **Not covered; found in the same check:**
  - **Duplicate histories.** Alpaca serves a renamed company's history under both tickers: IAC/PPLI (2,607 identical days, 2016-01 to 2026-06), CHK/EXE, ECA/OVV, SPRU/XL, DD/DWDP and APTV/DLPH.
    - Both IAC and PPLI were in the top-300 universe in 18 months (2017-12 to 2020-08). CHK and EXE were both in for 12 months, DLPH and APTV for 1.
    - So the research books held those companies twice.
    - None of these pairs is in the 2026-09 or 2026-10 universe.
  - **Zero-volume filler bars.** The raw research file has 13,715 flat bars with zero volume across 79 symbols, for example NIO before its 2018 listing, and BMR.
    - They never enter the universe, because they have no dollar volume, but a 6- or 12-month return can reach back to one.
    - The live files have none.
- **Earlier studies.** The studies registered before 2026-10-22 were run on uncleaned data. Their recorded results stand as run.

## DOW and XLRE (2026-10-22)

- **DOW** is missing from `daily_*`. The data API silently left it out of the 100-symbol request (CL … DVA).
  - Reproduced on 2026-10-22, through alpaca-py and through plain HTTP: the page token skips from DOV to DPZ, and no error is returned.
  - Requested alone, or with two other symbols, DOW returns all 2,714 bars.
  - **Fix:** `fetch_bars` now requests once more, together, the symbols that came back empty.
  - **Not fixed:** the research files were not rewritten. DOW's own history also mixes companies: Dow Chemical until 2017-08-31, then flat zero-volume bars (2017-09-01 to 2019-04-01), then Dow Inc. from 2019-04-02.
  - DOW is not in the 2026-09 or 2026-10 universe, so the live desk is unaffected.
- **XLRE** was never in the store's universe (`config/universe.json`, confirmed by the owner on 2026-10-20). That universe uses VNQ for real estate, and so does the sector rotation's sector list.
  - **Back-filled once on 2026-10-22:** 2,716 daily bars (raw and adjusted), 2016-01-04 to 2026-10-21.
  - It is refreshed daily only if it is added to the universe (owner decision).

## Live stock book, 2026-10-22

- **The live files have no spurious day, so the target list does not change.**
  - Decision of 2026-10-19, data to 2026-10-20: 303 names (300 stocks, plus USO, DBC and CPER at 6.67% each).
  - The weights are identical with and without cleaning.
- **For contrast:** using the raw return on every flagged day would have changed 300 weights (KLAC 0.18% → 0.13%, FDX 0.42% → 0.38%, BKNG 0.20% → 0.19%).
- **Monitoring:** the desk's target report now lists any cleaned day under `adjusted_data_fixes`.
