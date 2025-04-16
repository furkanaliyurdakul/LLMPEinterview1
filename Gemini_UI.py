import streamlit as st
import os
import time
import whisper
import win32com.client
import pythoncom
from PIL import Image
from google import genai
import json
import re
from personalized_learning_logger import get_learning_logger

# Define directories for uploads and outputs.
UPLOAD_DIR_AUDIO = "uploads/audio"
UPLOAD_DIR_PPT = "uploads/ppt"
UPLOAD_DIR_PROFILE = "uploads/profile"
TRANSCRIPTION_DIR = "transcriptions"

# Optional: Adjust container styling.
st.markdown(
    """
    <style>
    .block-container {
        max-width: 90%;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Create directories if they don't exist.
for d in [UPLOAD_DIR_AUDIO, UPLOAD_DIR_PPT, UPLOAD_DIR_PROFILE, TRANSCRIPTION_DIR]:
    os.makedirs(d, exist_ok=True)

# Initialize persistent session state variables.
if "exported_images" not in st.session_state:
    st.session_state.exported_images = []
if "transcription_text" not in st.session_state:
    st.session_state.transcription_text = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_slide" not in st.session_state:
    st.session_state.selected_slide = "Slide 1"
if "profile_dict" not in st.session_state:
    st.session_state.profile_dict = {}

def create_summary_prompt(profile_dict, selected_slide):
    name = profile_dict.get("Name", "the student")
    proficiency = profile_dict.get("CurrentProficiency", "Unknown proficiency level")
    strongest_subject = profile_dict.get("StrongestSubject", "Unknown")
    weakest_subject = profile_dict.get("WeakestSubject", "Unknown")
    learning_strategies = ", ".join(profile_dict.get("PreferredLearningStrategies", []))
    barriers = ', '.join(profile_dict.get("PotentialBarriers", []))
    short_term_goals = "; ".join(profile_dict.get("ShortTermGoals", []))

    summary = (
        f"Generating a personalized explanation for {selected_slide} tailored specifically to {name}, "
        f"who is at a {proficiency.lower()} level.\n\n"
        f"{name}'s strongest subject is {profile_dict.get('StrongestSubject', 'N/A')}, "
        f"while they find {profile_dict.get('WeakestSubject', 'N/A')} challenging.\n"
        f"Preferred learning methods include: {', '.join(profile_dict.get('PreferredLearningStrategies', []))}.\n\n"
        f"The explanation will explicitly address potential barriers such as {barriers}, "
        f"while aligning with their short-term academic goal(s): {short_term_goals}.\n\n"
        f"Language complexity and examples will reflect their interests ({', '.join(profile_dict.get('Hobbies', []))}) "
        f"and major ({profile_dict.get('Major', 'N/A')})."
    )

    return summary


def create_structured_prompt(slide_content, transcript_text, profile_dict, selected_slide):
    prompt = {
        "Slides": {
            "content": slide_content,
            "usage_hint": f"Reference key concepts from {selected_slide} clearly."
        },
        "Transcript": {
            "content": transcript_text,
            "usage_hint": "Include relevant examples or details from lecture."
        },
        "StudentProfile": profile_dict,
        "AdaptationOptions": {
            "UseQuestioningFormat": "Interactive problem‑solving exercises and guided project-based tasks" in profile_dict.get("PreferredLearningStrategies", []),
            "ProvideStepByStep": "Detailed, step‑by‑step explanations similar to in‑depth lectures" in profile_dict["PreferredLearningStrategies"],
            "UseAnalogies": profile_dict["LearningPriorities"].get("Understanding interrelationships among various concepts", 0) >= 4,
            "IncludeRealWorldApplications": profile_dict["LearningPriorities"].get("Applying theory to real-world problems", 0) >= 4
        },
        "Instructions": {
            "TailorToStudent": True,
            "Guidelines": [
                "Adjust language complexity based on student's proficiency.",
                "Explicitly address student's weakest subject.",
                "Make explanations relevant to student's major, hobbies, or interests.",
                "Use student's preferred learning strategies.",
                "Address potential barriers explicitly to facilitate understanding.",
                "Use Markdown formatting for mathematical expressions (e.g., use ^ for superscripts, _ for subscripts) instead of HTML tags."
            ],
            "ReferenceStrategy": "Directly use Slides and Transcript to ground explanations.",
            "FormattingRequirements": {
                "UseMathMarkdown": True,
                "AvoidHtmlTags": ["<sup>", "<sub>", "<i>", "<b>"],
                "PreferredFormatting": "Markdown"
            }
        },
        "Objective": f"Provide a personalized, student-specific explanation clearly tailored for {profile_dict.get('Name', 'the student')}."
    }
    return json.dumps(prompt, indent=2)

def parse_detailed_student_profile(profile_text):
    profile = {}

    def safe_extract(pattern, default=""):
        match = re.search(pattern, profile_text, re.MULTILINE)
        return match.group(1).strip() if match else default

    # Basic Information
    profile["Name"] = safe_extract(r"1\.\s*Name:\s*(.+)")
    profile["Age"] = int(safe_extract(r"2\.\s*Age:\s*(\d+)", "0"))
    profile["StudyBackground"] = safe_extract(r"3\.\s*Study background:\s*(.+)")
    profile["Major"] = safe_extract(r"4\.\s*Major of education:\s*(.+)")
    profile["WorkExperience"] = safe_extract(r"5\.\s*Work experience:\s*(.+)")
    hobbies = safe_extract(r"6\.\s*Hobbies or interests:\s*(.+)")
    profile["Hobbies"] = [h.strip() for h in hobbies.split(",")] if hobbies else []

    # Academic Performance
    performance_section = re.search(r"7\. Academic performance ranking.*?:(.*?)(?=8\.)", profile_text, re.DOTALL)
    performance = {}
    if performance_section:
        matches = re.findall(r"[A-L]\.\s*(.+?):\s*(\d)", performance_section.group(1))
        for subject, score in matches:
            performance[subject.strip()] = int(score)
    profile["AcademicPerformance"] = performance

    profile["StrongestSubject"] = safe_extract(r"8\.\s*Strongest Subject:\s*(.+)")
    profile["WeakestSubject"] = safe_extract(r"9\.\s*Most Challenging Subject:\s*(.+)")

    # Learning Priorities
    priorities_section = re.search(r"10\. Learning priorities ranking.*?:(.*?)(?=11\.)", profile_text, re.DOTALL)
    learning_priorities = {}
    if priorities_section:
        matches = re.findall(r"[A-F]\.\s*(.+?):\s*(\d)", priorities_section.group(1))
        for priority, rating in matches:
            learning_priorities[priority.strip()] = int(rating)
    profile["LearningPriorities"] = learning_priorities

    # Preferred Learning Strategies
    strategies_text = safe_extract(r"11\. Preferred learning strategy:\s*(.+)")
    strategies = [s.strip() for s in strategies_text.split(";") if s.strip()]
    profile["PreferredLearningStrategies"] = strategies

    # Current proficiency level
    profile["CurrentProficiency"] = safe_extract(r"12\.\s*Current proficiency level:\s*(.+)")

    # Short-term academic goals
    short_term_goals = safe_extract(r"13\.\s*Short-term academic goals:\s*(.+)")
    profile["ShortTermGoals"] = [g.strip() for g in short_term_goals.split(";") if g.strip()]

    # Long-term academic/career goals
    long_term_goals = safe_extract(r"14\.\s*Long-term academic/career goals:\s*(.+)")
    profile["LongTermGoals"] = [g.strip() for g in long_term_goals.split(";") if g.strip()]

    # Potential Barriers
    barriers = safe_extract(r"15\.\s*Potential Barriers:\s*(.+)")
    profile["PotentialBarriers"] = [b.strip() for b in barriers.split(";") if b.strip()]

    return profile

def debug_log(message):
    st.session_state.setdefault("debug_logs", []).append(message)

def transcribe_audio_from_file(audio_file_path, debug_log_fn):
    model_name = "turbo"
    base_name = os.path.basename(audio_file_path)
    name, ext = os.path.splitext(base_name)
    transcription_filename = f"{model_name}_transcription_{name}.txt"
    transcription_path = os.path.join(TRANSCRIPTION_DIR, transcription_filename)
    
    if os.path.exists(transcription_path):
        debug_log_fn(f"Transcription already exists for {base_name}. Loading existing transcription.")
        with open(transcription_path, "r", encoding="utf-8") as f:
            transcription_text = f.read()
        return transcription_text

    debug_log_fn(f"Loading model: {model_name}")
    model = whisper.load_model(model_name)
    
    debug_log_fn(f"Processing {base_name} with model: {model_name}...")
    start_time = time.time()
    
    result = model.transcribe(
        audio_file_path,
        language="en",
        fp16=False,
        verbose=False,
        patience=2,
        beam_size=5,
    )
    
    end_time = time.time()
    latency = end_time - start_time
    debug_log_fn(f"Completed transcription of {base_name} in {latency:.2f} seconds.")
    
    transcription_text = result["text"]
    with open(transcription_path, "w", encoding="utf-8") as f:
        f.write(transcription_text)
    debug_log_fn(f"Transcription saved to: {transcription_path}")
    
    return transcription_text

def process_ppt_file(ppt_file_path, debug_log_fn):
    pythoncom.CoInitialize()
    
    ppt_file_path = os.path.abspath(ppt_file_path)
    debug_log_fn(f"Opening PPT file: {ppt_file_path}")
    
    ppt_app = win32com.client.Dispatch("PowerPoint.Application")
    ppt_app.Visible = True  # For debugging; set to False for production
    
    base_dir = os.path.dirname(ppt_file_path)
    picture_folder = os.path.join(base_dir, "picture")
    os.makedirs(picture_folder, exist_ok=True)
    
    try:
        presentation = ppt_app.Presentations.Open(
            ppt_file_path,
            ReadOnly=True,
            Untitled=False,
            WithWindow=False
        )
    except Exception as e:
        debug_log_fn(f"Failed to open PPT file: {e}")
        pythoncom.CoUninitialize()
        return []
    
    exported_images = []
    base_name = os.path.splitext(os.path.basename(ppt_file_path))[0]
    
    for slide in presentation.Slides:
        image_filename = f"Slide_{slide.SlideIndex} of {base_name}.png"
        image_path = os.path.join(picture_folder, image_filename)
        slide.Export(image_path, "PNG")
        exported_images.append(image_path)
        debug_log_fn(f"Exported slide {slide.SlideIndex} to {image_path}")
    
    presentation.Close()
    ppt_app.Quit()
    pythoncom.CoUninitialize()
    
    debug_log_fn(f"Total slides exported: {len(exported_images)}")
    return exported_images

# Set your API key for Google GenAI here.
my_api = "AIzaSyCdNS08cjO_lvj35Ytvs8szbUmeAdo4aIA"  # Replace with your actual API key.
client = genai.Client(api_key=my_api)

def main():
    st.title("Personalized Explanation Generator")
    
    # Load session-specific profile at startup if it exists
    if "profile_dict" not in st.session_state or not st.session_state.profile_dict:
        try:
            from session_manager import get_session_manager
            session_manager = get_session_manager()
            profile_path = os.path.join(session_manager.profile_dir, "original_profile.txt")
            
            if os.path.exists(profile_path):
                with open(profile_path, "r", encoding="utf-8") as f:
                    profile_text = f.read()
                st.session_state.profile_text = profile_text
                st.session_state.profile_dict = parse_detailed_student_profile(profile_text)
                debug_log(f"Loaded session-specific profile from {profile_path}")
        except Exception as e:
            debug_log(f"Error loading session profile: {e}")
    
    # Use the sidebar for all file inputs and related actions.
    st.sidebar.header("Input Files")
    audio_file = st.sidebar.file_uploader("Upload Audio File", type=["wav", "mp3", "ogg", "flac", "m4a", "mp4"])
    ppt_file = st.sidebar.file_uploader("Upload PPT", type=["ppt", "pptx"])
    profile_file = st.sidebar.file_uploader("Upload Student Profile (Text File)", type=["txt"])
    
    if st.checkbox("Show Debug Logs"):
        st.subheader("Debug Logs")
        for log in st.session_state.get("debug_logs", []):
            st.text(log)

    if st.checkbox("Show Parsed Profile"):
        st.json(st.session_state.profile_dict)

    # Process audio file.
    if audio_file is not None:
        audio_path = os.path.join(UPLOAD_DIR_AUDIO, audio_file.name)
        with open(audio_path, "wb") as f:
            f.write(audio_file.getbuffer())
        st.sidebar.success(f"Audio file saved as {audio_path}")
        if st.sidebar.button("Transcribe Audio"):
            st.session_state.transcription_text = transcribe_audio_from_file(audio_path, debug_log)
            st.sidebar.success("Transcription complete!")
    
    # Process PPT file.
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
    
    # Process Student Profile.
    if profile_file is not None:
        # First save the uploaded profile to the uploads directory
        profile_path = os.path.join(UPLOAD_DIR_PROFILE, profile_file.name)
        with open(profile_path, "wb") as f:
            f.write(profile_file.getbuffer())
        st.sidebar.success(f"Student Profile file saved as {profile_path}")

        # Read the uploaded profile
        with open(profile_path, "r", encoding="utf-8") as f:
            profile_text = f.read()

        # Get the session manager to access the session-specific profile
        from session_manager import get_session_manager
        session_manager = get_session_manager()
        
        # Check if a session-specific profile exists
        pseudo_file_path = os.path.join(session_manager.profile_dir, "original_profile.txt")
        
        # If session-specific profile exists, use it instead of the uploaded profile
        if os.path.exists(pseudo_file_path):
            with open(pseudo_file_path, "r", encoding="utf-8") as f:
                profile_text = f.read()
            st.sidebar.info(f"Using session-specific profile from {pseudo_file_path}")
        
        st.session_state.profile_text = profile_text
        st.session_state.profile_dict = parse_detailed_student_profile(profile_text)
    
    # If PPT processing has occurred, show slide selection in the sidebar.
    if st.session_state.exported_images:
        slide_choices = [f"Slide {i+1}" for i in range(len(st.session_state.exported_images))]
        selected_slide = st.sidebar.selectbox("Select a Slide", slide_choices, key="selected_slide")
    
    # Main area: Two columns for chat and file previews.
    col_chat, col_preview = st.columns([2, 1])
    
    with col_chat:
        st.header("LLM Chat")
        # Display conversation history as chat bubbles.
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                # Use unsafe_allow_html=True to properly render Markdown while preserving math formatting
                st.markdown(msg["content"], unsafe_allow_html=True)
        
        # Instead of a text input, we now use a submit button.
        if st.session_state.transcription_text and st.session_state.exported_images and "profile_dict" in st.session_state:
            if st.button("Submit Prompt"):
                slide_index = int(selected_slide.split(" ")[1]) - 1
                slide_content = f"Content from {selected_slide} (see slide image)."

                structured_prompt_json = create_structured_prompt(
                    slide_content,
                    st.session_state.transcription_text,
                    st.session_state.profile_dict,
                    selected_slide
                )

                # Optional: debugging structured prompt
                debug_log(structured_prompt_json)

                response = client.models.generate_content(
                    model="gemini-2.0-flash-thinking-exp-01-21",
                    contents=[
                        Image.open(st.session_state.exported_images[slide_index]),
                        structured_prompt_json
                    ]
                )

                summary_prompt = create_summary_prompt(st.session_state.profile_dict, selected_slide)
                st.session_state.messages.append({"role": "user", "content": summary_prompt})
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                # Log the interaction using the learning logger
                learning_logger = get_learning_logger()
                metadata = {
                    "slide": selected_slide,
                    "profile": st.session_state.profile_dict.get("Name", "Unknown"),
                    "session_id": learning_logger.session_manager.session_id
                }
                learning_logger.log_interaction(
                    interaction_type="personalized_explanation",
                    user_input=structured_prompt_json,
                    system_response=response.text,
                    metadata=metadata
                )
                # Make sure to save logs after each interaction
                log_file_path = learning_logger.save_logs()
                debug_log(f"Learning logs saved to: {log_file_path}")
                
                # Display a success message to the user
                st.success("Interaction logged successfully!")

        else:
            st.info("Please upload and process all files (Audio, PPT, and Student Profile) to enable prompt submission.")
            

    with col_preview:
        st.header("Preview Files")
        # Preview transcription.
        if st.session_state.transcription_text:
            st.subheader("Transcription")
            st.text_area("Transcription Output", value=st.session_state.transcription_text, height=150)
        
        # Preview selected slide.
        if st.session_state.exported_images and selected_slide:
            index = int(selected_slide.split(" ")[1]) - 1
            st.subheader("Slide Preview")
            st.image(st.session_state.exported_images[index], caption=selected_slide, use_container_width=True)
        
        # Preview student profile.
        if "profile_text" in st.session_state:
            st.subheader("Student Profile")
            st.text_area("Student Profile", value=st.session_state.profile_text, height=150)

if __name__ == "__main__":
    main()