import streamlit as st
import os

from session_manager import get_session_manager
session_manager = get_session_manager()

st.title("User Experience Questionnaire")

st.markdown("""
This questionnaire helps evaluate your experience with the tool. For each item, please select a point on the scale that best represents your impression.

Please decide spontaneously. Don't think too long about your decision to make sure that you convey your original impression.

Sometimes you may not be completely sure about your agreement with a particular attribute or you may find that the attribute does not apply completely to the particular product.

Nevertheless, please tick a circle in every line. It is your personal opinion that counts.

Please remember: there is no wrong or right answer!
""")

# Dictionary to store responses
if "responses" not in st.session_state:
    st.session_state.responses = {}

# UEQ Questions - each with a 7-point scale
questions = [
    {"number": 1,  "left": "Annoying",           "right": "Enjoyable"},
    {"number": 2,  "left": "Not Understandable", "right": "Understandable"},
    {"number": 3,  "left": "Dull",               "right": "Creative"},
    {"number": 4,  "left": "Difficult to Learn", "right": "Easy to Learn"},
    {"number": 5,  "left": "Inferior",           "right": "Valuable"},
    {"number": 6,  "left": "Boring",             "right": "Exciting"},
    {"number": 7,  "left": "Not Interesting",    "right": "Interesting"},
    {"number": 8,  "left": "Unpredictable",      "right": "Predictable"},
    {"number": 9,  "left": "Slow",               "right": "Fast"},
    {"number": 10, "left": "Conventional",       "right": "Inventive"},
    {"number": 11, "left": "Obstructive",        "right": "Supportive"},
    {"number": 12, "left": "Bad",                "right": "Good"},
    {"number": 13, "left": "Complicated",        "right": "Easy"},
    {"number": 14, "left": "Unlikable",          "right": "Pleasing"},
    {"number": 15, "left": "Usual",              "right": "Leading Edge"},
    {"number": 16, "left": "Unpleasant",         "right": "Pleasant"},
    {"number": 17, "left": "Not Secure",         "right": "Secure"},
    {"number": 18, "left": "Demotivating",       "right": "Motivating"},
    {"number": 19, "left": "Does not meet expectations", "right": "Meets Expectations"},
    {"number": 20, "left": "Inefficient",        "right": "Efficient"},
    {"number": 21, "left": "Confusing",          "right": "Clear"},
    {"number": 22, "left": "Impractical",        "right": "Practical"},
    {"number": 23, "left": "Cluttered",          "right": "Organized"},
    {"number": 24, "left": "Unattractive",       "right": "Attractive"},
    {"number": 25, "left": "Unfriendly",         "right": "Friendly"},
    {"number": 26, "left": "Conservative",       "right": "Innovative"}
]

# Custom CSS to improve the layout
st.markdown("""
<style>
    .scale-container {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    .scale-label {
        width: 150px;
        text-align: right;
        padding-right: 10px;
        font-weight: bold;
    }
    .scale-label-right {
        width: 150px;
        text-align: left;
        padding-left: 10px;
        font-weight: bold;
    }
    .scale-numbers {
        display: flex;
        justify-content: space-between;
        width: 100%;
        max-width: 350px;
        margin: 0 10px;
    }
    .scale-number {
        text-align: center;
        width: 30px;
    }
    .stRadio > div {
        display: flex;
        justify-content: space-between;
        max-width: 350px;
    }
    .stRadio > div > label {
        margin: 0 !important;
        padding: 0 !important;
    }
    .question-divider {
        margin: 10px 0;
        border-bottom: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# Display each question with a 7-point scale
for q in questions:
    st.markdown(f"**{q['number']}.**")
    
    # Create a row for the scale labels and radio buttons
    col_left, col_scale, col_right = st.columns([2, 6, 2])
    
    with col_left:
        st.markdown(f"<div style='text-align: right;'>{q['left']}</div>", unsafe_allow_html=True)
    
    with col_scale:
        # Remove the custom number display since radio buttons already show numbers
        
        # Create the radio buttons
        key = f"q{q['number']}"
        selected_value = st.radio(
            f"Select a value for question {q['number']}",
            options=list(range(1, 8)),
            horizontal=True,
            key=key,
            label_visibility="collapsed",
            index=None
        )
    
    with col_right:
        st.markdown(f"<div style='text-align: left;'>{q['right']}</div>", unsafe_allow_html=True)
    
    # Store the response
    st.session_state.responses[key] = {
        "question": f"{q['left']} --- {q['right']}",
        "value": selected_value
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
        st.stop()          # abort the rest of the submit logic

    # --- all items answered: continue as before ---------------------
    st.success("Thank you for completing the User Experience Questionnaire!")

    answers_dict = {
    key: entry["value"]          # 1‑7 scale value
    for key, entry in st.session_state.responses.items()
    }

    response_text = "User Experience Questionnaire Responses:\n"
    response_text += "=" * 50 + "\n\n"

    for q in questions:
        key   = f"q{q['number']}"
        value = st.session_state.responses[key]["value"]
        response_text += (
            f"{q['number']}. {q['left']} --- {q['right']}: {value}/7\n"
        )
    
    # Display the responses
    st.text_area("Your Responses:", value=response_text, height=400)
    
    # Import the session manager
    from session_manager import get_session_manager
    
    # Get or create a session manager instance
    session_manager = get_session_manager()
    
    bench = evaluate_ueq(answers_dict)

    txt_path = session_manager.save_ueq(
        answers   = answers_dict,
        benchmark = bench,
        free_text = st.session_state.get("saved_comment")   # ← not “extra_comment”
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

# --- save button --------------------------------------------
if st.button("Save comment"):
    st.session_state["saved_comment"] = comment_txt.strip()

    if st.session_state["saved_comment"]:
        # keep one copy for later use in save_ueq()
        session_manager.save_ueq(
        answers   = answers_dict,
        benchmark = bench,
        free_text = st.session_state.get("saved_comment")   # ← not “extra_comment”
    )

        st.success("Comment saved")
    else:
        st.warning("Please enter a comment before saving.")

# helper ------------------------------------------------------
def show_ueq_benchmark(responses: dict) -> None:
    """Convert radio answers (1‑7) to –3…+3, compute the six
    UEQ scale means, compare with the public benchmark, and
    print a short table."""
    
    def to_interval(v: int) -> int:
        return v - 4                       # 1→‑3 … 7→+3

    SCALES = {
        "Attractiveness": [1, 6, 7,16,24,25],
        "Perspicuity"   : [2, 4, 8,13,21,23],
        "Task ease"     : [9,20,26],            # three items in short UEQ
        "Dependability" : [3,11,17,22],
        "Stimulation"   : [5,18,19],
        "Novelty"       : [10,12,14,15],
    }

    BENCHMARK = {
        "Attractiveness": (1.50, 0.85),
        "Perspicuity"   : (1.45, 0.83),
        "Task ease"     : (1.38, 0.79),
        "Dependability" : (1.25, 0.86),
        "Stimulation"   : (1.17, 0.96),
        "Novelty"       : (0.78, 0.96),
    }

    # mean per scale
    scale_scores = {}
    for scale, q_nums in SCALES.items():
        vals = [to_interval(responses[f"q{n}"]["value"]) for n in q_nums]
        scale_scores[scale] = sum(vals) / len(vals)

    # grade vs benchmark: ±0.5 sd bands
    def grade(x, m, sd):
        if x >= m + 0.5*sd: return "excellent"
        if x >= m        : return "good"
        if x >= m - 0.5*sd: return "okay"
        return "weak"

    rows = []
    for scale, score in scale_scores.items():
        m, sd = BENCHMARK[scale]
        rows.append(f"- **{scale}**: {score:+.2f} ({grade(score, m, sd)})")

    st.markdown("### UEQ benchmark")
    st.markdown("\n".join(rows))
# ------------------------------------------------------------


def evaluate_ueq(raw: dict) -> dict:
    """Return {"means": {...}, "grades": {...}}."""
    def to_interval(v): return v - 4
    SCALES = {
        "Attractiveness": [1, 6, 7,16,24,25],
        "Perspicuity"   : [2, 4, 8,13,21,23],
        "Efficiency"     : [9,20,26],            # three items in short UEQ
        "Dependability" : [3,11,17,22],
        "Stimulation"   : [5,18,19],
        "Novelty"       : [10,12,14,15],
    }      
    BENCH  = {
        "Attractiveness": (1.50, 0.85),
        "Perspicuity"   : (1.45, 0.83),
        "Efficiency"     : (1.38, 0.79),
        "Dependability" : (1.25, 0.86),
        "Stimulation"   : (1.17, 0.96),
        "Novelty"       : (0.78, 0.96),
    }        # same stats

    means, grades = {}, {}
    for scale, q_nums in SCALES.items():
        vals  = [to_interval(raw[f"q{n}"]) for n in q_nums]
        mean  = sum(vals) / len(vals)
        means[scale] = mean

        m, sd = BENCH[scale]
        if mean >= m + 0.5*sd: grade = "excellent"
        elif mean >= m:        grade = "good"
        elif mean >= m - 0.5*sd: grade = "okay"
        else:                  grade = "weak"
        grades[scale] = grade
    return {"means": means, "grades": grades}