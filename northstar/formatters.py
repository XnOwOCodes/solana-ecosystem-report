from __future__ import annotations

import html
import math
from typing import Any


def fmt_int(n: Any, dash: str = "—") -> str:
    if n is None:
        return dash
    try:
        return f"{int(round(float(n))):,}"
    except (TypeError, ValueError):
        return dash


def fmt_num(n: Any, digits: int = 2, dash: str = "—") -> str:
    if n is None:
        return dash
    try:
        x = float(n)
    except (TypeError, ValueError):
        return dash
    if math.isnan(x) or math.isinf(x):
        return dash
    return f"{x:,.{digits}f}"


def fmt_pct(n: Any, digits: int = 2, signed: bool = False) -> str:
    if n is None:
        return "—"
    try:
        x = float(n)
    except (TypeError, ValueError):
        return "—"
    sign = "+" if signed and x > 0 else ""
    return f"{sign}{x:.{digits}f}%"


def fmt_usd(n: Any, digits: int | None = None) -> str:
    if n is None:
        return "—"
    try:
        x = float(n)
    except (TypeError, ValueError):
        return "—"
    absx = abs(x)
    if digits is None:
        if absx >= 1_000_000_000:
            return f"${x/1_000_000_000:.2f}B"
        if absx >= 1_000_000:
            return f"${x/1_000_000:.2f}M"
        if absx >= 1_000:
            return f"${x/1_000:.2f}K"
        return f"${x:,.2f}"
    return f"${x:,.{digits}f}"


def fmt_sol(n: Any) -> str:
    if n is None:
        return "—"
    try:
        x = float(n)
    except (TypeError, ValueError):
        return "—"
    if abs(x) >= 1_000_000:
        return f"{x/1_000_000:.2f}M SOL"
    return f"{x:,.0f} SOL"


def escape(s: Any) -> str:
    return html.escape("" if s is None else str(s), quote=True)
