"""The PGLU brand banner, shown when the CLI runs (Windows-safe)."""

from __future__ import annotations

import os
import sys

_CYAN = "\033[96m"
_MAGENTA = "\033[95m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"

_UNICODE = r"""
██████╗  ██████╗ ██╗     ██╗   ██╗
██╔══██╗██╔════╝ ██║     ██║   ██║
██████╔╝██║  ███╗██║     ██║   ██║
██╔═══╝ ██║   ██║██║     ██║   ██║
██║     ╚██████╔╝███████╗╚██████╔╝
╚═╝      ╚═════╝ ╚══════╝ ╚═════╝
"""

_ASCII = r"""
 ____   ____ _    _   _
|  _ \ / ___| |  | | | |
| |_) | |  _| |  | | | |
|  __/| |_| | |__| |_| |
|_|    \____|_____\___/
"""


def _supports_unicode(stream) -> bool:
    enc = getattr(stream, "encoding", None) or "ascii"
    try:
        "█╗".encode(enc)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def _color_on(flag, stream) -> bool:
    if flag is not None:
        return flag
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(stream, "isatty") and stream.isatty()


def render_banner(color=None, unicode_ok=None, stream=None) -> str:
    stream = stream or sys.stderr
    on = _color_on(color, stream)
    uni = _supports_unicode(stream) if unicode_ok is None else unicode_ok
    art = (_UNICODE if uni else _ASCII).strip("\n")
    sep = "·" if uni else "-"

    if on:
        art = f"{_BOLD}{_CYAN}{art}{_RESET}"
        tag = f"  {_MAGENTA}PGLU{_RESET}{_DIM} {sep} site-doctor{_RESET}"
    else:
        tag = f"  PGLU {sep} site-doctor"
    return f"{art}\n{tag}\n"


def print_banner(color=None) -> None:
    # Banner goes to stderr so stdout (reports / --json) stays clean for piping.
    try:
        sys.stderr.write(render_banner(color=color))
        sys.stderr.flush()
    except Exception:  # noqa: BLE001 - a banner must never break the tool
        pass
