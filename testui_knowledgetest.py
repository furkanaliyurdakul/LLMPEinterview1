import streamlit as st
import os
import datetime
st.title("📧 Knowledge Test - AI Techniques for Detecting Email Threats")

st.markdown("""
Welcome to the knowledge assessment on machine learning concepts and email threat detection. This brief test is designed to evaluate your understanding of key concepts in this domain through a mix of single and multiple-choice questions.

The assessment consists of 5 questions that cover both theoretical understanding and practical applications. You'll receive immediate feedback on your performance, with a fair scoring system that considers both your correct and incorrect selections. Feel free to trust your intuition - your spontaneous responses often best reflect your true understanding.

At the end of the test, you'll be able to see your score and download your results for future reference. Remember, this is a learning opportunity to help you gauge your knowledge in this field.

Ready to begin? Let's explore your understanding together!
""")

# Question 1 - Changed to radio button for single selection
st.markdown("**1. What is a fundamental distinction between a perceptron and a support vector machine in the context of supervised learning algorithms?**")
q1_options = [
    "Perceptron employs a kernel trick to enhance its capabilities",
    "Support Vector Machine utilizes a kernel trick to handle complex data distributions.",
    "Perceptron is limited to handling only linearly separable datasets.",
    "Support Vector Machine is restricted to binary classification problems."
]
q1 = st.radio("Select one answer for question 1:", q1_options, key="q1", index = None)

# Question 2 - Kept as multiple choice with checkboxes
st.markdown("**2. Which characteristics are accurate for artificial neural networks? (Select all that apply)**")
q2_options = [
    "They are comprised of interconnected neurons with adjustable weights",
    "They have the capability to model and learn complex nonlinear relationships.",
    "They are always dependent on labeled datasets for training",
    "They are exclusively employed for image recognition tasks."
]
q2_selected = [st.checkbox(option, key=f"q2_{i}") for i, option in enumerate(q2_options)]
q2 = [option for selected, option in zip(q2_selected, q2_options) if selected]

# Question 3 - Changed to radio button for single selection
st.markdown("**3. In the machine learning development process, which of the following are typically the preliminary stages that a data scientist should address?**")
q3_options = [
    "Collecting and preprocessing data",
    "Conducting model tuning and optimizing hyperparameters",
    "Performing feature scaling and deploying the model",
    "Evaluating the model and selecting appropriate metrics"
]
q3 = st.radio("Select one answer for question 3:", q3_options, key="q3", index = None)

# Question 4 - Kept as multiple choice with checkboxes
st.markdown("**4. What are some significant historical advancements in spam filtering technologies? (Select all that apply)**")
q4_options = [
    "Adoption of Bayesian filtering techniques",
    "Introduction of challenge-response systems",
    "Creation of CAPTCHA systems",
    "Integration of machine learning algorithms into spam filtering"
]
q4_selected = [st.checkbox(option, key=f"q4_{i}") for i, option in enumerate(q4_options)]
q4 = [option for selected, option in zip(q4_selected, q4_options) if selected]

# Question 5 - Changed to radio button for single selection
st.markdown("**5. Imagine your organization is experiencing a high volume of spam emails despite having a basic spam filter in place. You're tasked with improving the spam detection system. Considering current techniques, which approach would be most effective to enhance the filter's accuracy?**")
q5_options = [
    "Implementing a Support Vector Machine with a kernel trick to improve classification accuracy.",
    "Relying solely on linear regression for spam classification",
    "Utilizing K-Means Clustering to categorize emails",
    "Adding more CAPTCHAs to verify sender authenticity."
]
q5 = st.radio("Select one answer for question 5:", q5_options, key="q5", index = None)

# Correct Answers
correct_answers = {
    "q1": "Support Vector Machine utilizes a kernel trick to handle complex data distributions.",
    "q2": [
        "They are comprised of interconnected neurons with adjustable weights",
        "They have the capability to model and learn complex nonlinear relationships."
    ],
    "q3": "Collecting and preprocessing data",
    "q4": [
        "Adoption of Bayesian filtering techniques",
        "Introduction of challenge-response systems",
        "Integration of machine learning algorithms into spam filtering"
    ],
    "q5": "Implementing a Support Vector Machine with a kernel trick to improve classification accuracy."
}

# Initialize session state for test completion status
if "test_submitted" not in st.session_state:
    st.session_state.test_submitted = False

# Calculate Score
score = 0

# Disable inputs if test has already been submitted
if st.session_state.test_submitted:
    st.warning("You have already submitted this test. Your results have been saved.")
    
    # Display the saved results if available
    if "result_summary" in st.session_state:
        st.success(f"You scored {st.session_state.score:.2f}/5!")
        st.markdown("### Your Test Results")
        st.markdown(st.session_state.result_summary.replace('\n', '<br>'), unsafe_allow_html=True)
else:
    # Two-step submission process
    if "confirm_submission" not in st.session_state:
        st.session_state.confirm_submission = False
        
    if st.button("Submit and calculate score"):
        st.session_state.confirm_submission = True
        
    if st.session_state.confirm_submission:
        st.warning("⚠️ Are you sure you want to submit? You won't be able to retake this test.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cancel"):
                st.session_state.confirm_submission = False
                st.experimental_rerun()
        with col2:
            if st.button("Confirm Submission"):
                # For single-choice questions (q1, q3, q5)
                if q1 == correct_answers["q1"]:
                    score += 1
                if q3 == correct_answers["q3"]:
                    score += 1
                if q5 == correct_answers["q5"]:
                    score += 1

                # For multiple-choice questions (q2, q4)
                # Calculate partial credit for q2
                q2_correct = set(correct_answers["q2"])
                q2_selected = set(q2)
                q2_score = 0
                if q2_selected:
                    # Calculate true positives and false positives
                    true_positives = len(q2_selected.intersection(q2_correct))
                    false_positives = len(q2_selected - q2_correct)
                    # Award points for correct selections and penalize for incorrect ones
                    q2_score = max(0, (true_positives / len(q2_correct)) - (false_positives * 0.25))
                    score += q2_score

                # Calculate partial credit for q4
                q4_correct = set(correct_answers["q4"])
                q4_selected = set(q4)
                q4_score = 0
                if q4_selected:
                    # Calculate true positives and false positives
                    true_positives = len(q4_selected.intersection(q4_correct))
                    false_positives = len(q4_selected - q4_correct)
                    # Award points for correct selections and penalize for incorrect ones
                    q4_score = max(0, (true_positives / len(q4_correct)) - (false_positives * 0.25))
                    score += q4_score

                # Store the score in session state to mark test as completed
                st.session_state.score = score
                st.session_state.test_submitted = True
                
                st.success(f"You scored {score:.2f}/5!")

                # Summary with detailed breakdown
                result_summary = f"""
Your Responses:
--------------------------------------
1. {q1} {'✓' if q1 == correct_answers['q1'] else '✗'}
2. {', '.join(q2)} (Score: {q2_score:.2f})
3. {q3} {'✓' if q3 == correct_answers['q3'] else '✗'}
4. {', '.join(q4)} (Score: {q4_score:.2f})
5. {q5} {'✓' if q5 == correct_answers['q5'] else '✗'}

Total Score: {score:.2f}/5
"""

                # Store the result summary in session state
                st.session_state.result_summary = result_summary
                
                # Import the session manager
                from session_manager import get_session_manager
                
                # Get or create a session manager instance
                session_manager = get_session_manager()
                
                # Save the test results using the session manager
                file_path = session_manager.save_knowledge_test_results(result_summary)
                
                # Get the session info for display
                session_info = session_manager.get_session_info()
                fake_name = session_info["fake_name"]
                
                st.success(f"Your results have been saved with pseudonymized ID: {fake_name}")
                
                # Display detailed results with correct/incorrect answers highlighted
                st.markdown("### Your Test Results")
                
                # Format the results with colored indicators for correct/incorrect answers
                formatted_results = "<h4>Question 1:</h4>"
                formatted_results += f"<p>Your answer: {q1} {'✅' if q1 == correct_answers['q1'] else '❌'}</p>"
                if q1 != correct_answers['q1']:
                    formatted_results += f"<p>Correct answer: {correct_answers['q1']}</p>"
                
                formatted_results += "<h4>Question 2:</h4>"
                formatted_results += f"<p>Your answers: {', '.join(q2)} (Score: {q2_score:.2f})</p>"
                if q2_score < 1:
                    formatted_results += f"<p>Correct answers: {', '.join(correct_answers['q2'])}</p>"
                
                formatted_results += "<h4>Question 3:</h4>"
                formatted_results += f"<p>Your answer: {q3} {'✅' if q3 == correct_answers['q3'] else '❌'}</p>"
                if q3 != correct_answers['q3']:
                    formatted_results += f"<p>Correct answer: {correct_answers['q3']}</p>"
                
                formatted_results += "<h4>Question 4:</h4>"
                formatted_results += f"<p>Your answers: {', '.join(q4)} (Score: {q4_score:.2f})</p>"
                if q4_score < 1:
                    formatted_results += f"<p>Correct answers: {', '.join(correct_answers['q4'])}</p>"
                
                formatted_results += "<h4>Question 5:</h4>"
                formatted_results += f"<p>Your answer: {q5} {'✅' if q5 == correct_answers['q5'] else '❌'}</p>"
                if q5 != correct_answers['q5']:
                    formatted_results += f"<p>Correct answer: {correct_answers['q5']}</p>"
                
                formatted_results += f"<h4>Total Score: {score:.2f}/5</h4>"
                
                st.markdown(formatted_results, unsafe_allow_html=True)
                
                st.download_button(
                    label="Download your results",
                    data=result_summary,
                    file_name="email_threat_detection_test_results.txt",
                    mime="text/plain"
                )
