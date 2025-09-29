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
import json
import streamlit as st

LABEL: str = "Learning" # internal flag stays in use_personalisation
st.set_page_config(page_title=f"{LABEL} Platform", layout="wide")
atexit.register(lambda: get_learning_logger().save_logs(force=True))
atexit.register(lambda: page_dump(Path(sm.session_dir)))

# ── std‑lib ────────────────────────────────────────────
import os
from pathlib import Path
from typing import Dict, List

# ── third‑party ────────────────────────────────────────────────
#import google.generativeai as genai
#from google.genai.types import Content, Part
from PIL import Image
from google import genai
from google.genai import types

# ── local ──────────────────────────────────────────────────────
# NEW – GDPR docs ------------------------------------------------
DOCS_DIR   = Path(__file__).parent / "docs"
INFO_PDF   = DOCS_DIR / "Model informatiebrief AVG English.pdf"
CONSENT_PDF = DOCS_DIR / "ICF SMEC ENG.pdf"

from Gemini_UI import (
    TRANSCRIPTION_DIR,
    UPLOAD_DIR_AUDIO,
    UPLOAD_DIR_PPT,
    UPLOAD_DIR_PROFILE,
    build_prompt,
    create_summary_prompt,
    make_base_context,
    debug_log,
    parse_detailed_student_profile,
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
from page_timer import start as page_timer_start      # put this with the other imports
from page_timer import dump as page_dump

sm = get_session_manager()

if "_page_timer" not in st.session_state:
    from page_timer import start as page_timer_start
    
    page_timer_start("home")

# ── study-condition toggle ────────────────────────────────────────────
# True  -> personalised explanations
# False -> generic explanations
DEFAULT_PERSONALISED: bool = False            # ← change this for each study run

# ---------------------------------------------------------------------
# set study condition from the constant above (runs once per session)
# ---------------------------------------------------------------------
if "condition_chosen" not in st.session_state:
    st.session_state["use_personalisation"] = DEFAULT_PERSONALISED
    st.session_state["condition_chosen"]    = True
    sm.condition = "personalised" if DEFAULT_PERSONALISED else "generic"

# ───────────────────────────────────────────────────────────────
# Globals & constants
# ───────────────────────────────────────────────────────────────
DEV_MODE: bool = False
TOPIC: str = "'Introduction to Cancer Biology'"
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

def current_condition() -> str:
    return "personalised" if st.session_state.get("use_personalisation", True) else "generic"

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
        page_dump(Path(sm.session_dir))
        page_timer_start(page)
        st.session_state.current_page  = page
        st.rerun()


# ───────────────────────────────────────────────────────────────
# Sidebar navigation
# ───────────────────────────────────────────────────────────────

st.sidebar.title("Navigation")
nav_items = [
    ("🏠 Home", "home", True),
    ("Student Profile Survey", "profile_survey", st.session_state.profile_completed),
    (f"{LABEL}", "personalized_learning", st.session_state.learning_completed),
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
    st.title(f"🎓 {LABEL} Platform")
    st.markdown(
        f"""
### Welcome – what this session is about  
You are taking part in our KU Leuven study on **AI‑generated, personalised learning explanations**.  
We are studying whether tailoring explanations to a learner’s background affects their understanding of the material compared to providing general explanations.

In today's session, it will be about **{TOPIC}**.

---
#### What will happen? – step by step  
| Step | What you do | Time | What you provide |
|------|-------------|------|------------------|
| 1 | Read & sign the digital consent form | ≈ 2 min | e‑signature |
| 2 | **Student Profile Survey** | ≈ 8 min | background, learning goals |
| 3 | **{LABEL}** using LLM | ≈ 25 min | questions to the LLM (optional) |
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
We log your inputs and the system's responses to analyse the tutor’s effectiveness.  
Your name is replaced by a random code; you may stop at any moment without penalty.

---
When you are ready, click **“Start the Student Profile Survey”** below.  
Thank you for helping us improve adaptive learning experiences!
"""
    )
    # --- GDPR / informed-consent box ---------------------------------
    with st.expander("ℹ️  Study information & GDPR (click to read)"):
        st.markdown(
            "**Your key rights in 2 lines**  \n"
            "• You may stop at any moment without consequences.  \n"
            "• Pseudonymised study data are used **only** for academic research."
        )

        col_a, col_b = st.columns(2)
        with col_a:
            with open(CONSENT_PDF, "rb") as f:
                st.download_button(
                    "📄 Informed-consent form (PDF)", f, file_name=CONSENT_PDF.name
                )
        with col_b:
            with open(INFO_PDF, "rb") as f:
                st.download_button(
                    "📄 GDPR information letter (PDF)", f, file_name=INFO_PDF.name
                )
    # one-line checkbox underneath the expander (outside the `with` block!)
    consent_ok = st.checkbox(
        "I have read the documents above and **give my consent** to participate.",
        key="consent_checkbox"
    )
    st.session_state["consent_given"] = consent_ok

    # ─── write a one-time log entry ─────────────────────────────────
    if consent_ok and not st.session_state.get("consent_logged"):
        get_learning_logger().log_interaction(
            interaction_type="consent",
            user_input="checkbox ticked",
            system_response="(none)",
            metadata={}
        )
        st.session_state["consent_logged"] = True

    # — facilitator: choose study condition --------------------------------
#    if "condition_chosen" not in st.session_state:
#        st.sidebar.subheader("⚙️ Study condition (facilitator only)")
#        cond = st.sidebar.radio(
#            "Show explanations as …", ["personalised", "generic"], key="cond_radio"
#        )
#        if st.sidebar.button("Assign & start"):

#            cond_flag = (cond == "personalised")          # True / False
#            cond_name = "personalised" if cond_flag else "generic"

#            st.session_state["use_personalisation"] = cond_flag
#            st.session_state["condition_chosen"] = True

            # --- NEW ----------------------------------------------------------
#            sm.condition = cond_name                     # <- update existing SessionManager
            # ------------------------------------------------------------------
#
#            st.rerun()


    # — dev helper ---------------------------------------------------------
    if DEV_MODE:
        st.button("Enable Fast Test Mode (Dev Only)")
        st.session_state["fast_test_mode"] = True
        # minimal stubs used by Gemini_UI
        st.session_state.exported_images = [
            Path("uploads/ppt/picture/Slide_4 of Lecture8.png")
        ]
        st.session_state.transcription_text = (
            "This is a mock transcription for fast testing."
        )
        sample_path = Path(__file__).parent / "uploads" / "profile" / "Test_User_profile.txt" 
        profile_txt = sample_path.read_text(encoding="utf-8")

        st.session_state.profile_text  = profile_txt
        st.session_state.profile_dict  = parse_detailed_student_profile(profile_txt)

        st.session_state.selected_slide = "Slide 1"
        st.rerun()

    if st.button(
        "Start Student Profile Survey",
        use_container_width=True,
        disabled=not st.session_state.get("consent_given", False),
    ):
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

        st.success(f"Profile saved – proceed to the {LABEL} section.")
        if st.button(f"Continue to {LABEL}", use_container_width=True):
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
        st.title(f"Explanation Generator")
        st.markdown(
            f"This component lets you generate explanations with the uploaded slides and lecture audio."
        )

        #genai.configure(api_key=API_KEY)
        client = genai.Client(  api_key=API_KEY# picks up GEMINI_API_KEY env automatically
            # http_options={"api_version": "v1alpha"}  # optional if you need early features
        )

        # … after starting the chat object …
        if "gemini_chat" not in st.session_state:
            #model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")
            #st.session_state.gemini_chat = model.start_chat(history=[])
            st.session_state.gemini_chat = client.chats.create(
                model="gemini-2.5-flash",
                history=[]
            )
            PERSONALISED = st.session_state.get("use_personalisation", True)

            base_ctx = make_base_context(
                st.session_state.profile_dict if PERSONALISED else None,
                personalised=PERSONALISED
            )

            st.session_state.gemini_chat.send_message(json.dumps(base_ctx))

            get_learning_logger().log_interaction(
                interaction_type="prime_context",
                user_input=base_ctx,           # already a small dict
                system_response="(no reply – prime only)",
                metadata={"condition": current_condition()},
            )

            #st.session_state.messages.append(
            #    {"role": "system", "content": json.dumps(base_ctx, indent=2)}
            #)

        
        #        # Sidebar uploads -------------------------------------------------
        #        st.sidebar.header("Input Files")
        #        audio_up = st.sidebar.file_uploader(
        #            "Upload Audio File", ["wav", "mp3", "ogg", "flac", "m4a", "mp4"]
        #        )
        #        ppt_up = st.sidebar.file_uploader("Upload PPT", ["ppt", "pptx"])
        #        st.sidebar.success("✅ Profile loaded from survey responses")

        

        if DEV_MODE:
            # Live interaction tracking for development
            interaction_counts = get_learning_logger().get_interaction_counts()
            st.sidebar.info(
                f"📝 {len(get_learning_logger().log_entries)} interactions buffered"
            )
            st.sidebar.metric("Slide Explanations", interaction_counts["slide_explanations"])
            st.sidebar.metric("Manual Chat", interaction_counts["manual_chat"]) 
            st.sidebar.metric("Total User Interactions", interaction_counts["total_user_interactions"])
            # Sidebar: Input Files
            st.sidebar.header("Input Files")
            audio_up = st.sidebar.file_uploader("Upload Audio File", ["wav", "mp3", "ogg", "flac", "m4a", "mp4"])
            ppt_up   = st.sidebar.file_uploader("Upload PPT", ["ppt", "pptx"])
            #st.sidebar.success("✅ Profile loaded from survey responses")
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
        else:
            # Production mode: Use pre-processed Cancer Biology content
            st.sidebar.header("Course Content")
            st.sidebar.info("📚 **Introduction to Cancer Biology**\n\nUsing pre-loaded course materials:\n- 27 lecture slides\n- Complete audio transcription")
            
            # Load pre-transcribed Cancer Biology content
            if not st.session_state.transcription_text:
                transcription_file = TRANSCRIPTION_DIR / "turbo_transcription_Introduction to Cancer Biology.txt"
                if transcription_file.exists():
                    try:
                        st.session_state.transcription_text = transcription_file.read_text(encoding="utf-8")
                        st.sidebar.success(f"✅ Transcription loaded ({len(st.session_state.transcription_text):,} chars)")
                        debug_log(f"Loaded Cancer Biology transcription from {transcription_file.name}")
                    except Exception as e:
                        st.sidebar.error(f"❌ Error loading transcription: {e}")
                        debug_log(f"Error loading transcription: {e}")
                else:
                    st.sidebar.error("❌ Cancer Biology transcription not found")
                    debug_log(f"Transcription file not found: {transcription_file}")
            else:
                st.sidebar.success(f"✅ Transcription loaded ({len(st.session_state.transcription_text):,} chars)")
            
            # Load pre-processed Cancer Biology slides  
            if not st.session_state.exported_images:
                slides_dir = UPLOAD_DIR_PPT / "fixed" / "picture"
                if slides_dir.exists():
                    slide_files = list(slides_dir.glob("Slide_*.jpg"))
                    if slide_files:
                        # Sort numerically by extracting the number from the filename
                        def extract_slide_number(path):
                            import re
                            match = re.search(r'Slide_(\d+)', path.name)
                            return int(match.group(1)) if match else 0
                        
                        slide_files = sorted(slide_files, key=extract_slide_number)
                        st.session_state.exported_images = slide_files
                        st.sidebar.success(f"✅ {len(slide_files)} slides loaded")
                        debug_log(f"Loaded {len(slide_files)} Cancer Biology slides from {slides_dir}")
                        
                        # Debug: show the first and last few slide names to verify sorting
                        first_few = [f.name for f in slide_files[:5]]
                        last_few = [f.name for f in slide_files[-3:]]
                        debug_log(f"First 5 slides: {first_few}")
                        debug_log(f"Last 3 slides: {last_few}")
                        
                        # Debug: show extracted numbers to verify sorting function
                        extracted_numbers = [extract_slide_number(f) for f in slide_files[:10]]
                        debug_log(f"First 10 extracted numbers: {extracted_numbers}")
                    else:
                        st.sidebar.error("❌ No slide images found in slides directory")
                        debug_log(f"No slide files found in {slides_dir}")
                else:
                    st.sidebar.error("❌ Slides directory not found")
                    debug_log(f"Slides directory not found: {slides_dir}")
            else:
                st.sidebar.success(f"✅ {len(st.session_state.exported_images)} slides loaded")




        # Slide selector --------------------------------------------------
        if st.session_state.exported_images:
            # Since files are already sorted numerically, create simple sequential labels
            slides = [f"Slide {i+1}" for i in range(len(st.session_state.exported_images))]
            
            selected_slide = st.sidebar.selectbox(
                "Select a Slide", slides, key="selected_slide"
            )
            
            # Show current slide filename for debugging
            if selected_slide:
                try:
                    # Extract index from the dropdown selection (Slide 1 = index 0, etc.)
                    slide_idx = int(selected_slide.split()[1]) - 1
                    if 0 <= slide_idx < len(st.session_state.exported_images):
                        current_file = st.session_state.exported_images[slide_idx].name
                        st.sidebar.caption(f"File: {current_file}")
                        
                        # Extract actual slide number from filename for verification
                        import re
                        match = re.search(r'Slide_(\d+)', current_file)
                        if match:
                            actual_slide_num = match.group(1)
                            expected_slide_num = str(slide_idx + 1)
                            if actual_slide_num != expected_slide_num:
                                st.sidebar.warning(f"⚠️ Mismatch: Selected {selected_slide} but showing Slide_{actual_slide_num}")
                except (ValueError, IndexError):
                    st.sidebar.error("Error parsing slide selection")
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
            PERSONALISED = st.session_state.get("use_personalisation", True)
            if user_chat:
                payload = json.dumps({
                    **make_base_context(
                        st.session_state.profile_dict if PERSONALISED else None,
                        personalised=PERSONALISED
                    ),
                    "UserQuestion": user_chat
                })

                #reply = st.session_state.gemini_chat.send_message(payload)
                
                # Create thinking config step by step for debugging
                thinking_config = types.ThinkingConfig(includeThoughts=True)
                content_config = types.GenerateContentConfig(thinking_config=thinking_config)
                
                reply = st.session_state.gemini_chat.send_message(
                    payload,
                    config=content_config
                )
                
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
                    metadata={"slide": None, "condition": current_condition()},
                )
                st.rerun()

            # Generate explanation button --------------------------------
            ready = (
                st.session_state.transcription_text
                and st.session_state.exported_images
                and st.session_state.profile_dict
            )
            if ready and selected_slide and st.button(f"Generate slide summary"):
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

                # Create thinking config step by step for debugging
                thinking_config = types.ThinkingConfig(includeThoughts=True)
                content_config = types.GenerateContentConfig(thinking_config=thinking_config)
                
                reply = st.session_state.gemini_chat.send_message([img, prompt_json], config=content_config)

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
                        "condition": current_condition(),
                        "session_id": ll.session_manager.session_id,
                    },
                )
                st.rerun()

            if not ready:
                # Check what's missing and provide specific guidance
                missing_items = []
                if not st.session_state.transcription_text:
                    missing_items.append("audio transcription")
                if not st.session_state.exported_images:
                    missing_items.append("lecture slides") 
                if not st.session_state.profile_dict:
                    missing_items.append("student profile")
                
                if missing_items:
                    if "student profile" in missing_items and len(missing_items) == 1:
                        st.info("📝 Complete the Student Profile Survey first to enable explanation generation.")
                    else:
                        st.info(f"⏳ Loading course content... Missing: {', '.join(missing_items)}")
                else:
                    st.info("⏳ Preparing explanation generator...")

        # ----- preview column -------------------------------------------
        with col_prev:
            st.header("Preview Files")
            if st.session_state.transcription_text:
                st.subheader("Transcription")
                st.text_area("Output", st.session_state.transcription_text, height=150)

            if st.session_state.exported_images and selected_slide:
                idx = int(selected_slide.split()[1]) - 1
                
                from pathlib import Path
                slide_path = st.session_state.exported_images[idx]
                
                # Convert to Path object if it isn't already
                if not isinstance(slide_path, Path):
                    slide_path = Path(slide_path)
                
                # Check if file exists
                if not slide_path.exists():
                    st.error(f"Slide not found: {slide_path.resolve()}")
                    st.write(f"Current working directory: {Path.cwd()}")
                    st.write(f"Looking for: {slide_path}")
                    st.stop()
                
                try:
                    # Use PIL to open and verify the image
                    img = Image.open(slide_path)
                    st.image(img, caption=str(slide_path.name), use_column_width=True)
                except Exception as e:
                    st.exception(e)
                    st.stop()

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
        st.warning(f"Please complete the {LABEL.lower()} section first.")
        if st.button(f"Go to {LABEL} Learning"):
            navigate_to("personalized_learning")
    else:
        if "score" in st.session_state:
            st.session_state.test_completed = True

        st.markdown("---")
        prev, nxt = st.columns(2)
        with prev:
            if st.button(f"Previous: {LABEL}"):
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
                # Generate final consolidated analytics
                try:
                    sm = get_session_manager()
                    final_analytics_path = sm.create_final_analytics()
                    st.success(f"Thank you for completing all components of the platform!")
                    st.info(f"Final research analytics saved: `{os.path.basename(final_analytics_path)}`")
                except Exception as e:
                    st.warning(f"Could not generate final analytics: {e}")
                    st.success("Thank you for completing all components of the platform!")
                navigate_to("home")
