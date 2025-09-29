import os

import streamlit as st
from session_manager import get_session_manager

session_manager = get_session_manager()

# ---- UEQ CALCULATION FUNCTION ------
def evaluate_ueq(raw: dict) -> dict:
    """Evaluate UEQ scores based on the raw responses.
    Handles the original question format and standard inversion logic.
    """
    # These are the specific questions that need to be inverted
    # Based on standard UEQ format where left side is negative for these items
    inverted_questions = [3, 4, 5, 8, 9, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 25, 26]

    # Initialize dimension totals
    attractiveness_total = 0
    perspicuity_total = 0
    efficiency_total = 0
    dependability_total = 0
    stimulation_total = 0
    novelty_total = 0

    # Process each response
    for q_key, value in raw.items():
        q_num = int(q_key[1:])  # Extract number from "q1", "q2", etc.

        # Invert score if needed (8 - value for 1-7 scale)
        if q_num in inverted_questions:
            adjusted_value = 8 - value
        else:
            adjusted_value = value

        # Assign to appropriate dimension based on UEQ structure
        if q_num in [1, 12, 14, 16, 24, 25]:  # Attractiveness
            attractiveness_total += adjusted_value
        elif q_num in [2, 4, 13, 21]:  # Perspicuity (formerly Clarity)
            perspicuity_total += adjusted_value
        elif q_num in [9, 20, 22, 23]:  # Efficiency
            efficiency_total += adjusted_value
        elif q_num in [8, 11, 17, 19]:  # Dependability
            dependability_total += adjusted_value
        elif q_num in [5, 6, 7, 18]:  # Stimulation
            stimulation_total += adjusted_value
        elif q_num in [3, 10, 15, 26]:  # Novelty
            novelty_total += adjusted_value

    # Calculate averages (each dimension has different number of items)
    dimensions = {
        "Attractiveness": attractiveness_total / 6,
        "Perspicuity": perspicuity_total / 4, 
        "Efficiency": efficiency_total / 4,
        "Dependability": dependability_total / 4,
        "Stimulation": stimulation_total / 4,
        "Novelty": novelty_total / 4,
    }

    return dimensions

st.title("User Experience Questionnaire")

st.markdown(
    """
This questionnaire helps us evaluate your experience with the platform. For each item, please select a point on the scale that best represents your impression.

Please decide spontaneously. Don't think too long about your decision to make sure that you convey your original impression.

Sometimes you may not be completely sure about your agreement with a particular attribute or you may find that the attribute does not apply completely to the particular product.

Nevertheless, please tick a circle in every line. It is your personal opinion that counts.

Please remember: there is no wrong or right answer!
"""
)

# Dictionary to store responses
if "responses" not in st.session_state:
    st.session_state.responses = {}

# CSS for styling
st.markdown(
    """
<style>
.question-container {
    margin-bottom: 20px;
    padding: 10px;
    border-left: 3px solid #0E4B99;
    background-color: #f0f2f6;
}
.question-divider {
    margin: 10px 0;
    border-bottom: 1px solid #e0e0e0;
}
</style>
""",
    unsafe_allow_html=True,
)

# The 26 question pairs from the actual UEQ
questions = [
    {"number": 1, "left": "annoying", "right": "enjoyable"},
    {"number": 2, "left": "not understandable", "right": "understandable"},
    {"number": 3, "left": "creative", "right": "dull"},
    {"number": 4, "left": "easy to learn", "right": "difficult to learn"},
    {"number": 5, "left": "valuable", "right": "inferior"},
    {"number": 6, "left": "boring", "right": "exciting"},
    {"number": 7, "left": "not interesting", "right": "interesting"},
    {"number": 8, "left": "unpredictable", "right": "predictable"},
    {"number": 9, "left": "fast", "right": "slow"},
    {"number": 10, "left": "inventive", "right": "conventional"},
    {"number": 11, "left": "obstructive", "right": "supportive"},
    {"number": 12, "left": "good", "right": "bad"},
    {"number": 13, "left": "complicated", "right": "easy"},
    {"number": 14, "left": "unlikable", "right": "pleasing"},
    {"number": 15, "left": "usual", "right": "leading edge"},
    {"number": 16, "left": "unpleasant", "right": "pleasant"},
    {"number": 17, "left": "secure", "right": "not secure"},
    {"number": 18, "left": "motivating", "right": "demotivating"},
    {"number": 19, "left": "meets expectations", "right": "does not meet expectations"},
    {"number": 20, "left": "inefficient", "right": "efficient"},
    {"number": 21, "left": "clear", "right": "confusing"},
    {"number": 22, "left": "impractical", "right": "practical"},
    {"number": 23, "left": "organized", "right": "cluttered"},
    {"number": 24, "left": "attractive", "right": "unattractive"},
    {"number": 25, "left": "friendly", "right": "unfriendly"},
    {"number": 26, "left": "conservative", "right": "innovative"},
]

# Display each question with improved layout
for q in questions:
    # Create three columns for better layout
    col_left, col_scale, col_right = st.columns([1, 3, 1])

    with col_left:
        st.markdown(
            f"<div style='text-align: right;'>{q['left']}</div>",
            unsafe_allow_html=True,
        )

    with col_scale:
        # Create the radio buttons
        key = f"q{q['number']}"
        selected_value = st.radio(
            f"Select a value for question {q['number']}",
            options=list(range(1, 8)),
            horizontal=True,
            key=key,
            label_visibility="collapsed",
            index=None,
        )

    with col_right:
        st.markdown(
            f"<div style='text-align: left;'>{q['right']}</div>", unsafe_allow_html=True
        )

    # Store the response
    st.session_state.responses[key] = {
        "question": f"{q['left']} --- {q['right']}",
        "value": selected_value,
    }

    # Add a subtle divider between questions
    st.markdown("<div class='question-divider'></div>", unsafe_allow_html=True)

# Submit button
if st.button("Submit Responses"):
    # list any questions without a value
    missing = [
        str(q["number"])
        for q in questions
        if st.session_state.responses[f"q{q['number']}"]["value"] is None
    ]

    if missing:
        st.error(
            "Please give a score (1 – 7) for every statement "
            f"before sending the survey. Missing: {', '.join(missing)}"
        )
        st.stop()  # abort the rest of the submit logic

    # --- all items answered: continue as before ---------------------
    st.success("Thank you for completing the User Experience Questionnaire!")

    answers_dict = {
        key: entry["value"]  # 1‑7 scale value
        for key, entry in st.session_state.responses.items()
    }

    response_text = "User Experience Questionnaire Responses:\n"
    response_text += "=" * 50 + "\n\n"

    for q in questions:
        key = f"q{q['number']}"
        value = st.session_state.responses[key]["value"]
        response_text += f"{q['number']}. {q['left']} --- {q['right']}: {value}/7\n"

    # Display the responses
    st.text_area("Your Responses:", value=response_text, height=400)

    # Import the session manager
    from session_manager import get_session_manager

    # Get or create a session manager instance
    session_manager = get_session_manager()

    bench = evaluate_ueq(answers_dict)

    txt_path = session_manager.save_ueq(
        answers=answers_dict,
        benchmark=bench,
        free_text=st.session_state.get("saved_comment"),  # ← not "extra_comment"
    )

    # Get the session info for display
    session_info = session_manager.get_session_info()
    fake_name = session_info["fake_name"]

    st.success(f"Your responses have been saved with pseudonymized ID: {fake_name}")

st.markdown("#### Extra comment")
# --- comment widget -----------------------------------------
comment_txt = st.text_area(
    "Anything else you would like to share?",
    placeholder="Feel free to note technical issues, UI feedback, ideas, specific notes, etc.",
    key="extra_comment",
    height=120,
)

# --- save comment widget -----------------------------------
if st.button("Save comment", key="save_extra_comment"):
    if comment_txt.strip():
        st.session_state["saved_comment"] = comment_txt.strip()
        st.success("Your comment has been saved!")
    else:
        st.warning("Please enter a comment before saving.")