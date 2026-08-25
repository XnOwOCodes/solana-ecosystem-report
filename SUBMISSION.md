# Superteam Earn submission notes

Public repo placeholder (replace after you push):

```
https://github.com/XnOwOCodes/solana-ecosystem-report
```

Live dashboard placeholder (GitHub Pages, Cloudflare Pages, or a VPS running `python3 -m northstar serve --watch`):

```
https://xnowocodes.github.io/solana-ecosystem-report/
```

## What to paste into Superteam

**Title:** Northstar — a keyless, auto-updating Solana ecosystem report (dashboard + Markdown + JSON)

**Repo:** `https://github.com/XnOwOCodes/solana-ecosystem-report`

**Demo:** attach `samples/dashboard.html` / hosted URL, plus `samples/report.md`

**Checklist to tick in the form**

- Python project, original code, README with sources / automation / anomalies / how to run / how to interpret
- Live RPC: slot, block height, epoch, TPS, slot time, health, supply, vote accounts, priority fees
- DeFiLlama: TVL, DEX volume, fees, revenue, stablecoins, RWA/tokenized TVL
- CoinGecko attempted (falls back when 429)
- solana.com/data fetched; no keyless JSON, documented
- Dune/Twitter skipped (keys)
- Alpenglow + SIMD-0525 researched with 2026-dated sources
- `python3 -m northstar watch` / `serve --watch` for configurable refresh
- Anomaly desk (absolute + local z-score)
- Outputs: interactive dark HTML, Markdown, JSON
- No API keys, stdlib-only

## Pitch (one paragraph)

Northstar is a from-scratch Solana briefing machine: a stdlib Python pipeline that failovers across public RPCs, overlays DeFiLlama (and CoinGecko when it answers), names validators via Stakewiz, and writes three artifacts every few minutes — a dark interactive dashboard, a Markdown desk report, and JSON. It does not clone SolPulse; it treats SIMD-0525 as a measured slot-time ladder rather than a 400 ms constant, splits vote vs non-vote TPS, computes Nakamoto/HHI from `getVoteAccounts`, and keeps Alpenglow + SIMD-0525 as a sourced 2026 editorial block so operators can see both the live clock and the roadmap without buying a single API key.

## After you publish

1. Push this directory as a public GitHub repo (do not commit `.env`; there isn't one).
2. Replace the two placeholders above and the `user_agent` URL in `config.json`.
3. Optional: GitHub Action on a cron that runs `python3 -m northstar run` and deploys `output/` to Pages — still no secrets required.
4. Paste the pitch + repo + demo URL into the Earn listing before 2026-09-01.
