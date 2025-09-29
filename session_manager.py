import datetime
import json
import os
import random
import string

import streamlit as st

# List of fake first names and last names for pseudonymization
FIRST_NAMES = [
    "Alex",
    "Bailey",
    "Cameron",
    "Dakota",
    "Ellis",
    "Finley",
    "Gray",
    "Harper",
    "Indigo",
    "Jordan",
    "Kennedy",
    "Logan",
    "Morgan",
    "Noah",
    "Oakley",
    "Parker",
    "Quinn",
    "Riley",
    "Sawyer",
    "Taylor",
    "Ursa",
    "Val",
    "Winter",
    "Xen",
    "Yael",
    "Zephyr",
]

LAST_NAMES = [
    "Adams",
    "Brooks",
    "Chen",
    "Davis",
    "Evans",
    "Foster",
    "Garcia",
    "Hayes",
    "Ivanov",
    "Johnson",
    "Kim",
    "Lee",
    "Miller",
    "Nguyen",
    "Ortiz",
    "Patel",
    "Quinn",
    "Robinson",
    "Smith",
    "Taylor",
    "Ueda",
    "Vargas",
    "Williams",
    "Xu",
    "Young",
    "Zhang",
]


class SessionManager:
    """Manages session data and file organization for the personalized learning platform."""

    def __init__(self, condition: str | None = None):
        """Initialize the session manager."""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = os.path.join(self.base_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)

        self.condition = condition or "personalised"  # default

        # Generate session ID if not already exists
        if not hasattr(self, "session_id"):
            self.create_new_session()

    def create_new_session(self):
        """Create a new session with timestamp and fake name as identifier."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fake_name = self._generate_fake_name()
        self.session_id = f"{timestamp}_{fake_name}"
        self.session_dir = os.path.join(self.output_dir, self.session_id)
        os.makedirs(self.session_dir, exist_ok=True)

        # Create subdirectories for different types of data
        self.profile_dir = os.path.join(self.session_dir, "profile")
        self.knowledge_test_dir = os.path.join(self.session_dir, "knowledge_test")
        self.learning_logs_dir = os.path.join(self.session_dir, "learning_logs")
        self.ueq_dir = os.path.join(self.session_dir, "ueq")
        self.analytics_dir = os.path.join(self.session_dir, "analytics")  # New analytics directory

        os.makedirs(self.profile_dir, exist_ok=True)
        os.makedirs(self.knowledge_test_dir, exist_ok=True)
        os.makedirs(self.learning_logs_dir, exist_ok=True)
        os.makedirs(self.ueq_dir, exist_ok=True)
        os.makedirs(self.analytics_dir, exist_ok=True)

        with open(os.path.join(self.session_dir, "condition.txt"), "w") as f:
            f.write(self.condition)

        return self.session_id

    def _generate_fake_name(self):
        """Generate a random fake name for pseudonymization."""
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        return f"{first_name}_{last_name}"

    def save_profile(self, profile_data, original_name):
        """Save the student profile with pseudonymization.

        Args:
            profile_data (dict): The profile data to save
            original_name (str): The original name from the profile

        Returns:
            str: Path to the saved profile file
        """
        # Create a pseudonymized version of the profile
        pseudo_profile = profile_data.copy()

        # Replace the real name with the fake name from the session ID
        fake_name = self.session_id.split("_", 1)[
            1
        ]  # Extract fake name from session ID
        pseudo_profile["name"] = fake_name

        # Save both original and pseudonymized profiles
        original_file_path = os.path.join(self.profile_dir, "original_profile.txt")
        pseudo_file_path = os.path.join(self.profile_dir, "pseudonymized_profile.txt")

        # Save as text files
        with open(original_file_path, "w", encoding="utf-8") as f:
            for key, value in profile_data.items():
                f.write(f"{key}: {value}\n")

        with open(pseudo_file_path, "w", encoding="utf-8") as f:
            for key, value in pseudo_profile.items():
                f.write(f"{key}: {value}\n")

        # Also save as JSON for easier programmatic access
        with open(
            os.path.join(self.profile_dir, "original_profile.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(profile_data, f, indent=4)

        with open(
            os.path.join(self.profile_dir, "pseudonymized_profile.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(pseudo_profile, f, indent=4)

        return pseudo_file_path

    def save_knowledge_test_results(self, result_summary):
        """Save knowledge test results to the session directory.

        Args:
            result_summary (str): The test results summary

        Returns:
            str: Path to the saved results file
        """
        filename = "knowledge_test_results.txt"
        file_path = os.path.join(self.knowledge_test_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Condition : {self.condition}\n\n")
            f.write(result_summary)

        return file_path

    def save_interaction_analytics(self, interaction_counts):
        """Save interaction analytics for research analysis.

        Args:
            interaction_counts (dict): Dictionary with interaction statistics

        Returns:
            str: Path to the saved analytics file
        """
        filename = "interaction_analytics.json"
        file_path = os.path.join(self.analytics_dir, filename)

        analytics_data = {
            "condition": self.condition,
            "session_id": self.session_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "interaction_counts": interaction_counts,
            "engagement_metrics": {
                "total_user_interactions": interaction_counts.get("total_user_interactions", 0),
                "slide_to_chat_ratio": (
                    interaction_counts.get("slide_explanations", 0) / 
                    max(interaction_counts.get("manual_chat", 1), 1)  # Avoid division by zero
                ),
                "interaction_distribution": {
                    "slide_explanations_pct": (
                        interaction_counts.get("slide_explanations", 0) / 
                        max(interaction_counts.get("total_user_interactions", 1), 1) * 100
                    ),
                    "manual_chat_pct": (
                        interaction_counts.get("manual_chat", 0) / 
                        max(interaction_counts.get("total_user_interactions", 1), 1) * 100
                    )
                }
            }
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(analytics_data, f, indent=4)

        return file_path

    def save_learning_log(self, log_data):
        """Save learning interaction logs.

        Args:
            log_data (dict): The log data to save

        Returns:
            str: Path to the saved log file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"learning_log_{timestamp}.txt"
        file_path = os.path.join(self.learning_logs_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            # Write session information
            f.write(f"Session ID: {log_data['session_id']}\n")
            f.write(f"Fake Name: {log_data['fake_name']}\n")
            f.write(f"Condition : {self.condition}\n\n")
            f.write(f"Timestamp: {log_data['timestamp']}\n")
            
            # Write interaction summary if available
            if "interaction_counts" in log_data:
                counts = log_data["interaction_counts"]
                f.write("\n=== INTERACTION SUMMARY ===\n")
                f.write(f"Slide Explanations Generated: {counts['slide_explanations']}\n")
                f.write(f"Manual Chat Messages: {counts['manual_chat']}\n")
                f.write(f"Total User Interactions: {counts['total_user_interactions']}\n")
                if counts['total_user_interactions'] > 0:
                    slide_pct = (counts['slide_explanations'] / counts['total_user_interactions']) * 100
                    chat_pct = (counts['manual_chat'] / counts['total_user_interactions']) * 100
                    f.write(f"Interaction Distribution: {slide_pct:.1f}% slides, {chat_pct:.1f}% chat\n")
            
            f.write("\n=== INTERACTIONS ===\n\n")

            # Write each interaction
            for interaction in log_data["interactions"]:
                f.write(f"--- Interaction at {interaction['timestamp']} ---\n")
                f.write(f"Type: {interaction['interaction_type']}\n")
                f.write(f"User Input: {interaction['user_input']}\n")
                f.write(f"System Response: {interaction['system_response']}\n")

                # Write metadata if available
                if "metadata" in interaction:
                    f.write("Metadata:\n")
                    for key, value in interaction["metadata"].items():
                        f.write(f"  {key}: {value}\n")

                f.write("\n")

        return file_path

    def save_ueq_responses(self, response_text):
        """Save UEQ survey responses.

        Args:
            response_text (str): The UEQ responses as text

        Returns:
            str: Path to the saved responses file
        """
        filename = "ueq_responses.txt"
        file_path = os.path.join(self.ueq_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Condition : {self.condition}\n\n")
            f.write(response_text)

        return file_path

    def get_session_info(self):
        """Get information about the current session.

        Returns:
            dict: Session information
        """
        return {
            "session_id": self.session_id,
            "session_dir": self.session_dir,
            "fake_name": self.session_id.split("_", 1)[1],
            "timestamp": self.session_id.split("_", 1)[0],
            "condition": self.condition,
        }

    def save_ueq(self, answers: dict, benchmark: dict, free_text: str | None) -> str:
        """
        Store the raw answers (dict q→1‑7), scale means, benchmark grades
        and an optional comment.  Returns the TXT path.
        """
        payload = {
            "answers": answers,  # e.g. {"q1": 5, …}
            "scale_means": benchmark["means"],
            "grades": benchmark["grades"],
            "comment": free_text or "",
            "condition": self.condition,
        }

        path = os.path.join(self.ueq_dir, "ueq_responses.txt")
        with open(path, "w", encoding="utf‑8") as f:
            json.dump(payload, f, indent=2)

        return path

    def create_final_analytics(self):
        """Create a comprehensive analytics JSON with all research data consolidated."""
        # Ensure analytics directory exists
        os.makedirs(self.analytics_dir, exist_ok=True)
        
        final_analytics = {
            "session_info": {
                "session_id": self.session_id,
                "pseudonym": self.session_id.split("_", 1)[1],
                "timestamp": self.session_id.split("_", 1)[0],
                "condition": self.condition,
                "session_dir": self.session_dir
            },
            "profile_data": None,
            "page_timings": None,
            "interaction_analytics": None,
            "ueq_results": None,
            "knowledge_test_results": None,
            "summary_metrics": {}
        }

        # Load profile data
        try:
            profile_path = os.path.join(self.profile_dir, "pseudonymized_profile.json")
            if os.path.exists(profile_path):
                with open(profile_path, "r", encoding="utf-8") as f:
                    final_analytics["profile_data"] = json.load(f)
        except Exception as e:
            print(f"Could not load profile data: {e}")

        # Load page timings
        try:
            page_timings_path = os.path.join(self.session_dir, "meta", "page_durations.json")
            if os.path.exists(page_timings_path):
                with open(page_timings_path, "r", encoding="utf-8") as f:
                    timings = json.load(f)
                    final_analytics["page_timings"] = timings
                    # Calculate total session time
                    final_analytics["summary_metrics"]["total_session_time_seconds"] = sum(timings.values())
                    final_analytics["summary_metrics"]["total_session_time_minutes"] = sum(timings.values()) / 60
        except Exception as e:
            print(f"Could not load page timings: {e}")

        # Load interaction analytics
        try:
            if os.path.exists(self.analytics_dir):
                interaction_files = [f for f in os.listdir(self.analytics_dir) if f.startswith("interaction_analytics")]
                if interaction_files:
                    # Get the most recent interaction analytics file
                    latest_file = max(interaction_files)
                    interaction_path = os.path.join(self.analytics_dir, latest_file)
                    with open(interaction_path, "r", encoding="utf-8") as f:
                        final_analytics["interaction_analytics"] = json.load(f)
        except Exception as e:
            print(f"Could not load interaction analytics: {e}")

        # Load UEQ results
        try:
            ueq_path = os.path.join(self.ueq_dir, "ueq_responses.txt")
            if os.path.exists(ueq_path):
                with open(ueq_path, "r", encoding="utf-8") as f:
                    final_analytics["ueq_results"] = json.load(f)
        except Exception as e:
            print(f"Could not load UEQ results: {e}")

        # Load knowledge test results
        try:
            if os.path.exists(self.knowledge_test_dir):
                # Look for knowledge test files
                knowledge_files = [f for f in os.listdir(self.knowledge_test_dir) if f.endswith('.json')]
                if knowledge_files:
                    # Get the most recent knowledge test file
                    latest_knowledge_file = max(knowledge_files)
                    knowledge_path = os.path.join(self.knowledge_test_dir, latest_knowledge_file)
                    with open(knowledge_path, "r", encoding="utf-8") as f:
                        final_analytics["knowledge_test_results"] = json.load(f)
        except Exception as e:
            print(f"Could not load knowledge test results: {e}")

        # Calculate additional summary metrics
        try:
            # Learning engagement metrics
            if final_analytics["interaction_analytics"]:
                interaction_data = final_analytics["interaction_analytics"]
                final_analytics["summary_metrics"]["learning_engagement"] = {
                    "total_ai_interactions": interaction_data.get("interaction_counts", {}).get("total_user_interactions", 0),
                    "slide_explanations": interaction_data.get("interaction_counts", {}).get("slide_explanations", 0),
                    "manual_chat": interaction_data.get("interaction_counts", {}).get("manual_chat", 0),
                    "slide_to_chat_ratio": interaction_data.get("engagement_metrics", {}).get("slide_to_chat_ratio", 0)
                }

            # UEQ summary metrics
            if final_analytics["ueq_results"]:
                ueq_data = final_analytics["ueq_results"]
                final_analytics["summary_metrics"]["ueq_summary"] = {
                    "scale_means": ueq_data.get("scale_means", {}),
                    "overall_grades": ueq_data.get("grades", {}),
                    "has_comment": bool(ueq_data.get("comment", "").strip())
                }

            # Knowledge test summary
            if final_analytics["knowledge_test_results"]:
                knowledge_data = final_analytics["knowledge_test_results"]
                if "answers" in knowledge_data:
                    total_questions = len(knowledge_data["answers"])
                    correct_answers = sum(1 for ans in knowledge_data["answers"].values() if ans.get("is_correct", False))
                    final_analytics["summary_metrics"]["knowledge_test_summary"] = {
                        "total_questions": total_questions,
                        "correct_answers": correct_answers,
                        "accuracy_percentage": (correct_answers / total_questions * 100) if total_questions > 0 else 0
                    }

            # Learning efficiency metrics
            if final_analytics["page_timings"] and final_analytics["interaction_analytics"]:
                learning_time = final_analytics["page_timings"].get("personalized_learning", 0)
                total_interactions = final_analytics["summary_metrics"].get("learning_engagement", {}).get("total_ai_interactions", 0)
                if learning_time > 0 and total_interactions > 0:
                    final_analytics["summary_metrics"]["learning_efficiency"] = {
                        "avg_time_per_interaction_seconds": learning_time / total_interactions,
                        "interactions_per_minute": (total_interactions / learning_time) * 60
                    }

        except Exception as e:
            print(f"Could not calculate summary metrics: {e}")

        # Save the final analytics file
        final_analytics_path = os.path.join(self.analytics_dir, "final_research_analytics.json")
        with open(final_analytics_path, "w", encoding="utf-8") as f:
            json.dump(final_analytics, f, indent=4, ensure_ascii=False)

        return final_analytics_path


session_manager = None  # keeps the singleton in the module


def get_session_manager() -> SessionManager:
    """Return ONE shared SessionManager instance for the whole app."""
    global session_manager

    if session_manager is not None:  # we already created / cached it
        return session_manager

    # Was it created somewhere else (e.g. on the Home page) and put into
    # session_state?  → reuse it
    if "session_manager" in st.session_state:
        session_manager = st.session_state["session_manager"]
        return session_manager

    # First call overall → create it, remember it everywhere
    session_manager = SessionManager()
    st.session_state["session_manager"] = session_manager
    return session_manager
