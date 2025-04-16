import streamlit as st
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
    {"number": 1, "left": "Annoying", "right": "Enjoyable"},
    {"number": 2, "left": "Not Understandable", "right": "Understandable"},
    {"number": 3, "left": "Creative", "right": "Dull"},
    {"number": 4, "left": "Easy to Learn", "right": "Difficult to Learn"},
    {"number": 5, "left": "Valuable", "right": "Inferior"},
    {"number": 6, "left": "Boring", "right": "Exciting"},
    {"number": 7, "left": "Not Interesting", "right": "Interesting"},
    {"number": 8, "left": "Unpredictable", "right": "Predictable"},
    {"number": 9, "left": "Fast", "right": "Slow"},
    {"number": 10, "left": "Inventive", "right": "Conventional"},
    {"number": 11, "left": "Obstructive", "right": "Supportive"},
    {"number": 12, "left": "Good", "right": "Bad"},
    {"number": 13, "left": "Complicated", "right": "Easy"},
    {"number": 14, "left": "Unlikable", "right": "Pleasing"},
    {"number": 15, "left": "Usual", "right": "Leading Edge"},
    {"number": 16, "left": "Unpleasant", "right": "Pleasant"},
    {"number": 17, "left": "Secure", "right": "Not Secure"},
    {"number": 18, "left": "Motivating", "right": "Demotivating"},
    {"number": 19, "left": "Meets Expectations", "right": "Does not meet expectations"},
    {"number": 20, "left": "Inefficient", "right": "Efficient"},
    {"number": 21, "left": "Clear", "right": "Confusing"},
    {"number": 22, "left": "Impractical", "right": "Practical"},
    {"number": 23, "left": "Organized", "right": "Cluttered"},
    {"number": 24, "left": "Attractive", "right": "Unattractive"},
    {"number": 25, "left": "Friendly", "right": "Unfriendly"},
    {"number": 26, "left": "Conservative", "right": "Innovative"}
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
    st.success("Thank you for completing the User Experience Questionnaire!")
    
    # Prepare the responses as text
    response_text = "User Experience Questionnaire Responses:\n"
    response_text += "=" * 50 + "\n\n"
    
    for q in questions:
        key = f"q{q['number']}"
        response = st.session_state.responses.get(key, {})
        value = response.get("value", "Not answered")
        response_text += f"{q['number']}. {q['left']} --- {q['right']}: {value}/7\n"
    
    # Display the responses
    st.text_area("Your Responses:", value=response_text, height=400)
    
    # Import the session manager
    from session_manager import get_session_manager
    
    # Get or create a session manager instance
    session_manager = get_session_manager()
    
    # Save the UEQ responses using the session manager
    file_path = session_manager.save_ueq_responses(response_text)
    
    # Get the session info for display
    session_info = session_manager.get_session_info()
    fake_name = session_info["fake_name"]
    
    st.success(f"Your responses have been saved with pseudonymized ID: {fake_name}")
    
    # Download button
    st.download_button(
        label="Download your responses as .txt",
        data=response_text,
        file_name="ueq_survey_responses.txt",
        mime="text/plain"    )
