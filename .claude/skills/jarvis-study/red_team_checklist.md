# Red-team checklist

Attack the result. Try to make it fail. Recompute anything you doubt from the raw files. Record every correction, even when it reverses the conclusion.

## Integrity

- **Was the pre-registration written before any return?**
  - Compare its SHA-256 and timestamps with the deviations log.
  - Was any rule chosen after a result (for example the exit rule, the threshold, or the universe)?
- **Were the confirmation and holdout periods used only once?** Did any development result leak into the choice of what to hold out?
- **Is the trial count complete,** including earlier Jarvis studies of the same family? Recompute the deflated Sharpe.

## Look-ahead and survivorship

- **Does any signal use data from after the decision time?** Typical culprits:
  - the day's close used for a same-day trade;
  - a full-day bar used before the day ends;
  - an availability lag not respected;
  - vendor revisions.
- **Is the universe point-in-time?** Are delisted and failed names included, and valued at zero where they failed?
- **Were adjusted prices used where raw prices traded** (stops, strikes, price filters)? Corporate-action errors at spin-offs and ticker reuse belong here.

## Execution realism

- **Fills:**
  - a stop fill at the stop price in a gap;
  - an entry and a stop in the same bar;
  - a bar close used as a fill price.
- **Costs:**
  - Are spreads at the open or close, and for small or volatile stocks, realistic?
  - Rerun with costs doubled and tripled. At what cost does it break even?
- **Does the broker actually allow it?**
  - order types and their cutoffs (market-on-open by 9:28 ET, market-on-close by 3:50 ET);
  - shortability (only easy-to-borrow names; fractional shorts are not allowed);
  - margin and intraday leverage;
  - whole shares versus fractional.
- **Timing:** can the decision really be made and sent in time? For example, a 10:00 ET routine cannot capture a move it measures at the close.

## Robustness

- **By year and by regime:** is the result driven by one year (such as 2017 crypto or 2020), one stock, or the top 5% of trades?
- **Neighbouring parameters:** do they also work, or only the registered one? Report, but do not adopt.
- **Leverage:** does it raise or lower the Sharpe? Compare half Kelly on a shrunk Sharpe with the leverage used.
- **Correlation with the running desks and SPY,** in calm markets and in stress.

## Honesty of the write-up

- Does the summary say what the numbers say?
- Is the +15%-a-month goal assessed plainly?
- What should the owner expect in a typical year and in a bad year?
- Give a 2-year bootstrap range if it is cheap.
