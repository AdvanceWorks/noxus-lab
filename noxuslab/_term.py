"""Tiny ANSI helper. NO_COLOR-aware. Stdlib only.

from noxuslab._term import dim, bold, red
print(red("error:"), dim("file not found"))
"""

import os
import sys


def _enabled() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stderr.isatty() or sys.stdout.isatty()


def _wrap(code: str, s: str) -> str:
    if not _enabled():
        return s
    return f"\x1b[{code}m{s}\x1b[0m"


def bold(s: str) -> str:
    return _wrap("1", s)


def dim(s: str) -> str:
    return _wrap("2", s)


def red(s: str) -> str:
    return _wrap("31", s)


def green(s: str) -> str:
    return _wrap("32", s)
