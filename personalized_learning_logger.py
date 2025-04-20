import datetime
import json
import os

from session_manager import get_session_manager


class LearningLogger:
    """Handles logging of interactions with the personalized learning tool."""

    def __init__(self):
        """Initialize the learning logger."""
        self.session_manager = get_session_manager()
        self.log_entries = []

    def log_interaction(
        self, interaction_type, user_input, system_response, metadata=None
    ):
        """Log an interaction with the personalized learning tool.

        Args:
            interaction_type (str): Type of interaction (e.g., 'question', 'explanation')
            user_input (str): The input provided by the user
            system_response (str): The response from the system
            metadata (dict, optional): Additional metadata about the interaction
        """
        timestamp = datetime.datetime.now().isoformat()

        # Pseudonymize profile if present in user_input
        pseudonymized_user_input = user_input
        try:
            if isinstance(user_input, dict) and "StudentProfile" in user_input:
                pseudo_profile = user_input["StudentProfile"].copy()
                session_info = self.session_manager.get_session_info()
                pseudo_profile["Name"] = session_info["fake_name"]
                pseudonymized_user_input = user_input.copy()
                pseudonymized_user_input["StudentProfile"] = pseudo_profile
        except Exception:
            pass

        log_entry = {
            "timestamp": timestamp,
            "interaction_type": interaction_type,
            "user_input": pseudonymized_user_input,
            "system_response": system_response,
        }
        if metadata:
            log_entry["metadata"] = metadata
        self.log_entries.append(log_entry)

    def save_logs(self, force: bool = False):
        """
        Write the buffered interactions to disk and clear the buffer.

        If force == False (default) and the buffer is empty,
        do nothing and return None.
        """
        if not self.log_entries and not force:
            return None

        # Create a log data structure with session information
        session_info = self.session_manager.get_session_info()
        log_data = {
            "session_id": session_info["session_id"],
            "fake_name": session_info["fake_name"],
            "condition": session_info["condition"],
            "timestamp": datetime.datetime.now().isoformat(),
            "interactions": self.log_entries,
        }

        # Save the logs using the session manager
        file_path = self.session_manager.save_learning_log(log_data)

        # Clear the log entries after saving to prevent duplicate entries
        self.log_entries = []

        return file_path


# Create a singleton instance
learning_logger = None


def get_learning_logger():
    """Get or create the learning logger instance.

    Returns:
        LearningLogger: The learning logger instance
    """
    global learning_logger
    if learning_logger is None:
        learning_logger = LearningLogger()
    return learning_logger
