import streamlit as st
from google.genai.types import Content, Part
import google.generativeai as genai
from PIL import Image
import os

FAST_TEST_MODE = True  # Set to True to enable fast testing mode

# Set page configuration
st.set_page_config(page_title="Personalized Learning Platform", layout="wide")

# -------------------------------------------------
# chat state (put right after your other initialisers)
# -------------------------------------------------
if "chat_history" not in st.session_state:
    # store ready‑to‑send Content objects here
    st.session_state.chat_history = []          # google.genai.types.Content
if "latest_user_chat" not in st.session_state:  # helper for the input box
    st.session_state.latest_user_chat = ""


# Initialize session state variables
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

# Initialize completion tracking variables
if "profile_completed" not in st.session_state:
    st.session_state.profile_completed = False
if "learning_completed" not in st.session_state:
    st.session_state.learning_completed = False
if "test_completed" not in st.session_state:
    st.session_state.test_completed = False
if "ueq_completed" not in st.session_state:
    st.session_state.ueq_completed = False

if FAST_TEST_MODE:
    st.session_state.exported_images = ["uploads/ppt/picture/Slide_1 of Lecture8.png"]
    st.session_state.transcription_text = "This is a mock transcription for fast testing."
    st.session_state.profile_dict = {
        "Name": "Test User",
        "CurrentProficiency": "Intermediate",
        "StrongestSubject": "Mathematics",
        "WeakestSubject": "Physics",
        "PreferredLearningStrategies": ["Detailed, step‑by‑step explanations similar to in‑depth lectures"],
        "PotentialBarriers": ["Lack of prior knowledge"],
        "ShortTermGoals": ["Understand core concepts"],
        "Hobbies": ["Chess", "Reading"],
        "Major": "Engineering",
        "LearningPriorities": {"Understanding interrelationships among various concepts": 5, "Applying theory to real-world problems": 5}
    }
    st.session_state.selected_slide = "Slide 1"

def dict_to_content(d: dict) -> Content:
    """{"role": "...", "content": "..."} → Content(role, parts[Part(text)])"""
    return Content(role=d["role"], parts=[Part.from_text(text = d["content"])])

# Function to navigate between pages with restrictions
def navigate_to(page):
    # Apply navigation restrictions based on completion status
    if page == "profile_survey":
        # Always allow access to profile survey
        st.session_state.current_page = page
    elif page == "personalized_learning":
        # Only allow if profile is completed
        if st.session_state.profile_completed:
            st.session_state.current_page = page
        else:
            st.warning("Please complete the Student Profile Survey first.")
    elif page == "knowledge_test":
        # Only allow if profile and learning are completed
        if st.session_state.profile_completed and st.session_state.learning_completed:
            st.session_state.current_page = page
        else:
            st.warning("Please complete the Student Profile Survey and explore the Personalized Learning content first.")
    elif page == "ueq_survey":
        # Only allow if profile, learning, and test are completed
        if st.session_state.profile_completed and st.session_state.learning_completed and st.session_state.test_completed:
            st.session_state.current_page = page
        else:
            st.warning("Please complete all previous components before accessing the User Experience Survey.")
    elif page == "home":
        # Always allow access to home
        st.session_state.current_page = page

    st.rerun()

# Sidebar navigation with visual indicators of completion status
st.sidebar.title("Navigation")

# Home button
if st.sidebar.button("🏠 Home"):
    navigate_to("home")
    st.rerun()

# Profile Survey button with completion indicator
profile_status = "✅" if st.session_state.profile_completed else "⬜"
if st.sidebar.button(f"{profile_status} Student Profile Survey"):
    navigate_to("profile_survey")
    st.rerun()

# Personalized Learning button with completion indicator
learning_status = "✅" if st.session_state.learning_completed else "⬜"
if st.sidebar.button(f"{learning_status} Personalized Learning"):
    navigate_to("personalized_learning")
    st.rerun()

# Knowledge Test button with completion indicator
test_status = "✅" if st.session_state.test_completed else "⬜"
if st.sidebar.button(f"{test_status} Knowledge Test"):
    navigate_to("knowledge_test")
    st.rerun()

# UEQ Survey button with completion indicator
ueq_status = "✅" if st.session_state.ueq_completed else "⬜"
if st.sidebar.button(f"{ueq_status} User Experience Survey"):
    navigate_to("ueq_survey")
    st.rerun()

# Main content area
if st.session_state.current_page == "home":
    st.title("🎓 Personalized Learning Platform")
    
    st.markdown("""
    ## Welcome to the Personalized Learning Platform
    
    This platform is designed to provide personalized learning experiences based on your profile, 
    knowledge level, and learning preferences. The platform consists of the following components:
    
    1. **Student Profile Survey** - Collects information about your academic background, learning preferences, and goals
    2. **Personalized Learning** - Provides customized explanations based on your profile and knowledge level
    3. **Knowledge Test** - Assesses your understanding of the subject matter after learning
    4. **User Experience Survey** - Gathers feedback about your experience with the platform
    
    Please follow the components in the order listed above for the best experience.
    
    ### Getting Started
    
    Click the button below to start with the Student Profile Survey.
    """)
    
    # Fast Test Mode toggle button (Dev Only)
    if st.button("Enable Fast Test Mode (Dev Only)"):
        st.session_state["fast_test_mode"] = True
        st.rerun()
    
    # Quick navigation button to start the process
    if st.button("Start with Student Profile Survey", use_container_width=True):
        navigate_to("profile_survey")
        st.rerun()

elif st.session_state.current_page == "profile_survey":
    # Import and run the profile survey code with forced reload to prevent caching issues
    import importlib
    import testui_profilesurvey
    importlib.reload(testui_profilesurvey)
    
    # Add diagnostic output to verify the module is loading
    st.sidebar.success("Profile survey module loaded successfully")
    
    # Check if the review section is shown (indicating form submission)
    if st.session_state.get("show_review", False):
        # Mark profile as completed when review section is shown
        # This ensures the flag is set regardless of whether profile_text needs to be recreated
        st.session_state.profile_completed = True
        
        # Create a formatted profile text for saving if not already created
        # This prevents recreating the profile text on every rerun
        if "profile_text" not in st.session_state or st.session_state.get("profile_text", "") == "":
            # Format the responses into a structured text file
            name = st.session_state.get("name", "")
            age = st.session_state.get("age", "")
            education_level = st.session_state.get("education_level", "")
            major = st.session_state.get("major", "")
            work_exp = st.session_state.get("work_exp", "")
            hobbies = st.session_state.get("hobbies", "")
            strongest_subject = st.session_state.get("strongest_subject", "")
            challenging_subject = st.session_state.get("challenging_subject", "")
            proficiency_level = st.session_state.get("proficiency_level", "")
            
            # Get ratings
            ratings = {}
            for subject in testui_profilesurvey.subjects:
                ratings[subject] = st.session_state.get(f"{subject}", None)
            
            # Get priority ratings
            priority_ratings = {}
            for priority in testui_profilesurvey.learning_priorities:
                priority_ratings[priority] = st.session_state.get(f"{priority}", None)
            
            # Get selected strategies
            selected_strategies = []
            for strategy in testui_profilesurvey.learning_strategies:
                if st.session_state.get(strategy, False):
                    selected_strategies.append(strategy)
            
            # Get selected short-term goals
            selected_short_goals = []
            for goal in testui_profilesurvey.short_term_goals:
                if st.session_state.get(f"short_{goal}", False):
                    selected_short_goals.append(goal)
            
            # Get selected long-term goals
            selected_long_goals = []
            for goal in testui_profilesurvey.long_term_goals:
                if st.session_state.get(f"long_{goal}", False):
                    selected_long_goals.append(goal)
            
            # Get selected barriers
            selected_barriers = []
            for barrier in testui_profilesurvey.barriers:
                if st.session_state.get(f"barrier_{barrier}", False):
                    selected_barriers.append(barrier)
            
            # Create the formatted profile text
            profile_text = f"""Student Profile Survey Responses:
====================================

Section 1: Academic and Background Information
---------------------------------------------
1. Name: {name}
2. Age: {age}
3. Study background: {education_level}
4. Major of education: {major}
5. Work experience: {work_exp}
6. Hobbies or interests: {hobbies}

7. Academic performance ranking (1=Weakest, 5=Strongest):
"""
            
            # Add subject ratings
            for i, (subject, rating) in enumerate(ratings.items()):
                letter = chr(65 + i)  # A, B, C, etc.
                profile_text += f"   {letter}. {subject}: {rating}\n"
            
            profile_text += f"\n8. Strongest Subject: {strongest_subject}\n"
            profile_text += f"9. Most Challenging Subject: {challenging_subject}\n\n"
            
            profile_text += "10. Learning priorities ranking (1=least important, 5=most important):\n"
            
            # Add priority ratings
            for i, (priority, rating) in enumerate(priority_ratings.items()):
                letter = chr(65 + i)  # A, B, C, etc.
                profile_text += f"   {letter}. {priority}: {rating}\n"
            
            profile_text += f"\n11. Preferred learning strategy: {'; '.join(selected_strategies)}\n"
            profile_text += f"12. Current proficiency level: {proficiency_level}\n"
            profile_text += f"13. Short-term academic goals: {'; '.join(selected_short_goals)}\n"
            profile_text += f"14. Long-term academic/career goals: {'; '.join(selected_long_goals)}\n"
            profile_text += f"15. Potential Barriers: {'; '.join(selected_barriers)}\n"
            
            # Save the profile text to session state
            st.session_state.profile_text = profile_text
            
            # Save the profile to a file in the uploads/profile directory
            from Gemini_UI import UPLOAD_DIR_PROFILE
            os.makedirs(UPLOAD_DIR_PROFILE, exist_ok=True)
            profile_path = os.path.join(UPLOAD_DIR_PROFILE, f"{name.replace(' ', '_')}_profile.txt")
            with open(profile_path, "w", encoding="utf-8") as f:
                f.write(profile_text)
            
            # Parse the profile text into a dictionary for later use
            from Gemini_UI import parse_detailed_student_profile
            st.session_state.profile_dict = parse_detailed_student_profile(profile_text)
        
        # Show a success message and next steps
        st.success("Profile saved successfully! You can now proceed to the Personalized Learning section.")
        
        # Add navigation button to the next step
        if st.button("Continue to Personalized Learning", use_container_width=True):
            navigate_to("personalized_learning")
            st.rerun()

elif st.session_state.current_page == "personalized_learning":
    # Check if profile is completed
    if not st.session_state.profile_completed:
        st.warning("Please complete the Student Profile Survey first.")
        if st.button("Go to Student Profile Survey"):
            navigate_to("profile_survey")
    else:
        # Modified approach to load Gemini_UI
        st.title("Personalized Explanation Generator")
        st.markdown("""This component allows you to generate personalized explanations based on your profile, 
        uploaded slides, and lecture audio. Please use the sidebar to upload the necessary files.""")
        
        # Import necessary components from Gemini_UI without running the main function
        from Gemini_UI import (
            create_summary_prompt, create_structured_prompt, parse_detailed_student_profile,
            debug_log, transcribe_audio_from_file, process_ppt_file,
            UPLOAD_DIR_AUDIO, UPLOAD_DIR_PPT, UPLOAD_DIR_PROFILE, TRANSCRIPTION_DIR
        )

        my_api = "AIzaSyCdNS08cjO_lvj35Ytvs8szbUmeAdo4aIA"  # Replace with your actual API key.
        genai.configure(api_key=my_api)

        if "gemini_chat" not in st.session_state:
            model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")
            st.session_state.gemini_chat = model.start_chat(history=[])
        chat = st.session_state.gemini_chat    # convenience handle
        
        # Create directories if they don't exist
        for d in [UPLOAD_DIR_AUDIO, UPLOAD_DIR_PPT, UPLOAD_DIR_PROFILE, TRANSCRIPTION_DIR]:
            os.makedirs(d, exist_ok=True)
        
        # Initialize session state variables if not already present
        if "exported_images" not in st.session_state:
            st.session_state.exported_images = []
        if "transcription_text" not in st.session_state:
            st.session_state.transcription_text = ""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "selected_slide" not in st.session_state:
            st.session_state.selected_slide = "Slide 1"
        
        # Use the sidebar for all file inputs and related actions
        st.sidebar.header("Input Files")
        audio_file = st.sidebar.file_uploader("Upload Audio File", type=["wav", "mp3", "ogg", "flac", "m4a", "mp4"])
        ppt_file = st.sidebar.file_uploader("Upload PPT", type=["ppt", "pptx"])
        
        # Display profile information (already loaded from profile survey)
        st.sidebar.success("✅ Profile already loaded from your survey responses")
        
        if st.checkbox("Show Debug Logs"):
            st.subheader("Debug Logs")
            for log in st.session_state.get("debug_logs", []):
                st.text(log)

        if st.checkbox("Show Parsed Profile") and "profile_dict" in st.session_state:
            st.json(st.session_state.profile_dict)

        # Process audio file
        if audio_file is not None:
            audio_path = os.path.join(UPLOAD_DIR_AUDIO, audio_file.name)
            with open(audio_path, "wb") as f:
                f.write(audio_file.getbuffer())
            st.sidebar.success(f"Audio file saved as {audio_path}")
            if st.sidebar.button("Transcribe Audio"):
                st.session_state.transcription_text = transcribe_audio_from_file(audio_path, debug_log)
                st.sidebar.success("Transcription complete!")
        
        # Process PPT file
        if ppt_file is not None:
            ppt_path = os.path.join(UPLOAD_DIR_PPT, ppt_file.name)
            with open(ppt_path, "wb") as f:
                f.write(ppt_file.getbuffer())
            st.sidebar.success(f"PPT file saved as {ppt_path}")
            if st.sidebar.button("Process PPT"):
                exported_images = process_ppt_file(ppt_path, debug_log)
                if exported_images:
                    st.sidebar.success(f"Exported {len(exported_images)} slides.")
                    st.session_state.exported_images = exported_images
                else:
                    st.sidebar.error("No slides were exported.")
        
        # If PPT processing has occurred, show slide selection in the sidebar
        if st.session_state.exported_images:
            slide_choices = [f"Slide {i+1}" for i in range(len(st.session_state.exported_images))]
            selected_slide = st.sidebar.selectbox("Select a Slide", slide_choices, key="selected_slide")
        
        # Main area: Two columns for chat and file previews
        col_chat, col_preview = st.columns([2, 1])
        
        with col_chat:
            st.header("LLM Chat")
            # Display conversation history as chat bubbles
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            user_chat = st.chat_input("Ask a follow‑up…")

            if user_chat:
                # Gemini:
                reply = chat.send_message(user_chat)      # ↩ returns a response object

                # Streamlit display:
                st.session_state.messages.extend([
                    {"role": "user",      "content": user_chat},
                    {"role": "assistant", "content": reply.text},
                ])
                st.rerun()


            # Instead of a text input, we now use a submit button
            if st.session_state.transcription_text and st.session_state.exported_images and "profile_dict" in st.session_state:
                if st.button("Submit Prompt"):
                    slide_idx  = int(selected_slide.split()[1]) - 1
                    img_obj    = Image.open(st.session_state.exported_images[slide_idx])

                    structured_prompt = create_structured_prompt(
                        f"Content from {selected_slide} (see slide image).",
                        st.session_state.transcription_text,
                        st.session_state.profile_dict,
                        selected_slide
                    )
                    debug_log(structured_prompt)

                    # -------- Gemini call (multimodal, retains history) -------------------
                    reply = chat.send_message([img_obj, structured_prompt])
                    #  ↑ we pass a *list* with raw PIL.Image + plain string → SDK coerces them

                    # -------- Streamlit display & bookkeeping -----------------------------
                    summary_prompt = create_summary_prompt(st.session_state.profile_dict,
                                                        selected_slide)
                    st.session_state.messages.extend([
                        {"role": "user",      "content": summary_prompt},
                        {"role": "assistant", "content": reply.text},
                    ])
                    st.session_state.learning_completed = True
                    
                    # Log the interaction using the learning logger
                    from personalized_learning_logger import get_learning_logger
                    learning_logger = get_learning_logger()
                    metadata = {
                        "slide": selected_slide,
                        "profile": st.session_state.profile_dict.get("Name", "Unknown"),
                        "session_id": learning_logger.session_manager.session_id
                    }
                    learning_logger.log_interaction(
                        interaction_type="personalized_explanation",
                        user_input=structured_prompt,
                        system_response=reply.text,
                        metadata=metadata
                    )
                    # Make sure to save logs after each interaction
                    log_file_path = learning_logger.save_logs()
                    debug_log(f"Learning logs saved to: {log_file_path}")
                    
                    # Mark learning as completed after generating at least one explanation
                    st.session_state.learning_completed = True

                    st.rerun()

            else:
                st.info("Please upload and process all files (Audio and PPT) to enable prompt submission.")
                

        with col_preview:
            st.header("Preview Files")
            # Preview transcription
            if st.session_state.transcription_text:
                st.subheader("Transcription")
                st.text_area("Transcription Output", value=st.session_state.transcription_text, height=150)
            
            # Preview selected slide
            if st.session_state.exported_images and selected_slide:
                index = int(selected_slide.split(" ")[1]) - 1
                st.subheader("Slide Preview")
                st.image(st.session_state.exported_images[index], caption=selected_slide, use_container_width=True)
            
            # Preview student profile
            if "profile_text" in st.session_state:
                st.subheader("Student Profile")
                st.text_area("Student Profile", value=st.session_state.profile_text, height=150)
        
        # Add navigation buttons at the bottom
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Previous: Student Profile"):
                navigate_to("profile_survey")
        with col2:
            # Only enable the next button if learning is completed
            next_disabled = not st.session_state.learning_completed
            if next_disabled:
                st.button("Next: Knowledge Test", disabled=True)
                st.info("Please generate at least one explanation before proceeding to the Knowledge Test.")
            else:
                if st.button("Next: Knowledge Test"):
                    navigate_to("knowledge_test")

elif st.session_state.current_page == "knowledge_test":
    import importlib
    import testui_knowledgetest
    importlib.reload(testui_knowledgetest)
    # Check if profile and learning are completed
    if not st.session_state.profile_completed:
        st.warning("Please complete the Student Profile Survey first.")
        if st.button("Go to Student Profile Survey"):
            navigate_to("profile_survey")
    elif not st.session_state.learning_completed:
        st.warning("Please complete the Personalized Learning section first.")
        if st.button("Go to Personalized Learning"):
            navigate_to("personalized_learning")
    else:
        # Import and run the knowledge test code
        import testui_knowledgetest
        
        # Check if the test has been submitted (score calculated)
        if "score" in st.session_state:
            # Mark test as completed
            st.session_state.test_completed = True
        
        # Add navigation buttons at the bottom
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Previous: Personalized Learning"):
                navigate_to("personalized_learning")
        with col2:
            # Only enable the next button if test is completed
            next_disabled = not st.session_state.test_completed
            if next_disabled:
                st.button("Next: User Experience Survey", disabled=True)
                st.info("Please complete the Knowledge Test before proceeding to the User Experience Survey.")
            else:
                if st.button("Next: User Experience Survey"):
                    navigate_to("ueq_survey")

elif st.session_state.current_page == "ueq_survey":
    import importlib
    import testui_ueqsurvey
    importlib.reload(testui_ueqsurvey)
    # Check if all previous components are completed
    if not st.session_state.profile_completed:
        st.warning("Please complete the Student Profile Survey first.")
        if st.button("Go to Student Profile Survey"):
            navigate_to("profile_survey")
    elif not st.session_state.learning_completed:
        st.warning("Please complete the Personalized Learning section first.")
        if st.button("Go to Personalized Learning"):
            navigate_to("personalized_learning")
    elif not st.session_state.test_completed:
        st.warning("Please complete the Knowledge Test first.")
        if st.button("Go to Knowledge Test"):
            navigate_to("knowledge_test")
    else:
        # Import and run the UEQ survey code
        import testui_ueqsurvey
        
        # Check if the UEQ has been submitted
        if st.session_state.get("responses", {}) and any("value" in response and response["value"] is not None for response in st.session_state.responses.values()):
            # Mark UEQ as completed
            st.session_state.ueq_completed = True
        
        # Add navigation buttons at the bottom
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Previous: Knowledge Test"):
                navigate_to("knowledge_test")
        with col2:
            if st.button("Finish"):
                navigate_to("home")
                st.success("Thank you for completing all components of the platform!")