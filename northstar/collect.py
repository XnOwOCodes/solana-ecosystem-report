from __future__ import annotations

import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

from .net import FetchResult, HttpClient
from .rpc import RpcCluster

LAMPORTS = 1_000_000_000


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _num(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _median(values: list[float]) -> float | None:
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return float(statistics.median(clean))


def _pctile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    idx = min(len(ordered) - 1, max(0, int(round((p / 100) * (len(ordered) - 1)))))
    return float(ordered[idx])


def collect_http_sources(client: HttpClient, sources: dict[str, str]) -> dict[str, FetchResult]:
    results: dict[str, FetchResult] = {}

    def one(name: str, url: str) -> tuple[str, FetchResult]:
        return name, client.request(url)

    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(one, name, url) for name, url in sources.items()]
        for fut in as_completed(futs):
            name, result = fut.result()
            results[name] = result
    return results


def collect_rpc(cluster: RpcCluster, sample_count: int = 60) -> dict[str, Any]:
    out: dict[str, Any] = {"ok": True, "errors": []}

    def need(method: str, params: list[Any] | None = None) -> Any:
        res = cluster.call(method, params)
        if not res.ok:
            out["errors"].append({"method": method, "error": res.error, "url": res.url})
            return None
        data = res.data
        if isinstance(data, dict):
            return data.get("result")
        return None

    out["health"] = need("getHealth")
    out["version"] = need("getVersion")
    out["slot"] = need("getSlot")
    out["epoch"] = need("getEpochInfo")
    slot = out.get("slot")
    out["block_time"] = need("getBlockTime", [slot]) if isinstance(slot, int) else None
    out["samples"] = need("getRecentPerformanceSamples", [sample_count]) or []
    out["supply"] = need("getSupply", [{"commitment": "finalized", "excludeNonCirculatingAccountsList": True}])
    out["inflation"] = need("getInflationRate")
    out["prio_fees"] = need("getRecentPrioritizationFees") or []
    out["vote_accounts"] = need("getVoteAccounts", [{"commitment": "finalized"}])
    out["cluster_nodes"] = need("getClusterNodes")
    out["rpc_endpoint"] = cluster.active
    out["rpc_log"] = cluster.log
    out["ok"] = len(out["errors"]) == 0 or bool(out.get("epoch") or out.get("samples"))
    return out


def interpret_network(rpc: dict[str, Any]) -> dict[str, Any]:
    epoch = rpc.get("epoch") or {}
    samples = rpc.get("samples") or []
    supply_wrap = rpc.get("supply") or {}
    supply = supply_wrap.get("value") if isinstance(supply_wrap, dict) else {}
    inflation = rpc.get("inflation") or {}
    version = rpc.get("version") or {}

    parsed_samples = []
    for row in samples:
        period = _num(row.get("samplePeriodSecs")) or 60.0
        slots = _num(row.get("numSlots")) or 0.0
        txs = _num(row.get("numTransactions")) or 0.0
        nonvote = _num(row.get("numNonVoteTransactions"))
        slot_time_ms = (period * 1000.0 / slots) if slots else None
        tps = txs / period if period else None
        nv_tps = (nonvote / period) if (nonvote is not None and period) else None
        parsed_samples.append(
            {
                "slot": row.get("slot"),
                "period_s": period,
                "slots": slots,
                "transactions": txs,
                "nonvote": nonvote,
                "slot_time_ms": slot_time_ms,
                "tps": tps,
                "nonvote_tps": nv_tps,
            }
        )

    recent = parsed_samples[:15]
    latest = parsed_samples[0] if parsed_samples else {}
    slot_index = _num(epoch.get("slotIndex"))
    slots_in_epoch = _num(epoch.get("slotsInEpoch"))
    epoch_pct = (100.0 * slot_index / slots_in_epoch) if slot_index is not None and slots_in_epoch else None
    remaining_slots = (slots_in_epoch - slot_index) if slot_index is not None and slots_in_epoch else None
    median_slot_ms = _median([s["slot_time_ms"] for s in recent if s.get("slot_time_ms")])
    eta_hours = None
    if remaining_slots is not None and median_slot_ms:
        eta_hours = remaining_slots * median_slot_ms / 3_600_000.0

    circulating = _num((supply or {}).get("circulating"))
    total = _num((supply or {}).get("total"))
    noncirc = _num((supply or {}).get("nonCirculating"))

    fees = rpc.get("prio_fees") or []
    fee_vals = [_num(x.get("prioritizationFee"), 0.0) or 0.0 for x in fees if isinstance(x, dict)]
    nonzero = [v for v in fee_vals if v > 0]

    health = rpc.get("health")
    healthy = health == "ok" or health is True

    return {
        "health": "ok" if healthy else (health if health is not None else "unknown"),
        "healthy": bool(healthy),
        "rpc_endpoint": rpc.get("rpc_endpoint"),
        "rpc_version": (version or {}).get("solana-core"),
        "feature_set": (version or {}).get("feature-set"),
        "slot": rpc.get("slot"),
        "block_height": epoch.get("blockHeight"),
        "block_time_unix": rpc.get("block_time"),
        "transaction_count": epoch.get("transactionCount"),
        "epoch": epoch.get("epoch"),
        "slot_index": epoch.get("slotIndex"),
        "slots_in_epoch": epoch.get("slotsInEpoch"),
        "epoch_progress_pct": epoch_pct,
        "epoch_remaining_slots": remaining_slots,
        "epoch_eta_hours": eta_hours,
        "tps_latest": latest.get("tps"),
        "nonvote_tps_latest": latest.get("nonvote_tps"),
        "tps_median_15m": _median([s["tps"] for s in recent if s.get("tps")]),
        "nonvote_tps_median_15m": _median([s["nonvote_tps"] for s in recent if s.get("nonvote_tps")]),
        "slot_time_ms_latest": latest.get("slot_time_ms"),
        "slot_time_ms_median_15m": median_slot_ms,
        "samples": parsed_samples[:60],
        "supply_total_sol": (total / LAMPORTS) if total is not None else None,
        "supply_circulating_sol": (circulating / LAMPORTS) if circulating is not None else None,
        "supply_noncirculating_sol": (noncirc / LAMPORTS) if noncirc is not None else None,
        "inflation_total": _num((inflation or {}).get("total")),
        "inflation_validator": _num((inflation or {}).get("validator")),
        "prio_fee_median": _median(fee_vals),
        "prio_fee_p90": _pctile(fee_vals, 90),
        "prio_fee_median_nonzero": _median(nonzero),
        "prio_fee_unit": "micro-lamports per compute unit",
        "cluster_node_count": len(rpc.get("cluster_nodes") or []) or None,
        "errors": rpc.get("errors") or [],
    }


def interpret_validators(rpc: dict[str, Any], stakewiz: Any) -> dict[str, Any]:
    votes = rpc.get("vote_accounts") or {}
    current = votes.get("current") or []
    delinquent = votes.get("delinquent") or []
    names: dict[str, dict[str, Any]] = {}
    if isinstance(stakewiz, list):
        for row in stakewiz:
            vote = row.get("vote_identity") or row.get("votePubkey")
            if vote:
                names[vote] = {
                    "name": row.get("name") or row.get("moniker") or "",
                    "identity": row.get("identity") or row.get("nodePubkey"),
                    "version": row.get("version"),
                    "skip_rate": row.get("skip_rate"),
                    "website": row.get("website"),
                }

    def pack(row: dict[str, Any], status: str) -> dict[str, Any]:
        vote = row.get("votePubkey")
        extra = names.get(vote, {})
        stake = _num(row.get("activatedStake"), 0.0) or 0.0
        return {
            "vote": vote,
            "identity": row.get("nodePubkey") or extra.get("identity"),
            "name": extra.get("name") or (vote[:8] + "…" if vote else "unknown"),
            "commission": row.get("commission"),
            "activated_stake_sol": stake / LAMPORTS,
            "activated_stake_lamports": stake,
            "last_vote": row.get("lastVote"),
            "root_slot": row.get("rootSlot"),
            "epoch_vote_account": row.get("epochVoteAccount"),
            "status": status,
            "version": extra.get("version"),
            "skip_rate": extra.get("skip_rate"),
        }

    active = [pack(r, "active") for r in current]
    delin = [pack(r, "delinquent") for r in delinquent]
    all_rows = active + delin
    total_stake = sum(r["activated_stake_sol"] for r in all_rows) or 0.0
    active_stake = sum(r["activated_stake_sol"] for r in active)
    delin_stake = sum(r["activated_stake_sol"] for r in delin)
    ranked = sorted(all_rows, key=lambda r: r["activated_stake_sol"], reverse=True)
    for i, row in enumerate(ranked, 1):
        row["rank"] = i
        row["stake_share_pct"] = (100.0 * row["activated_stake_sol"] / total_stake) if total_stake else 0.0

    def concentration(threshold_pct: float) -> int | None:
        if not total_stake:
            return None
        acc = 0.0
        for i, row in enumerate(ranked, 1):
            acc += row["stake_share_pct"]
            if acc >= threshold_pct:
                return i
        return len(ranked)

    shares = [r["stake_share_pct"] / 100.0 for r in ranked]
    hhi = sum(s * s for s in shares) * 10_000 if shares else None
    commissions = [int(r["commission"]) for r in active if r.get("commission") is not None]
    zero_c = sum(1 for c in commissions if c == 0)
    high_c = sum(1 for c in commissions if c >= 10)
    alerts = [
        r
        for r in delin
        if r["activated_stake_sol"] >= 10_000
    ]
    alerts.sort(key=lambda r: r["activated_stake_sol"], reverse=True)

    versions: dict[str, dict[str, float | int]] = {}
    for row in active:
        ver = row.get("version") or "unknown"
        bucket = versions.setdefault(ver, {"count": 0, "stake_sol": 0.0})
        bucket["count"] = int(bucket["count"]) + 1
        bucket["stake_sol"] = float(bucket["stake_sol"]) + row["activated_stake_sol"]

    return {
        "active_count": len(active),
        "delinquent_count": len(delin),
        "total_count": len(all_rows),
        "active_stake_sol": active_stake,
        "delinquent_stake_sol": delin_stake,
        "total_stake_sol": total_stake,
        "delinquent_stake_pct": (100.0 * delin_stake / total_stake) if total_stake else None,
        "nakamoto_33": concentration(33.34),
        "supermajority_66": concentration(66.67),
        "top10_share_pct": sum(r["stake_share_pct"] for r in ranked[:10]),
        "top20_share_pct": sum(r["stake_share_pct"] for r in ranked[:20]),
        "hhi": hhi,
        "median_commission_pct": _median([float(c) for c in commissions]),
        "zero_commission_count": zero_c,
        "high_commission_count": high_c,
        "top": ranked[:25],
        "delinquency_alerts": alerts[:15],
        "versions": [
            {"version": k, "count": int(v["count"]), "stake_sol": float(v["stake_sol"])}
            for k, v in sorted(versions.items(), key=lambda kv: kv[1]["stake_sol"], reverse=True)
        ],
        "stakewiz_enriched": bool(names),
        "stakewiz_count": len(names),
    }


def interpret_markets(http: dict[str, FetchResult], network: dict[str, Any]) -> dict[str, Any]:
    sources_used: list[str] = []
    price = None
    change_24h = None
    volume_24h = None
    market_cap = None
    price_source = None

    cg = http.get("coingecko_simple")
    if cg and cg.ok and isinstance(cg.data, dict) and "solana" in cg.data:
        sol = cg.data["solana"]
        price = _num(sol.get("usd"))
        change_24h = _num(sol.get("usd_24h_change"))
        volume_24h = _num(sol.get("usd_24h_vol"))
        market_cap = _num(sol.get("usd_market_cap"))
        price_source = "CoinGecko"
        sources_used.append("CoinGecko /simple/price")

    if price is None:
        llama_p = http.get("llama_price")
        if llama_p and llama_p.ok and isinstance(llama_p.data, dict):
            coin = (llama_p.data.get("coins") or {}).get("coingecko:solana") or {}
            price = _num(coin.get("price"))
            if price is not None:
                price_source = "DeFiLlama coins"
                sources_used.append("DeFiLlama coins.llama.fi")
        llama_pct = http.get("llama_pct")
        if llama_pct and llama_pct.ok and isinstance(llama_pct.data, dict):
            change_24h = _num((llama_pct.data.get("coins") or {}).get("coingecko:solana"))
            if change_24h is not None:
                sources_used.append("DeFiLlama coins percentage")

    circ = network.get("supply_circulating_sol")
    if market_cap is None and price is not None and circ is not None:
        market_cap = price * circ
        sources_used.append("market cap = price × RPC circulating supply")

    tvl = None
    tvl_1d = None
    tvl_7d = None
    chains = http.get("llama_chains")
    if chains and chains.ok and isinstance(chains.data, list):
        for row in chains.data:
            if str(row.get("name", "")).lower() == "solana":
                tvl = _num(row.get("tvl"))
                sources_used.append("DeFiLlama /v2/chains")
                break
    hist = http.get("llama_tvl_hist")
    if hist and hist.ok and isinstance(hist.data, list) and hist.data:
        series = hist.data
        latest = _num(series[-1].get("tvl"))
        tvl = tvl or latest
        if len(series) >= 2:
            prev = _num(series[-2].get("tvl"))
            if latest and prev:
                tvl_1d = 100.0 * (latest - prev) / prev
        if len(series) >= 8:
            week = _num(series[-8].get("tvl"))
            if latest and week:
                tvl_7d = 100.0 * (latest - week) / week
        sources_used.append("DeFiLlama /v2/historicalChainTvl/Solana")

    def overview(key: str, label: str) -> dict[str, Any]:
        res = http.get(key)
        if not (res and res.ok and isinstance(res.data, dict)):
            return {"ok": False, "error": (res.error if res else "missing")}
        data = res.data
        protocols = []
        for p in data.get("protocols") or []:
            vol = _num(p.get("total24h"))
            if vol:
                protocols.append(
                    {
                        "name": p.get("displayName") or p.get("name"),
                        "total24h": vol,
                        "change_1d": _num(p.get("change_1d")),
                        "category": p.get("category"),
                    }
                )
        protocols.sort(key=lambda x: x["total24h"], reverse=True)
        sources_used.append(label)
        return {
            "ok": True,
            "total24h": _num(data.get("total24h")),
            "total7d": _num(data.get("total7d")),
            "total30d": _num(data.get("total30d")),
            "change_1d": _num(data.get("change_1d")),
            "change_7d": _num(data.get("change_7d")),
            "top": protocols[:12],
        }

    dex = overview("llama_dex", "DeFiLlama DEX overview/Solana")
    fees = overview("llama_fees", "DeFiLlama fees overview/Solana")
    revenue = overview("llama_revenue", "DeFiLlama revenue overview/Solana")

    stables_usd = None
    stables_detail = {}
    st = http.get("llama_stables")
    if st and st.ok and isinstance(st.data, list):
        for row in st.data:
            if str(row.get("name", "")).lower() == "solana":
                circ_usd = row.get("totalCirculatingUSD") or {}
                stables_detail = {k: _num(v) for k, v in circ_usd.items()}
                stables_usd = sum(v for v in stables_detail.values() if v)
                sources_used.append("DeFiLlama stablecoinchains")
                break

    rwa_tvl = 0.0
    rwa_list = []
    proto = http.get("llama_protocols")
    if proto and proto.ok and isinstance(proto.data, list):
        for p in proto.data:
            cat = str(p.get("category") or "").lower()
            chains_p = p.get("chains") or []
            if cat in {"rwa", "rwa lending", "real world assets"} and "Solana" in chains_p:
                chain_tvls = p.get("chainTvls") or {}
                sol_tvl = _num(chain_tvls.get("Solana"), 0.0) or 0.0
                if sol_tvl <= 0:
                    continue
                rwa_tvl += sol_tvl
                rwa_list.append({"name": p.get("name"), "tvl_solana": sol_tvl, "category": p.get("category")})
        rwa_list.sort(key=lambda x: x["tvl_solana"], reverse=True)
        sources_used.append("DeFiLlama protocols (RWA ∩ Solana)")

    failed = {k: v.error for k, v in http.items() if v and not v.ok}

    return {
        "price_usd": price,
        "price_source": price_source,
        "change_24h_pct": change_24h,
        "volume_24h_usd": volume_24h,
        "market_cap_usd": market_cap,
        "tvl_usd": tvl,
        "tvl_change_1d_pct": tvl_1d,
        "tvl_change_7d_pct": tvl_7d,
        "dex": dex,
        "fees": fees,
        "revenue": revenue,
        "stablecoin_mcap_usd": stables_usd,
        "stablecoin_breakdown": stables_detail,
        "rwa_tvl_usd": rwa_tvl or None,
        "rwa_count": len(rwa_list),
        "rwa_top": rwa_list[:12],
        "sources_used": sources_used,
        "failed_sources": failed,
    }


def interpret_ecosystem(http: dict[str, FetchResult]) -> dict[str, Any]:
    page = http.get("solana_data_page")
    available = bool(page and page.ok)
    note = (
        "solana.com/data is a JavaScript dashboard powered by the Solana Data Aggregator. "
        "The public HTML does not expose a keyless JSON feed, so Northstar records page "
        "availability and uses RPC + DeFiLlama for numeric metrics. Tokenized-asset TVL is "
        "derived from DeFiLlama RWA protocols with a Solana deployment."
    )
    text_preview = ""
    if available and isinstance(page.data, str):
        text_preview = page.data[:180].replace("\n", " ")
    return {
        "solana_data_fetchable": available,
        "solana_data_status": page.status if page else None,
        "solana_data_bytes": page.bytes if page else None,
        "solana_data_ms": page.elapsed_ms if page else None,
        "solana_data_note": note,
        "solana_data_preview": text_preview,
        "dune": {
            "attempted": False,
            "reason": "Dune Analytics HTTP API requires an API key; skipped per no-secrets policy.",
        },
        "twitter": {
            "attempted": False,
            "reason": "X/Twitter API requires keys; skipped.",
        },
        "daily_active_addresses": {
            "available": False,
            "reason": (
                "No keyless public JSON endpoint currently publishes Solana daily active addresses. "
                "DeFiLlama's chain ranking UI shows the figure but it is not on the free /v2/chains API."
            ),
        },
    }


def source_health(http: dict[str, FetchResult], rpc: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    rows.append(
        {
            "name": "Solana RPC",
            "ok": bool(rpc.get("ok") or rpc.get("epoch") or rpc.get("samples")),
            "detail": rpc.get("rpc_endpoint"),
            "errors": rpc.get("errors") or [],
        }
    )
    labels = {
        "coingecko_simple": "CoinGecko",
        "llama_price": "DeFiLlama price",
        "llama_pct": "DeFiLlama 24h change",
        "llama_chains": "DeFiLlama chains",
        "llama_tvl_hist": "DeFiLlama TVL history",
        "llama_dex": "DeFiLlama DEX",
        "llama_fees": "DeFiLlama fees",
        "llama_revenue": "DeFiLlama revenue",
        "llama_stables": "DeFiLlama stablecoins",
        "llama_protocols": "DeFiLlama protocols",
        "stakewiz_validators": "Stakewiz validators",
        "solana_data_page": "solana.com/data",
    }
    for key, label in labels.items():
        res = http.get(key)
        rows.append(
            {
                "name": label,
                "ok": bool(res and res.ok),
                "status": res.status if res else None,
                "ms": res.elapsed_ms if res else None,
                "bytes": res.bytes if res else None,
                "error": res.error if res else "not fetched",
            }
        )
    return rows
