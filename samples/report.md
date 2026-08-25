# Northstar — Solana ecosystem report

_Generated 2026-08-25T15:40:35Z (UTC). Local readers in Europe/Madrid: add two hours in summer (CEST)._

**RPC:** `https://api.mainnet-beta.solana.com` · **client seen:** `4.2.0` · **health:** ok

Northstar is a keyless collector. Numbers below come from public Solana RPC, DeFiLlama, optional CoinGecko, Stakewiz names, and a static 2026 upgrade brief. They are a snapshot, not investment advice.

## Headline gauges

| Gauge | Value |
| --- | ---: |
| Slot / block height | 441,661,847 / 419,710,574 |
| Epoch | 1,022 — 36.54% complete |
| Epoch remaining (est.) | 27.7 hours |
| TPS (all txs, ~15-sample median) | 4,248 |
| Non-vote TPS (same window) | 2,407 |
| Slot time (median) | 364 ms |
| SIMD-0525 readout | 350ms (SIMD-0525 stage 1) |
| SOL price | $98.29 (+0.71%) via DeFiLlama coins |
| Circulating SOL | 583.38M SOL |
| Market cap (price × circulating) | $57.34B |
| DeFi TVL | $5.66B (+1.72% 1d) |
| DEX volume 24h | $3.00B (+1.96%) |
| App fees 24h | $14.49M |
| App revenue 24h | $5.79M |
| Stablecoin supply on Solana | $15.96B |
| Tokenized / RWA TVL on Solana | $2.00B (26 protocols) |
| Median priority fee | 0 µ-lamports/CU (nonzero median —) |
| Inflation (on-chain) | 3.68% |

## How to read TPS and slot time

Solana RPC `getRecentPerformanceSamples` returns ~60-second windows. **All-tx TPS includes vote transactions** (consensus chatter). **Non-vote TPS** is closer to user and program load. Slot time is `samplePeriodSecs / numSlots`. During SIMD-0525 the target is no longer a fixed 400 ms; compare the measured median to the staged ladder (400 → 350 → 300 → 250 → 200).

Measured median slot time is 364 ms, nearest staged target 350 ms (350ms (SIMD-0525 stage 1)).

## Anomaly desk

- **WARNING** — Staked validators marked delinquent: Project 0 Horizon (91,110 SOL), EAC (29,733 SOL), Project 0 Meridian (26,113 SOL)

Rules mix hard thresholds (slow slots, delinquent stake, large 24h market moves) with a local z-score once this install has enough history. A first run will usually look quiet unless something is already outside the absolute bands.

## Validators

Active vote accounts: **686**. Delinquent: **9** (0.04% of activated stake).

Nakamoto coefficient (33% of stake): **18**. Supermajority (66.7%): **79**. Top-10 share: **24.28%**. HHI: **100** (10,000 = monopoly).

Median commission **5.0%**. Zero-commission active: 256. Commission ≥10%: 93.

### Top validators by activated stake

| Rank | Name | Stake | Share | Commission | Status | Version |
| ---: | --- | ---: | ---: | ---: | --- | --- |
| 1 | Figment | 17.07M SOL | 3.92% | 7% | active | 4.2.1 |
| 2 | Helius | 16.04M SOL | 3.69% | 0% | active | 4.2.1 |
| 3 | binance staking | 12.27M SOL | 2.82% | 0% | active | 4.2.1 |
| 4 | Jupiter | 11.74M SOL | 2.70% | 5% | active | 4.2.1 |
| 5 | Ledger by Figment | 9.20M SOL | 2.11% | 7% | active | 4.2.1 |
| 6 | Kraken 2 | 8.92M SOL | 2.05% | 10% | active | 4.2.1 |
| 7 | Bitwise Onchain Solutions | 8.58M SOL | 1.97% | 0% | active | 4.2.0-rc.1 |
| 8 | Everstake | 7.95M SOL | 1.83% | 7% | active | 0.1105.40200 |
| 9 | Galaxy | 7.30M SOL | 1.68% | 5% | active | 0.1105.40200 |
| 10 | Staking Facilities / MEV 🔥 | 6.57M SOL | 1.51% | 0% | active | 0.1106.40201 |
| 11 | HZKopZYv… | 6.12M SOL | 1.41% | 100% | active | 1.1.4 |
| 12 | Forward Industries | 6.02M SOL | 1.38% | 0% | active | 0.1105.40200 |
| 13 | Kiln1 | 5.93M SOL | 1.36% | 5% | active | 4.2.0-rc.1 |
| 14 | Upbit Staking | 5.67M SOL | 1.30% | 100% | active | 4.2.0 |
| 15 | P2P.org | 4.83M SOL | 1.11% | 7% | active | 4.2.1 |
| 16 | HimWQUK6… | 4.67M SOL | 1.07% | 8% | active | 4.2.1 |
| 17 | 3ZYJxzCe… | 4.10M SOL | 0.94% | 100% | active | 4.2.1 |
| 18 | G9x1mqew… | 4.03M SOL | 0.93% | 100% | active | 4.2.1 |
| 19 | EcEowA4G… | 4.00M SOL | 0.92% | 100% | active | 4.2.1 |
| 20 | AZoCYB4V… | 3.98M SOL | 0.91% | 100% | active | 4.2.1 |

### Delinquency alerts (activated stake ≥ 10k SOL)

- Project 0 Horizon — 91,110 SOL, last vote slot 441,654,232, vote `mrgn2vsZ5EJ8YEfAMNPXmRux7th9cNfBasQ1JJvVwPn`
- EAC — 29,733 SOL, last vote slot 440,639,999, vote `Gar9q7Ru2sKfVxFnR5xmV8GieJeUSTp7Uf3ixai9BQKS`
- Project 0 Meridian — 26,113 SOL, last vote slot 441,557,504, vote `mrgn4t2JabSgvGnrCaHXMvz8ocr4F52scsxJnkQMQsQ`
- 9hHEiSDT… — 24,002 SOL, last vote slot 440,639,999, vote `9hHEiSDTz9LeA4B4N2tJp6SPchwWZbV1X7zWN8hYoMhb`
- The Lotus Validator — 16,660 SOL, last vote slot 441,252,679, vote `gangtRyGPTvYWb8K3xS2feJQaCks4iJ7rytFUPtVqSY`

### Client versions among active validators (Stakewiz overlay)

- `4.2.1` — 524 validators, 325.06M SOL
- `0.1105.40200` — 19 validators, 33.65M SOL
- `4.2.0-rc.1` — 28 validators, 24.59M SOL
- `4.2.0` — 61 validators, 24.31M SOL
- `0.1106.40201` — 23 validators, 11.47M SOL
- `1.1.4` — 11 validators, 10.74M SOL
- `26.8.1` — 2 validators, 1.90M SOL
- `26.8.0` — 1 validators, 1,000,000 SOL

## Markets and DeFi

Price source waterfall: CoinGecko if the demo API answers, otherwise DeFiLlama `coins.llama.fi`. This run used **DeFiLlama coins**.

### Top DEX venues by 24h volume

| Venue | 24h volume | 1d change |
| --- | ---: | ---: |
| PumpSwap | $694.81M | -2.51% |
| Orca DEX | $518.19M | +29.25% |
| BisonFi | $409.15M | -6.69% |
| Meteora DLMM | $278.05M | +3.35% |
| Scorch | $218.92M | -19.10% |
| Manifest Trade | $215.15M | +51.92% |
| Raydium AMM | $198.64M | -4.06% |
| pump.fun | $95.40M | +24.76% |
| Axiom | $81.49M | +30.71% |
| Jupiterz | $66.78M | +75.36% |

Fees and revenue are DeFiLlama *application* totals on Solana (swaps, lending spread, etc.), not the same object as Blockworks REV. They are the closest keyless REV-like series. Median priority fee comes from `getRecentPrioritizationFees` and is in micro-lamports per compute unit, including zeros.

### Tokenized assets (RWA protocols with Solana TVL)

- **BlackRock BUIDL** — $828.75M
- **xStocks** — $419.70M
- **OnRe** — $276.36M
- **Ondo Yield Assets** — $178.41M
- **Hastra** — $166.29M
- **Theo Network thBill** — $26.39M
- **Ondo Global Markets** — $24.78M
- **Nest Credit** — $22.54M
- **Apollo Diversified Credit Securitize Fund** — $18.23M
- **VanEck Treasury Fund** — $13.93M

## Ecosystem coverage notes

solana.com/data is a JavaScript dashboard powered by the Solana Data Aggregator. The public HTML does not expose a keyless JSON feed, so Northstar records page availability and uses RPC + DeFiLlama for numeric metrics. Tokenized-asset TVL is derived from DeFiLlama RWA protocols with a Solana deployment.

- solana.com/data fetch: ok (HTTP 200, 771,353 bytes).
- Dune: Dune Analytics HTTP API requires an API key; skipped per no-secrets policy.
- Twitter/X: X/Twitter API requires keys; skipped.
- Daily active addresses: No keyless public JSON endpoint currently publishes Solana daily active addresses. DeFiLlama's chain ranking UI shows the figure but it is not on the free /v2/chains API.

## Upcoming and in-flight upgrades (researched 2026-08-25)

This section is researched editorial content, not live RPC state. Dates and statuses were checked against primary Solana Foundation pages and SIMD text on 2026-08-25. Feature activation can move; treat target windows as the Foundation's published schedule, not a guarantee.

### Alpenglow (SIMD-0326 family)

**Status:** In development — expected with Agave 4.3 / Q3 2026

Replace TowerBFT + on-chain votes with Votor; target ~150ms finality.

Alpenglow is Solana's first major consensus rewrite since TowerBFT. Phase 1 (Votor) removes Proof of History as a consensus clock and drops vote transactions from blocks. Validators exchange votes directly; certificates live in a Pool/Blokstor path instead of as regular txs. Fast path finalizes a block when ≥80% of stake notarizes in round one; otherwise a second round can finalize at a 60% stake threshold. The resilience claim is a 20+20 model: 20% adversarial stake plus 20% offline stake. Rotor, the later block-propagation replacement for Turbine, is explicitly out of scope for the first activation.

BLS pubkey management (SIMD-0387) activated on mainnet 2026-07-08. Validator Admission Ticket / VAT (SIMD-0357) activated 2026-07-22. Operators who have not registered a BLS pubkey are excluded from the VAT-admitted set and stop participating in consensus. VAT gating is not the same as turning Alpenglow consensus on — that remains a separate Agave 4.3 activation. VAT is 1.6 SOL per epoch at 400ms slots, scaling down with SIMD-0525 so daily cost stays ~0.8 SOL.

Related SIMDs: SIMD-0326 Alpenglow Consensus Protocol; SIMD-0337 Markers for Alpenglow Fast Leader Handover; SIMD-0357 Alpenglow Validator Admission Ticket; SIMD-0384 Alpenglow Migration; SIMD-0387 BLS Pubkey Management in Vote Account

Sources:

- Solana Upgrades — Alpenglow (Foundation, June 2026; page current as of Aug 2026) (2026-06 / checked 2026-08-25) — https://solana.com/upgrades/alpenglow
- Solana Network Upgrades index (Agave 4.3 planned October 2026) (checked 2026-08-25) — https://solana.com/news/solana-network-upgrades
- SIMD-0326 Alpenglow proposal (created 2025-07-25; still the canonical spec in 2026) — https://github.com/solana-foundation/solana-improvement-documents/blob/main/proposals/0326-alpenglow.md

### SIMD-0525 / SIMD-525 — Reduce Slot Times

**Status:** Shipped with Agave 4.2 (August 2026); staged feature gates, pending full 200ms

Cut target slot time from 400ms to 200ms in four 50ms steps.

PR #525 in the SIMD repo landed as SIMD-0525 on 2026-05-14. The design keeps ticks_per_slot = 64, leader span = 4 slots, and epoch length = 432,000 slots. Per-slot CU / shred budgets scale down with slot time so wall-clock throughput does not silently jump. slots_per_year is scaled up so inflation stays roughly constant in wall-clock terms. Each gate becomes effective one epoch after activation so Turbine shred limits stay synchronized. Skip-rate is the published brake: the cluster is not supposed to take the next 50ms step if skips climb.

Agave 4.2 shipped August 2026 and is visible on public RPC as solana-core 4.2.0. Official upgrade copy still lists the 200ms end-state as pending feature activation. Northstar therefore treats SIMD-0525 as a live, staged rollout and compares measured slot time from getRecentPerformanceSamples against the 400/350/300/250/200 ms ladder instead of assuming the final target is already on.

Related SIMDs: SIMD-0525 Reduce Slot Times (GitHub PR #525); Related: SIMD-0357 VAT scaling with slot time

Sources:

- SIMD-0525 Reduce Slot Times (merged 2026-05-14) (created 2026-05-01, merged 2026-05-14) — https://github.com/solana-foundation/solana-improvement-documents/blob/main/proposals/0525-reduce-slot-times.md
- Reduced Slot Times upgrade page (updated August 2026) (2026-08) — https://solana.com/upgrades/reduced-slot-times
- Solana Network Upgrades — Agave 4.2 shipped August 2026 (checked 2026-08-25) — https://solana.com/news/solana-network-upgrades

### Agave 4.2 companions (rent, transaction size)

**Status:** Client shipped August 2026; feature gates pending/activating

90% rent reduction (phased) and 4096-byte transactions riding with 4.2.

The same Agave 4.2 train that carries SIMD-0525 also ships a staged 90% rent cut (target 696 lamports/byte vs 6,960) and a jump in max transaction size from 1232 to 4096 bytes. Those changes matter for tokenized assets and ZK-heavy programs that previously packed against the 1232-byte ceiling.

Sources:

- Solana Network Upgrades — Agave 4.2 (checked 2026-08-25) — https://solana.com/news/solana-network-upgrades

### Already live from Agave 4.1 (May 2026)

**Status:** Live on mainnet

100M CU blocks, XDP, optimized Token Program, VAT/BLS gates.

Agave 4.1 raised the block compute limit from 60M to 100M CU, enabled XDP kernel-bypass networking for block propagation, and shipped a much cheaper Token Program. Those pieces are the reason a 200ms slot target is even discussable: replay and networking had to get faster before the clock could.

Related SIMDs: SIMD-0286 / 100M CU blocks context

Sources:

- Solana Network Upgrades — Agave 4.1 shipped May 2026 (checked 2026-08-25) — https://solana.com/news/solana-network-upgrades

## Source health this run

| Source | Status | Detail |
| --- | --- | --- |
| Solana RPC | ok | https://api.mainnet-beta.solana.com |
| CoinGecko | fail | 24 ms · HTTP 429: {"status":{"error_code":429,"error_message":"You've exceeded the Rate Limit. Please visit https://www.coingecko.com/en/api/pric... |
| DeFiLlama price | ok | 636 ms |
| DeFiLlama 24h change | ok | 36 ms |
| DeFiLlama chains | ok | 38 ms |
| DeFiLlama TVL history | ok | 39 ms |
| DeFiLlama DEX | ok | 42 ms |
| DeFiLlama fees | ok | 45 ms |
| DeFiLlama revenue | ok | 1060 ms |
| DeFiLlama stablecoins | ok | 35 ms |
| DeFiLlama protocols | ok | 113 ms |
| Stakewiz validators | ok | 1083 ms |
| solana.com/data | ok | 832 ms |

## Automation

Refresh interval is `refresh_seconds` in `config.json` (default 300). `python3 -m northstar watch` loops; `python3 -m northstar serve` exposes the dashboard and can rebuild on a timer. History is appended to `data/history.jsonl` so later runs can z-score TPS against *this* machine's baseline.

---
Northstar · original collector · no API keys required.
