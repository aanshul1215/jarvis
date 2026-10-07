# 16 — News & Event Intelligence (the "Information Intelligence" service)

Research date: 2026-10-01. Basis tags: FETCHED = opened in this session (note: pages were read through a summarising fetch tool, so numbers extracted from long papers carry "medium" unless they appear in the abstract); RECALLED = from memory, not opened; UNVERIFIED = could not confirm.

## 1. Questions asked

1. FinBERT vs modern LLMs for financial sentiment / event extraction: accuracy and cost.
2. How fast is news priced in? Is there tradable drift after news / earnings / filings at retail latency?
3. Value of Form 4, 8-K, 13F and earnings-call signals; novelty and de-duplication.
4. Flaws of the current JARVIS layer and how to rebuild it point-in-time (PIT) correct.
5. What role should the layer play: alpha source, risk filter, or explanation only?

Facts I set out to pin down and the authoritative source for each: model economics (Anthropic pricing page); news feed fields and limits (Alpaca docs); filing timestamps, rate limits, deadlines (SEC.gov); predictive evidence (the original papers on arXiv / NBER / journal sites).

## 2. Findings

### 2.1 FinBERT vs LLMs

**F1. FinBERT is a 3-class sentence classifier fine-tuned on Financial PhraseBank.** The ProsusAI model card states it is BERT further trained on a financial corpus and fine-tuned on Financial PhraseBank (Malo et al. 2014); output is positive/negative/neutral softmax. PhraseBank is short news sentences labelled by annotators for *investor-perceived tone*, not for subsequent returns. Source: https://huggingface.co/ProsusAI/finbert and https://arxiv.org/abs/1908.10063 — FETCHED, high. Implication (my inference): applying it to 10-K/10-Q sections, as JARVIS v1 does, is out-of-domain use; and "tone" is not "event type", "novelty" or "materiality".

**F2. On return prediction from headlines, FinBERT did poorly and large LLMs did well — in one prominent study.** Lopez-Lira & Tang, "Can ChatGPT Forecast Stock Price Movements?" (arXiv 2304.07619, v6 dated Oct 2025). Sample: Oct 2021–May 2024 (deliberately after the GPT training cutoff), 159,137 firm-headline observations, 4,123 US stocks, RavenPack headlines, CRSP/TAQ returns. Long-short daily strategy Sharpe (gross): GPT-4 2.97 (overnight news, enter at open, exit at close), GPT-3.5 1.66, FinBERT −0.33, BERT/GPT-1/GPT-2 negative. Source: https://arxiv.org/html/2304.07619v6 — FETCHED; abstract-level claims high, table numbers medium.

**F3. A second study finds FinBERT respectable but still behind a larger model.** Kirtac & Germano, "Sentiment trading with large language models" (arXiv 2412.19245): 965,375 Refinitiv articles, 6,214 US firms, Jan 2010–Jun 2023; models fine-tuned on 3-day excess returns with a 60/20/20 split. Direction accuracy: OPT 74.4%, BERT 72.5%, FinBERT 72.2%, Loughran-McDonald dictionary 50.1%. Long-short Sharpe after an assumed 10 bps per trade: OPT 3.05, BERT 2.11, FinBERT 2.07, LM 1.23. Source: https://arxiv.org/abs/2412.19245 and /html — FETCHED, medium-high. Caveats I would attach: value-weighted quintile portfolios rebalanced daily with frictionless shorting; a 10 bps flat cost is optimistic for a small account in small caps; Sharpe ratios of 2–3 from academic daily long-short backtests have historically not survived implementation.

**F4. On pure classification benchmarks the picture is mixed; general LLMs are not uniformly better than fine-tuned small models.** Li et al. (EMNLP 2023 Industry, arXiv 2305.05862) evaluated ChatGPT/GPT-4 on eight financial benchmarks across five task types and report both strengths and limitations versus fine-tuned domain models (abstract only; no numbers extracted). Rodriguez Inserte et al. (arXiv 2401.14777) report that small (<1.5B parameter) fine-tuned LLMs reach performance comparable to much larger ones. Source: both abstracts FETCHED, medium. A search snippet claimed "FinBERT 0.85 vs GPT-4 0.71 accuracy on PhraseBank"; I could not trace that to a table I opened — UNVERIFIED, low. Honest summary: FinBERT is adequate at what it was trained for (sentence tone); the LLM advantage is in tasks FinBERT cannot do at all — event typing, entity/relevance resolution, "is this new?", "good or bad for *this* ticker" — and in return-relevance of the score (F2).

**F5. Cost today is not the binding constraint.** Anthropic pricing page (FETCHED, high): Claude Haiku 4.5 $1 / $5 per million input/output tokens; Batch API −50% ($0.50 / $2.50); cache reads at 0.1x input; Sonnet 5 $2 / $10; Opus 5.5 $4 / $20. My arithmetic: a headline + short instruction ≈ 300 input / 60 output tokens ≈ $0.0006 real-time on Haiku 4.5, ≈ $0.0003 batched. 200 items/day ≈ $2–4/month; a 100k-headline historical backfill ≈ $30–60 batched. FinBERT runs locally on CPU at zero marginal cost. So a tiered design (free local filter → cheap LLM only on survivors) fits a "close to zero" budget; an 18-agent debate on every headline does not.

**F6. Look-ahead bias makes historical LLM backtests untrustworthy.** Sarkar & Vafa (ICML 2025; https://icml.cc/virtual/2025/48685, FETCHED abstract, high) show pretrained LMs leak future information in earnings-call risk prediction and election prediction, and that prompting-based fixes are unreliable; the remedy is models whose pretraining data ends before the analysis period. Glasserman & Lin (arXiv 2309.17322, FETCHED abstract, high) find, for GPT headline sentiment, that a "distraction effect" (the model's general knowledge of the company contaminating its reading of the headline) matters more than look-ahead in-sample, and anonymising company names *improves* in-sample performance. He, Lv, Manela & Wu (arXiv 2502.21206, FETCHED abstract, high) trained chronologically consistent models and found look-ahead bias "modest" for next-day news prediction. Net: bias magnitude is debated, but any Claude model scored over text from before its training cutoff cannot be cleanly validated. Only forward (paper-trading) evidence, or evidence from time-consistent/local models, counts.

### 2.2 How fast is news priced in?

**F7. Most of the reaction is immediate and non-tradable; residual drift is short, small-cap and shrinking.** Lopez-Lira & Tang (FETCHED): GPT-4 "predicts" the initial reaction with ~90% portfolio-day hit rate, but the authors label that reaction non-tradable. The tradable part is drift over roughly 1–2 days; for intraday news, entry must be within ~15 minutes. Predictability is concentrated in small stocks and negative news (which requires shorting small caps). With transaction costs the strategy remains positive at 5–10 bps round-trip and becomes unprofitable around 20 bps (medium — table values via summariser). Sharpe by period: 6.54 (2021 Q4), 3.68 (2022), 2.33 (2023), 1.22 (Jan–May 2024); the abstract itself states returns decline as LLM adoption rises (high). That is a 2024 endpoint; in October 2026 the reasonable prior is that it has decayed further — UNVERIFIED.

**F8. Earnings drift is largely gone for liquid stocks.** Martineau, "Rest in Peace Post-Earnings Announcement Drift", Critical Finance Review 11(3-4), 2022: prices now reflect earnings surprises on the announcement date; PEAD non-existent for large stocks since 2006, and gone only recently for microcaps. Source: https://ideas.repec.org/a/now/jnlcfr/104.00000122.html — FETCHED abstract, high (full PDF would not parse). A UCLA Anderson Review piece titled "Is post-earnings announcement drift a thing again?" appeared in search results, so the finding is contested; I did not open it — UNVERIFIED.

**F9. Classic text-return evidence says the delay is in small, volatile stocks.** Ke, Kelly & Xiu, "Predicting Returns with Text Data" (NBER w26186): on Dow Jones Newswires, news is assimilated with a delay that is worse for smaller and more volatile firms. Source: https://www.nber.org/papers/w26186 — FETCHED page (method only); the delay statement came from a search snippet of the abstract — medium.

**Retail-latency reading (my inference, medium):** the owner's free feed is Alpaca's Benzinga-sourced news (REST: 100 req/min, history back to 2015, `created_at`/`updated_at` timestamps; WebSocket stream available) plus the free market data plan (IEX only, 30 WebSocket symbols, 200 calls/min) — https://docs.alpaca.markets/reference/news-3, https://docs.alpaca.markets/docs/historical-news-data, https://alpaca.markets/data, all FETCHED, high (whether news access is restricted by plan was not stated — UNVERIFIED). The documented edge needs (a) a premium low-latency feed in the papers (RavenPack / Refinitiv / DJ Newswires), (b) long-short baskets of hundreds of names, (c) shorting small caps, (d) sub-20 bps round-trip costs, (e) daily turnover near 190%. A $1k–$10k account with a free feed satisfies none of these. Daily open-to-close round trips also raise day-trading account-rule questions (owned by another research topic — UNVERIFIED here).

### 2.3 Filings and slower signals

**F10. Form 4 (insider trades): real but slow and selective.** Cohen, Malloy & Pomorski, "Decoding Inside Information", Journal of Finance 67(3), 2012: after removing "routine" (calendar-repeating) insider trades, a portfolio following "opportunistic" insiders earned value-weighted abnormal returns of 82 bps/month; routine trades ≈ 0. Source: search snippet of abstract (Harvard DASH / EconBiz) — RECALLED + snippet, medium-high. This is a 1986–2007-era sample, gross of costs; post-publication decay is UNVERIFIED. Filing deadline: two business days after the transaction (sec.gov rule releases via search snippet; also in the owner's v1 document) — medium-high. Horizon is weeks to months, which suits a small account far better than intraday news.

**F11. 10-K/10-Q language changes ("Lazy Prices").** Cohen, Malloy & Nguyen (NBER w25084; Journal of Finance): shorting "changers" and buying "non-changers" earned up to 188 bps/month alpha, 1995–2014; most informative changes are in risk factors, litigation and CEO/CFO language; the market does not react at filing, returns arrive over following months. Source: https://www.nber.org/papers/w25084 — FETCHED, high. Important for JARVIS: the signal is the *diff against last year's filing*, not the FinBERT tone level v1 computed. "Up to" denotes the best specification; out-of-sample persistence after 2014 UNVERIFIED.

**F12. 13F is stale and long-only.** SEC 13F FAQ (FETCHED, high): due within 45 days of quarter-end; only long positions in 13(f) securities; shorts are not reported or netted; confidential treatment can delay disclosure by up to a year. Usable only as slow "crowding/ownership" context, never as a timing signal — which matches the v1 document's own description.

**F13. 8-K.** Deadline four business days after the triggering event (SEC Release 33-8400, search snippet — medium-high). I did not find and open a quantitative paper on 8-K item-level drift in this session — evidence on 8-K alpha is UNVERIFIED. Their uncontested value is as a timestamped, typed event stream (Item 2.02 results, 5.02 officer departure, 4.02 non-reliance, 1.01 agreements) for risk gating and explanation.

**F14. Earnings calls.** No paper opened on call-text alpha in this session — UNVERIFIED. Note Sarkar & Vafa found look-ahead leakage specifically in an earnings-call application, so LLM-on-transcript backtests deserve extra suspicion. Free, timely transcripts are also a data-access problem at zero budget (UNVERIFIED).

**F15. Novelty / staleness matters.** Tetlock, "All the News That's Fit to Reprint: Do Investors React to Stale Information?", RFS 24(5), 2011, pp. 1481–1512 (citation confirmed via the author's CV in search; abstract not opened — RECALLED, medium): staleness is measured as textual similarity to recent stories about the same firm; reactions to stale news partially reverse. Design consequence: de-duplication is not just hygiene — a repeated story should be *down-weighted or treated as a reversal risk*, and the first-seen timestamp of a story cluster is the event time.

### 2.4 Point-in-time infrastructure facts

**F16. EDGAR gives free, keyless, near-real-time PIT data.** data.sec.gov submissions JSON updates with typically <1 s delay; XBRL companyfacts/frames <1 min; no API key. Fair-access limit 10 requests/second with a declared User-Agent. Sources: https://www.sec.gov/search-filings/edgar-application-programming-interfaces and https://www.sec.gov/about/webmaster-frequently-asked-questions — FETCHED, high. The submissions feed carries an acceptance timestamp per filing (RECALLED, high) — this, not the period-of-report or filing date, is the correct knowledge time.

## 3. What this means for the JARVIS documents

- **"Wrap current JARVIS as the Information Intelligence service rather than rewriting it" (v3 build step 2; v2 section 2) — contradicted.** The context file establishes there is no deduplication, RAG store or ticker mapping in the published Space, the SEC/social features reach the LLM as zeros, and the dataset is one ticker over ~123 days. There is nothing PIT-correct to wrap. Only the idea list survives.
- **"News & Event Agent: Existing JARVIS + FinBERT/RAG" (v3 agent table) — weakened.** FinBERT tone is the weakest performer in F2 and merely adequate in F3; it cannot do event typing, novelty or relevance. Keep it only as a free first-pass filter.
- **"News impact model" inside the Model Ensemble (v1 layer C, v3) — weakened as an alpha source.** F7–F9: documented drift is short-lived, small-cap, short-side, cost-sensitive and decaying, and was measured on premium feeds. The examples in all three docs treat news as a *veto/neutral check* ("news is neutral") — that modest usage is the part the evidence supports.
- **"Form 4 insider signal and 13F long-horizon positioning" (v1 page 2) — partially supported.** Form 4 has peer-reviewed support but only after routine/opportunistic filtering and at multi-week horizons (F10). 13F description as "slower positioning signal" is accurate (F12).
- **"Event time vs ingestion time", "point-in-time features" (v2, v3 step 1) — strongly supported**, and achievable for free via EDGAR acceptance timestamps and Alpaca `created_at`/`updated_at` (F16).
- **"Removes duplicate stories" (v3) — supported and should go further**: novelty should be a scored feature (F15).
- **Bull/Bear LLM agents reasoning over news on historical data — a hidden leakage path** (F6). Any backtest in which a Claude agent reads pre-cutoff news is not out-of-sample.
- **Multi-agent LLM use on every candidate — conflicts with the near-zero budget** unless tiered (F5).
- **v1 feature design flaw repeated in the vision:** daily "news sentiment with decay" and "event-study CAR" features. CAR over a window after the filing uses post-event returns; if joined to the filing date it is direct leakage, the same class of bug as `return_pct_t1`.

## 4. Recommended changes

1. **Rebuild, do not wrap.** New service with one append-only `events` table: `event_id, entity_id (CIK + ticker as-of), event_type, source, source_published_at, first_seen_at (our clock), available_at = max(published, first_seen) + safety lag, cluster_id, novelty_score, payload_hash, extractor_version`. Features may join only on `available_at <= decision_time`. Never overwrite; revisions (`updated_at` changes) are new rows.
2. **Start archiving now.** Free historical news is thin and LLM backtests are contaminated, so the only clean dataset is the one JARVIS records itself going forward. Log every raw item with first-seen time from day one.
3. **Three-tier extraction.** Tier 0 deterministic: EDGAR form type, 8-K item numbers, Form 4 transaction codes, earnings calendar. Tier 1 local and free: embedding similarity for de-dup/novelty clustering, FinBERT tone as a coarse filter. Tier 2 Claude Haiku-class, batched and cached, only for novel, held-or-candidate tickers: structured JSON (event type, direction for this ticker, materiality, is-it-new, confidence, quoted evidence span). Hard monthly token cap.
4. **Primary role = risk filter + explanation; alpha only on probation.** Deterministic gates fed by this layer: no new entries across a scheduled earnings date unless the strategy is explicitly an earnings strategy; block or size-down after 8-K items such as 4.02 or 5.02; flag halts, offerings and unusual news volume; mark stale-news spikes as reversal risk. Explanations in the ledger cite event IDs.
5. **Alpha candidates, in order of fit to a small slow account:** (a) opportunistic Form 4 buy clusters, multi-week holding; (b) 10-K/10-Q year-over-year text-diff as a long-only avoid list; (c) LLM headline score on liquid names as a *shadow* signal logged for at least 6–12 months before any capital. Each must pass walk-forward testing net of realistic spread and with entry at the next tradable price after `available_at`.
6. **Leakage controls for LLM signals:** validate only on data after the model's cutoff; pin the model version in the ledger; anonymise ticker/company names in sentiment prompts as an A/B arm (Glasserman & Lin); re-validate on every model upgrade.
7. **Drop** social-media sentiment (Reddit/Electrek) from the first build: no evidence gathered here supports it, it is the main pump-and-dump surface, and it adds scraping fragility. Revisit later as a *manipulation-risk* input, not a buy signal.
8. **Remove event-study CAR as a feature**; keep it only as an offline evaluation label.

## 5. Open uncertainties

- Whether the Lopez-Lira drift survives at all after May 2024; no post-2024 evidence opened.
- Martineau's PEAD result is contested by later work I did not open.
- No opened evidence on 8-K item-level drift or earnings-call text alpha.
- Post-publication decay of the opportunistic-insider and Lazy Prices effects.
- Tetlock (2011) details and Cohen-Malloy-Pomorski numbers come from snippets/memory, not full text.
- Whether Alpaca news (REST and stream) is fully available on the free plan and its true latency vs wire services.
- Free, licensed source of earnings dates and transcripts.
- Table-level numbers from long papers were extracted by a summarising fetch tool and should be spot-checked against the PDFs before being quoted in a final design.
- The FinBERT-vs-GPT-4 PhraseBank accuracy figures (0.85 vs 0.71) are unverified.

## 6. Source list

- Lopez-Lira & Tang — https://arxiv.org/abs/2304.07619 , https://arxiv.org/html/2304.07619v6 (FETCHED)
- Kirtac & Germano — https://arxiv.org/abs/2412.19245 (FETCHED)
- Glasserman & Lin — https://arxiv.org/abs/2309.17322 (FETCHED)
- Sarkar & Vafa — https://icml.cc/virtual/2025/48685 (FETCHED abstract)
- He, Lv, Manela, Wu — https://arxiv.org/abs/2502.21206 (FETCHED)
- Araci, FinBERT — https://arxiv.org/abs/1908.10063 ; https://huggingface.co/ProsusAI/finbert (FETCHED)
- Li et al. — https://arxiv.org/abs/2305.05862 (FETCHED abstract)
- Rodriguez Inserte et al. — https://arxiv.org/abs/2401.14777 (FETCHED abstract)
- Martineau — https://ideas.repec.org/a/now/jnlcfr/104.00000122.html (FETCHED abstract)
- Ke, Kelly, Xiu — https://www.nber.org/papers/w26186 (FETCHED)
- Cohen, Malloy, Nguyen — https://www.nber.org/papers/w25084 (FETCHED)
- Cohen, Malloy, Pomorski — https://dash.harvard.edu/entities/publication/73120379-15cc-6bd4-e053-0100007fdf3b (search snippet only)
- Tetlock 2011 — https://academic.oup.com/rfs/issue/24/5 (not opened; RECALLED)
- SEC EDGAR APIs — https://www.sec.gov/search-filings/edgar-application-programming-interfaces (FETCHED)
- SEC fair access — https://www.sec.gov/about/webmaster-frequently-asked-questions (FETCHED)
- SEC 13F FAQ — https://www.sec.gov/divisions/investment/13ffaq (FETCHED)
- SEC 8-K rule release — https://www.sec.gov/files/rules/final/33-8400.pdf (search snippet)
- Alpaca news — https://docs.alpaca.markets/reference/news-3 , https://docs.alpaca.markets/docs/historical-news-data , https://docs.alpaca.markets/docs/streaming-real-time-news , https://alpaca.markets/data (FETCHED)
- Anthropic pricing — https://platform.claude.com/docs/en/about-claude/pricing (FETCHED)


## Independent verification (2026-10-01)

**Confirmed (opened primary source):**
- Anthropic pricing: Haiku 4.5 $1/$5, batch $0.50/$2.50, Sonnet 5 $2/$10 (introductory price made permanent; no Sept-1 rise), Opus 5.5 $4/$20, standard cache read 0.1x (Opus 5.5 is 0.05x). https://platform.claude.com/docs/en/about-claude/pricing
- Lopez-Lira & Tang: v6 revised 28 Oct 2025; Oct 2021-May 2024; 159,137 observations; 4,123 firms; Sharpe GPT-4 2.97, GPT-3.5 1.66, FinBERT -0.33 (overnight-news, open-to-close daily strategy); subperiod Sharpe 6.54/3.68/2.33/1.22; profitable at 5-10 bps round trip, unprofitable at 20 bps. https://arxiv.org/html/2304.07619v6
- Kirtac & Germano: 965,375 articles, Jan 2010-Jun 2023; accuracy 74.4/72.5/72.2/50.1; Sharpe 3.05/2.11/2.07/1.23. https://arxiv.org/abs/2412.19245
- Martineau (CFR 11(3-4), 2022, pp. 613-646): PEAD gone for large caps since ~2006, recently for microcaps. https://ideas.repec.org/a/now/jnlcfr/104.00000122.html
- EDGAR: no API key; submissions API <1 s delay, XBRL <1 min; 10 req/s with declared User-Agent. https://www.sec.gov/search-filings/edgar-application-programming-interfaces , https://www.sec.gov/about/webmaster-frequently-asked-questions
- Deadlines: 8-K 4 business days, Form 4 2 business days, 13F 45 days (a petition to shorten 13F to 2 business days exists; not a rule). https://governance.weil.com/wp-content/uploads/2025/09/2026-SEC-Filing-Calendar-Deadlines.pdf

**Corrected / weakened:**
- Alpaca news on the free plan is NOT established. The market-data plan page (https://docs.alpaca.markets/docs/about-market-data-api) does not list news at all, and the historical-news page says only Benzinga-sourced, back to 2015, ~130+ articles/day, with no plan terms. The "100 req/min" REST limit was not reproduced. Also, free-plan historical SIP data is delayed 15 minutes, which is incompatible with the "enter within 15 minutes" intraday idea. Treat free Alpaca news as unconfirmed until a key is tested.
- Kirtac & Germano "10 bps cost" is not stated in the abstract-level content; treat as unverified, and the Sharpe ratios as gross-ish academic figures.
- The Lopez-Lira Sharpe figures are for a daily open-to-close, overnight-news long-short basket; the whole-sample 2.97 is dominated by 2021-22 (latest period 1.22). Do not cite 2.97 as an expected figure.
- EDGAR: the API <1 s figure is API-side; documents on the sec.gov website appear in about 1-3 minutes after acceptance. Use a safety lag of at least a few minutes in available_at.

**Unverifiable in this pass:** Cohen-Malloy-Pomorski 82 bps/month, Lazy Prices 188 bps/month, Tetlock 2011, Ke-Kelly-Xiu delay claim, Sarkar-Vafa/Glasserman-Lin/He et al. details, FinBERT-vs-GPT-4 PhraseBank 0.85/0.71 (still unverified), post-2024 decay of any effect.

**Missed considerations (owner constraints):** (1) Account under $25k: pattern-day-trader rules limit round trips in a margin account, and shorting small caps needs margin plus borrow; cash accounts face settlement limits. Daily open-to-close news strategies are therefore effectively out. Verify current FINRA/broker rules before design. (2) Claude API usage is billed separately from any Claude subscription; the "near-zero" budget needs a hard spend cap in the console. (3) Newer Claude tokenizers produce ~30% more tokens than the older ones, so the brief's 300-token item estimate should be re-measured with the token counting endpoint. (4) Model-pinning matters: Claude models are being retired on a schedule, which breaks the "pin model version in the ledger" plan for long shadow periods.
