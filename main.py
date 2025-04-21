# SPDX-License-Identifier: MIT
"""Streamlit entry point – multi‑step learning platform wrapper.

Pages:
  • *Home* (study intro)
  • *Student Profile Survey*
  • *Personalised / Generic Learning* (Gemini tutor)
  • *Knowledge Test*
  • *User‑Experience Questionnaire*

Relies on :pyfile:`Gemini_UI.py` for all tutor‑specific helpers.
"""

# ───────────────────────────────────────────────────────────────
# Streamlit‑wide setup
# ───────────────────────────────────────────────────────────────
from __future__ import annotations

import atexit

import streamlit as st

LABEL: str = (
    "Personalised" if st.session_state.get("use_personalisation", True) else "Generic"
)
st.set_page_config(page_title=f"{LABEL} Learning Platform", layout="wide")
atexit.register(lambda: get_learning_logger().save_logs(force=True))

# ── std‑lib ────────────────────────────────────────────
import os
from pathlib import Path
from typing import Dict, List

# ── third‑party ────────────────────────────────────────────────
import google.generativeai as genai
from google.genai.types import Content, Part
from PIL import Image

# ── local ──────────────────────────────────────────────────────
from Gemini_UI import (
    TRANSCRIPTION_DIR,
    UPLOAD_DIR_AUDIO,
    UPLOAD_DIR_PPT,
    UPLOAD_DIR_PROFILE,
    build_prompt,
    create_summary_prompt,
    debug_log,
)
from Gemini_UI import export_ppt_slides as process_ppt_file  # alias → keep old name
from Gemini_UI import (
    parse_detailed_student_profile,
)
from Gemini_UI import (
    transcribe_audio as transcribe_audio_from_file,  # alias → keep old name
)
from personalized_learning_logger import get_learning_logger
from session_manager import get_session_manager

sm = get_session_manager()

# ───────────────────────────────────────────────────────────────
# Globals & constants
# ───────────────────────────────────────────────────────────────
DEV_MODE: bool = True
TOPIC: str = "'Machine Learning Techniques for Detecting Email Threats'"
API_KEY: str = "AIzaSyArkmZSrZaeWQSfL9CFkQ0jXaEe4D9sMEQ"

# Yiman = AIzaSyCdNS08cjO_lvj35Ytvs8szbUmeAdo4aIA
# Furkan Ali = AIzaSyArkmZSrZaeWQSfL9CFkQ0jXaEe4D9sMEQ

# --- tutor‑related objects that Gemini_UI expects -----------------
DEFAULTS = {
    "exported_images": [],  # list[Path] – exported PPT slides
    "transcription_text": "",  # Whisper output
    "selected_slide": "Slide 1",
    "profile_text": "",  # long plain‑text profile
    "profile_dict": {},  # parsed dict version
    "debug_logs": [],  # collected via Gemini_UI.debug_log(...)
    "messages": []
}

for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

# Navigation & completion flags
for key in (
    "current_page",
    "profile_completed",
    "learning_completed",
    "test_completed",
    "ueq_completed",
):
    st.session_state.setdefault(key, False if key != "current_page" else "home")

# ───────────────────────────────────────────────────────────────
# Helper functions
# ───────────────────────────────────────────────────────────────


def dict_to_content(d: Dict[str, str]) -> Content:
    """Convert a dict with *role* & *content* into a Gemini :class:`Content`."""
    return Content(role=d["role"], parts=[Part.from_text(text=d["content"])])


def navigate_to(page: str) -> None:
    """Client‑side router with prerequisite checks."""

    allowed = False
    if page == "profile_survey":
        allowed = True
    elif page == "personalized_learning":
        allowed = st.session_state.profile_completed
        if not allowed:
            st.warning("Please complete the Student Profile Survey first.")
    elif page == "knowledge_test":
        allowed = (
            st.session_state.profile_completed and st.session_state.learning_completed
        )
        if not allowed:
            st.warning(
                "Please finish the profile survey and explore the learning content first."
            )
    elif page == "ueq_survey":
        allowed = (
            st.session_state.profile_completed
            and st.session_state.learning_completed
            and st.session_state.test_completed
        )
        if not allowed:
            st.warning("Please finish all previous components before the UEQ survey.")
    elif page == "home":
        allowed = True

    if allowed:
        st.session_state.current_page = page
        st.rerun()


# ───────────────────────────────────────────────────────────────
# Sidebar navigation
# ───────────────────────────────────────────────────────────────

st.sidebar.title("Navigation")
nav_items = [
    ("🏠 Home", "home", True),
    ("Student Profile Survey", "profile_survey", st.session_state.profile_completed),
    (f"{LABEL} Learning", "personalized_learning", st.session_state.learning_completed),
    ("Knowledge Test", "knowledge_test", st.session_state.test_completed),
    ("User Experience Survey", "ueq_survey", st.session_state.ueq_completed),
]

for title, target, done in nav_items:
    prefix = "✅ " if done else "⬜ "
    if st.sidebar.button(f"{prefix}{title}"):
        navigate_to(target)
        st.rerun()

# ───────────────────────────────────────────────────────────────
# Page logic – each branch keeps the original behaviour
# ───────────────────────────────────────────────────────────────

if st.session_state.current_page == "home":
    # ------------------------------------------------------------------
    # HOME  ─ study intro
    # ------------------------------------------------------------------
    st.title(f"🎓 {LABEL} Learning Platform")
    st.markdown(
        f"""
### Welcome – what this session is about  
You are taking part in our KU Leuven study on **AI‑generated, personalised learning explanations**.  
We want to find out whether explanations that match a learner's background help them understand course material better than generic ones.

In today's session, it will be about **{TOPIC}**.

---
#### What will happen? – step by step  
| Step | What you do | Time | What you provide |
|------|-------------|------|------------------|
| 1 | Read & sign the digital consent form | ≈ 2 min | e‑signature |
| 2 | **Student Profile Survey** | ≈ 8 min | background, learning goals |
| 3 | **({LABEL}) Learning** using LLM | ≈ 25 min | questions to the LLM (optional) |
| 4 | **Knowledge Test** | ≈ 10 min | answers to 5 quiz items |
| 5 | **User‑Experience Questionnaire** | ≈ 8 min | 26 quick ratings |
| 6 | Short verbal interview / Q&A | ≈ 5 min | feedback |

*Total time*: **~ 60 minutes**

---
#### Your role  
* Work through the steps **in the order shown** (use the sidebar).  
* Give honest answers – there are no right or wrong responses.  
* **Ask questions any time** – just speak to the facilitator.

---
#### Why we record your data  
We log your inputs and the system's responses to analyse how well the personalised tutor works.  
Your name is replaced by a random code; you may stop at any moment without penalty.

---
When you are ready, click **“Start the Student Profile Survey”** below.  
Thank you for helping us improve personalised learning!
"""
    )

    # — facilitator: choose study condition --------------------------------
    if "condition_chosen" not in st.session_state:
        st.sidebar.subheader("⚙️ Study condition (facilitator only)")
        cond = st.sidebar.radio(
            "Show explanations as …", ["personalised", "generic"], key="cond_radio"
        )
        if st.sidebar.button("Assign & start"):

            st.session_state["session_manager"] = sm
            st.session_state["use_personalisation"] = cond == "personalised"
            st.session_state["condition_chosen"] = True
            st.rerun()

    # — dev helper ---------------------------------------------------------
    if DEV_MODE and st.button("Enable Fast Test Mode (Dev Only)"):
        st.session_state["fast_test_mode"] = True
        # minimal stubs used by Gemini_UI
        st.session_state.exported_images = [
            Path("uploads/ppt/picture/Slide_4 of Lecture8.png")
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
        st.rerun()

    if st.button("Start with Student Profile Survey", use_container_width=True):
        navigate_to("profile_survey")

# ------------------------------------------------------------------------
# PROFILE SURVEY  – writes profile text & dict to session_state
# ------------------------------------------------------------------------
elif st.session_state.current_page == "profile_survey":
    import importlib

    import testui_profilesurvey

    importlib.reload(testui_profilesurvey)  # ensure fresh on each run
    st.sidebar.success("Profile survey module loaded successfully")

    if st.session_state.get("show_review", False):
        st.session_state.profile_completed = True

        # Build a *single* long profile string (if not yet done) --------------
        if not st.session_state.get("profile_text"):
            # Collect answers from the survey widgets (mirrors the original logic)
            survey = testui_profilesurvey  # alias
            name = st.session_state.get("name", "")
            age = st.session_state.get("age", "")
            edu = st.session_state.get("education_level", "")
            major = st.session_state.get("major", "")
            work = st.session_state.get("work_exp", "")
            hobbies = st.session_state.get("hobbies", "")
            strongest = st.session_state.get("strongest_subject", "")
            weakest = st.session_state.get("challenging_subject", "")
            prof_level = st.session_state.get("proficiency_level", "")

            ratings = {s: st.session_state.get(s) for s in survey.subjects}
            prio_ratings = {
                p: st.session_state.get(p) for p in survey.learning_priorities
            }
            sel_strats = [
                s for s in survey.learning_strategies if st.session_state.get(s)
            ]
            short_goals = [
                g for g in survey.short_term_goals if st.session_state.get(f"short_{g}")
            ]
            long_goals = [
                g for g in survey.long_term_goals if st.session_state.get(f"long_{g}")
            ]
            barriers = [
                b for b in survey.barriers if st.session_state.get(f"barrier_{b}")
            ]

            profile_lines: List[str] = [
                "Student Profile Survey Responses:",
                "=" * 36,
                "",
                "Section 1: Academic and Background Information",
                "-" * 45,
                f"1. Name: {name}",
                f"2. Age: {age}",
                f"3. Study background: {edu}",
                f"4. Major of education: {major}",
                f"5. Work experience: {work}",
                f"6. Hobbies or interests: {hobbies}",
                "",
                "7. Academic performance ranking (1=Weakest, 5=Strongest):",
            ]
            for i, (subj, rating) in enumerate(ratings.items()):
                profile_lines.append(f"   {chr(65+i)}. {subj}: {rating}")

            profile_lines.extend(
                [
                    "",
                    f"8. Strongest Subject: {strongest}",
                    f"9. Most Challenging Subject: {weakest}",
                    "",
                    "10. Learning priorities ranking (1=least important, 5=most important):",
                ]
            )
            for i, (prio, rating) in enumerate(prio_ratings.items()):
                profile_lines.append(f"   {chr(65+i)}. {prio}: {rating}")

            profile_lines.extend(
                [
                    "",
                    f"11. Preferred learning strategy: {'; '.join(sel_strats)}",
                    f"12. Current proficiency level: {prof_level}",
                    f"13. Short-term academic goals: {'; '.join(short_goals)}",
                    f"14. Long-term academic/career goals: {'; '.join(long_goals)}",
                    f"15. Potential Barriers: {'; '.join(barriers)}",
                ]
            )
            profile_text = "\n".join(profile_lines)
            st.session_state.profile_text = profile_text

            # Persist original profile
            profile_path = UPLOAD_DIR_PROFILE / f"{name.replace(' ', '_')}_profile.txt"
            profile_path.write_text(profile_text, encoding="utf‑8")

            # Dict version for later use
            st.session_state.profile_dict = parse_detailed_student_profile(profile_text)

        st.success(f"Profile saved – proceed to the {LABEL} Learning section.")
        if st.button(f"Continue to {LABEL} Learning", use_container_width=True):
            navigate_to("personalized_learning")

# ------------------------------------------------------------------------
# PERSONALISED / GENERIC LEARNING  – Gemini tutor UI
# ------------------------------------------------------------------------
elif st.session_state.current_page == "personalized_learning":
    if not st.session_state.profile_completed:
        st.warning("Please complete the Student Profile Survey first.")
        if st.button("Go to Student Profile Survey"):
            navigate_to("profile_survey")
    else:
        # --- header ------------------------------------------------------
        st.title(f"{LABEL} Explanation Generator")
        st.markdown(
            f"This component lets you generate **{LABEL.lower()}** explanations based on your profile, uploaded slides, and lecture audio."
        )

        genai.configure(api_key=API_KEY)

        if "gemini_chat" not in st.session_state:
            #model = genai.GenerativeModel("gemini-2.5-pro-exp-03-25")
            model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")
            st.session_state.gemini_chat = model.start_chat(history=[])
        chat = st.session_state.gemini_chat

        if DEV_MODE:
            st.sidebar.info(
                f"📝 {len(get_learning_logger().log_entries)} interactions buffered"
            )

        # Sidebar uploads -------------------------------------------------
        st.sidebar.header("Input Files")
        audio_up = st.sidebar.file_uploader(
            "Upload Audio File", ["wav", "mp3", "ogg", "flac", "m4a", "mp4"]
        )
        ppt_up = st.sidebar.file_uploader("Upload PPT", ["ppt", "pptx"])
        st.sidebar.success("✅ Profile loaded from survey responses")

        # Debug toggles ---------------------------------------------------
        if st.checkbox("Show Debug Logs"):
            st.subheader("Debug Logs")
            for l in st.session_state.get("debug_logs", []):
                st.text(l)
        if st.checkbox("Show Parsed Profile"):
            st.json(st.session_state.profile_dict)

        # Handle audio upload -------------------------------------------
        if audio_up is not None:
            a_path = UPLOAD_DIR_AUDIO / audio_up.name
            a_path.write_bytes(audio_up.getbuffer())
            st.sidebar.success(f"Saved {audio_up.name}")
            if st.sidebar.button("Transcribe Audio"):
                st.session_state.transcription_text = transcribe_audio_from_file(a_path)
                st.sidebar.success("Transcription complete!")

        # Handle PPT upload ---------------------------------------------
        if ppt_up is not None:
            p_path = UPLOAD_DIR_PPT / ppt_up.name
            p_path.write_bytes(ppt_up.getbuffer())
            st.sidebar.success(f"Saved {ppt_up.name}")
            if st.sidebar.button("Process PPT"):
                st.session_state.exported_images = process_ppt_file(p_path)
                st.sidebar.success(
                    f"Exported {len(st.session_state.exported_images)} slides"
                )

        # Slide selector --------------------------------------------------
        if st.session_state.exported_images:
            slides = [
                f"Slide {i+1}" for i in range(len(st.session_state.exported_images))
            ]
            selected_slide = st.sidebar.selectbox(
                "Select a Slide", slides, key="selected_slide"
            )
        else:
            selected_slide = None

        # Layout ---------------------------------------------------------
        col_chat, col_prev = st.columns([2, 1])

        # ----- chat column ---------------------------------------------
        with col_chat:
            st.header("LLM Chat")
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"], unsafe_allow_html=True)

            user_chat = st.chat_input("Ask a follow‑up question …")
            if user_chat:
                reply = chat.send_message(user_chat)
                st.session_state.messages.extend(
                    [
                        {"role": "user", "content": user_chat},
                        {"role": "assistant", "content": reply.text},
                    ]
                )
                get_learning_logger().log_interaction(
                    interaction_type="chat",
                    user_input=user_chat,
                    system_response=reply.text,
                    metadata={"slide": None, "condition": LABEL.lower()},
                )
                st.rerun()

            # Generate explanation button --------------------------------
            ready = (
                st.session_state.transcription_text
                and st.session_state.exported_images
                and st.session_state.profile_dict
            )
            if ready and selected_slide and st.button(f"Generate {LABEL} explanation"):
                s_idx = int(selected_slide.split()[1]) - 1
                img = Image.open(st.session_state.exported_images[s_idx])

                prompt_json = build_prompt(
                    f"Content from {selected_slide} (see slide image).",
                    st.session_state.transcription_text,
                    st.session_state.profile_dict,
                    selected_slide,
                    personalised=st.session_state.get("use_personalisation", True),
                )
                debug_log(prompt_json)

                reply = chat.send_message([img, prompt_json])

                summary = create_summary_prompt(
                    st.session_state.profile_dict,
                    selected_slide,
                    personalised=st.session_state.get("use_personalisation", True),
                )
                st.session_state.messages.extend(
                    [
                        {"role": "user", "content": summary},
                        {"role": "assistant", "content": reply.text},
                    ]
                )
                st.session_state.learning_completed = True

                # Log & persist ----------------------------------------
                ll = get_learning_logger()
                ll.log_interaction(
                    interaction_type="personalized_explanation",
                    user_input=prompt_json,
                    system_response=reply.text,
                    metadata={
                        "slide": selected_slide,
                        "profile": st.session_state.profile_dict.get("Name", "Unknown"),
                        "condition": LABEL.lower(),
                        "session_id": ll.session_manager.session_id,
                    },
                )
                st.rerun()

            if not ready:
                st.info("Upload & process audio + PPT to enable prompting.")

        # ----- preview column -------------------------------------------
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

            if st.session_state.get("profile_text"):
                st.subheader("Student Profile")
                st.text_area("Profile", st.session_state.profile_text, height=150)

        # Navigation buttons ---------------------------------------------
        st.markdown("---")
        col_p, col_n = st.columns(2)
        with col_p:
            if st.button("Previous: Student Profile"):
                navigate_to("profile_survey")
        with col_n:
            if st.session_state.learning_completed:
                if st.button("Next: Knowledge Test"):
                    log_path = get_learning_logger().save_logs()
                    st.session_state["learning_log_file"] = log_path
                    navigate_to("knowledge_test")
            else:
                st.button("Next: Knowledge Test", disabled=True)
                st.info("Generate at least one explanation before proceeding.")

# ------------------------------------------------------------------------
# KNOWLEDGE TEST  – simple wrapper around *testui_knowledgetest*
# ------------------------------------------------------------------------
elif st.session_state.current_page == "knowledge_test":
    import importlib

    import testui_knowledgetest

    importlib.reload(testui_knowledgetest)

    if not st.session_state.profile_completed:
        st.warning("Please complete the Student Profile Survey first.")
        if st.button("Go to Student Profile Survey"):
            navigate_to("profile_survey")
    elif not st.session_state.learning_completed:
        st.warning(f"Please complete the {LABEL.lower()} Learning section first.")
        if st.button(f"Go to {LABEL} Learning"):
            navigate_to("personalized_learning")
    else:
        if "score" in st.session_state:
            st.session_state.test_completed = True

        st.markdown("---")
        prev, nxt = st.columns(2)
        with prev:
            if st.button(f"Previous: {LABEL} Learning"):
                navigate_to("personalized_learning")
        with nxt:
            if st.session_state.test_completed:
                if st.button("Next: User Experience Survey"):
                    navigate_to("ueq_survey")
            else:
                st.button("Next: User Experience Survey", disabled=True)
                st.info("Complete the Knowledge Test first.")

# ------------------------------------------------------------------------
# UEQ SURVEY  – wrapper around *testui_ueqsurvey*
# ------------------------------------------------------------------------
elif st.session_state.current_page == "ueq_survey":
    import importlib

    import testui_ueqsurvey

    importlib.reload(testui_ueqsurvey)

    if not st.session_state.profile_completed:
        st.warning("Please complete the Student Profile Survey first.")
        if st.button("Go to Student Profile Survey"):
            navigate_to("profile_survey")
    elif not st.session_state.learning_completed:
        st.warning(f"Please complete the {LABEL} Learning section first.")
        if st.button(f"Go to {LABEL} Learning"):
            navigate_to("personalized_learning")
    elif not st.session_state.test_completed:
        st.warning("Please complete the Knowledge Test first.")
        if st.button("Go to Knowledge Test"):
            navigate_to("knowledge_test")
    else:
        # mark as completed once at least one answer present
        if any(
            resp.get("value") is not None
            for resp in st.session_state.get("responses", {}).values()
        ):
            st.session_state.ueq_completed = True

        st.markdown("---")
        col_b, col_f = st.columns(2)
        with col_b:
            if st.button("Previous: Knowledge Test"):
                navigate_to("knowledge_test")
        with col_f:
            if st.button("Finish"):
                navigate_to("home")
                st.success("Thank you for completing all components of the platform!")
