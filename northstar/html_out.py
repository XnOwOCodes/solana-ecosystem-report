from __future__ import annotations

import json
from typing import Any

from .formatters import escape, fmt_int, fmt_num, fmt_pct, fmt_sol, fmt_usd


def _sparkline(samples: list[dict[str, Any]], key: str, width: int = 320, height: int = 72) -> str:
    vals = [s.get(key) for s in reversed(samples) if s.get(key) is not None]
    if len(vals) < 2:
        return f'<svg class="spark" viewBox="0 0 {width} {height}"></svg>'
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    pts = []
    for i, v in enumerate(vals):
        x = i * (width / (len(vals) - 1))
        y = height - 6 - ((v - lo) / span) * (height - 14)
        pts.append(f"{x:.1f},{y:.1f}")
    last = vals[-1]
    return (
        f'<svg class="spark" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{escape(key)} sparkline">'
        f'<polyline fill="none" stroke="currentColor" stroke-width="2" points="{" ".join(pts)}"/>'
        f'<text x="{width-6}" y="14" text-anchor="end" class="spark-label">{fmt_num(last, 0)}</text>'
        f"</svg>"
    )


def _donut(top10: float | None, rest: float | None) -> str:
    a = max(0.0, float(top10 or 0))
    b = max(0.0, float(rest or 0))
    total = a + b or 1.0
    # stroke-dasharray on r=40, C=2*pi*40 ≈ 251.3
    c = 251.327
    a_len = c * (a / total)
    b_len = c - a_len
    return f"""
    <svg class="donut" viewBox="0 0 120 120" role="img" aria-label="stake share donut">
      <circle cx="60" cy="60" r="40" fill="none" stroke="#2a3448" stroke-width="16"/>
      <circle cx="60" cy="60" r="40" fill="none" stroke="#e0a36a" stroke-width="16"
        stroke-dasharray="{a_len:.1f} {b_len:.1f}" stroke-dashoffset="62.8"
        transform="rotate(-90 60 60)"/>
      <text x="60" y="56" text-anchor="middle" class="donut-n">{a:.0f}%</text>
      <text x="60" y="72" text-anchor="middle" class="donut-l">top 10</text>
    </svg>
    """


def _bar(pct: float | None) -> str:
    x = max(0.0, min(100.0, float(pct or 0)))
    return f'<div class="bar"><span style="width:{x:.2f}%"></span><em>{x:.1f}%</em></div>'


def render_html(report: dict[str, Any]) -> str:
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
    payload = json.dumps(
        {
            "generated_at": report.get("generated_at"),
            "validators": v.get("top") or [],
            "samples": (n.get("samples") or [])[:60],
        },
        default=str,
    )

    chips = []
    for flag in a:
        chips.append(
            f'<span class="chip chip-{escape(flag.get("level"))}" title="{escape(flag.get("detail"))}">'
            f"{escape(flag.get('title'))}</span>"
        )

    val_rows = []
    for row in v.get("top") or []:
        val_rows.append(
            "<tr>"
            f"<td>{row.get('rank')}</td>"
            f"<td>{escape(row.get('name'))}</td>"
            f"<td class='num'>{escape(fmt_sol(row.get('activated_stake_sol')))}</td>"
            f"<td class='num'>{escape(fmt_pct(row.get('stake_share_pct')))}</td>"
            f"<td class='num'>{escape(fmt_num(row.get('commission'), 0))}%</td>"
            f"<td><span class='pill pill-{escape(row.get('status'))}'>{escape(row.get('status'))}</span></td>"
            f"<td>{escape(row.get('version') or '—')}</td>"
            "</tr>"
        )

    dex_rows = []
    for row in (dex.get("top") or [])[:10]:
        dex_rows.append(
            f"<tr><td>{escape(row.get('name'))}</td>"
            f"<td class='num'>{escape(fmt_usd(row.get('total24h')))}</td>"
            f"<td class='num'>{escape(fmt_pct(row.get('change_1d'), signed=True))}</td></tr>"
        )

    rwa_rows = []
    for row in (m.get("rwa_top") or [])[:10]:
        rwa_rows.append(
            f"<tr><td>{escape(row.get('name'))}</td>"
            f"<td class='num'>{escape(fmt_usd(row.get('tvl_solana')))}</td></tr>"
        )

    upgrade_cards = []
    for item in u.get("items") or []:
        srcs = "".join(
            f"<li><a href='{escape(s.get('url'))}' target='_blank' rel='noopener'>"
            f"{escape(s.get('title'))}</a> <span class='muted'>{escape(s.get('dated'))}</span></li>"
            for s in item.get("sources") or []
        )
        upgrade_cards.append(
            f"<article class='card upgrade'>"
            f"<p class='eyebrow'>{escape(item.get('status'))}</p>"
            f"<h3>{escape(item.get('title'))}</h3>"
            f"<p class='lede'>{escape(item.get('headline'))}</p>"
            f"<p>{escape(item.get('summary'))}</p>"
            + (f"<p class='note'>{escape(item.get('operator_notes'))}</p>" if item.get("operator_notes") else "")
            + f"<ul class='sources'>{srcs}</ul></article>"
        )

    health_rows = []
    for row in health:
        cls = "ok" if row.get("ok") else "fail"
        extra = row.get("detail") or row.get("error") or ""
        health_rows.append(
            f"<tr><td>{escape(row.get('name'))}</td>"
            f"<td><span class='pill pill-{cls}'>{cls}</span></td>"
            f"<td class='muted'>{escape(extra)}</td>"
            f"<td class='num'>{escape(str(row.get('ms') or '—'))}</td></tr>"
        )

    alert_html = ""
    for row in v.get("delinquency_alerts") or []:
        alert_html += (
            f"<li><strong>{escape(row.get('name'))}</strong> · {escape(fmt_sol(row.get('activated_stake_sol')))} · "
            f"last vote {escape(fmt_int(row.get('last_vote')))}</li>"
        )
    if not alert_html:
        alert_html = "<li class='muted'>No delinquent vote account currently holds ≥ 10k SOL.</li>"

    version_html = "".join(
        f"<li><code>{escape(row.get('version'))}</code> · {escape(fmt_int(row.get('count')))} · "
        f"{escape(fmt_sol(row.get('stake_sol')))}</li>"
        for row in (v.get("versions") or [])[:8]
    )

    samples = n.get("samples") or []
    rest_share = None
    if v.get("top10_share_pct") is not None:
        rest_share = 100.0 - float(v.get("top10_share_pct"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Northstar · Solana ecosystem</title>
<style>
:root {{
  --bg: #0b0e13;
  --bg2: #121722;
  --card: #171d29;
  --line: #2b3548;
  --text: #e7edf7;
  --muted: #8d97ab;
  --copper: #e0a36a;
  --teal: #5ee0d0;
  --ok: #7fd99a;
  --warn: #e6c35c;
  --fail: #f07178;
  --info: #7eb6ff;
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--text);
  font: 16px/1.5 ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; }}
body {{ background-image:
  radial-gradient(1200px 500px at 10% -10%, rgba(224,163,106,.08), transparent 50%),
  radial-gradient(900px 400px at 110% 0%, rgba(94,224,208,.06), transparent 45%),
  linear-gradient(180deg, rgba(255,255,255,.02) 1px, transparent 1px),
  linear-gradient(90deg, rgba(255,255,255,.02) 1px, transparent 1px);
  background-size: auto, auto, 48px 48px, 48px 48px; }}
a {{ color: var(--teal); }}
header.hero {{ padding: 2.2rem 6vw 1rem; border-bottom: 1px solid var(--line); }}
.kicker {{ letter-spacing: .18em; text-transform: uppercase; color: var(--copper); font-size: .72rem; }}
h1 {{ font-size: clamp(1.8rem, 4vw, 3rem); margin: .2rem 0 .4rem; font-weight: 650; }}
.sub {{ color: var(--muted); max-width: 70ch; }}
nav.toc {{ display: flex; gap: .6rem; flex-wrap: wrap; padding: .8rem 6vw; position: sticky; top: 0;
  background: rgba(11,14,19,.92); backdrop-filter: blur(8px); border-bottom: 1px solid var(--line); z-index: 5; }}
nav.toc a {{ color: var(--text); text-decoration: none; font-size: .85rem; padding: .25rem .55rem; border: 1px solid var(--line); border-radius: 999px; }}
nav.toc a:hover {{ border-color: var(--copper); color: var(--copper); }}
main {{ padding: 1.5rem 6vw 4rem; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: .9rem; }}
.card {{ background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 1rem 1.1rem; }}
.card .label {{ color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; }}
.card .value {{ font-size: 1.45rem; font-variant-numeric: tabular-nums; margin-top: .15rem; }}
.card .hint {{ color: var(--muted); font-size: .8rem; }}
section {{ margin-top: 2.2rem; }}
h2 {{ font-size: 1.35rem; margin: 0 0 .8rem; }}
.chips {{ display: flex; flex-wrap: wrap; gap: .45rem; margin: .6rem 0 1rem; }}
.chip {{ font-size: .78rem; padding: .2rem .55rem; border-radius: 999px; border: 1px solid var(--line); }}
.chip-ok {{ color: var(--ok); border-color: #2f5; }}
.chip-info {{ color: var(--info); }}
.chip-warning {{ color: var(--warn); border-color: var(--warn); }}
.chip-critical {{ color: var(--fail); border-color: var(--fail); }}
.pill {{ font-size: .72rem; padding: .1rem .45rem; border-radius: 999px; border: 1px solid var(--line); }}
.pill-active, .pill-ok {{ color: var(--ok); }}
.pill-delinquent, .pill-fail {{ color: var(--fail); }}
table {{ width: 100%; border-collapse: collapse; font-size: .92rem; }}
th, td {{ text-align: left; padding: .45rem .4rem; border-bottom: 1px solid var(--line); }}
th {{ color: var(--muted); font-weight: 600; cursor: pointer; }}
td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.muted {{ color: var(--muted); }}
.bar {{ position: relative; height: 1.1rem; background: #222a38; border-radius: 999px; overflow: hidden; }}
.bar span {{ display: block; height: 100%; background: linear-gradient(90deg, var(--copper), var(--teal)); }}
.bar em {{ position: absolute; right: .4rem; top: 0; font-size: .75rem; font-style: normal; }}
.spark {{ width: 100%; height: 72px; color: var(--teal); }}
.spark-label {{ fill: var(--muted); font-size: 11px; }}
.donut {{ width: 140px; height: 140px; }}
.donut-n {{ fill: var(--text); font-size: 16px; font-weight: 650; }}
.donut-l {{ fill: var(--muted); font-size: 9px; }}
.split {{ display: grid; grid-template-columns: 1.2fr .8fr; gap: 1rem; }}
@media (max-width: 900px) {{ .split {{ grid-template-columns: 1fr; }} }}
input[type=search] {{ width: 100%; max-width: 320px; background: var(--bg2); color: var(--text);
  border: 1px solid var(--line); border-radius: 8px; padding: .45rem .7rem; }}
.upgrade h3 {{ margin: .2rem 0; }}
.eyebrow {{ color: var(--copper); font-size: .78rem; margin: 0; }}
.lede {{ font-weight: 600; }}
.note {{ color: var(--muted); }}
.sources {{ padding-left: 1.1rem; }}
footer {{ padding: 2rem 6vw; color: var(--muted); border-top: 1px solid var(--line); font-size: .85rem; }}
</style>
</head>
<body>
<header class="hero">
  <div class="kicker">Northstar · living Solana meridian</div>
  <h1>Current state of the Solana ecosystem</h1>
  <p class="sub">Snapshot generated <strong>{escape(report.get('generated_at'))}</strong> UTC
    from public RPC <code>{escape(n.get('rpc_endpoint'))}</code>
    (client {escape(n.get('rpc_version') or 'unknown')}). Open this file directly or via
    <code>python3 -m northstar serve</code>. Not investment advice.</p>
  <div class="chips">{''.join(chips)}</div>
</header>
<nav class="toc">
  <a href="#network">Network</a>
  <a href="#validators">Validators</a>
  <a href="#markets">Markets</a>
  <a href="#ecosystem">Ecosystem</a>
  <a href="#upgrades">Upgrades</a>
  <a href="#sources">Sources</a>
  <a href="report.md">Markdown</a>
  <a href="report.json">JSON</a>
</nav>
<main>
<section id="network">
  <h2>Network pulse</h2>
  <div class="grid">
    <article class="card"><div class="label">TPS (all txs)</div><div class="value">{escape(fmt_num(n.get('tps_median_15m'), 0))}</div><div class="hint">15-sample median · latest {escape(fmt_num(n.get('tps_latest'), 0))}</div></article>
    <article class="card"><div class="label">Non-vote TPS</div><div class="value">{escape(fmt_num(n.get('nonvote_tps_median_15m'), 0))}</div><div class="hint">user/program load, votes stripped</div></article>
    <article class="card"><div class="label">Slot time</div><div class="value">{escape(fmt_num(n.get('slot_time_ms_median_15m'), 0))} ms</div><div class="hint">{escape(stage.get('nearest_label') or '')}</div></article>
    <article class="card"><div class="label">Slot / height</div><div class="value">{escape(fmt_int(n.get('slot')))}</div><div class="hint">block height {escape(fmt_int(n.get('block_height')))}</div></article>
    <article class="card"><div class="label">Epoch {escape(fmt_int(n.get('epoch')))}</div><div class="value">{escape(fmt_pct(n.get('epoch_progress_pct')))}</div>{_bar(n.get('epoch_progress_pct'))}<div class="hint">~{escape(fmt_num(n.get('epoch_eta_hours'), 1))} h remaining</div></article>
    <article class="card"><div class="label">Health</div><div class="value">{escape(n.get('health'))}</div><div class="hint">getHealth · inflation {escape(fmt_pct((n.get('inflation_total') or 0)*100 if n.get('inflation_total') is not None else None))}</div></article>
    <article class="card"><div class="label">Median priority fee</div><div class="value">{escape(fmt_num(n.get('prio_fee_median'), 0))}</div><div class="hint">µ-lamports / CU · p90 {escape(fmt_num(n.get('prio_fee_p90'), 0))} · nonzero median {escape(fmt_num(n.get('prio_fee_median_nonzero'), 0))}</div></article>
    <article class="card"><div class="label">Circulating supply</div><div class="value">{escape(fmt_sol(n.get('supply_circulating_sol')))}</div><div class="hint">total {escape(fmt_sol(n.get('supply_total_sol')))}</div></article>
  </div>
  <div class="split" style="margin-top:1rem">
    <article class="card">
      <div class="label">TPS, last ~60 minutes</div>
      {_sparkline(samples, 'tps')}
      <div class="hint">Includes votes. Non-vote sparkline below.</div>
      {_sparkline(samples, 'nonvote_tps')}
    </article>
    <article class="card">
      <div class="label">Slot time, last ~60 minutes</div>
      {_sparkline(samples, 'slot_time_ms')}
      <p class="hint">{escape(stage.get('interpretation') or '')}</p>
    </article>
  </div>
</section>

<section id="validators">
  <h2>Validator set</h2>
  <div class="grid">
    <article class="card"><div class="label">Active / delinquent</div><div class="value">{escape(fmt_int(v.get('active_count')))} / {escape(fmt_int(v.get('delinquent_count')))}</div><div class="hint">{escape(fmt_pct(v.get('delinquent_stake_pct')))} of stake delinquent</div></article>
    <article class="card"><div class="label">Nakamoto (33%)</div><div class="value">{escape(fmt_int(v.get('nakamoto_33')))}</div><div class="hint">supermajority 66.7% = {escape(fmt_int(v.get('supermajority_66')))}</div></article>
    <article class="card"><div class="label">HHI</div><div class="value">{escape(fmt_num(v.get('hhi'), 0))}</div><div class="hint">10,000 = one validator has it all</div></article>
    <article class="card"><div class="label">Median commission</div><div class="value">{escape(fmt_num(v.get('median_commission_pct'), 1))}%</div><div class="hint">{escape(fmt_int(v.get('zero_commission_count')))} at 0% · {escape(fmt_int(v.get('high_commission_count')))} at ≥10%</div></article>
  </div>
  <div class="split" style="margin-top:1rem">
    <article class="card">
      <div class="label">Search top validators</div>
      <p><input id="q" type="search" placeholder="Filter by name, vote, version…"/></p>
      <div style="overflow:auto">
        <table id="vt">
          <thead><tr>
            <th data-k="rank">#</th><th data-k="name">Name</th><th class="num" data-k="activated_stake_sol">Stake</th>
            <th class="num" data-k="stake_share_pct">Share</th><th class="num" data-k="commission">Comm.</th>
            <th data-k="status">Status</th><th data-k="version">Version</th>
          </tr></thead>
          <tbody>{''.join(val_rows)}</tbody>
        </table>
      </div>
    </article>
    <div>
      <article class="card">
        <div class="label">Stake in the top 10</div>
        {_donut(v.get('top10_share_pct'), rest_share)}
        <p class="hint">Top-20 share {escape(fmt_pct(v.get('top20_share_pct')))}. Names overlay from Stakewiz when that public API answers; stake itself is RPC <code>getVoteAccounts</code>.</p>
      </article>
      <article class="card" style="margin-top:.9rem">
        <div class="label">Delinquency alerts</div>
        <ul>{alert_html}</ul>
      </article>
      <article class="card" style="margin-top:.9rem">
        <div class="label">Client versions (active, named overlay)</div>
        <ul>{version_html or '<li class="muted">Stakewiz overlay unavailable this run.</li>'}</ul>
      </article>
    </div>
  </div>
</section>

<section id="markets">
  <h2>Markets, fees, tokenized assets</h2>
  <div class="grid">
    <article class="card"><div class="label">SOL</div><div class="value">{escape(fmt_usd(m.get('price_usd'), 2))}</div><div class="hint">{escape(fmt_pct(m.get('change_24h_pct'), signed=True))} 24h · {escape(m.get('price_source') or '—')}</div></article>
    <article class="card"><div class="label">Market cap</div><div class="value">{escape(fmt_usd(m.get('market_cap_usd')))}</div><div class="hint">price × circulating supply</div></article>
    <article class="card"><div class="label">DeFi TVL</div><div class="value">{escape(fmt_usd(m.get('tvl_usd')))}</div><div class="hint">{escape(fmt_pct(m.get('tvl_change_1d_pct'), signed=True))} 1d · {escape(fmt_pct(m.get('tvl_change_7d_pct'), signed=True))} 7d</div></article>
    <article class="card"><div class="label">DEX volume 24h</div><div class="value">{escape(fmt_usd(dex.get('total24h')))}</div><div class="hint">{escape(fmt_pct(dex.get('change_1d'), signed=True))} vs previous day</div></article>
    <article class="card"><div class="label">App fees 24h</div><div class="value">{escape(fmt_usd(fees.get('total24h')))}</div><div class="hint">DeFiLlama application fees</div></article>
    <article class="card"><div class="label">App revenue 24h</div><div class="value">{escape(fmt_usd(rev.get('total24h')))}</div><div class="hint">closest keyless REV-like series</div></article>
    <article class="card"><div class="label">Stablecoins on Solana</div><div class="value">{escape(fmt_usd(m.get('stablecoin_mcap_usd')))}</div><div class="hint">DeFiLlama circulating USD-pegged + others</div></article>
    <article class="card"><div class="label">Tokenized / RWA TVL</div><div class="value">{escape(fmt_usd(m.get('rwa_tvl_usd')))}</div><div class="hint">{escape(fmt_int(m.get('rwa_count')))} protocols with Solana TVL</div></article>
  </div>
  <div class="split" style="margin-top:1rem">
    <article class="card">
      <div class="label">Top DEX venues</div>
      <table><thead><tr><th>Venue</th><th class="num">24h</th><th class="num">1d</th></tr></thead>
      <tbody>{''.join(dex_rows) or '<tr><td colspan="3" class="muted">DEX overview unavailable</td></tr>'}</tbody></table>
    </article>
    <article class="card">
      <div class="label">Tokenized asset protocols</div>
      <table><thead><tr><th>Protocol</th><th class="num">Solana TVL</th></tr></thead>
      <tbody>{''.join(rwa_rows) or '<tr><td colspan="2" class="muted">No RWA rows</td></tr>'}</tbody></table>
    </article>
  </div>
</section>

<section id="ecosystem">
  <h2>Ecosystem coverage</h2>
  <article class="card">
    <p>{escape(e.get('solana_data_note'))}</p>
    <p>solana.com/data this run: <strong>{'reachable' if e.get('solana_data_fetchable') else 'not reachable'}</strong>
      (HTTP {escape(str(e.get('solana_data_status')))}, {escape(fmt_int(e.get('solana_data_bytes')))} bytes).</p>
    <p class="muted">Dune: {escape((e.get('dune') or {}).get('reason'))}<br/>
    Twitter/X: {escape((e.get('twitter') or {}).get('reason'))}<br/>
    Daily active addresses: {escape((e.get('daily_active_addresses') or {}).get('reason'))}</p>
  </article>
</section>

<section id="upgrades">
  <h2>Upgrades on the 2026 clock</h2>
  <p class="muted">{escape(u.get('disclaimer'))}</p>
  <div class="grid">{''.join(upgrade_cards)}</div>
</section>

<section id="sources">
  <h2>Source health</h2>
  <article class="card" style="overflow:auto">
    <table>
      <thead><tr><th>Source</th><th>Status</th><th>Detail</th><th class="num">ms</th></tr></thead>
      <tbody>{''.join(health_rows)}</tbody>
    </table>
  </article>
</section>
</main>
<footer>
  Northstar writes three artifacts each run: this dashboard, <a href="report.md">report.md</a>, and <a href="report.json">report.json</a>.
  Automation: <code>python3 -m northstar watch</code> or <code>serve --watch</code>. Stdlib only. Original architecture — not a SolPulse fork.
</footer>
<script>
const DATA = {payload};
const q = document.getElementById('q');
const tbody = document.querySelector('#vt tbody');
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}})[c]);
function rowsFrom(list) {{
  return list.map(r => `<tr>
    <td>${{r.rank}}</td><td>${{esc(r.name || '')}}</td>
    <td class="num">${{(r.activated_stake_sol||0).toLocaleString(undefined, {{maximumFractionDigits:0}})}} SOL</td>
    <td class="num">${{(r.stake_share_pct||0).toFixed(2)}}%</td>
    <td class="num">${{r.commission}}%</td>
    <td><span class="pill pill-${{esc(r.status)}}">${{esc(r.status)}}</span></td>
    <td>${{esc(r.version || '—')}}</td></tr>`).join('');
}}
if (q) q.addEventListener('input', () => {{
  const s = q.value.toLowerCase();
  const filtered = DATA.validators.filter(r => JSON.stringify(r).toLowerCase().includes(s));
  tbody.innerHTML = rowsFrom(filtered);
}});
document.querySelectorAll('#vt th[data-k]').forEach(th => {{
  th.addEventListener('click', () => {{
    const k = th.getAttribute('data-k');
    DATA.validators.sort((a,b) => (a[k] > b[k] ? 1 : -1));
    tbody.innerHTML = rowsFrom(DATA.validators);
  }});
}});
</script>
</body>
</html>
"""
