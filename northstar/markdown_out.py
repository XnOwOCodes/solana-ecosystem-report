from __future__ import annotations

from typing import Any

from .formatters import fmt_int, fmt_num, fmt_pct, fmt_sol, fmt_usd


def _cell(s: Any) -> str:
    return str(s if s is not None else "").replace("|", "/").replace("\n", " ")


def render_markdown(report: dict[str, Any]) -> str:
    n = report.get("network") or {}
    v = report.get("validators") or {}
    m = report.get("markets") or {}
    e = report.get("ecosystem") or {}
    u = report.get("upgrades") or {}
    a = report.get("anomalies") or []
    stage = report.get("slot_time_stage") or {}
    health = report.get("source_health") or []
    dex = m.get("dex") or {}
    fees = m.get("fees") or {}
    rev = m.get("revenue") or {}

    lines: list[str] = []
    w = lines.append
    w(f"# Northstar — Solana ecosystem report")
    w("")
    w(f"_Generated {report.get('generated_at')} (UTC). Local readers in Europe/Madrid: add two hours in summer (CEST)._")
    w("")
    w(f"**RPC:** `{n.get('rpc_endpoint')}` · **client seen:** `{n.get('rpc_version') or 'unknown'}` · **health:** {n.get('health')}")
    w("")
    w("Northstar is a keyless collector. Numbers below come from public Solana RPC, DeFiLlama, optional CoinGecko, Stakewiz names, and a static 2026 upgrade brief. They are a snapshot, not investment advice.")
    w("")
    w("## Headline gauges")
    w("")
    w("| Gauge | Value |")
    w("| --- | ---: |")
    w(f"| Slot / block height | {fmt_int(n.get('slot'))} / {fmt_int(n.get('block_height'))} |")
    w(f"| Epoch | {fmt_int(n.get('epoch'))} — {fmt_pct(n.get('epoch_progress_pct'))} complete |")
    w(f"| Epoch remaining (est.) | {fmt_num(n.get('epoch_eta_hours'), 1)} hours |")
    w(f"| TPS (all txs, ~15-sample median) | {fmt_num(n.get('tps_median_15m'), 0)} |")
    w(f"| Non-vote TPS (same window) | {fmt_num(n.get('nonvote_tps_median_15m'), 0)} |")
    w(f"| Slot time (median) | {fmt_num(n.get('slot_time_ms_median_15m'), 0)} ms |")
    w(f"| SIMD-0525 readout | {stage.get('nearest_label') or '—'} |")
    w(f"| SOL price | {fmt_usd(m.get('price_usd'), 2)} ({fmt_pct(m.get('change_24h_pct'), signed=True)}) via {m.get('price_source') or '—'} |")
    w(f"| Circulating SOL | {fmt_sol(n.get('supply_circulating_sol'))} |")
    w(f"| Market cap (price × circulating) | {fmt_usd(m.get('market_cap_usd'))} |")
    w(f"| DeFi TVL | {fmt_usd(m.get('tvl_usd'))} ({fmt_pct(m.get('tvl_change_1d_pct'), signed=True)} 1d) |")
    w(f"| DEX volume 24h | {fmt_usd(dex.get('total24h'))} ({fmt_pct(dex.get('change_1d'), signed=True)}) |")
    w(f"| App fees 24h | {fmt_usd(fees.get('total24h'))} |")
    w(f"| App revenue 24h | {fmt_usd(rev.get('total24h'))} |")
    w(f"| Stablecoin supply on Solana | {fmt_usd(m.get('stablecoin_mcap_usd'))} |")
    w(f"| Tokenized / RWA TVL on Solana | {fmt_usd(m.get('rwa_tvl_usd'))} ({fmt_int(m.get('rwa_count'))} protocols) |")
    w(f"| Median priority fee | {fmt_num(n.get('prio_fee_median'), 0)} µ-lamports/CU (nonzero median {fmt_num(n.get('prio_fee_median_nonzero'), 0)}) |")
    w(f"| Inflation (on-chain) | {fmt_pct((n.get('inflation_total') or 0) * 100 if n.get('inflation_total') is not None else None)} |")
    w("")
    w("## How to read TPS and slot time")
    w("")
    w("Solana RPC `getRecentPerformanceSamples` returns ~60-second windows. **All-tx TPS includes vote transactions** (consensus chatter). **Non-vote TPS** is closer to user and program load. Slot time is `samplePeriodSecs / numSlots`. During SIMD-0525 the target is no longer a fixed 400 ms; compare the measured median to the staged ladder (400 → 350 → 300 → 250 → 200).")
    w("")
    w(stage.get("interpretation") or "")
    w("")
    w("## Anomaly desk")
    w("")
    for flag in a:
        w(f"- **{flag.get('level', '').upper()}** — {flag.get('title')}: {flag.get('detail')}")
    w("")
    w("Rules mix hard thresholds (slow slots, delinquent stake, large 24h market moves) with a local z-score once this install has enough history. A first run will usually look quiet unless something is already outside the absolute bands.")
    w("")
    w("## Validators")
    w("")
    w(f"Active vote accounts: **{fmt_int(v.get('active_count'))}**. Delinquent: **{fmt_int(v.get('delinquent_count'))}** ({fmt_pct(v.get('delinquent_stake_pct'))} of activated stake).")
    w("")
    w(f"Nakamoto coefficient (33% of stake): **{fmt_int(v.get('nakamoto_33'))}**. Supermajority (66.7%): **{fmt_int(v.get('supermajority_66'))}**. Top-10 share: **{fmt_pct(v.get('top10_share_pct'))}**. HHI: **{fmt_num(v.get('hhi'), 0)}** (10,000 = monopoly).")
    w("")
    w(f"Median commission **{fmt_num(v.get('median_commission_pct'), 1)}%**. Zero-commission active: {fmt_int(v.get('zero_commission_count'))}. Commission ≥10%: {fmt_int(v.get('high_commission_count'))}.")
    w("")
    w("### Top validators by activated stake")
    w("")
    w("| Rank | Name | Stake | Share | Commission | Status | Version |")
    w("| ---: | --- | ---: | ---: | ---: | --- | --- |")
    for row in (v.get("top") or [])[:20]:
        w(
            f"| {row.get('rank')} | {_cell(row.get('name'))} | {fmt_sol(row.get('activated_stake_sol'))} | "
            f"{fmt_pct(row.get('stake_share_pct'))} | {fmt_num(row.get('commission'), 0)}% | "
            f"{_cell(row.get('status'))} | {_cell(row.get('version') or '—')} |"
        )
    w("")
    alerts = v.get("delinquency_alerts") or []
    if alerts:
        w("### Delinquency alerts (activated stake ≥ 10k SOL)")
        w("")
        for row in alerts:
            w(
                f"- {row.get('name')} — {fmt_sol(row.get('activated_stake_sol'))}, "
                f"last vote slot {fmt_int(row.get('last_vote'))}, vote `{row.get('vote')}`"
            )
        w("")
    else:
        w("No delinquent vote account currently holds ≥ 10k SOL.")
        w("")
    if v.get("versions"):
        w("### Client versions among active validators (Stakewiz overlay)")
        w("")
        for row in v["versions"][:8]:
            w(f"- `{row.get('version')}` — {fmt_int(row.get('count'))} validators, {fmt_sol(row.get('stake_sol'))}")
        w("")
    w("## Markets and DeFi")
    w("")
    w(f"Price source waterfall: CoinGecko if the demo API answers, otherwise DeFiLlama `coins.llama.fi`. This run used **{m.get('price_source') or 'none'}**.")
    w("")
    w("### Top DEX venues by 24h volume")
    w("")
    w("| Venue | 24h volume | 1d change |")
    w("| --- | ---: | ---: |")
    for row in (dex.get("top") or [])[:10]:
        w(f"| {_cell(row.get('name'))} | {fmt_usd(row.get('total24h'))} | {fmt_pct(row.get('change_1d'), signed=True)} |")
    w("")
    w("Fees and revenue are DeFiLlama *application* totals on Solana (swaps, lending spread, etc.), not the same object as Blockworks REV. They are the closest keyless REV-like series. Median priority fee comes from `getRecentPrioritizationFees` and is in micro-lamports per compute unit, including zeros.")
    w("")
    w("### Tokenized assets (RWA protocols with Solana TVL)")
    w("")
    for row in (m.get("rwa_top") or [])[:10]:
        w(f"- **{row.get('name')}** — {fmt_usd(row.get('tvl_solana'))}")
    if not m.get("rwa_top"):
        w("_No RWA protocols returned a Solana chain TVL in this run._")
    w("")
    w("## Ecosystem coverage notes")
    w("")
    w(e.get("solana_data_note") or "")
    w("")
    w(f"- solana.com/data fetch: {'ok' if e.get('solana_data_fetchable') else 'failed'} (HTTP {e.get('solana_data_status')}, {fmt_int(e.get('solana_data_bytes'))} bytes).")
    dune = e.get("dune") or {}
    tw = e.get("twitter") or {}
    daa = e.get("daily_active_addresses") or {}
    w(f"- Dune: {dune.get('reason')}")
    w(f"- Twitter/X: {tw.get('reason')}")
    w(f"- Daily active addresses: {daa.get('reason')}")
    w("")
    w("## Upcoming and in-flight upgrades (researched 2026-08-25)")
    w("")
    w(u.get("disclaimer") or "")
    w("")
    for item in u.get("items") or []:
        w(f"### {item.get('title')}")
        w("")
        w(f"**Status:** {item.get('status')}")
        w("")
        w(item.get("headline") or "")
        w("")
        w(item.get("summary") or "")
        w("")
        if item.get("operator_notes"):
            w(item["operator_notes"])
            w("")
        if item.get("simds"):
            w("Related SIMDs: " + "; ".join(item["simds"]))
            w("")
        w("Sources:")
        w("")
        for src in item.get("sources") or []:
            w(f"- {src.get('title')} ({src.get('dated')}) — {src.get('url')}")
        w("")
    w("## Source health this run")
    w("")
    w("| Source | Status | Detail |")
    w("| --- | --- | --- |")
    for row in health:
        mark = "ok" if row.get("ok") else "fail"
        extra = row.get("detail") or row.get("error") or ""
        extra = extra.replace("|", "/").replace("\n", " ")
        if len(extra) > 140:
            extra = extra[:137] + "..."
        if row.get("ms") is not None:
            extra = f"{row.get('ms')} ms · {extra}".strip(" ·")
        w(f"| {row.get('name')} | {mark} | {extra} |")
    w("")
    w("## Automation")
    w("")
    w("Refresh interval is `refresh_seconds` in `config.json` (default 300). `python3 -m northstar watch` loops; `python3 -m northstar serve` exposes the dashboard and can rebuild on a timer. History is appended to `data/history.jsonl` so later runs can z-score TPS against *this* machine's baseline.")
    w("")
    w("---")
    w("Northstar · original collector · no API keys required.")
    return "\n".join(lines) + "\n"
