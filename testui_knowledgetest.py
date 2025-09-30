import datetime
import os

import streamlit as st
from config import config

st.title(f"🧬 Knowledge Test - {config.course.course_title}")

st.markdown(
    f"""
Welcome to the knowledge assessment on {config.course.subject_area.lower()} and genetics. This brief test is designed to evaluate your understanding of key concepts in cancer development, genetics, and cellular processes through multiple-choice questions.

The assessment consists of 5 questions that cover fundamental concepts in {config.course.subject_area.lower()} including BRCA mutations, cancer genetics analogies, epigenetic regulation, genomic instability, and cellular processes in malignancy. You'll receive immediate feedback on your performance.

Feel free to trust your intuition and apply the knowledge you've gained from the lecture materials. Your spontaneous responses often best reflect your true understanding of these important biological concepts.

At the end of the test, you'll be able to see your score and download your results for future reference. Remember, this is a learning opportunity to help you gauge your knowledge in {config.course.subject_area.lower()}.

Ready to begin? Let's explore your understanding together!
"""
)

# Question 1 - Single choice radio button
st.markdown(
    "**1. A woman inherits one mutated BRCA1 allele. Which statement best explains why her risk of breast cancer is elevated but not certain?**"
)
q1_options = [
    "Both alleles are already inactive from birth.",
    "The remaining wild-type allele can still produce functional protein until a second mutation occurs.",
    "BRCA1 is only important in embryonic cells, not in adult tissue.",
    "Inherited mutations always guarantee cancer, regardless of environment.",
]
q1 = st.radio("Select one answer for question 1:", q1_options, key="knowledge_q1", index=None)

# Question 2 - Single choice radio button
st.markdown(
    "**2. Which scenario best illustrates the \"gas and brakes\" analogy of cancer genetics?**"
)
q2_options = [
    "A cell acquires an inactivating mutation in p53, leading to loss of cell cycle arrest after DNA damage.",
    "A cell acquires an inactivating mutation in Ras, reducing MAPK pathway signaling.",
    "A cell deletes genes controlling glycolysis, reducing its metabolic activity.",
    "A cell undergoes benign variation in a noncoding intron sequence.",
]
q2 = st.radio("Select one answer for question 2:", q2_options, key="knowledge_q2", index=None)

# Question 3 - Single choice radio button
st.markdown(
    "**3. Why does epigenetic regulation play a critical role in explaining cellular diversity despite identical DNA sequences in different tissues?**"
)
q3_options = [
    "Epigenetics modifies gene expression without altering DNA sequence, enabling cell-type-specific transcription programs.",
    "Cells randomly delete DNA they do not need, creating diversity.",
    "DNA sequence varies significantly between liver and skin cells.",
    "Epigenetic changes occur only in cancer cells, not in normal tissues.",
]
q3 = st.radio("Select one answer for question 3:", q3_options, key="knowledge_q3", index=None)

# Question 4 - Single choice radio button
st.markdown(
    "**4. How does genomic instability accelerate tumor evolution?**"
)
q4_options = [
    "It maintains identical DNA across all tumor cells, ensuring stability.",
    "It introduces a higher rate of mutation, increasing the chance of acquiring oncogene activation and tumor suppressor loss.",
    "It prevents mutations from being passed to daughter cells, stabilizing growth.",
    "It reduces mutation frequency, protecting the genome from becoming oncogenic.",
]
q4 = st.radio("Select one answer for question 4:", q4_options, key="knowledge_q4", index=None)

# Question 5 - Single choice radio button
st.markdown(
    "**5. According to the lecture, which of the following is not one of the three major cellular processes that a cancer cell must overcome to become malignant?**"
)
q5_options = [
    "Regulation of proliferation",
    "Regulation of apoptosis/cell survival",
    "Regulation of cellular communication",
    "Regulation of protein translation",
]
q5 = st.radio("Select one answer for question 5:", q5_options, key="knowledge_q5", index=None)

# Correct Answers
correct_answers = {
    "knowledge_q1": "The remaining wild-type allele can still produce functional protein until a second mutation occurs.",
    "knowledge_q2": "A cell acquires an inactivating mutation in p53, leading to loss of cell cycle arrest after DNA damage.",
    "knowledge_q3": "Epigenetics modifies gene expression without altering DNA sequence, enabling cell-type-specific transcription programs.",
    "knowledge_q4": "It introduces a higher rate of mutation, increasing the chance of acquiring oncogene activation and tumor suppressor loss.",
    "knowledge_q5": "Regulation of protein translation",
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
        st.markdown(
            st.session_state.result_summary.replace("\n", "<br>"),
            unsafe_allow_html=True,
        )
else:
    # Two-step submission process
    if "confirm_submission" not in st.session_state:
        st.session_state.confirm_submission = False

    if st.button("Submit and calculate score"):
        st.session_state.confirm_submission = True

    if st.session_state.confirm_submission:
        st.warning(
            "⚠️ Are you sure you want to submit? You won't be able to retake this test."
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cancel"):
                st.session_state.confirm_submission = False
                st.rerun()
        with col2:
            if st.button("Confirm Submission"):
                # All questions are now single-choice
                if q1 == correct_answers["knowledge_q1"]:
                    score += 1
                if q2 == correct_answers["knowledge_q2"]:
                    score += 1
                if q3 == correct_answers["knowledge_q3"]:
                    score += 1
                if q4 == correct_answers["knowledge_q4"]:
                    score += 1
                if q5 == correct_answers["knowledge_q5"]:
                    score += 1

                # Store the score in session state to mark test as completed
                st.session_state.score = score
                st.session_state.test_submitted = True

                st.success(f"You scored {score:.2f}/5!")

                # Summary with detailed breakdown
                result_summary = f"""
Your Responses:
--------------------------------------
1. {q1} {'✓' if q1 == correct_answers['knowledge_q1'] else '✗'}
2. {q2} {'✓' if q2 == correct_answers['knowledge_q2'] else '✗'}
3. {q3} {'✓' if q3 == correct_answers['knowledge_q3'] else '✗'}
4. {q4} {'✓' if q4 == correct_answers['knowledge_q4'] else '✗'}
5. {q5} {'✓' if q5 == correct_answers['knowledge_q5'] else '✗'}

Total Score: {score}/5
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

                st.success(
                    f"Your results have been saved with pseudonymized ID: {fake_name}"
                )

                # Display detailed results with correct/incorrect answers highlighted
                st.markdown("### Your Test Results")

                # Format the results with colored indicators for correct/incorrect answers
                formatted_results = "<h4>Question 1:</h4>"
                formatted_results += f"<p>Your answer: {q1} {'✅' if q1 == correct_answers['knowledge_q1'] else '❌'}</p>"
                if q1 != correct_answers["knowledge_q1"]:
                    formatted_results += (
                        f"<p>Correct answer: {correct_answers['knowledge_q1']}</p>"
                    )

                formatted_results += "<h4>Question 2:</h4>"
                formatted_results += f"<p>Your answer: {q2} {'✅' if q2 == correct_answers['knowledge_q2'] else '❌'}</p>"
                if q2 != correct_answers["knowledge_q2"]:
                    formatted_results += (
                        f"<p>Correct answer: {correct_answers['knowledge_q2']}</p>"
                    )

                formatted_results += "<h4>Question 3:</h4>"
                formatted_results += f"<p>Your answer: {q3} {'✅' if q3 == correct_answers['knowledge_q3'] else '❌'}</p>"
                if q3 != correct_answers["knowledge_q3"]:
                    formatted_results += (
                        f"<p>Correct answer: {correct_answers['knowledge_q3']}</p>"
                    )

                formatted_results += "<h4>Question 4:</h4>"
                formatted_results += f"<p>Your answer: {q4} {'✅' if q4 == correct_answers['knowledge_q4'] else '❌'}</p>"
                if q4 != correct_answers["knowledge_q4"]:
                    formatted_results += (
                        f"<p>Correct answer: {correct_answers['knowledge_q4']}</p>"
                    )

                formatted_results += "<h4>Question 5:</h4>"
                formatted_results += f"<p>Your answer: {q5} {'✅' if q5 == correct_answers['knowledge_q5'] else '❌'}</p>"
                if q5 != correct_answers["knowledge_q5"]:
                    formatted_results += (
                        f"<p>Correct answer: {correct_answers['knowledge_q5']}</p>"
                    )

                formatted_results += f"<h4>Total Score: {score}/5</h4>"

                st.markdown(formatted_results, unsafe_allow_html=True)
