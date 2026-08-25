# Northstar

**A living meridian of the Solana network** — original Python collector that turns public, keyless data into three artifacts: an interactive dark-theme dashboard, a human-readable Markdown briefing, and a machine-readable JSON snapshot.

This is not a fork of SolPulse or any existing dashboard. The architecture is a small stdlib-only pipeline: failover JSON-RPC → parallel HTTP overlays → local concentration/anomaly math → three renderers. No API keys, no paid SDKs, no telemetry.

Deadline context: Superteam Earn bounty, human-judged, due 2026-09-01.

## What you get

| Artifact | Path | Purpose |
| --- | --- | --- |
| Dashboard | `output/dashboard.html` | Dark observatory UI. Works as a file or via the tiny server. |
| Markdown | `output/report.md` | Briefing you can paste into a doc or PR. |
| JSON | `output/report.json` | Full snapshot for bots and diffs. |
| Samples | `samples/` | Copies from the last successful live run. |

Headline metrics each run:

- **Network:** TPS (all txs and non-vote), slot time, slot, block height, epoch progress + ETA, `getHealth`, inflation, circulating supply, median / p90 priority fees.
- **Validators:** active vs delinquent, stake share, Nakamoto coefficient (33%), supermajority (66.7%), HHI, top operators, commissions, named delinquency alerts.
- **Markets:** SOL price, 24h change, market cap, DeFi TVL, DEX volume, application fees, application revenue (closest keyless REV-like series), stablecoin supply.
- **Ecosystem:** tokenized / RWA TVL on Solana from DeFiLlama protocol × chain intersection; solana.com/data reachability.
- **Upgrades:** researched 2026 section covering **Alpenglow** and **SIMD-0525 / SIMD-525** with dated sources.

## How to run

Python 3.11+ (the box this was built on is 3.13). **No `pip install` is required.**

```bash
cd solana-ecosystem-report

# one snapshot, also copied into samples/
python3 -m northstar run

# rebuild every N seconds (default 300, from config.json)
python3 -m northstar watch --interval 180

# serve the dashboard; optional background refresh
python3 -m northstar serve --port 8765
python3 -m northstar serve --watch --interval 300
```

Then open `output/dashboard.html` in a browser, or visit `http://127.0.0.1:8765/`. The server maps `/` to the dashboard and also serves `report.md` and `report.json` next to it.

Custom config:

```bash
python3 -m northstar run --config /path/to/config.json
```

## Data sources

Northstar prefers sources that answer without a key. Failures are recorded in `source_health` rather than crashing the run.

### Solana JSON-RPC (authoritative for chain state)

Public endpoints, tried in order, sticky on the last healthy one:

1. `https://api.mainnet-beta.solana.com`
2. `https://api.mainnet.solana.com`
3. `https://solana-rpc.publicnode.com`
4. `https://solana.drpc.org`

Methods used:

| Method | Why |
| --- | --- |
| `getHealth` | Cluster liveness as the RPC node sees it |
| `getVersion` | `solana-core` string (e.g. Agave 4.2.0) |
| `getSlot` | Current slot |
| `getEpochInfo` | Epoch, slot index, block height, tx count |
| `getBlockTime` | Wall-clock of the tip slot |
| `getRecentPerformanceSamples` | TPS and slot time from ~60s windows |
| `getVoteAccounts` | Active vs delinquent stake, commissions |
| `getSupply` | Circulating / total SOL (`excludeNonCirculatingAccountsList`) |
| `getInflationRate` | Current issuance |
| `getRecentPrioritizationFees` | Median / p90 micro-lamports per CU |
| `getClusterNodes` | Gossip node count |

Rate limits: HTTP 429/5xx retry with backoff; a `rpc_gap_seconds` pause between calls; automatic endpoint failover. If `getVoteAccounts` is the call that trips a public node, the next endpoint is used for that method and then kept.

### DeFiLlama (authoritative for DeFi overlays)

Free API, no auth.

- `coins.llama.fi` current price and 24h percentage (price fallback)
- `/v2/chains` current Solana TVL
- `/v2/historicalChainTvl/Solana` 1d / 7d TVL change
- `/overview/dexs/Solana` 24h/7d DEX volume + venue table
- `/overview/fees/Solana` application fees
- `/overview/fees/Solana?dataType=dailyRevenue` application revenue
- `stablecoins.llama.fi/stablecoinchains` stablecoin supply on Solana
- `/protocols` filtered to category RWA ∩ chain Solana for tokenized assets

**REV:** Blockworks REV is not a public keyless feed. Northstar reports DeFiLlama application fees *and* revenue on Solana, plus on-chain median priority fees, and labels the distinction in the report.

### CoinGecko

`/api/v3/simple/price` is attempted first (no key). In practice the demo API often returns HTTP 429. Price then falls through to DeFiLlama coins. The `price_source` field tells you which one won.

### Stakewiz

`https://api.stakewiz.com/validators` is a public JSON list. It is used **only as a name/version overlay**. Stake, commission, and delinquency always come from RPC. If Stakewiz is down, validators still render with truncated vote pubkeys.

### solana.com/data

Fetched every run. As of 2026-08-25 the page is a client-rendered Solana Data Aggregator dashboard: HTTP 200, no `__NEXT_DATA__` JSON, no keyless `/api` sibling. The Foundation's [SDA repo](https://github.com/solana-foundation/solana-data-aggregator) itself needs provider keys (Allium, Dune, …). Northstar records reachability and does **not** invent numbers from the HTML.

### Intentionally skipped

- **Dune** — HTTP API needs a key.
- **Twitter / X** — needs keys.
- **DeFiLlama Pro RWA routes** (`/rwa/chain/solana`, etc.) — Pro-only. Tokenized assets instead use the free protocols list.

## Automation strategy

1. `config.json` holds `refresh_seconds` (default 300), RPC list, timeouts, and anomaly bands.
2. `python3 -m northstar watch` is a blocking loop. `serve --watch` runs the same rebuild on a daemon thread so the HTML file on disk updates under the server.
3. Each successful run appends a compact row to `data/history.jsonl` (capped by `history_keep`, default 288 ≈ a day of 5-minute samples).
4. Renderers always overwrite `output/dashboard.html`, `output/report.md`, `output/report.json`. Sample copies are opt-out (`--no-samples`).
5. Independent HTTP sources are fetched in a thread pool; RPC stays serial + gapped so a public node is less likely to ban the process.

This is designed to sit on a cheap VPS or a laptop cron:

```cron
*/5 * * * * cd /opt/solana-ecosystem-report && python3 -m northstar run --no-samples
```

## Anomaly detection

Two layers, both documented in the JSON `anomalies` array.

**Absolute rules** (fire on a first run):

| Code | Default trigger |
| --- | --- |
| `rpc_unhealthy` | `getHealth` is not `ok` |
| `slow_slots` | median slot time ≥ 650 ms |
| `fast_slots` | median slot time ≤ 180 ms |
| `high_delinquency` | delinquent stake ≥ 5% |
| `many_delinquent` | ≥ 80 delinquent vote accounts |
| `named_delinquents` | a delinquent account still has ≥ 10k SOL |
| `price_move` | \|24h SOL change\| ≥ 8% |
| `tvl_move` | \|1d TVL change\| ≥ 12% |
| `dex_move` | \|1d DEX volume change\| ≥ 60% |
| `quiet_nonvote` | non-vote TPS < 50 |

**Local baseline** (needs history): TPS drop/spike vs this install's median, plus a z-score (`zscore` default 2.6) on TPS. A fresh clone will usually print a single `nominal` chip unless the chain is already outside the absolute bands. That is intentional — Northstar does not pretend a global “normal TPS” exists independent of the SIMD-0525 clock.

Thresholds live in `config.json` → `anomalies`.

## How to interpret the numbers

- **TPS, all transactions** includes vote transactions. During TowerBFT that inflates the headline. Watch **non-vote TPS** for application load.
- **Slot time** is `samplePeriodSecs / numSlots` from performance samples, not the SDK constant of 400 ms. SIMD-0525 is a staged cut 400 → 350 → 300 → 250 → 200. Northstar maps the measured median onto that ladder (`slot_time_stage` in JSON). Epoch ETA uses the *measured* slot time, so it stays honest as gates flip.
- **Nakamoto coefficient** here is “fewest validators whose combined activated stake ≥ 33.34%”. Supermajority is the same at 66.67%. HHI is the sum of squared shares × 10,000.
- **Priority fees** are micro-lamports per compute unit over the last ~150 slots. Many slots are zero; the dashboard shows median of all, p90, and median of non-zeros.
- **Application revenue ≠ chain REV.** If you need Blockworks REV, wire a keyed provider later; do not treat the DeFiLlama revenue number as a drop-in.
- **RWA TVL** is the sum of DeFiLlama protocol TVL attributed to Solana for protocols tagged RWA. It is not a NAV of every tokenized share on-chain.
- **Upgrade cards** are editorial, dated 2026-08-25, with primary URLs. They do not auto-scrape SIMD status.

## Project layout

```
solana-ecosystem-report/
  config.json            refresh interval, RPC list, anomaly bands
  northstar/             stdlib package
    __main__.py          run | watch | serve
    collect.py           RPC + HTTP interpreters
    rpc.py               endpoint failover
    analyze.py           history + anomalies + SIMD-0525 ladder
    research.py          Alpenglow / SIMD-0525 briefing
    html_out.py          self-contained dashboard
    markdown_out.py
    pipeline.py
  output/                live artifacts
  samples/               last successful run (md + json + html)
  data/history.jsonl     compact time series
```

## Fallbacks observed while building

- CoinGecko demo API: HTTP 429 → DeFiLlama coins price.
- Binance public ticker: HTTP 451 from this environment (not used in the default waterfall).
- `solana.com/data`: HTML only, no JSON feed.
- Public RPC: `api.mainnet-beta.solana.com` answered `getHealth`, `getEpochInfo`, samples, supply, fees during the first live run. If it 429s, the client walks the list.

## License

MIT. Do not commit secrets; this repo is designed so you never need any.
