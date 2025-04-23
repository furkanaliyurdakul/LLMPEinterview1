# SPDX-License-Identifier: MIT
import time
import json
from pathlib import Path
import streamlit as st

# one dict that lives in session_state
_DEFAULT = {"enter_ts": None, "durations": {}}     # {page: seconds}

def start(page: str):
    """Call when a page becomes active."""
    data = st.session_state.setdefault("_page_timer", _DEFAULT.copy())

    # If we came from another page, stop its clock first
    prev_start = data["enter_ts"]
    prev_page  = data.get("current_page")
    if prev_start and prev_page:
        data["durations"][prev_page] = data["durations"].get(prev_page, 0) + (
            time.time() - prev_start
        )

    # Start timer for the new page
    data["current_page"] = page
    data["enter_ts"]     = time.time()

def dump(session_dir: Path):
    """Write durations.json next to the other session artefacts."""
    data = st.session_state.get("_page_timer")
    if not data:
        return None

    # stop timing the last open page
    if data["enter_ts"]:
        data["durations"][data["current_page"]] = (
            data["durations"].get(data["current_page"], 0)
            + time.time() - data["enter_ts"]
        )
        data["enter_ts"] = None

    # write INSIDE the per-session directory (≙ output/20250423_0834…/)
    out = session_dir / "meta"
    out.mkdir(exist_ok=True)
    json_path = out / "page_durations.json"
    json_path.write_text(json.dumps(data["durations"], indent=2))

    return json_path


# --- live snapshot --------------------------------------------------------
import math  # std-lib | already imported? then skip

def snapshot() -> dict[str, float]:
    """
    Return the current durations in SECONDS.
    Includes the page that is still running.
    """
    data = st.session_state.get("_page_timer")
    if not data:
        return {}

    # finished pages
    out = data["durations"].copy()

    # add the still-running page
    if data["enter_ts"]:
        running = time.time() - data["enter_ts"]
        out[data["current_page"]] = out.get(data["current_page"], 0) + running

    return out
