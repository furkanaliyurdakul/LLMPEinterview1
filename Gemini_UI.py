# SPDX‑License‑Identifier: MIT
"""Gemini‑powered slide tutor.

Streamlit page that lets a user upload slides, audio and a student profile,
then requests a personalised (or generic) explanation from Gemini 2.5.
"""

# ── std‑lib ────────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

# Heavy / Windows‑only libs are *imported* but only initialised when needed
import pythoncom

# ── third‑party ────────────────────────────────────────────────────────────
import streamlit as st
import whisper
import win32com.client

# ── local ─────────────────────────────────────────────────────────────────
from session_manager import get_session_manager

# ──────────────────────────────────────────────────────────────────────────
# Configuration constants
# ──────────────────────────────────────────────────────────────────────────
ROOT: Path = Path.cwd()
UPLOAD_DIR_AUDIO: Path = ROOT / "uploads" / "audio"
UPLOAD_DIR_PPT: Path = ROOT / "uploads" / "ppt"
UPLOAD_DIR_PROFILE: Path = ROOT / "uploads" / "profile"
TRANSCRIPTION_DIR: Path = ROOT / "transcriptions"

for p in (
    UPLOAD_DIR_AUDIO,
    UPLOAD_DIR_PPT,
    UPLOAD_DIR_PROFILE,
    TRANSCRIPTION_DIR,
):
    p.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────
# Streamlit page‑level setup
# ──────────────────────────────────────────────────────────────────────────
FAST_TEST_MODE: bool = st.session_state.get("fast_test_mode", False)
if st.sidebar.button("Enable Fast Test Mode (Dev Only)"):
    st.session_state["fast_test_mode"] = True
    st.rerun()

st.markdown(
    """
    <style>
    .block-container {max-width: 90%; padding-left: 2rem; padding-right: 2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

label: str = (
    "Personalised" if st.session_state.get("use_personalisation", True) else "Generic"
)

# ──────────────────────────────────────────────────────────────────────────
# Session‑state helpers
# ──────────────────────────────────────────────────────────────────────────

_DEFAULT_SESSION_STATE = {
    "exported_images": [],
    "transcription_text": "",
    "messages": [],
    "selected_slide": "Slide 1",
    "profile_dict": {},
}

for k, v in _DEFAULT_SESSION_STATE.items():
    st.session_state.setdefault(k, v)


def debug_log(msg: str) -> None:
    """Collect debug statements in *one* place so they can be shown via a checkbox."""
    st.session_state.setdefault("debug_logs", []).append(msg)


# ──────────────────────────────────────────────────────────────────────────
# Prompt builders
# ──────────────────────────────────────────────────────────────────────────


def create_summary_prompt(profile: dict, slide: str, personalised: bool = True) -> str:
    """Return the user‑facing summary prompt passed to Gemini."""
    label_loc = "Personalised" if personalised else "Generic"

    if not personalised:
        return (
            f"Generating a {label_loc} explanation for {slide}. "
            "Please keep the wording suitable for an average under‑grad audience."
        )

    name = profile.get("Name", "the student")
    proficiency = profile.get("CurrentProficiency", "unknown level")
    learning_strats = ", ".join(profile.get("PreferredLearningStrategies", []))
    barriers = ", ".join(profile.get("PotentialBarriers", []))
    short_goals = "; ".join(profile.get("ShortTermGoals", []))

    return (
        f"Generating a {label_loc} explanation for {slide} tailored specifically to {name}, "
        f"who is at a {proficiency.lower()} level.\n\n"
        f"{name}'s strongest subject is {profile.get('StrongestSubject', 'N/A')}, "
        f"while they find {profile.get('WeakestSubject', 'N/A')} challenging.\n"
        f"Preferred learning methods include: {learning_strats}.\n\n"
        f"The explanation will explicitly address potential barriers such as {barriers}, "
        f"while aligning with their short‑term academic goal(s): {short_goals}.\n\n"
        f"Language complexity and examples will reflect their interests "
        f"({', '.join(profile.get('Hobbies', []))}) and major ({profile.get('Major', 'N/A')})."
    )


def create_structured_prompt(
    slide_txt: str, transcript: str, profile: dict, slide: str
) -> str:
    """Gemini JSON prompt – rich variant that references the student profile."""

    # ── new prompt ----------------------------------------------------- #
    system_msg = (
        "You are an adaptive teaching assistant. Use the provided context, "
        "and reply only in Markdown addressed to the student."
    )

    prompt_dict = {
        # ── SYSTEM (high‑level reminders) ───────────────────────────────
        "System": system_msg,

        # ── ROLE & OBJECTIVE ────────────────────────────────────────────
        "Role": "Personalised Slide‑Tutor",
        "Objective": (
            f"Explain *{slide}* in a way that is fitting **for "
            f"{profile.get('Name','the student')}**."
        ),

        # ── INSTRUCTIONS / RESPONSE RULES ───────────────────────────────
        "Instructions": {
            "Formatting": (
                "Return Markdown. Do **not** output JSON or wrap the entire reply in ``` … ```.\n"
                "If you need to show a code snippet, use fenced code‑blocks "
                "(```python` … ```). Write math inline as LaTeX ($x^2$)."
            ),
            "Tone": "Friendly, concise, expert",
            "Guidelines": [
                "Adjust language to the student’s proficiency",
                "Explicitly tackle the student’s weakest subject",
                "Link examples to the student’s major / hobbies",
                "Reflect preferred learning strategies",
                "Mention potential barriers & short‑term goals",
            ],
            # optional agentic bits
            "ToolUse": "No external tools available – rely on context below.",
        },

        # ── STUDENT PROFILE (for grounding) ─────────────────────────────
        "StudentProfile": profile,          # ← unchanged dictionary

        # ── CONTEXT ─────────────────────────────────────────────────────
        "Context": {
            "Slides": {
                "content": slide_txt,
                "usage_hint": f"Pull core concepts from {slide} verbatim when useful."
            },
            "Transcript": {
                "content": transcript,
                "usage_hint": (
                    "Use concrete examples or analogies that appear in the lecture."
                ),
            },
        },
    }

    # Return pretty‑printed JSON string because `build_prompt()` expects it
    return json.dumps(prompt_dict, indent=2)



# ──────────────────────────────────────────────────────────────────────────
# Profile parser (regex‑based, matches the survey export)
# ──────────────────────────────────────────────────────────────────────────


def parse_detailed_student_profile(text: str) -> dict:
    """Convert the long profile *text blob* into a structured dict."""

    def _grab(pattern: str, default: str = "") -> str:
        m = re.search(pattern, text, re.MULTILINE)
        return m.group(1).strip() if m else default

    profile: dict = {
        "Name": _grab(r"1\.\s*Name:\s*(.+)"),
        "Age": int(_grab(r"2\.\s*Age:\s*(\d+)", "0")),
        "StudyBackground": _grab(r"3\.\s*Study background:\s*(.+)"),
        "Major": _grab(r"4\.\s*Major of education:\s*(.+)"),
        "WorkExperience": _grab(r"5\.\s*Work experience:\s*(.+)"),
    }

    hobbies = _grab(r"6\.\s*Hobbies or interests:\s*(.+)")
    profile["Hobbies"] = [h.strip() for h in hobbies.split(",")] if hobbies else []

    # --- academic performance table -------------------------------------
    perf_section = re.search(
        r"7\. Academic performance ranking.*?:(.*?)(?=8\.)", text, re.DOTALL
    )
    scores: dict[str, int] = {}
    if perf_section:
        for subj, sc in re.findall(r"[A-L]\.\s*(.+?):\s*(\d)", perf_section.group(1)):
            scores[subj.strip()] = int(sc)
    profile["AcademicPerformance"] = scores

    profile["StrongestSubject"] = _grab(r"8\.\s*Strongest Subject:\s*(.+)")
    profile["WeakestSubject"] = _grab(r"9\.\s*Most Challenging Subject:\s*(.+)")

    # --- learning priorities -------------------------------------------
    prio_section = re.search(
        r"10\. Learning priorities ranking.*?:(.*?)(?=11\.)", text, re.DOTALL
    )
    priorities: dict[str, int] = {}
    if prio_section:
        for item, rating in re.findall(
            r"[A-F]\.\s*(.+?):\s*(\d)", prio_section.group(1)
        ):
            priorities[item.strip()] = int(rating)
    profile["LearningPriorities"] = priorities

    # --- rest -----------------------------------------------------------
    profile["PreferredLearningStrategies"] = [
        s.strip()
        for s in _grab(r"11\. Preferred learning strategy:\s*(.+)").split(";")
        if s.strip()
    ]
    profile["CurrentProficiency"] = _grab(r"12\.\s*Current proficiency level:\s*(.+)")

    profile["ShortTermGoals"] = [
        g.strip()
        for g in _grab(r"13\.\s*Short-term academic goals:\s*(.+)").split(";")
        if g.strip()
    ]
    profile["LongTermGoals"] = [
        g.strip()
        for g in _grab(r"14\.\s*Long-term academic/career goals:\s*(.+)").split(";")
        if g.strip()
    ]
    profile["PotentialBarriers"] = [
        b.strip()
        for b in _grab(r"15\.\s*Potential Barriers:\s*(.+)").split(";")
        if b.strip()
    ]

    return profile


# ──────────────────────────────────────────────────────────────────────────
# File helpers (Whisper + PowerPoint automation)
# ──────────────────────────────────────────────────────────────────────────


def transcribe_audio(audio_path: Path) -> str:
    """Transcribe *audio_path* with Whisper – cached on disk."""
    model_name = "turbo"
    trans_path = TRANSCRIPTION_DIR / f"{model_name}_transcription_{audio_path.stem}.txt"

    if trans_path.exists():
        debug_log(f"Using cached transcription: {trans_path.name}")
        return trans_path.read_text(encoding="utf‑8")

    debug_log(f"Loading Whisper model '{model_name}' …")
    whisper_model = whisper.load_model(model_name)

    start = time.time()
    result = whisper_model.transcribe(
        str(audio_path),
        language="en",
        fp16=False,
        verbose=False,
        patience=2,
        beam_size=5,
    )
    debug_log(f"Whisper latency: {time.time() - start:.1f}s")

    trans_path.write_text(result["text"], encoding="utf‑8")
    return result["text"]


def export_ppt_slides(ppt_path: Path) -> list[Path]:
    """Return a list of exported PNG slide paths given a .pptx file."""
    pythoncom.CoInitialize()
    ppt_app = win32com.client.Dispatch("PowerPoint.Application")
    ppt_app.Visible = True

    img_dir = ppt_path.parent / "picture"
    img_dir.mkdir(exist_ok=True)

    try:
        pres = ppt_app.Presentations.Open(
            str(ppt_path), ReadOnly=True, WithWindow=False
        )
    except Exception as e:  # noqa: BLE001
        debug_log(f"PowerPoint error: {e}")
        pythoncom.CoUninitialize()
        return []

    exported: list[Path] = []
    for slide in pres.Slides:
        out = img_dir / f"Slide_{slide.SlideIndex} of {ppt_path.stem}.png"
        slide.Export(str(out), "PNG")
        exported.append(out)
        debug_log(f"Exported {out.name}")

    pres.Close()
    ppt_app.Quit()
    pythoncom.CoUninitialize()
    return exported


# ──────────────────────────────────────────────────────────────────────────
# Prompt wrapper (generic vs personalised)
# ──────────────────────────────────────────────────────────────────────────


def build_prompt(
    slide_txt: str, transcript: str, profile: dict, slide: str, personalised: bool
) -> str:
    """Return the JSON prompt string – personalised or generic."""
    if personalised:
        return create_structured_prompt(slide_txt, transcript, profile, slide)

    base = {
        "Slides": {"content": slide_txt},
        "Transcript": {"content": transcript},
        "Instructions": {
            "TailorToStudent": False,
            "Guidelines": [
                "Explain so that an average under‑grad understands the idea"
            ],
            "FormattingRequirements": {"PreferredFormatting": "Markdown"},
        },
        "Objective": f"Give a clear, generic explanation of {slide}",
    }
    return json.dumps(base, indent=2)


# ──────────────────────────────────────────────────────────────────────────
# Streamlit UI logic – *main* entry point
# ──────────────────────────────────────────────────────────────────────────


def main() -> None:
    st.title(f"{label} Explanation Generator")

    # 1) Fast‑test stub ---------------------------------------------------
    if FAST_TEST_MODE:
        st.session_state.exported_images = [
            ROOT / "uploads" / "ppt" / "picture" / "Slide_1 of Lecture8.png"
        ]
        st.session_state.transcription_text = (
            "This is a mock transcription for fast testing."
        )
        st.session_state.profile_dict = {
            "Name": "Test User",
            "CurrentProficiency": "Intermediate",
            "StrongestSubject": "Mathematics",
            "WeakestSubject": "Physics",
            "PreferredLearningStrategies": [
                "Detailed, step‑by‑step explanations similar to in‑depth lectures",
            ],
            "PotentialBarriers": ["Lack of prior knowledge"],
            "ShortTermGoals": ["Understand core concepts"],
            "Hobbies": ["Chess", "Reading"],
            "Major": "Engineering",
            "LearningPriorities": {
                "Understanding interrelationships among various concepts": 5,
                "Applying theory to real-world problems": 5,
            },
        }
        st.session_state.selected_slide = "Slide 1"

    # 2) Load profile from session dir if already stored ------------------
    if not st.session_state.profile_dict:
        sm = get_session_manager()
        orig_profile = sm.profile_dir / "original_profile.txt"
        if orig_profile.exists():
            prof_txt = orig_profile.read_text(encoding="utf‑8")
            st.session_state.profile_text = prof_txt
            st.session_state.profile_dict = parse_detailed_student_profile(prof_txt)
            debug_log(f"Loaded profile from {orig_profile}")

    # 3) Sidebar – uploads -------------------------------------------------
    st.sidebar.header("Input Files")
    audio_up = st.sidebar.file_uploader(
        "Upload Audio File", ["wav", "mp3", "ogg", "flac", "m4a", "mp4"]
    )
    ppt_up = st.sidebar.file_uploader("Upload PPT", ["ppt", "pptx"])
    profile_up = st.sidebar.file_uploader("Upload Student Profile (TXT)", ["txt"])

    # -- debug toggles ----------------------------------------------------
    if st.checkbox("Show Debug Logs"):
        st.subheader("Debug Logs")
        for l in st.session_state.get("debug_logs", []):
            st.text(l)

    if st.checkbox("Show Parsed Profile"):
        st.json(st.session_state.profile_dict)

    # 3a) audio -----------------------------------------------------------
    if audio_up is not None:
        audio_path = UPLOAD_DIR_AUDIO / audio_up.name
        audio_path.write_bytes(audio_up.getbuffer())
        st.sidebar.success(f"Saved {audio_up.name}")
        if st.sidebar.button("Transcribe Audio"):
            st.session_state.transcription_text = transcribe_audio(audio_path)
            st.sidebar.success("Transcription complete!")
            st.rerun()

    # 3b) slides ----------------------------------------------------------
    if ppt_up is not None:
        ppt_path = UPLOAD_DIR_PPT / ppt_up.name
        ppt_path.write_bytes(ppt_up.getbuffer())
        st.sidebar.success(f"Saved {ppt_up.name}")
        if st.sidebar.button("Process PPT"):
            st.session_state.exported_images = export_ppt_slides(ppt_path)
            st.sidebar.success(
                f"Exported {len(st.session_state.exported_images)} slides"
            )
            st.rerun()

    # 3c) profile ---------------------------------------------------------
    if profile_up is not None:
        prof_path = UPLOAD_DIR_PROFILE / profile_up.name
        prof_path.write_bytes(profile_up.getbuffer())
        st.sidebar.success(f"Saved {profile_up.name}")
        st.session_state.profile_text = prof_path.read_text(encoding="utf‑8")
        st.session_state.profile_dict = parse_detailed_student_profile(
            st.session_state.profile_text
        )
        st.rerun()

    # 4) Sidebar – slide selector ----------------------------------------
    if st.session_state.exported_images:
        slide_opts = [
            f"Slide {i+1}" for i in range(len(st.session_state.exported_images))
        ]
        selected_slide = st.sidebar.selectbox(
            "Select a Slide", slide_opts, key="selected_slide"
        )

    # 5) Layout: chat (left) • previews (right) ---------------------------
    col_chat, col_prev = st.columns([2, 1])

    # ----- chat --------------------------------------------------------
    with col_chat:
        st.header("LLM Chat")
        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"], unsafe_allow_html=True)

        if (
            not st.session_state.exported_images
            or not st.session_state.transcription_text
        ):
            st.info(
                "Upload and process audio + PPT (and a profile) to enable prompting."
            )

    # ----- previews ----------------------------------------------------
    with col_prev:
        st.header("Preview Files")
        if st.session_state.transcription_text:
            st.subheader("Transcription")
            st.text_area("Output", st.session_state.transcription_text, height=150)

        if st.session_state.exported_images and selected_slide:
            idx = int(selected_slide.split()[1]) - 1
            st.subheader("Selected Slide")
            st.image(
                str(st.session_state.exported_images[idx]),
                caption=selected_slide,
                use_container_width=True,
            )

        if "profile_text" in st.session_state:
            st.subheader("Student Profile")
            st.text_area("Profile", st.session_state.profile_text, height=150)


if __name__ == "__main__":
    main()
