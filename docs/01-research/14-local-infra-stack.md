# 14 — Local infrastructure stack: what a solo developer on a Windows 11 laptop should actually run

Research date: 2026-10-01. Every finding is tagged FETCHED (opened in this session) or RECALLED (from memory, not re-checked) with a confidence level. Sizing and "burden" judgements that are my own reasoning are labelled ESTIMATE.

## 1. Questions asked

1. What is the real operational burden of each proposed component (Docker Compose, Redis Streams/NATS, Redis, PostgreSQL+TimescaleDB, Parquet+MinIO, MLflow, FastAPI, React/Next.js, Grafana, OpenTelemetry+Prometheus, Feast) for one person on Windows 11? Which are premature?
2. What leaner alternatives exist, and at what point does each heavy component become justified?
3. Is Feast needed, or do disciplined as-of joins give point-in-time correctness? What is Feast's current status?
4. How reliable is a laptop for 24/7 crypto trading versus a small VPS, and what does a VPS cost?
5. What phase-1 stack and upgrade path, with explicit triggers?

Facts I decided I needed before searching, and the authoritative source for each: project status and licences (official GitHub repos and licence pages); concurrency limits of SQLite and DuckDB (official docs); as-of join semantics (DuckDB and Polars docs); Feast's mechanism (Feast docs); WSL2/Docker Desktop behaviour (Microsoft Learn, Docker docs); Windows sleep and update behaviour (Microsoft Learn); VPS prices (provider pricing pages); broker-side order types (Alpaca docs); feed behaviour on disconnect (Coinbase docs).

## 2. Findings

### 2.1 Component status and facts

**F1. MinIO community edition is dead.** The `minio/minio` repository was archived by its owner on 25 April 2026 and is read-only. The README says the project is no longer maintained, that the community edition is distributed as source only with no new pre-compiled binaries, and points users to the vendor's "AIStor" products. Source: https://github.com/minio/minio — FETCHED — high confidence.
The v3 document's "Parquet + local/MinIO object store" therefore names an unmaintained component. On one machine an object store adds nothing over a directory of Parquet files anyway.

**F2. Feast is alive and actively released, but it is a join-and-serve layer, not a feature computer.** Latest release v0.66.0 on 21 August 2026, roughly monthly releases through 2026, Apache-2.0, about 7.3k stars. Source: https://github.com/feast-dev/feast and https://github.com/feast-dev/feast/releases — FETCHED — high. Still pre-1.0 (version 0.x), so API churn is a live risk — inference from the version number, medium.
Feast's point-in-time join takes an "entity dataframe" of (entity id, timestamp) rows and, for each, scans backwards from that timestamp up to a TTL to find the latest feature row. Feast only joins features that already exist in a data source; it does not compute them. Source: https://docs.feast.dev/getting-started/concepts/point-in-time-joins — FETCHED — high.
Feast can run with no servers (local provider, file registry, SQLite online store, file/DuckDB offline store), but requires `feast apply` on every definition change and a regularly scheduled `feast materialize-incremental` to keep the online store fresh. Sources: https://docs.feast.dev/getting-started/quickstart and https://docs.feast.dev/reference/offline-stores/duckdb — FETCHED — high.

**F3. As-of joins are a built-in primitive in the lean tools.** DuckDB supports `ASOF JOIN` and `ASOF LEFT JOIN` with any of `>=, >, <=, <` as the inequality plus equality conditions for the key (e.g. symbol). Source: https://duckdb.org/docs/current/sql/query_syntax/from.html — FETCHED — high. Polars `join_asof` offers backward/forward/nearest strategies, a `by` grouping key, a `tolerance` (equivalent to Feast's TTL) and `allow_exact_matches` (set false for a strict "known strictly before" rule). Source: https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.join_asof.html — FETCHED — high.
So the exact operation Feast performs is one SQL clause or one function call.

**F4. DuckDB is single-writer-process.** One process may read and write; many processes may read only if all open read-only. Multi-process writing exists only through a remote protocol the docs describe as beta. Source: https://duckdb.org/docs/current/connect/concurrency.html — FETCHED — high. Consequence: DuckDB is the research/analytics engine over Parquet, not the live system of record shared by several services.

**F5. SQLite in WAL mode allows concurrent readers with one writer at a time, same host only, not on a network filesystem.** Source: https://www.sqlite.org/wal.html — FETCHED — high. That is sufficient for a ledger written by one trading process and read by a dashboard.

**F6. Redis Streams gives at-least-once delivery only when consumer groups, explicit acknowledgement, reclaiming of abandoned messages and append-only-file persistence are all configured correctly;** duplicates are possible and consumers must be idempotent. Source: https://redis.io/docs/latest/develop/data-types/streams/ — FETCHED — high (the fetched summary also mentioned newer idempotency commands in Redis 8.x; I did not verify those individually — medium).
Redis 8.0+ is tri-licensed RSALv2 / SSPLv1 / AGPLv3; versions up to 7.2 were BSD. Source: https://redis.io/legal/licenses/ — FETCHED — high. Irrelevant for private personal use, but it is no longer the simple BSD project the docs may assume.

**F7. NATS core does not persist: at-most-once, no replay.** Persistence and at-least-once need JetStream. Source: https://docs.nats.io/nats-concepts/jetstream — FETCHED — high. So "Redis Streams or NATS" is not a like-for-like choice; plain NATS would silently drop events while a consumer is down.

**F8. MLflow needs no server for a solo user.** SQLite is now the default backend (`sqlite:///mlflow.db`); the plain file store is in maintenance mode; the model registry requires a database-backed store, which SQLite satisfies. Source: https://mlflow.org/docs/latest/self-hosting/architecture/backend-store/ — FETCHED — high.

**F9. TimescaleDB** is distributed and documented primarily via Docker, including for Windows; the README advertises hypertables, columnstore compression and continuous aggregates. Source: https://github.com/timescale/timescaledb — FETCHED — medium (the page did not show the latest version, and did not break down which features sit under the Apache licence versus the vendor's own licence; that split is RECALLED as existing but unverified today).

**F10. Docker Desktop on Windows** requires 8 GB system RAM minimum, the WSL2 backend, and Windows 11 23H2 or later; it is free for personal use. Source: https://docs.docker.com/desktop/setup/install/windows-install/ — FETCHED — high.
WSL2 by default takes up to 50% of host RAM, and has idle timeouts (VM idle timeout 60 s, distro instance idle timeout 15 s by default) that are configurable in `.wslconfig`. Source: https://learn.microsoft.com/en-us/windows/wsl/wsl-config — FETCHED — high. Docker Desktop starts when a user logs in, not at boot as a system service — RECALLED — medium; this matters after an unattended reboot (see F12).

**F11. Streamlit** runs as a Python server with a websocket to the browser; no JavaScript build chain. Source: https://docs.streamlit.io/develop/concepts/architecture/architecture — FETCHED — high. Its rerun-the-script-on-interaction model (RECALLED — high) makes it fine for a read-only personal dashboard and poor for hosting trading logic.

### 2.2 Laptop reliability

**F12. Windows will restart itself for updates.** Automatic restarts happen outside "active hours"; the maximum active-hours window is 18 hours, so at least 6 hours a day are always eligible. Several of the older policies that delay or deadline restarts are marked legacy and not applicable to Windows 11. Source: https://learn.microsoft.com/en-us/windows/deployment/update/waas-restart — FETCHED — high. A 24/7 crypto process on Windows 11 must therefore be designed to be killed and restarted without supervision at least monthly.

**F13. Modern Standby.** On laptops using the S0 low-power idle model, closing the lid or idling into sleep lets software run only in short controlled bursts, and desktop applications resume only when the screen comes back on. The power model cannot be switched to classic S3 sleep without reinstalling the OS. Source: https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/modern-standby (page dated 2020, written for Windows 10) — FETCHED — medium for Windows 11 specifics. A sleeping laptop is a stopped trading system; sleep, hibernate and lid-close action must all be disabled, and that still leaves battery wear, heat, Wi-Fi drops and home ISP/power outages (ESTIMATE, no authoritative statistics found — see Open uncertainties).

**F14. Feeds are lossy even when the machine is fine.** Coinbase's Advanced Trade WebSocket documentation says a connection is dropped if no subscribe arrives within 5 seconds, that messages can be dropped despite TCP, and that clients must detect sequence gaps. Source: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-overview — FETCHED — high. Gap detection and resync are required on any host.

**F15. Broker-side protective orders for crypto are limited at Alpaca.** Crypto supports market, limit and stop-limit orders with GTC or IOC time-in-force; bracket/OCO are not listed for crypto. For equities, bracket/OCO/OTO/trailing-stop exist but do not work in extended hours. Sources: https://docs.alpaca.markets/docs/crypto-orders and https://docs.alpaca.markets/docs/orders-at-alpaca — FETCHED — high for the listed order types; whether the resting stop-limit is held on the broker's servers is not stated explicitly (medium, but a GTC order by definition rests at the broker).
Implication: v2/v3's "Position Manager recomputes thesis and exits early" lives entirely on the laptop. If the laptop is down, the only protection is a resting stop-limit, which can fail to fill in a gap.

### 2.3 VPS prices (all FETCHED from provider pages today)

| Provider / plan | Spec | Price | Source | Confidence |
|---|---|---|---|---|
| DigitalOcean Basic | 1 GB / 1 vCPU / 25 GB | $6/mo | https://www.digitalocean.com/pricing/droplets | high |
| DigitalOcean Basic | 2 GB / 1 vCPU / 50 GB | $12/mo | same | high |
| DigitalOcean Basic | 4 GB / 2 vCPU / 80 GB | $24/mo | same | high |
| AWS Lightsail | 0.5 GB / 2 vCPU / 20 GB, IPv4 | $5/mo | https://aws.amazon.com/lightsail/pricing/ | high |
| Hetzner CPX11 (US) | 2 vCPU / 2 GB / 40 GB | $20.49/mo since 15 Jun 2026 (was $6.99) | https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/ | high |
| Hetzner CPX21 (US) | 3 vCPU / 4 GB / 80 GB | $37.49/mo (was $13.99) | same | high |
| Hetzner CX23 (EU only) | cheapest EU shared | $6.49/mo (was $4.99) | same | high |
| Oracle Always Free | Arm A1: page states 2 OCPU / 12 GB total; AMD micro: 1/8 OCPU / 1 GB x2 | $0, but idle instances are reclaimed if CPU, network (and memory on A1) all stay under 20% for 7 days | https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm | medium (the A1 allowance I recalled was 4 OCPU / 24 GB; the page fetched today shows half that — treat as changed) |

Notable: Hetzner, the usual "cheap VPS" recommendation, roughly tripled its US shared-plan prices in June 2026. Old blog advice on this is stale. A lean live-trading process (one Python process plus SQLite, no Docker) fits in 1-2 GB (ESTIMATE), i.e. $6-12/month. The full proposed Compose stack (Postgres, Redis, MinIO, MLflow, Grafana, Prometheus, an OpenTelemetry collector, Next.js, FastAPI) would need roughly 4-8 GB (ESTIMATE), i.e. $24-48/month — which conflicts with the owner's near-zero budget. Stack leanness is what makes the VPS affordable.

### 2.4 Operational burden per component (ESTIMATE, grounded in the facts above)

| Component | Burden for a solo dev on Windows 11 | Verdict for phase 1 |
|---|---|---|
| Docker Compose (via Docker Desktop/WSL2) | Medium. 8 GB RAM floor, WSL2 takes up to half of RAM, starts on login not boot, another layer between the trading process and the network. | Defer. Use a plain Python virtual environment with a lockfile. Add one Dockerfile when moving to a Linux VPS. |
| Redis Streams / NATS event bus | Medium-high. Correct at-least-once needs consumer groups, acks, reclaim, AOF and idempotent consumers (F6); NATS core loses messages (F7). | Premature. With one process there is nothing to bus. Use in-process `asyncio` queues and write every event to an append-only table. |
| Redis hot state | Low to run, but it is a second source of truth to reconcile after every crash. | Premature. Hold state in process memory, rebuilt on start from the ledger plus the broker's positions endpoint. |
| PostgreSQL + TimescaleDB | Medium. Server, backups, upgrades, extension versions. Timescale's benefits (compression, continuous aggregates) pay off at hundreds of millions of rows. | Premature. SQLite (WAL) for the ledger; Parquet for time series. |
| Parquet + MinIO | Parquet: near zero. MinIO: unmaintained (F1). | Keep Parquet in plain folders. Drop MinIO permanently. |
| MLflow | Low if used as a library with the SQLite backend (F8); medium if run as a tracking server. | Optional, library mode only, and only once real experiments start. A run table in SQLite plus git commit hashes is a sufficient start. |
| FastAPI | Low. | Defer until something other than the trading process needs an API. |
| React/Next.js | High for a non-frontend solo dev: Node toolchain, build, auth, state. | Premature. There are no outside investors (owner constraint), so one Streamlit page suffices. |
| Grafana + Prometheus + OpenTelemetry | Medium: three or four more services to watch a single process. | Premature. Structured JSON logs, a heartbeat row, and a dead-man's-switch alert. |
| Feast | Medium: registry, definitions, scheduled materialisation, a pre-1.0 API. | Not needed (section 2.5). |
| LangGraph | Out of scope here (covered by other topics). | — |

### 2.5 Is Feast needed?

No. Feast solves two problems: (a) point-in-time joins across many teams' feature tables, and (b) keeping a low-latency online store consistent with the offline store. JARVIS has one developer and one process, so (b) does not exist if the same feature function is called in backtest and live. Problem (a) is one `ASOF JOIN` (F3).

More important: Feast would not have prevented JARVIS v1's actual defect. The leak was a feature column (`return_pct_t1`) that was itself the label. Feast joins whatever timestamps it is given; it cannot tell that a row stamped "today" contains tomorrow's return (F2: it does not compute or inspect features). The Architecture document's claim that Feast is "useful for preventing future information leaking into training" is true only for join-time leakage and overstated for the kind of leakage this project has actually suffered.

What does prevent it, at zero infrastructure cost:
- Every stored record carries two timestamps: `event_time` (when it happened) and `knowledge_time` (when JARVIS could first have known it — bar close, filing acceptance time, article publish time plus ingestion lag). The v3 build order's step 1 already asks for "event time vs ingestion time"; this supports and sharpens it.
- Features are joined only with a backward as-of join on `knowledge_time <= decision_time` (strict `<` for bar data), with a tolerance.
- Labels are built in a separate module from strictly later data and are never stored in the feature table.
- Automated tests: (i) truncate the input at time T and assert that features at T are unchanged when later data is appended; (ii) a shuffled-label or future-shifted "canary" feature must show no predictive power; (iii) any out-of-sample correlation above a sanity threshold fails the build.
- One code path for features in backtest, paper and live.

## 3. What this means for the JARVIS design documents

- **v3 section 3, "Docker Compose on dedicated laptop" (Runtime row): weakened.** A Windows 11 laptop is acceptable for research, backtests and paper/shadow trading. For unattended 24/7 crypto with real money it has structural failure modes the document does not mention: forced update restarts (F12), sleep (F13), Docker Desktop not auto-starting without a login (F10, recalled), home network and power. The doc's own scale path ("Kubernetes only if needed") skips the realistic next step, which is a $6-12/month Linux VPS.
- **v3 "Event bus: Redis Streams or NATS": weakened.** Not equivalent options (F7), and unnecessary while there is one process. The stated scale path "Kafka when event volume justifies it" will not be reached at $1k-$10k capital on free data.
- **v3 "Hot state: Redis" and "Redis cluster": weakened** — premature; adds a reconciliation problem.
- **v3 "System of record: PostgreSQL + TimescaleDB": partly supported.** The idea of one relational system of record for trades, signals and risk decisions is right. The specific technology is heavier than the data. ESTIMATE: 1-minute bars for 500 symbols is about 49 million rows a year (390 bars x 252 days x 500) and compresses to a few GB of Parquet at most; daily bars are trivial.
- **v3 "Cold data: Parquet + local/MinIO": Parquet supported, MinIO contradicted** by its archival (F1).
- **Architecture doc, research anchor "Feast": weakened** (section 2.5). The goal is right; the tool is not required and would not have caught the v1 leak.
- **Architecture doc, "MLflow + OpenTelemetry ... professional auditability": partly supported.** Auditability comes from the ledger design (inputs snapshot, model version, decision, order, fill), which the docs specify well. MLflow is fine in library mode (F8). OpenTelemetry is tracing for distributed systems; with one process it adds a collector and a backend for no benefit.
- **v3 "API / dashboard: FastAPI + React/Next.js; separate investor view": weakened.** The owner has confirmed there are no outside investors. A read-only Streamlit page over the ledger delivers the same content.
- **v3 Position Manager and v2 early-exit logic: weakened as a safety mechanism.** It depends on the host being up. Every live position needs a broker-resting protective order placed at entry, and Alpaca crypto offers only stop-limit, with no bracket/OCO (F15).
- **v3 build order step 1 (freeze data contracts, event time vs ingestion time, replay IDs) and step 3 (same data path for backtest and live): supported.** These are the parts that actually deliver point-in-time correctness.
- **v3 Data Trust Gate / SAFE state: supported** by F14 (feeds drop messages) — and it must include a startup reconciliation routine, because restarts will be routine.

## 4. Recommended changes

### Phase-1 stack (research, backtest, shadow, paper)

- One Python package, one long-running `asyncio` process, plain virtual environment with a lockfile (no Docker on Windows).
- Time series and features: Parquet files in dated folders, queried with DuckDB or Polars (single writer).
- System of record (ledger, decisions, orders, fills, config changes, run registry): one SQLite database in WAL mode, single writer, nightly file copy as backup.
- Events: an append-only `events` table in SQLite, which doubles as the replay log; in-process queues between modules.
- Point-in-time: bitemporal columns plus as-of joins plus the leakage tests in 2.5. No Feast.
- Experiment tracking: git commit hash plus a `runs` table; add MLflow in SQLite library mode if comparing many runs becomes painful.
- Dashboard: one Streamlit page reading SQLite read-only; alerts by email.
- Monitoring: structured JSON logs, a heartbeat row every minute, and an external dead-man's-switch that alerts when the heartbeat stops.
- Laptop settings for paper trading: on mains power, sleep/hibernate/lid action disabled, wired network if possible, the process registered to auto-start and to reconcile with the broker on start.

### Upgrade path with explicit triggers

| Upgrade | Trigger |
|---|---|
| Move the live trader to a small Linux VPS ($6-12/month, with one Dockerfile and a systemd unit) | Before the first unattended real-money crypto position; or earlier if a 30-day paper run on the laptop shows more than about 1 unplanned outage a week or any outage over 15 minutes while a position was open. Research and training stay on the laptop. |
| SQLite to PostgreSQL | A second process genuinely needs to write concurrently; or the system of record lives on a different machine from a reader; or observed write-lock errors. |
| Add TimescaleDB | Time-series rows that must be queried live from SQL exceed roughly 100 million and Parquet+DuckDB scans are measurably too slow (measure first). |
| Add a broker/bus (Redis Streams, or NATS with JetStream) | Two or more independently deployed processes must exchange events with replay, and a database table as the queue has been measured to be inadequate. |
| Add Redis for hot state | Same trigger as the bus; never before. |
| MLflow tracking server | More than one machine or person logging runs. |
| FastAPI + web front end | A second human user, or a need for authenticated remote control beyond a read-only page. |
| Prometheus + Grafana (+ OpenTelemetry) | Three or more long-running services across hosts, or a debugging question logs cannot answer. |
| Feast | Multiple models served from multiple services needing a shared low-latency online store. Unlikely at this scale. |
| Object store | Data outgrows local disk or must be shared across machines; then use a cloud bucket, not MinIO. |
| Kubernetes, Kafka, Redis cluster | Remove from the document; no plausible trigger at $1k-$10k personal capital. |

### Document edits

1. Replace the v3 section 3 table with a "phase-1 choice / trigger / phase-2 choice" table as above.
2. Delete MinIO; note its archival.
3. Reword the Feast anchor: the requirement is "bitemporal data plus as-of joins plus leakage tests", with Feast as an optional later tool.
4. Add a "host failure" row to the failure-handling section: forced restart, sleep, network loss; required behaviour is broker-resting stop at entry, reconcile-on-start, dead-man's-switch alert, SAFE state until reconciled.
5. State that the "dedicated laptop" is the research and paper host, and that live 24/7 crypto runs on a VPS.

## 5. Open uncertainties

- Owner's hardware is unknown. If the laptop has 8 GB RAM, Docker Desktop plus the full stack is not viable at all; with 16 GB+ it is viable but still unjustified.
- I found no authoritative uptime statistics for consumer laptops or home broadband, so the laptop-versus-VPS comparison rests on documented mechanisms (F12, F13), not measured failure rates. The 30-day paper run is the way to measure it.
- The Modern Standby page is from 2020 and written for Windows 10; exact Windows 11 behaviour for a given laptop model is unverified. Whether Docker Desktop still lacks start-at-boot is recalled, not fetched.
- VPS providers publish SLAs, but I did not fetch them; "a VPS is more reliable" is a mechanism-based judgement.
- The Oracle Always Free Arm allowance fetched today (2 OCPU / 12 GB) differs from what I recalled; availability of free capacity in a given region is unverified, and the idle-reclaim rule is a risk for a low-CPU trading bot.
- TimescaleDB's current licence split and latest version were not confirmed.
- Whether a US-based VPS IP has any implications for Coinbase or Alpaca API access (IP allow-listing, terms) was not checked; another topic should confirm.
- Resource and data-volume figures in 2.3 and section 3 are estimates and should be measured.

## 6. Source list (all FETCHED 2026-10-01 unless noted)

- https://github.com/minio/minio
- https://github.com/feast-dev/feast
- https://github.com/feast-dev/feast/releases
- https://docs.feast.dev/getting-started/concepts/point-in-time-joins
- https://docs.feast.dev/getting-started/quickstart
- https://docs.feast.dev/reference/offline-stores/duckdb
- https://duckdb.org/docs/current/sql/query_syntax/from.html
- https://duckdb.org/docs/current/connect/concurrency.html
- https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.join_asof.html
- https://www.sqlite.org/wal.html
- https://redis.io/docs/latest/develop/data-types/streams/
- https://redis.io/legal/licenses/
- https://docs.nats.io/nats-concepts/jetstream
- https://mlflow.org/docs/latest/self-hosting/architecture/backend-store/
- https://github.com/timescale/timescaledb
- https://docs.docker.com/desktop/setup/install/windows-install/
- https://learn.microsoft.com/en-us/windows/wsl/wsl-config
- https://learn.microsoft.com/en-us/windows/deployment/update/waas-restart
- https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/modern-standby
- https://docs.streamlit.io/develop/concepts/architecture/architecture
- https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-overview
- https://docs.alpaca.markets/docs/crypto-orders
- https://docs.alpaca.markets/docs/orders-at-alpaca
- https://www.digitalocean.com/pricing/droplets
- https://aws.amazon.com/lightsail/pricing/
- https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/
- https://www.hetzner.com/cloud/regular-performance (plan specs only; prices did not render)
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- Not opened: https://www.oracle.com/cloud/free/ (HTTP 403). A web search surfaced third-party pages on Hetzner pricing; none were used as evidence — the Hetzner figures come from Hetzner's own documentation.

## Independent verification (2026-10-01)

Method: re-fetched primary sources for the claims that drive design decisions. Reliability of the brief: high.

Confirmed (re-fetched today):
- F1 MinIO archived 25 Apr 2026, README says no longer maintained, source-only, no new binaries; points to AIStor. https://github.com/minio/minio
- F2 Feast v0.66.0 on 21 Aug 2026, monthly cadence (v0.65 20 Jul, v0.64 13 Jun, v0.63 4 May, v0.62 8 Apr). https://github.com/feast-dev/feast/releases
- F4 DuckDB: one read-write process, or many read-only; multi-process write via "Quack" remote protocol still beta (v1.5.2). https://duckdb.org/docs/current/connect/concurrency.html
- F10 Docker Desktop: 8 GB RAM, Win 11 23H2+, WSL2 default backend, free for personal use. WSL2 memory default 50%, vmIdleTimeout 60000 ms, instanceIdleTimeout 15000 ms. https://docs.docker.com/desktop/setup/install/windows-install/ , https://learn.microsoft.com/en-us/windows/wsl/wsl-config
- F12 Windows auto-restart outside active hours; max active-hours length 18 h; several restart-delay policies legacy/not applicable to Windows 11 (page is IT-admin oriented, dated 2025-09). https://learn.microsoft.com/en-us/windows/deployment/update/waas-restart
- F15 Alpaca crypto: market, limit, stop_limit; GTC and IOC; no bracket/OCO/OTO listed. https://docs.alpaca.markets/docs/crypto-orders
- DigitalOcean $6 / $12 / $24 for 1/2/4 GB (also a $4 512 MiB plan exists). https://www.digitalocean.com/pricing/droplets
- Hetzner increase effective 15 Jun 2026; hourly US CPX11 now $0.0328 (was $0.0112), CPX21 $0.0601 (was $0.0224), CX23 $0.0104 (was $0.0080). https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/
- Oracle Always Free Arm A1: 2 OCPU / 12 GB (1,500 OCPU-h, 9,000 GB-h per month); reclaim rule 7 days under 20% CPU(p95)/network/(memory on A1). https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

Corrections / weakened:
- Docker auto-start (F10, "starts on login, not boot"): the Docker doc only says it does not auto-start after installation; the start-at-sign-in setting was not verified. Treat as "needs a signed-in user" unproven; test it on the owner's machine.
- Hetzner monthly figures ($20.49 / $37.49 / $6.49) were not visible in today's fetch (only hourly rates; $0.0328 x 730 h is about $24, so $20.49 is plausibly a monthly cap) - treat as unverified; use hourly rates or re-check the pricing page before budgeting.
- Oracle row: A1 allowance now 2 OCPU / 12 GB confirmed; the idle rule is a real risk for a low-CPU bot, and free capacity availability is not guaranteed.

Missed considerations (owner: US resident, $1k-$10k, near-zero budget):
- Trading costs: Alpaca crypto tier 1 (under $100k 30-day volume) is 15 bps maker / 25 bps taker per the Alpaca fee docs (found via search, https://docs.alpaca.markets/docs/crypto-fees; page itself not opened - verify). A round trip costs roughly 30-50 bps plus spread, which dwarfs infrastructure cost at this capital and should gate any high-turnover strategy.
- A near-zero budget argues for Oracle free tier or a $4-6 DigitalOcean droplet only after a paper run shows laptop outages matter; DuckLake+PostgreSQL is a documented production multi-writer path for DuckDB, not mentioned.
- Free dead-man's-switch services and Windows Task Scheduler / service wrappers for auto-start were not evaluated.
- US-specific constraints (state availability of Alpaca crypto, tax lot/wash-sale record keeping) not covered.

Could not verify: Alpaca crypto fee page directly; Hetzner monthly prices; TimescaleDB licence split; Redis licence and NATS JetStream pages, SQLite WAL, Streamlit, MLflow, Polars/DuckDB ASOF pages (not re-opened; low risk); Modern Standby Windows 11 specifics.
