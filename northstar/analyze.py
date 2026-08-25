from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any


def _mean_std(values: list[float]) -> tuple[float | None, float | None]:
    clean = [v for v in values if v is not None and not math.isnan(v)]
    if len(clean) < 4:
        return (None, None)
    return float(statistics.mean(clean)), float(statistics.pstdev(clean))


def _z(value: float | None, hist: list[float]) -> float | None:
    if value is None:
        return None
    mean, std = _mean_std(hist)
    if mean is None or not std:
        return None
    return (value - mean) / std


def compact_history_row(report: dict[str, Any]) -> dict[str, Any]:
    net = report.get("network") or {}
    val = report.get("validators") or {}
    mkt = report.get("markets") or {}
    return {
        "generated_at": report.get("generated_at"),
        "tps": net.get("tps_median_15m"),
        "nonvote_tps": net.get("nonvote_tps_median_15m"),
        "slot_time_ms": net.get("slot_time_ms_median_15m"),
        "delinquent_stake_pct": val.get("delinquent_stake_pct"),
        "delinquent_count": val.get("delinquent_count"),
        "price": mkt.get("price_usd"),
        "tvl": mkt.get("tvl_usd"),
        "dex_24h": (mkt.get("dex") or {}).get("total24h"),
        "epoch": net.get("epoch"),
        "slot": net.get("slot"),
    }


def load_history(path: Path, keep: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-keep:]


def append_history(path: Path, row: dict[str, Any], keep: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    rows = load_history(path, keep)
    with path.open("w", encoding="utf-8") as fh:
        for item in rows:
            fh.write(json.dumps(item) + "\n")


def detect_anomalies(report: dict[str, Any], history: list[dict[str, Any]], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Absolute thresholds plus optional z-score vs local history.

    First run has no history: only absolute rules fire. After a few refresh
    cycles the z-score layer starts tagging unusual deviations from *this*
    install's baseline, which is more useful than a global constant.
    """
    a = cfg.get("anomalies") or {}
    net = report.get("network") or {}
    val = report.get("validators") or {}
    mkt = report.get("markets") or {}
    flags: list[dict[str, Any]] = []

    def add(level: str, code: str, title: str, detail: str, value: Any = None) -> None:
        flags.append({"level": level, "code": code, "title": title, "detail": detail, "value": value})

    tps = net.get("tps_median_15m")
    nv = net.get("nonvote_tps_median_15m")
    slot_ms = net.get("slot_time_ms_median_15m")
    del_pct = val.get("delinquent_stake_pct")
    del_n = val.get("delinquent_count") or 0
    price_chg = mkt.get("change_24h_pct")
    tvl_chg = mkt.get("tvl_change_1d_pct")
    dex_chg = (mkt.get("dex") or {}).get("change_1d")

    if not net.get("healthy"):
        add("critical", "rpc_unhealthy", "RPC health is not ok", f"getHealth returned {net.get('health')!r}.")

    if slot_ms and slot_ms >= float(a.get("slot_time_slow_ms", 650)):
        add("warning", "slow_slots", "Slot time is slow", f"Median slot time {slot_ms:.0f} ms over ~15 samples.", slot_ms)
    if slot_ms and slot_ms <= float(a.get("slot_time_fast_ms", 180)):
        add("info", "fast_slots", "Slot time is unusually fast", f"Median slot time {slot_ms:.0f} ms.", slot_ms)

    hist_tps = [h.get("tps") for h in history if h.get("tps") is not None]
    if tps is not None and hist_tps:
        baseline = statistics.median(hist_tps)
        if baseline:
            drop = 100.0 * (baseline - tps) / baseline
            spike = 100.0 * (tps - baseline) / baseline
            if drop >= float(a.get("tps_drop_pct", 40)):
                add("warning", "tps_drop", "TPS dropped vs local baseline", f"{drop:.0f}% below median {baseline:.0f} TPS.", tps)
            elif spike >= float(a.get("tps_spike_pct", 80)):
                add("info", "tps_spike", "TPS spiked vs local baseline", f"{spike:.0f}% above median {baseline:.0f} TPS.", tps)

    z_tps = _z(tps, [float(x) for x in hist_tps])
    if z_tps is not None and abs(z_tps) >= float(a.get("zscore", 2.6)):
        add("info", "tps_zscore", "TPS z-score excursion", f"z={z_tps:.2f} versus this install's history.", tps)

    if del_pct is not None and del_pct >= float(a.get("delinquent_stake_pct", 5)):
        add("critical", "high_delinquency", "Delinquent stake is elevated", f"{del_pct:.2f}% of activated stake is delinquent.", del_pct)
    elif del_n >= int(a.get("delinquent_count", 80)):
        add("warning", "many_delinquent", "Many delinquent vote accounts", f"{del_n} delinquent vote accounts.", del_n)

    alerts = val.get("delinquency_alerts") or []
    if alerts:
        names = ", ".join(f"{x.get('name')} ({x.get('activated_stake_sol'):,.0f} SOL)" for x in alerts[:3])
        add("warning", "named_delinquents", "Staked validators marked delinquent", names)

    if price_chg is not None and abs(price_chg) >= float(a.get("price_move_pct", 8)):
        add("info", "price_move", "Large 24h SOL price move", f"{price_chg:+.2f}% over 24h.", price_chg)
    if tvl_chg is not None and abs(tvl_chg) >= float(a.get("tvl_move_pct", 12)):
        add("info", "tvl_move", "Large 1d TVL move", f"{tvl_chg:+.2f}% vs yesterday.", tvl_chg)
    if dex_chg is not None and abs(dex_chg) >= float(a.get("dex_move_pct", 60)):
        add("info", "dex_move", "Large 1d DEX volume move", f"{dex_chg:+.1f}% vs previous day.", dex_chg)

    if nv is not None and nv < 50:
        add("warning", "quiet_nonvote", "Non-vote TPS is very low", f"Median non-vote TPS {nv:.1f}.", nv)

    if not flags:
        add("ok", "nominal", "No threshold breaches", "Network, validator, and market gauges are inside configured bands.")
    return flags


def slot_time_stage(slot_ms: float | None) -> dict[str, Any]:
    """Map observed slot time onto SIMD-0525 staged targets."""
    stages = [
        (400, "400ms baseline (pre-SIMD-0525)"),
        (350, "350ms (SIMD-0525 stage 1)"),
        (300, "300ms (SIMD-0525 stage 2)"),
        (250, "250ms (SIMD-0525 stage 3)"),
        (200, "200ms (SIMD-0525 stage 4)"),
    ]
    if slot_ms is None:
        return {"observed_ms": None, "nearest": None, "interpretation": "no samples"}
    nearest = min(stages, key=lambda s: abs(s[0] - slot_ms))
    return {
        "observed_ms": slot_ms,
        "nearest_target_ms": nearest[0],
        "nearest_label": nearest[1],
        "delta_ms": slot_ms - nearest[0],
        "interpretation": (
            f"Measured median slot time is {slot_ms:.0f} ms, nearest staged target "
            f"{nearest[0]} ms ({nearest[1]})."
        ),
    }
