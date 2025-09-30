import streamlit as st

FAST_TEST_MODE = st.session_state.get("fast_test_mode")

st.title("Student Profile Survey")

# Initialize session state for form submission and to store form values
if "show_review" not in st.session_state:
    st.session_state.show_review = False


# Initialize form values in session state to prevent losing data on rerun
def init_form_field(key, default=None):
    if key not in st.session_state:
        st.session_state[key] = default
    elif st.session_state[key] is None and default is not None:
        st.session_state[key] = default


# Function to get value from session state
def get_state_value(key, default=None):
    return st.session_state.get(key, default)


# Function to reset form state
def reset_form_state():
    for key in list(st.session_state.keys()):
        if key != "show_review":
            del st.session_state[key]
    st.rerun()


# Function to initialize all form fields
def init_all_form_fields():
    # Basic fields
    init_form_field("name")
    init_form_field("age")
    init_form_field("education_level")
    init_form_field("major")
    init_form_field("work_exp")
    init_form_field("hobbies")
    init_form_field("strongest_subject")
    init_form_field("challenging_subject")
    init_form_field("proficiency_level")

    # Subject ratings
    for subject in subjects:
        init_form_field(subject)

    # Learning priorities
    for priority in learning_priorities:
        init_form_field(priority)

    # Learning strategies
    for strategy in learning_strategies:
        init_form_field(strategy, False)

    # Goals and barriers
    for goal in short_term_goals:
        init_form_field(f"short_{goal}", False)
    for goal in long_term_goals:
        init_form_field(f"long_{goal}", False)
    for barrier in barriers:
        init_form_field(f"barrier_{barrier}", False)


# Define all the lists needed for form fields
subjects = [
    "Mathematics",
    "Language Arts (reading, writing, speaking, listening, critical thinking)",
    "English ",
    "Science (Biology, Chemistry, Physics)",
    "Social Studies (History, Politics, Geography, Economics)",
    "Business & Finance",
    "Computer Science/Programming",
    "Engineering/Technology",
    "Health & Medicine",
    "Arts & Music",
    "Foreign Languages",
]

learning_priorities = [
    "Mastering relevant formulas and equations",
    "Understanding interrelationships among various concepts",
    "Grasping core concepts and key techniques",
    "Applying theory to real-world problems",
    "Critically analyzing and evaluating information",
]

learning_strategies = [
    "Real-world case studies with practical examples",
    "Interactive problem-solving exercises and guided project-based tasks",
    "Simulated group discussions and collaborative Q&A",
    "Detailed, step-by-step explanations similar to in-depth lectures",
    "Concise summaries and comprehensive textbook reviews",
    "Adaptive quizzes or exams",
]

short_term_goals = [
    "Improve foundational skills and core concepts",
    "Achieve higher grades or exam performance",
    "Develop better problem-solving or analytical abilities",
    "Gain new knowledge in specific areas",
]

long_term_goals = [
    "Gain admission to a top university or specialized program",
    "Advance my career or professional skills in this field",
    "Pursue personal development and lifelong learning",
    "Engage in research, innovation, or entrepreneurship",
]

barriers = [
    "Limited time or scheduling conflicts",
    "Difficulty understanding key concepts",
    "Lack of quality resources or guidance",
    "Emotional or motivational challenges",
    "Insufficient foundational skills in mathematics",
]

# Initialize all form fields at startup
init_all_form_fields()

st.header("Section 1: Academic and Background Information")

# Initialize form fields
init_form_field("name")
init_form_field("age")
init_form_field("education_level")
init_form_field("major")
init_form_field("work_exp")
init_form_field("hobbies")
init_form_field("strongest_subject")
init_form_field("challenging_subject")
init_form_field("proficiency_level")

# Question 1 - Open-ended
name = st.text_input(
    "1. What is your name? *",
    key="name",
    help="Write the name you would like us to use during the interview.",
)

# Question 2 - Open-ended
age = st.text_input(
    "2. What is your age? *", key="age", help="Whole years only, e.g. 22."
)

# Question 3 - Multiple-choice
education_level = st.radio(
    "3. Which of the following best describes your study background? *",
    [
        "Junior High School",
        "High School",
        "Undergraduate (Bachelor's)",
        "Graduate (Master's)",
        "Doctorate (Ph.D.)",
        "Other",
    ],
    index=None,
    key="education_level",
    help="Pick the highest level you have finished so far.",
)

# Question 4 - Open-ended
major = st.text_input(
    "4. What was your major or primary area of study in your previous education? *",
    key="major",
    help="Main field of study; one line is enough.",
)

# Question 5 - Multiple-choice
work_exp = st.radio(
    "5. Do you have any work experience? If yes, what is your current job level? *",
    [
        "No work experience",
        "Entry-level",
        "Mid-level",
        "Senior-level",
        "Executive/Leadership",
        "Other",
    ],
    index=None,
    key="work_exp",
    help="Choose the option that best matches your current or most recent role.",
)

# Question 6 - Open-ended
hobbies = st.text_area(
    "6. What are your hobbies or interests (please specify)? *",
    key="hobbies",
    help="Short list separated by commas, e.g. chess, hiking.",
)

# Question 7 - Rating (1-5)
st.markdown(
    "### 7. Assign a score from 1 to 5 to each subject, where 1 = Weakest and 5 = Strongest *"
)

subjects = [
    "Mathematics",
    "Language Arts (reading, writing, speaking, listening, critical thinking)",
    "English ",
    "Science (Biology, Chemistry, Physics)",
    "Social Studies (History, Politics, Geography, Economics)",
    "Business & Finance",
    "Computer Science/Programming",
    "Engineering/Technology",
    "Health & Medicine",
    "Arts & Music",
    "Foreign Languages",
]

ratings = {}
rating_options = [1, 2, 3, 4, 5]

for subject in subjects:
    # Initialize rating in session state if not already present
    init_form_field(subject)
    ratings[subject] = st.radio(
        subject,
        rating_options,
        horizontal=True,
        key=subject,
        index=None,
        help="1 = weakest, 5 = strongest. Select one score for each subject.",
    )

# Questions 8 and 9 - Open-ended
strongest_subject = st.text_input(
    "8. Which subject or area do you consider your strongest? *",
    key="strongest_subject",
    help="Type the subject you feel most confident in.",
)
challenging_subject = st.text_input(
    "9. Which subject or area do you find most challenging? *",
    key="challenging_subject",
    help="Type the subject you find hardest.",
)

st.markdown("---")
st.header("Section 2: Learning Style Preferred Learning Methods and Assessment")

# Question 10 - Rating (1-5)
st.markdown(
    "### 10. Assign a score from 1 to 5 to each of the following learning priorities based on their importance to you *"
)
st.markdown("(1 = least important, 5 = most important)")

learning_priorities = [
    "Mastering relevant formulas and equations",
    "Understanding interrelationships among various concepts",
    "Grasping core concepts and key techniques",
    "Applying theory to real-world problems",
    "Critically analyzing and evaluating information",
]

priority_ratings = {}

for priority in learning_priorities:
    # Initialize priority rating in session state if not already present
    init_form_field(priority)
    priority_ratings[priority] = st.radio(
        priority,
        rating_options,
        horizontal=True,
        key=priority,
        index=None,
        help="1 = least important to you, 5 = most important.",
    )

# Question 11 - Multiple selection
st.markdown(
    "### 11. Which learning strategy would you prefer if you had access to a tutor? *"
)
st.markdown("(Select one or more)")

learning_strategies = [
    "Real-world case studies with practical examples",
    "Interactive problem-solving exercises and guided project-based tasks",
    "Simulated group discussions and collaborative Q&A",
    "Detailed, step-by-step explanations similar to in-depth lectures",
    "Concise summaries and comprehensive textbook reviews",
    "Adaptive quizzes or exams",
]

selected_strategies = []
for strategy in learning_strategies:
    # Initialize strategy in session state if not already present
    init_form_field(strategy, False)
    if st.checkbox(strategy, key=strategy, help="Select at least one option"):
        selected_strategies.append(strategy)

st.markdown("---")
st.header("Section 3: Subject-Specific Proficiency, Goals, and Barriers")
st.markdown("### 12. What is your current proficiency level in this subject? *")
# Question 12 - Multiple-choice
proficiency_level = st.radio(
    "Select one",
    [
        "Beginner (I am new to this subject)",
        "Intermediate (I have a basic understanding but need improvement)",
        "Advanced (I have a strong grasp of the subject)",
        "Other",
    ],
    index=None,
    key="proficiency_level",
    help="Estimate how well you know this course topic right now.",
)

# Question 13 - Multiple selection
st.markdown("### 13. What are your short-term academic goals for this subject? *")
st.markdown("(Select one or more)")

short_term_goals = [
    "Improve foundational skills and core concepts",
    "Achieve higher grades or exam performance",
    "Develop better problem-solving or analytical abilities",
    "Gain new knowledge in specific areas",
]

selected_short_goals = []
for goal in short_term_goals:
    # Initialize checkbox in session state if not already present
    init_form_field(f"short_{goal}", False)
    if st.checkbox(goal, key=f"short_{goal}", help="Select at least one option"):
        selected_short_goals.append(goal)

# Question 14 - Multiple selection
st.markdown(
    "### 14. What are your long-term academic or career goals related to this subject? *"
)
st.markdown("(Select one or more)")

long_term_goals = [
    "Gain admission to a top university or specialized program",
    "Advance my career or professional skills in this field",
    "Pursue personal development and lifelong learning",
    "Engage in research, innovation, or entrepreneurship",
]

selected_long_goals = []
for goal in long_term_goals:
    # Initialize checkbox in session state if not already present
    init_form_field(f"long_{goal}", False)
    if st.checkbox(goal, key=f"long_{goal}", help="Select at least one option"):
        selected_long_goals.append(goal)

# Question 15 - Multiple selection
st.markdown(
    "### 15. What potential barriers do you anticipate encountering while studying this subject? *"
)
st.markdown("(Select one or more)")

barriers = [
    "Limited time or scheduling conflicts",
    "Difficulty understanding key concepts",
    "Lack of quality resources or guidance",
    "Emotional or motivational challenges",
    "Insufficient foundational skills in mathematics",
]

selected_barriers = []
for barrier in barriers:
    # Initialize checkbox in session state if not already present
    init_form_field(f"barrier_{barrier}", False)
    if st.checkbox(
        barrier, key=f"barrier_{barrier}", help="Select at least one option"
    ):
        selected_barriers.append(barrier)

# Submit button
submit_button = st.button("Submit", key="submit_profile_survey")
if submit_button:
    if "FAST_TEST_MODE" in globals() and FAST_TEST_MODE:
        st.session_state.form_data = {
            "name": "Test User",
            "age": "21",
            "education_level": "Undergraduate (Bachelor's)",
            "major": "Engineering",
            "work_exp": "Entry-level",
            "hobbies": "Chess, Reading",
            "strongest_subject": "Mathematics",
            "challenging_subject": "Physics",
            "ratings": {
                "Mathematics": 5,
                "Language Arts (reading, writing, speaking, listening, critical thinking)": 4,
                "English ": 4,
                "Science (Biology, Chemistry, Physics)": 3,
                "Social Studies (History, Politics, Geography, Economics)": 3,
                "Business & Finance": 2,
                "Computer Science/Programming": 5,
                "Engineering/Technology": 5,
                "Health & Medicine": 2,
                "Arts & Music": 3,
                "Foreign Languages": 3,
            },
            "priority_ratings": {
                "Mastering relevant formulas and equations": 5,
                "Understanding interrelationships among various concepts": 5,
                "Grasping core concepts and key techniques": 4,
                "Applying theory to real-world problems": 5,
                "Critically analyzing and evaluating information": 4,
            },
            "selected_strategies": [
                "Detailed, step-by-step explanations similar to in-depth lectures"
            ],
            "proficiency_level": "Intermediate (I have a basic understanding but need improvement)",
            "selected_short_goals": [
                "Understand core concepts",
                "Achieve higher grades or exam performance",
            ],
            "selected_long_goals": [
                "Gain admission to a top university or specialized program"
            ],
            "selected_barriers": ["Lack of prior knowledge"],
        }
        st.session_state.show_review = True
        st.success(
            "FAST_TEST_MODE enabled: Synthetic profile used. Showing review section..."
        )
    else:
        try:
            # Validate all inputs only when submit is clicked
            all_fields_filled = (
                name
                and age
                and education_level
                and major
                and work_exp
                and hobbies
                and strongest_subject
                and challenging_subject
                and all(rating is not None for rating in ratings.values())
                and all(rating is not None for rating in priority_ratings.values())
                and len(selected_strategies) > 0
                and proficiency_level
                and len(selected_short_goals) > 0
                and len(selected_long_goals) > 0
                and len(selected_barriers) > 0
            )

            if all_fields_filled:
                # Store current form values in session state
                st.session_state.form_data = {
                    "name": name,
                    "age": age,
                    "education_level": education_level,
                    "major": major,
                    "work_exp": work_exp,
                    "hobbies": hobbies,
                    "strongest_subject": strongest_subject,
                    "challenging_subject": challenging_subject,
                    "ratings": ratings,
                    "priority_ratings": priority_ratings,
                    "selected_strategies": selected_strategies,
                    "proficiency_level": proficiency_level,
                    "selected_short_goals": selected_short_goals,
                    "selected_long_goals": selected_long_goals,
                    "selected_barriers": selected_barriers,
                }
                # Save profile data to a file
                from session_manager import get_session_manager

                # Get or create a session manager instance
                session_manager = get_session_manager()

                # Save the profile data with pseudonymization
                original_name = name
                file_path = session_manager.save_profile(
                    st.session_state.form_data, original_name
                )

                # Set the session state flag before any other operations
                st.session_state.show_review = True
                # Add a success message to confirm the state change
                st.success("Form submitted successfully! Showing review section...")

            else:
                st.warning(
                    "Please fill in all required fields marked with * before submitting."
                )
                # For debugging
                if not name:
                    st.error("Name is required")
                if not age:
                    st.error("Age is required")
                if not education_level:
                    st.error("Education level is required")
                if not major:
                    st.error("Major is required")
                if not work_exp:
                    st.error("Work experience is required")
                if not hobbies:
                    st.error("Hobbies are required")
                if not strongest_subject:
                    st.error("Strongest subject is required")
                if not challenging_subject:
                    st.error("Challenging subject is required")
                if not all(rating is not None for rating in ratings.values()):
                    st.error("All subject ratings are required")
                if not all(rating is not None for rating in priority_ratings.values()):
                    st.error("All learning priority ratings are required")
                if len(selected_strategies) == 0:
                    st.error("At least one learning strategy is required")
                if not proficiency_level:
                    st.error("Proficiency level is required")
                if len(selected_short_goals) == 0:
                    st.error("At least one short-term goal is required")
                if len(selected_long_goals) == 0:
                    st.error("At least one long-term goal is required")
                if len(selected_barriers) == 0:
                    st.error("At least one potential barrier is required")
            st.rerun()
        except Exception as e:
            st.error(f"An error occurred during form submission: {str(e)}")
            import traceback

            st.error(traceback.format_exc())


# Only show review section after submission
if st.session_state.show_review:
    try:
        st.markdown("---")
        st.header("Review Your Responses")

        # Access form data from session state
        if "form_data" not in st.session_state:
            st.error(
                "Form data not found in session state. Please try submitting the form again."
            )
            st.session_state.show_review = False
        else:
            form_data = st.session_state.form_data

            # Prepare the responses as text
            response = f"""Student Profile Survey Responses:
====================================

Section 1: Academic and Background Information
            ---------------------------------------------
1. Name: {form_data['name']}
2. Age: {form_data['age']}
3. Study Background: {form_data['education_level']}
4. Major/Area of Study: {form_data['major']}
5. Work Experience: {form_data['work_exp']}
6. Hobbies and Interests: {form_data['hobbies']}

7. Subject Ratings:
"""

            for subject, rating in form_data["ratings"].items():
                response += f"   - {subject}: {rating}/5\n"

            response += f"""
8. Strongest Subject or Area: {form_data['strongest_subject']}
9. Most Challenging Subject or Area: {form_data['challenging_subject']}

Section 2: Learning Style Preferred Learning Methods and Assessment
-----------------------------------------------------------------
10. Learning Priorities (1 = least important, 5 = most important):
"""

            for priority, rating in form_data["priority_ratings"].items():
                response += f"   - {priority}: {rating}/5\n"

            response += "\n11. Preferred Learning Strategies:\n"
            for strategy in form_data["selected_strategies"]:
                response += f"   - {strategy}\n"

            response += f"""

Section 3: Subject-Specific Proficiency, Goals, and Barriers
----------------------------------------------------------
12. Current Proficiency Level: {form_data['proficiency_level']}

13. Short-term Academic Goals:
"""

            for goal in form_data["selected_short_goals"]:
                response += f"   - {goal}\n"

            response += "\n14. Long-term Academic/Career Goals:\n"
            for goal in form_data["selected_long_goals"]:
                response += f"   - {goal}\n"

            response += "\n15. Potential Barriers:\n"
            for barrier in form_data["selected_barriers"]:
                response += f"   - {barrier}\n"

            st.text_area(
                "Please review your responses below:", value=response, height=500
            )

    except Exception as e:
        st.error(f"An error occurred in the review section: {str(e)}")
        import traceback

        st.error(traceback.format_exc())
        # Reset the show_review state if there's an error
        st.session_state.show_review = False
