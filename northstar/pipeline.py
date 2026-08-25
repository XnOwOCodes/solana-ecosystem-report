from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .analyze import append_history, compact_history_row, detect_anomalies, load_history, slot_time_stage
from .collect import (
    collect_http_sources,
    collect_rpc,
    interpret_ecosystem,
    interpret_markets,
    interpret_network,
    interpret_validators,
    source_health,
    utc_now,
)
from .config import ROOT, load_config, resolve
from .html_out import render_html
from .markdown_out import render_markdown
from .net import HttpClient
from .research import upgrades_payload
from .rpc import RpcCluster


def build_report(cfg: dict[str, Any]) -> dict[str, Any]:
    client = HttpClient(
        user_agent=cfg.get("user_agent", "NorthstarSolanaReport/1.0"),
        timeout=float(cfg.get("request_timeout_seconds", 30)),
        max_retries=int(cfg.get("max_retries", 3)),
        backoff=float(cfg.get("retry_backoff_seconds", 1.6)),
    )
    http = collect_http_sources(client, cfg.get("sources") or {})
    cluster = RpcCluster(
        client,
        list(cfg.get("rpc_endpoints") or []),
        gap_seconds=float(cfg.get("rpc_gap_seconds", 0.35)),
        timeout=float(cfg.get("rpc_timeout_seconds", 45)),
    )
    rpc = collect_rpc(cluster, sample_count=int(cfg.get("performance_samples", 60)))
    network = interpret_network(rpc)
    stakewiz = http.get("stakewiz_validators")
    validators = interpret_validators(rpc, stakewiz.data if stakewiz and stakewiz.ok else None)
    markets = interpret_markets(http, network)
    ecosystem = interpret_ecosystem(http)
    report: dict[str, Any] = {
        "generator": "Northstar",
        "version": "1.0.0",
        "generated_at": utc_now(),
        "network": network,
        "validators": validators,
        "markets": markets,
        "ecosystem": ecosystem,
        "upgrades": upgrades_payload(),
        "slot_time_stage": slot_time_stage(network.get("slot_time_ms_median_15m")),
        "source_health": source_health(http, rpc),
    }
    hist_path = resolve(cfg, "history_path")
    history = load_history(hist_path, int(cfg.get("history_keep", 288)))
    report["anomalies"] = detect_anomalies(report, history, cfg)
    report["history_points"] = len(history)
    return report


def write_outputs(report: dict[str, Any], cfg: dict[str, Any], *, copy_samples: bool = False) -> dict[str, str]:
    out_dir = resolve(cfg, "output_dir")
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": out_dir / "report.json",
        "md": out_dir / "report.md",
        "html": out_dir / "dashboard.html",
    }
    paths["json"].write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    paths["md"].write_text(render_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_html(report), encoding="utf-8")

    snap = resolve(cfg, "snapshot_path")
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    append_history(resolve(cfg, "history_path"), compact_history_row(report), int(cfg.get("history_keep", 288)))

    if copy_samples:
        samples = ROOT / "samples"
        samples.mkdir(parents=True, exist_ok=True)
        (samples / "report.md").write_text(paths["md"].read_text(encoding="utf-8"), encoding="utf-8")
        (samples / "report.json").write_text(paths["json"].read_text(encoding="utf-8"), encoding="utf-8")
        (samples / "dashboard.html").write_text(paths["html"].read_text(encoding="utf-8"), encoding="utf-8")
        paths["samples_md"] = samples / "report.md"
        paths["samples_json"] = samples / "report.json"
        paths["samples_html"] = samples / "dashboard.html"
    return {k: str(v) for k, v in paths.items()}


def run_once(config_path: Path | None = None, copy_samples: bool = True) -> dict[str, Any]:
    cfg = load_config(config_path)
    report = build_report(cfg)
    outputs = write_outputs(report, cfg, copy_samples=copy_samples)
    return {"report": report, "outputs": outputs, "config": cfg}
