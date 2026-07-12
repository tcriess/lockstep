"""Shared test configuration — and the one place that decides whether the oracle is available.

Anything that needs a real emulator (the cycle measurements, the all-wakestate border matrix, the
sound profiler) is opt-in: it needs a cycle-exact `hatari` on PATH and a TOS/EmuTOS ROM. Mark those
tests `@pytest.mark.hatari` and they are SKIPPED — visibly — when the oracle is absent.

That word is load-bearing. The idiom this replaces was, in four separate files:

    if SKIP:
        print("skip (no hatari/tos)")
        return

which pytest counts as **PASSED**. On a machine without a TOS ROM the suite reported 101 green while
twelve tests — including the project's entire "all four borders, all four wakestates" guarantee —
executed nothing at all. A green suite that has not tested the central claim of the project is worse
than a red one. Now you get `12 skipped` in the summary line, and you can see what you did not run.
"""

from __future__ import annotations

import os
import shutil
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from st68k.hatari import HatariError, find_tos  # noqa: E402


def _oracle_available() -> tuple[bool, str]:
    if shutil.which(os.environ.get("STCYC_HATARI", "hatari")) is None:
        return False, "needs hatari on PATH (or set STCYC_HATARI)"
    try:
        find_tos()
    except HatariError as e:
        return False, f"needs a TOS/EmuTOS ROM ({e})"
    return True, ""


HAVE_ORACLE, WHY_NOT = _oracle_available()


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "hatari: needs a cycle-exact Hatari + a TOS ROM (slow: spawns an emulator)")


def pytest_collection_modifyitems(config, items):
    if HAVE_ORACLE:
        return
    skip = pytest.mark.skip(reason=WHY_NOT)
    for item in items:
        if "hatari" in item.keywords:
            item.add_marker(skip)
