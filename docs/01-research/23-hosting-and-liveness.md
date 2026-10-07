# 23 - Hosting and liveness for a single-process, daily-bar JARVIS

Date: 2026-10-01. Binding constraints: US resident, $1,000-$10,000 of own money, near-zero monthly budget, solo developer. Labels: FETCHED = opened this session; RECALLED = from memory; UNVERIFIED = snippet or blog only. Prices exclude sales tax/VAT unless noted.

## Questions

1. Where can a single-process bot run for $0-$12 a month today, and what do the official terms say (idle reclaim, US regions, data-centre IP rules)?
2. How far can a Windows 11 laptop be trusted (Task Scheduler, sleep, forced updates)?
3. Which dead-man's-switch and alert services are free?
4. For a once-a-day strategy, how much does 24/7 uptime matter, what restart-tolerant design fits, and what risk remains for 24/7 crypto?
5. How should broker keys be held on each host? Default and fallback?

## Findings

### 1. Hosts, as of today

| Option | Official price | Notes |
|---|---|---|
| Oracle Always Free | $0 | AMD E2.1.Micro 1 GB (up to 2) or A1 Arm, 2 OCPU/12 GB total; 200 GB storage; 10 TB egress. Home region fixed at signup. Credit card and phone needed (FETCHED, Oracle docs). |
| Google Cloud e2-micro | $0 | 1 non-preemptible instance, free hours = all hours in the month, only in us-west1, us-central1, us-east1; 30 GB standard disk; 1 GB/month NA egress. Secret Manager free: 6 active versions, 10,000 accesses a month (FETCHED, Google docs). |
| DigitalOcean Droplet | $4/mo (512 MiB, 10 GiB) or $6/mo (1 GiB, 25 GiB) | Per-second billing since 2026-01-01 (FETCHED). |
| AWS Lightsail | $5/mo (1 GB, 2 vCPU, 40 GB, 2 TB) | $3.50 IPv6-only tier (FETCHED). |
| Hetzner, EU | CX23 $6.49/mo (EUR 5.49) | Up from $4.99 on 2026-06-15 (FETCHED). |
| Hetzner, US (Ashburn/Hillsboro) | CPX11 $20.49/mo | Up from $6.99 on 2026-06-15; the listed US cheap tier is CPX, not CX/CAX (FETCHED). |
| Vultr | "$5/mo" | Pricing page returned 403; search snippet only (UNVERIFIED). |
| Raspberry Pi at home | Zero 2 W about $15 | Pi 4/5 4 GB and up rose $25-$100 on 2026-04-01 because LPDDR4 cost rose sevenfold; Zero and Pi 3 families were not raised (FETCHED, raspberrypi.com news). |
| GitHub Actions cron | $0 | See below. |

**Brief 14's "$6-12/month VPS" is stale for Hetzner US.** A US Hetzner box is now $20.49 a month, which is $245.88 a year. That is 24.6% of $1,000 and 2.5% of $10,000 (ESTIMATE: 20.49 x 12 / capital). Under brief 11's rule (drag under 2% a year needs capital of at least 600x the monthly bill), $20.49 needs $12,294 and $5 needs $3,000.

**Oracle idle reclaim is a poor fit for this bot.** Oracle's text: an instance is idle if, over 7 days, CPU 95th percentile is under 20%, network is under 20%, and (A1 only) memory is under 20%. A once-a-day job meets all of these by design (FETCHED). Oracle's docs say Always Free resources survive after the trial ends. They also say an "out of host capacity" error means a temporary shortage in the home region. They say upgrading to Pay As You Go leaves Always Free resources uncharged (FETCHED). The docs I opened do not say Pay As You Go exempts an instance from reclaim. Only a third-party blog says so (UNVERIFIED). Oracle is a last choice here because the reclaim risk is documented and the exemption is not.

**Data-centre IP rules.** Alpaca's disclosures page says brokerage service is for eligible US customers and that third-party access to the account is "solely at your risk" (FETCHED). I found no IP or data-centre clause in any Alpaca document I could open. The Customer Agreement PDF returned compressed content that I could not parse, so a clause could still exist (UNVERIFIED). Alpaca has no API-key IP allowlist; a June 2026 forum request says the dashboard field exists but is disabled, with no staff reply visible (FETCHED). Choose a US-region host to stay conservative, since no document I could read says EU or US is treated differently.

**GitHub Actions as a free run-to-completion host.** Schedules run on the default branch, minimum interval 5 minutes, "can be delayed" at high load (especially the start of each hour), and public-repo schedules are disabled after 60 days without repo activity. Private repos on the Free plan get 2,000 minutes a month (FETCHED). A 5-minute daily run is 150 minutes, 7.5% of the allowance (ESTIMATE; assumes Linux at a 1x multiplier, RECALLED). Costs: persistent state is awkward, and the runner's shared IP holds your full-power key. Treat it as a heartbeat or watcher, not as the live host.

**Home hardware.** A Pi Zero 2 W (1 GHz quad-core, 512 MB) is enough for one Python process (FETCHED). Electricity at 18.31 cents/kWh (US residential average, July 2026, FETCHED, EIA): 3 W x 24 h x 30 d = 2.16 kWh = $0.40 a month; a 20 W laptop = 14.4 kWh = $2.64 a month (ESTIMATE; wattages are assumptions). Home ISP and power outages are not covered by any SLA.

### 2. Windows 11 laptop

- **Run-to-completion jobs fit Task Scheduler.** StartWhenAvailable starts a task "at any time after its scheduled time has passed", but applies only to timed tasks. WakeToRun wakes the machine, but the screen may stay off. RestartOnFailure needs both Count and Interval set (FETCHED, Microsoft Learn schema pages).
- **Credentials.** Tasks registered with a password or S4U logon only launch if the account has the Logon as Batch privilege; Administrators have it by default (FETCHED).
- **Modern Standby.** The S0 low-power model keeps the NIC alive but only lets software run in "short, controlled bursts" (FETCHED). This hardware may therefore not behave like old S3 sleep. Check with `powercfg /availablesleepstates`. Set `powercfg /change standby-timeout-ac 0`. Use `/requests`, `/waketimers` and `/lastwake` to diagnose (FETCHED). The lid action is set via `/setacvalueindex` and `powercfg /aliases`.
- **Forced restarts.** Windows restarts outside active hours (default 8 AM-5 PM, max range 18 h). After 7 days without a successful restart the user is prompted. Where deadline policies are on, restarts happen regardless of active hours and cannot be rescheduled (FETCHED, Microsoft Learn). Microsoft says updates "can't" be stopped entirely (FETCHED). The documented knobs (`NoAutoRebootWithLoggedOnUsers`, deadline no-auto-reboot) have conflict and legacy caveats. On Pro, Group Policy is available, but it does not give a guarantee.
- **Wrapper.** WinSW (MIT licence, XML-configured services) exists for long-running processes (FETCHED), but a daily job needs no service.
- **Conclusion.** The laptop is acceptable only for a design that survives a missed day. No measured uptime figures exist.

### 3. Dead-man's switch and alerts

| Service | Free tier | Source status |
|---|---|---|
| Healthchecks.io | 20 checks, 100 log entries per check, no card; SMS/WhatsApp/phone credits are paid-plan only; Business is $20/mo | FETCHED |
| Healthchecks.io integrations | 30+ listed (email, Telegram, ntfy, Pushover, Signal, webhooks); the pricing page lists only SMS/phone as plan-gated | FETCHED, free-tier availability of each integration not confirmed |
| Healthchecks.io self-host | BSD-3 licence, Docker image | FETCHED |
| UptimeRobot | 50 monitors, 5-minute interval, heartbeat monitoring on free, hobby use | FETCHED |
| Better Stack | 10 monitors, 10 heartbeats, Slack and email | FETCHED |
| Cronitor | 5 monitors, email and Slack | FETCHED |
| ntfy.sh | HTTP POST to a topic; the topic name acts as the password; self-hosted default is a 60-request burst, refilling one per 5 s; public-server daily limits not found | FETCHED |
| Pushover | $4.99 once per platform, 10,000 messages/month free sending | FETCHED |
| Resend (email) | 3,000/month, 100/day | FETCHED |
| Telegram Bot API | `sendMessage` with a bot token; rate limits not shown on the page opened | FETCHED, limits UNVERIFIED |

Healthchecks accepts a period-and-grace schedule or cron expressions. For a daily job, set the cron to the run time and a grace of about 2 hours; the alert fires about 2 hours after a missed run (ESTIMATE from the grace definition). Healthchecks's /start and /fail signals are RECALLED from prior use, not read in this session. The watcher must be off-host, otherwise it dies with the laptop. Alpaca's status page also offers email, webhook and RSS subscriptions (FETCHED). Alpaca does not publish incident history on the page I could open.

### 4. Does 24/7 uptime matter for a daily strategy?

- **Equities and ETFs: barely.** One order window a day, plus a retry window, is all the process needs. Between runs nothing is needed if each held position has a broker-resting protection (see below) and entries are day or market-on-open orders. Alpaca supports `day, gtc, opg, cls, ioc, fok`, but fractional orders are day-only; GTC orders are auto-cancelled 90 days after creation at 4:15 pm ET (FETCHED). So: whole shares for anything needing a resting stop, and re-arm stops on every run.
- **Crypto: it matters more.** Alpaca crypto accepts Market, Limit and Stop-Limit, `gtc` and `ioc` only, no plain stop, no bracket or OCO (FETCHED). A resting GTC stop-limit can exist at the broker, so it can survive host death. It does not guarantee a fill when price gaps through the limit.
- **Residual risk with a dead host:**
  1. gap through the stop-limit;
  2. stale or auto-expired stops;
  3. missed exit signals until the next run;
  4. broker or API outage (not under owner control);
  5. a stop already filled while the ledger still says "holding".
- **Bounding it by sizing.** If the crypto sleeve is capped at 20% of equity and a one-day gap is -30% (the cap and the gap are both illustrative, UNVERIFIED), the loss is 6% of equity. That is the sleeve cap's job, not uptime's.
- **Restart-tolerant skeleton (one process per run; SQLite WAL):**
  1. Take a file lock and send /start to the dead-man's switch.
  2. Reconcile: fetch account, positions and open orders from the broker (the broker is the source of truth); diff against the intent ledger; adopt or cancel orphans.
  3. Check the calendar, data freshness and kill-switch flag; otherwise exit "skipped" with a log entry.
  4. Compute targets, apply the risk gate, then write intent rows with a deterministic `client_order_id` (max 128 characters, FETCHED) BEFORE any broker call.
  5. Before submit, look the order up by that id. Alpaca's documentation does not state duplicate-id behaviour (FETCHED), so that lookup, not the broker rejection, is the idempotency control.
  6. Poll to a terminal state; do not rely on websocket replay (the `trade_updates` documentation is silent on replay, FETCHED).
  7. Verify every held position has its resting stop; recreate any missing one.
  8. Ping success or /fail with a reason.
  - Schedule a main run plus a retry about an hour later that exits at once if today's intents are complete.
- **Rate limit.** 200 trading calls a minute per account (search-result summary of Alpaca support, UNVERIFIED); one run uses a small fraction.

### 5. Secrets

- **Facts about Alpaca keys (FETCHED, Alpaca 2026-09-14 article):** a leaked key can submit and cancel orders, liquidate positions, read the portfolio, and add crypto-wallet whitelist entries (`POST /v2/wallets/whitelists`). It cannot start ACH or wire transfers; those need the dashboard and MFA. The secret is shown once. Regeneration invalidates the old pair at once. Paper and live use separate hosts and keys. The article does not mention scoped keys or IP allowlists. I found no evidence of read-only keys, so every host holding the key can trade.
- **Windows laptop:** DPAPI (`CryptProtectData`): only the same logon user on the same machine can normally decrypt; the machine-scope flag lets any local user decrypt (FETCHED). Python `keyring` uses Windows Credential Locker on Windows (FETCHED). Whether it works under "run whether user is logged on or not" was not tested (UNVERIFIED). Plan: a DPAPI user-scope file, read by the Task Scheduler job running as that user. Malware running as the same user can still read it.
- **Linux VPS or GCP e2-micro:** systemd `LoadCredentialEncrypted=` places the secret in a non-swappable, per-service file, encrypted with a host key or TPM2 (FETCHED). The fallback is a 0600 environment file.
- **GCP Secret Manager** (6 versions free) adds rotation and audit, but the VM's own identity still reads the secret, so the host remains the trust boundary (reasoning).
- **Do not:** commit `.env` (v1 already committed a key), put keys in GitHub Actions on the main trading path, or enable crypto wallet transfers unless needed.

## What this decides for the JARVIS design

1. **Design the job, not the daemon.** A run-to-completion scheduled job with reconcile-on-start and an intent-before-broker-call ledger, on SQLite WAL, one writer.
2. **Default host (paper and daily equity/ETF live): the owner's Windows 11 Pro laptop under Task Scheduler.** Set StartWhenAvailable, WakeToRun, RestartOnFailure, AC-only sleep disabled and a two-run daily schedule. Cost $0 plus about $2.64 a month of power (ESTIMATE).
3. **Fallback and upgrade path: the same script on a Linux US-region box.**
   - First choice: Google e2-micro in us-central1 or us-west1 ($0). Systemd timer with `Persistent=true`, which runs a missed job after downtime (FETCHED).
   - Second choice: a $4-6 droplet or Lightsail.
   - Avoid Hetzner US at $20.49 and Oracle Always Free (documented idle reclaim).
   - Move before the first crypto position, or when the laptop misses 2 runs in a month (my threshold, not evidence-based).
4. **External dead-man's switch: Healthchecks.io free, with a cron schedule and 2-hour grace, plus a Telegram or ntfy channel and email.** Add a second independent check, e.g. Better Stack or UptimeRobot, only if it costs $0.
5. **Protection must live at the broker.** Whole shares with GTC stops (re-armed each run) for equities; stop-limit GTC for crypto. Cap the crypto sleeve by the gap-loss rule, not by uptime hopes.
6. **Secrets:** default is DPAPI user-scope on the laptop (live key never on a second host); fallback is systemd encrypted credentials on the VPS. Paper keys are separate. Regenerate on any doubt. Wallet transfers stay off.

## Open uncertainties

- No measured uptime of the owner's laptop; hardware spec unknown (Modern Standby behaviour depends on it).
- Alpaca Customer Agreement not parsed, so any IP, data-centre or automation clause is unconfirmed.
- Oracle: whether Pay As You Go prevents reclaim is only from a blog. A reclaimed instance's fate (stop vs delete) was not read.
- GCP e2-micro: possible hidden costs (egress beyond 1 GB, static IP) and any idle policy were not checked.
- Healthchecks free-tier integration list, minimum period and /start /fail semantics were not confirmed from the docs; ntfy.sh public daily limits not found; Telegram rate limits not read.
- Alpaca: duplicate `client_order_id` behaviour, whether stop-limit GTC exists for crypto in practice, quantity locking when a resting sell holds the position, and 90-day GTC expiry for crypto are all untested.
- Vultr price from a snippet; Pi 4 2 GB/4 GB list prices ($55/$100) from a snippet; mini-PC prices not researched.
- Task Scheduler + keyring behaviour under a non-interactive session untested.
- Crypto gap size and the 20% cap are illustrative.

## Source list

- Oracle Always Free resources: https://docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm and https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm (FETCHED); Free Tier overview https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm (FETCHED)
- Google Cloud free features: https://docs.cloud.google.com/free/docs/free-cloud-features (FETCHED)
- Hetzner price adjustment: https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/ ; https://docs.hetzner.cloud/whats-new (FETCHED)
- DigitalOcean: https://www.digitalocean.com/pricing/droplets (FETCHED); Lightsail: https://aws.amazon.com/lightsail/pricing/ (FETCHED); Vultr: https://www.vultr.com/pricing/ (403, snippet only)
- Raspberry Pi: https://www.raspberrypi.com/news/a-new-3gb-raspberry-pi-4-for-83-75-and-more-memory-driven-price-increases/ ; https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/ (FETCHED)
- EIA electricity: https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_5_6_a (FETCHED)
- GitHub Actions: https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows ; https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions (FETCHED)
- Microsoft Learn: Task Scheduler pages (StartWhenAvailable, WakeToRun, RestartOnFailure, security contexts) under https://learn.microsoft.com/en-us/windows/win32/taskschd/ ; https://learn.microsoft.com/en-us/windows/deployment/update/waas-restart ; https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-update ; https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/modern-standby ; https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/powercfg-command-line-options ; https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata ; https://support.microsoft.com/en-us/windows/windows-update-faq-8a903416-6f45-0718-f5c7-375e92dddeb2 (all FETCHED)
- WinSW: https://github.com/winsw/winsw (FETCHED)
- Healthchecks: https://healthchecks.io/pricing/ ; https://healthchecks.io/ ; https://github.com/healthchecks/healthchecks (FETCHED)
- UptimeRobot https://uptimerobot.com/pricing/ ; Better Stack https://betterstack.com/pricing ; Cronitor https://cronitor.io/pricing ; Pushover https://pushover.net/pricing ; Resend https://resend.com/pricing ; ntfy https://docs.ntfy.sh/publish/ and https://docs.ntfy.sh/config/ ; Telegram https://core.telegram.org/bots/api (all FETCHED)
- Alpaca: https://alpaca.markets/learn/api-key-security-best-practices-for-alpaca-builders ; https://forum.alpaca.markets/t/feature-request-api-key-ip-allowlisting/19087 ; https://alpaca.markets/disclosures ; https://docs.alpaca.markets/docs/orders-at-alpaca ; https://docs.alpaca.markets/docs/crypto-trading ; https://docs.alpaca.markets/reference/postorder ; https://docs.alpaca.markets/docs/websocket-streaming ; https://docs.alpaca.markets/docs/authentication (FETCHED); rate limit https://alpaca.markets/support/usage-limit-api-calls (search result only)
- Python keyring https://keyring.readthedocs.io/en/latest/ ; systemd credentials https://systemd.io/CREDENTIALS/ ; systemd.service and systemd.timer man pages on man7.org (all FETCHED)


## Independent verification (2026-10-01)

Confirmed (opened primary sources):
- Hetzner: CPX11 US $6.99 to $20.49/mo, CX23 $4.99 to $6.49/mo, effective 2026-06-15; applies to new orders and rescales, existing orders keep old price. https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/
- Oracle idle rule (7 days, CPU p95 <20%, network <20%, memory <20% A1 only), E2.1.Micro 1 GB up to 2, A1 2 OCPU/12 GB. Docs do not say what happens to a reclaimed instance. https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- GCP e2-micro: us-west1/us-central1/us-east1, hours = hours in month, 30 GB standard disk, 1 GB NA egress. https://docs.cloud.google.com/free/docs/free-cloud-features
- Alpaca: GTC auto-cancel 90 days at 4:15 pm ET; fractional = day only; crypto = gtc/ioc, market/limit/stop-limit, no stop. https://docs.alpaca.markets/docs/orders-at-alpaca ; client_order_id <=128 chars: https://docs.alpaca.markets/reference/postorder
- Healthchecks free: 20 checks, 100 log entries; Business $20/mo with SMS/phone. https://healthchecks.io/pricing/
- GitHub Actions: 5-minute minimum, delays at hour start, public-repo schedules disabled after 60 days inactivity, 2,000 free minutes private. https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows
- Arithmetic all re-checked and correct: 20.49x12=245.88 (24.6% of $1k, 2.46% of $10k); 600x rule gives $12,294 and $3,000; power $0.40 and $2.64/mo; 150 min = 7.5%; 20% x 30% = 6%.

Corrected / weakened:
- Oracle Pay As You Go: sources I could read disagree. A secondary summary of the Oracle docs found no PAYG exemption; third-party blog (51sec.org) says PAYG prevents reclaim. Remains UNVERIFIED either way; do not rely on PAYG as protection. Brief's choice to avoid Oracle stands.
- Secret Manager: the Google page may attach the 6-version/10,000-access free allowance to specific key types (a fetch summary tied it to Cloud KMS Autokey); re-read before depending on it. Low impact since the host remains the trust boundary.
- Hetzner US "$20.49" is the CPX11 list; confirm the exact US plan at order time.

Could not verify: Alpaca Customer Agreement IP/data-centre clause; Vultr price (not retried); Alpaca duplicate client_order_id behaviour; Healthchecks /start and /fail semantics; Modern Standby and Task Scheduler claims, DPAPI, systemd items (not re-opened); EIA 18.31 c/kWh; Pi price changes.
