from __future__ import annotations

import argparse
import sys
import threading
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .config import load_config, resolve
from .pipeline import run_once


def _print_headlines(report: dict) -> None:
    n = report.get("network") or {}
    m = report.get("markets") or {}
    v = report.get("validators") or {}
    print(f"generated: {report.get('generated_at')}")
    print(f"rpc:       {n.get('rpc_endpoint')} ({n.get('rpc_version')}) health={n.get('health')}")
    pct = n.get("epoch_progress_pct")
    if pct is not None:
        print(f"slot:      {n.get('slot')}  height={n.get('block_height')}  epoch={n.get('epoch')} ({pct:.2f}%)")
    else:
        print(f"slot:      {n.get('slot')}")
    print(
        f"tps:       median={n.get('tps_median_15m')}  nonvote={n.get('nonvote_tps_median_15m')}  "
        f"slot_ms={n.get('slot_time_ms_median_15m')}"
    )
    print(
        f"validators:{v.get('active_count')} active / {v.get('delinquent_count')} delinquent  "
        f"nakamoto33={v.get('nakamoto_33')}"
    )
    print(f"markets:   SOL={m.get('price_usd')}  tvl={m.get('tvl_usd')}  dex24h={(m.get('dex') or {}).get('total24h')}")


def cmd_run(args: argparse.Namespace) -> int:
    result = run_once(Path(args.config) if args.config else None, copy_samples=args.samples)
    _print_headlines(result["report"])
    print("wrote:")
    for k, v in result["outputs"].items():
        print(f"  {k}: {v}")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    cfg = load_config(Path(args.config) if args.config else None)
    interval = args.interval or int(cfg.get("refresh_seconds", 300))
    print(f"watching every {interval}s · ctrl-c to stop")
    while True:
        try:
            result = run_once(Path(args.config) if args.config else None, copy_samples=args.samples)
            _print_headlines(result["report"])
        except KeyboardInterrupt:
            print("\nstopped")
            return 0
        except Exception as exc:
            print(f"run failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nstopped")
            return 0


def cmd_serve(args: argparse.Namespace) -> int:
    cfg = load_config(Path(args.config) if args.config else None)
    out_dir = resolve(cfg, "output_dir")
    if not (out_dir / "dashboard.html").exists():
        print("no dashboard yet — generating one")
        run_once(Path(args.config) if args.config else None, copy_samples=True)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(out_dir), **k)

        def log_message(self, fmt: str, *log_args) -> None:
            print("[http]", fmt % log_args)

        def do_GET(self):  # noqa: N802
            if self.path in ("/", "/index.html"):
                self.path = "/dashboard.html"
            return super().do_GET()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"serving {out_dir} on http://{args.host}:{args.port}/")
    if args.watch:
        interval = args.interval or int(cfg.get("refresh_seconds", 300))

        def loop() -> None:
            while True:
                time.sleep(interval)
                try:
                    run_once(Path(args.config) if args.config else None, copy_samples=False)
                    print(f"refreshed at interval={interval}s")
                except Exception as exc:
                    print(f"refresh failed: {exc}", file=sys.stderr)

        threading.Thread(target=loop, daemon=True).start()
        print(f"auto-refresh every {interval}s")
    if args.open:
        webbrowser.open(f"http://127.0.0.1:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="northstar",
        description="Northstar — original Solana ecosystem report (RPC + DeFiLlama, no API keys).",
    )
    parser.add_argument("--config", help="Path to config.json")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Collect once and write dashboard / markdown / JSON")
    run_p.add_argument("--no-samples", dest="samples", action="store_false", help="Do not copy into samples/")
    run_p.set_defaults(samples=True, func=cmd_run)

    watch_p = sub.add_parser("watch", help="Collect on a loop")
    watch_p.add_argument("--interval", type=int, help="Seconds between runs (default: config.refresh_seconds)")
    watch_p.add_argument("--no-samples", dest="samples", action="store_false")
    watch_p.set_defaults(samples=False, func=cmd_watch)

    serve_p = sub.add_parser("serve", help="Tiny local HTTP server for the dashboard")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8765)
    serve_p.add_argument("--watch", action="store_true", help="Rebuild on the refresh interval")
    serve_p.add_argument("--interval", type=int)
    serve_p.add_argument("--open", action="store_true")
    serve_p.set_defaults(func=cmd_serve)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
