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

# ── Authentication Check (MUST BE FIRST) ──────────────────────
from login_page import require_authentication
credential_config = require_authentication()
print("🔧 DEBUG: Authentication completed")

# ── Initialize Session State (IMMEDIATELY AFTER AUTH) ─────────
def ensure_session_state_initialized():
    """Ensure all required session state variables are initialized with defaults."""
    print("🔧 DEBUG: Starting session state initialization")
    # --- tutor‑related objects that Gemini_UI expects -----------------
    DEFAULTS = {
        "exported_images": [],  # list[Path] – exported PPT slides
        "transcription_text": "",  # Whisper output
        "selected_slide": "Slide 1",
        "profile_text": "",  # long plain‑text profile
        "profile_dict": {},  # parsed dict version
        "debug_logs": [],  # collected via Gemini_UI.debug_log(...)
        "messages": [],
        "transcription_loaded": False,
        "slides_loaded": False
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
    print("🔧 DEBUG: Session state initialization completed")

# Always ensure session state is properly initialized
ensure_session_state_initialized()
print("🔧 DEBUG: About to start imports")

# ── Configuration ──────────────────────────────────────────────
from config import get_config, get_course_title, get_platform_name, get_ui_text
config = get_config()
print("🔧 DEBUG: Config loaded")

LABEL: str = config.platform.learning_section_name
st.set_page_config(page_title=f"{get_platform_name()}", layout="wide")
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

# Import UPLOAD_DIR_VIDEO with fallback for deployment issues
try:
    from Gemini_UI import UPLOAD_DIR_VIDEO
except ImportError:
    # Fallback: create video directory if import fails
    UPLOAD_DIR_VIDEO = Path.cwd() / "uploads" / "video"
    UPLOAD_DIR_VIDEO.mkdir(parents=True, exist_ok=True)
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

# ── Authentication-based Configuration ─────────────────────────────────
# Study condition and modes are now set based on login credentials
if "condition_chosen" not in st.session_state:
    # Get condition from authentication system
    from authentication import get_auth_manager
    auth_manager = get_auth_manager()
    condition_override = auth_manager.get_study_condition_override()
    
    if condition_override is not None:
        st.session_state["use_personalisation"] = condition_override
        st.session_state["condition_chosen"] = True
        sm.condition = "personalised" if condition_override else "generic"
    
    # Set special modes based on credentials
    if credential_config:
        st.session_state["dev_mode"] = credential_config.dev_mode
        st.session_state["fast_test_mode"] = credential_config.fast_test_mode
    else:
        # Default values when no authentication is active
        st.session_state["dev_mode"] = False
        st.session_state["fast_test_mode"] = False

# ───────────────────────────────────────────────────────────────
# Globals & constants
# ───────────────────────────────────────────────────────────────
DEV_MODE: bool = st.session_state.get("dev_mode", False)
FAST_TEST_MODE: bool = st.session_state.get("fast_test_mode", False)
TOPIC: str = config.course.course_title
API_KEY: str = st.secrets["google"]["api_key"]

# Yiman = AIzaSyCdNS08cjO_lvj35Ytvs8szbUmeAdo4aIA
# Furkan Ali = AIzaSyArkmZSrZaeWQSfL9CFkQ0jXaEe4D9sMEQ

# ───────────────────────────────────────────────────────────────
# Helper functions
# ───────────────────────────────────────────────────────────────

def current_condition() -> str:
    return "personalised" if st.session_state.get("use_personalisation", True) else "generic"

def navigate_to(page: str) -> None:
    """Client‑side router with prerequisite checks."""

    allowed = False
    if page == "profile_survey":
        allowed = True
    elif page == "personalized_learning":
        allowed = st.session_state.profile_completed
        if not allowed:
            st.warning(config.ui_text.warning_complete_profile)
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
    elif page == "completion":
        # Completion page - only accessible if everything is done
        allowed = (
            st.session_state.profile_completed
            and st.session_state.learning_completed
            and st.session_state.test_completed
            and st.session_state.ueq_completed
        )
        if not allowed:
            st.warning("Please complete all interview components first.")
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
    ("Home", "home", True),
    (config.ui_text.nav_profile, "profile_survey", st.session_state.get("profile_completed", False)),
    (f"{LABEL}", "personalized_learning", st.session_state.get("learning_completed", False)),
    (config.ui_text.nav_knowledge, "knowledge_test", st.session_state.get("test_completed", False)),
    (config.ui_text.nav_ueq, "ueq_survey", st.session_state.get("ueq_completed", False)),
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
    st.title(f"{config.platform.learning_section_name} Platform")
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
    with st.expander("Study information & GDPR (click to read)"):
        st.markdown(
            "**Your key rights in 2 lines**  \n"
            "• You may stop at any moment without consequences.  \n"
            "• Pseudonymised study data are used **only** for academic research."
        )

        col_a, col_b = st.columns(2)
        with col_a:
            with open(CONSENT_PDF, "rb") as f:
                st.download_button(
                    "Informed-consent form (PDF)", f, file_name=CONSENT_PDF.name
                )
        with col_b:
            with open(INFO_PDF, "rb") as f:
                st.download_button(
                    "GDPR information letter (PDF)", f, file_name=INFO_PDF.name
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


    # — fast test helper (mock data preloading) --------------------------------
    if FAST_TEST_MODE and not st.session_state.get("fast_test_setup_completed", False):
        print(f"🔧 DEBUG: Setting up fast test mode stubs")
        # minimal stubs used by Gemini_UI
        st.session_state.exported_images = [
            Path("uploads/ppt/picture/Slide_4 of Lecture8.png")
        ]
        st.session_state.transcription_text = (
            "This is a mock transcription for fast testing."
        )
        sample_path = Path(__file__).parent / "uploads" / "profile" / "Test_User_profile.txt" 
        print("🔧 DEBUG: Fast test mode stubs setup completed")
        profile_txt = sample_path.read_text(encoding="utf-8")

        st.session_state.profile_text  = profile_txt
        st.session_state.profile_dict  = parse_detailed_student_profile(profile_txt)

        st.session_state.selected_slide = "Slide 1"
        st.session_state["fast_test_setup_completed"] = True
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
            # Skip profile building in fast test mode since it's pre-loaded
            if not FAST_TEST_MODE:
                # Collect answers from the survey widgets (mirrors the original logic)
                survey = testui_profilesurvey  # alias
                name = st.session_state.get("name", "")
                if not name:  # Fallback for missing name
                    name = "Test_User"
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

        # Initialize Gemini chat only once per session
        print("🔧 DEBUG: About to check gemini_chat initialization")
        if "gemini_chat" not in st.session_state:
            print("🔧 DEBUG: Creating new Gemini chat session")
            st.session_state.gemini_chat = client.chats.create(
                model="gemini-2.5-flash",
                history=[]
            )
            st.session_state.gemini_chat_initialized = False
            print("🔧 DEBUG: Gemini chat session created")

        # Send base context only once per session  
        if not st.session_state.get("gemini_chat_initialized", False):
            print("🔧 DEBUG: About to send base context to Gemini")
            PERSONALISED = st.session_state.get("use_personalisation", True)

            base_ctx = make_base_context(
                st.session_state.profile_dict if PERSONALISED else None,
                personalised=PERSONALISED
            )
            print("🔧 DEBUG: Base context created, sending to Gemini...")

            st.session_state.gemini_chat.send_message(json.dumps(base_ctx))
            st.session_state.gemini_chat_initialized = True
            print("🔧 DEBUG: Base context sent successfully")

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
            print("🔧 DEBUG: Starting dev mode interaction tracking")
            # Live interaction tracking for development - TEMPORARILY DISABLED FOR DEBUGGING
            try:
                print("🔧 DEBUG: About to call get_interaction_counts()")
                # TEMPORARILY COMMENTED OUT TO TEST IF THIS IS THE HANG POINT
                # interaction_counts = get_learning_logger().get_interaction_counts()
                interaction_counts = {"slide_explanations": 0, "manual_chat": 0, "total_user_interactions": 0}
                print("🔧 DEBUG: get_interaction_counts() completed successfully (using mock data)")
                
                st.sidebar.info(
                    f"{len(get_learning_logger().log_entries) if hasattr(get_learning_logger(), 'log_entries') else 0} interactions buffered"
                )
                st.sidebar.metric("Slide Explanations", interaction_counts["slide_explanations"])
                st.sidebar.metric("Manual Chat", interaction_counts["manual_chat"]) 
                st.sidebar.metric("Total User Interactions", interaction_counts["total_user_interactions"])
                print("🔧 DEBUG: Dev mode metrics displayed successfully")
            except Exception as e:
                print(f"🔧 DEBUG: Error in dev mode interaction tracking: {e}")
                st.sidebar.error(f"Error loading interaction metrics: {e}")
            
            # Debug toggles ---------------------------------------------------
            if st.checkbox("Show Debug Logs"):
                st.subheader("Debug Logs")
                for l in st.session_state.get("debug_logs", []):
                    st.text(l)
            if st.checkbox("Show Parsed Profile"):
                st.json(st.session_state.profile_dict)

        # File upload section (controlled by upload_enabled flag) -------------
        if credential_config.upload_enabled:
            print("🔧 DEBUG: Starting file upload section (upload_enabled=True)")
            # Sidebar: Input Files
            st.sidebar.header("Input Files")
            audio_up = st.sidebar.file_uploader("Upload Audio File", ["wav", "mp3", "ogg", "flac", "m4a", "mp4"])
            ppt_up   = st.sidebar.file_uploader("Upload PPT", ["ppt", "pptx"])
            print("🔧 DEBUG: File upload section completed")
            
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
            # No upload access: Use pre-processed course content
            print("🔧 DEBUG: Starting no-upload mode file loading")
            st.sidebar.header("Course Content")
            st.sidebar.info(f"**{config.course.course_title}**\n\nUsing pre-loaded course materials:\n- {config.course.total_slides} lecture slides\n- Complete audio transcription")
            
            # Load pre-transcribed course content (cached)
            print("🔧 DEBUG: About to check transcription loading")
            if not st.session_state.get("transcription_text"):
                print("🔧 DEBUG: Loading transcription file")
                transcription_file = TRANSCRIPTION_DIR / config.course.transcription_filename
                if transcription_file.exists():
                    try:
                        st.session_state.transcription_text = transcription_file.read_text(encoding="utf-8")
                        st.session_state.transcription_loaded = True
                        st.sidebar.success(f"✅ Transcription loaded ({len(st.session_state.transcription_text):,} chars)")
                        print("🔧 DEBUG: Transcription loaded successfully")
                    except Exception as e:
                        print(f"🔧 DEBUG: Error loading transcription: {e}")
                        st.sidebar.error(f"❌ Error loading transcription: {e}")
                        st.session_state.transcription_loaded = False
                else:
                    print("🔧 DEBUG: Transcription file not found")
                    st.sidebar.error(f"❌ {config.course.course_title} transcription not found")
                    st.session_state.transcription_loaded = False
            elif st.session_state.get("transcription_loaded", False):
                print("🔧 DEBUG: Transcription already loaded")
                st.sidebar.success(f"✅ Transcription loaded ({len(st.session_state.transcription_text):,} chars)")
            
            # Load pre-processed course slides (cached)
            if not st.session_state.get("exported_images"):
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
                        st.session_state.slides_loaded = True
                        st.sidebar.success(f"✅ {len(slide_files)} slides loaded")
                    else:
                        st.sidebar.error("❌ No slide images found in slides directory")
                        st.session_state.slides_loaded = False
                else:
                    st.sidebar.error("❌ Slides directory not found")
                    st.session_state.slides_loaded = False
            elif st.session_state.get("slides_loaded", False):
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
                        st.info("Complete the Student Profile Survey first to enable explanation generation.")
                    else:
                        if DEV_MODE:
                            st.info(f"⏳ Loading course content... Missing: {', '.join(missing_items)}")
                        else:
                            st.info("⏳ Loading course content...")
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
                    if DEV_MODE:
                        st.error(f"Slide not found: {slide_path.resolve()}")
                        st.write(f"Current working directory: {Path.cwd()}")
                        st.write(f"Looking for: {slide_path}")
                    else:
                        st.error("Slide content is currently unavailable.")
                    st.stop()
                
                try:
                    # Use PIL to open and verify the image
                    img = Image.open(slide_path)
                    st.image(img, caption=str(slide_path.name), use_column_width=True)
                except Exception as e:
                    st.exception(e)
                    st.stop()

            # Video preview functionality
            video_path = UPLOAD_DIR_VIDEO / config.course.video_filename
            if video_path.exists():
                st.subheader("Lecture Recording")
                try:
                    with open(video_path, "rb") as video_file:
                        video_bytes = video_file.read()
                    st.video(video_bytes)
                    st.caption(f"{config.course.course_title} - Full Lecture")
                except Exception as e:
                    if DEV_MODE:
                        st.error(f"Error loading video: {e}")
                    else:
                        st.warning("Video content is temporarily unavailable.")
            else:
                st.info("Lecture recording will appear here when available")

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
                # Simple completion - just navigate to thank you page
                navigate_to("completion")

# ------------------------------------------------------------------------
# COMPLETION PAGE  – Thank you page with upload processing
# ------------------------------------------------------------------------
elif st.session_state.current_page == "completion":
    # Clean completion page with upload processing in background
    st.title("Interview Complete!")
    
    st.markdown(f"""
    ## {config.ui_text.completion_thanks}
    
    You have successfully completed all components of the {config.course.course_title} learning interview:
    
    ✅ **{config.ui_text.nav_profile}**  
    ✅ **{config.platform.learning_section_name}**  
    ✅ **{config.ui_text.nav_knowledge}**  
    ✅ **{config.ui_text.nav_ueq}**
    
    ---
    
    ### What happens next?
    
    Your responses are being processed and uploaded securely for research analysis. This helps us improve AI-powered learning experiences for future students.
    
    **Research Impact**: Your participation contributes to understanding how personalized AI explanations affect learning outcomes in complex scientific topics.
    
    **Data Security**: All your responses are pseudonymized and stored securely according to GDPR guidelines.
    """)
    
    # Process uploads in background (only once)
    if not st.session_state.get("completion_processed", False):
        st.session_state["completion_processed"] = True
        
        # Show processing status
        with st.spinner("Processing your responses..."):
            try:
                sm = get_session_manager()
                
                # Generate final analytics
                final_analytics_path = sm.create_final_analytics()
                
                # Upload to Supabase
                from supabase_storage import get_supabase_storage
                storage = get_supabase_storage()
                session_info = sm.get_session_info()
                session_id = session_info["session_id"]
                
                # Upload all session files
                success = storage.upload_session_files(sm, DEV_MODE)
                
                if success:
                    st.success("✅ Your responses have been successfully processed and uploaded!")
                    if DEV_MODE:
                        st.info(f"Session ID: `{session_id}`")
                else:
                    st.info("✅ Your responses have been saved locally.")
                    if DEV_MODE:
                        st.warning("⚠️ Cloud backup experienced some issues, but your data is secure.")
                
            except Exception as e:
                st.info("✅ Your responses have been saved locally.")
                if DEV_MODE:
                    st.warning(f"⚠️ Upload processing had issues: {str(e)}")
    else:
        # Already processed - show completion message
        st.success("✅ Your responses have been processed!")
        if DEV_MODE:
            session_info = sm.get_session_info()
            st.info(f"Session ID: `{session_info['session_id']}`")
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### What would you like to do?")
        
        if st.button("🔄 Start New Interview Session", use_container_width=True):
            # Reset all session state for new interview
            for key in ["profile_completed", "learning_completed", "test_completed", "ueq_completed", 
                       "completion_processed", "upload_completed", "responses", "messages", 
                       "profile_text", "profile_dict", "exported_images", "transcription_text"]:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Navigate to home
            navigate_to("home")
        
        if st.button("Return to Home Page", use_container_width=True):
            navigate_to("home")
