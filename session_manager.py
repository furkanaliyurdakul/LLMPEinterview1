import os
import datetime
import random
import string
import json

# List of fake first names and last names for pseudonymization
FIRST_NAMES = [
    "Alex", "Bailey", "Cameron", "Dakota", "Ellis", "Finley", "Gray", "Harper",
    "Indigo", "Jordan", "Kennedy", "Logan", "Morgan", "Noah", "Oakley", "Parker",
    "Quinn", "Riley", "Sawyer", "Taylor", "Ursa", "Val", "Winter", "Xen", "Yael", "Zephyr"
]

LAST_NAMES = [
    "Adams", "Brooks", "Chen", "Davis", "Evans", "Foster", "Garcia", "Hayes",
    "Ivanov", "Johnson", "Kim", "Lee", "Miller", "Nguyen", "Ortiz", "Patel",
    "Quinn", "Robinson", "Smith", "Taylor", "Ueda", "Vargas", "Williams", "Xu", "Young", "Zhang"
]

class SessionManager:
    """Manages session data and file organization for the personalized learning platform."""
    
    def __init__(self):
        """Initialize the session manager."""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = os.path.join(self.base_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)
        
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
        
        os.makedirs(self.profile_dir, exist_ok=True)
        os.makedirs(self.knowledge_test_dir, exist_ok=True)
        os.makedirs(self.learning_logs_dir, exist_ok=True)
        os.makedirs(self.ueq_dir, exist_ok=True)
        
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
        fake_name = self.session_id.split("_", 1)[1]  # Extract fake name from session ID
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
        with open(os.path.join(self.profile_dir, "original_profile.json"), "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=4)
        
        with open(os.path.join(self.profile_dir, "pseudonymized_profile.json"), "w", encoding="utf-8") as f:
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
            f.write(result_summary)
        
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
            f.write(f"Timestamp: {log_data['timestamp']}\n")
            f.write("\n=== INTERACTIONS ===\n\n")
            
            # Write each interaction
            for interaction in log_data['interactions']:
                f.write(f"--- Interaction at {interaction['timestamp']} ---\n")
                f.write(f"Type: {interaction['interaction_type']}\n")
                f.write(f"User Input: {interaction['user_input']}\n")
                f.write(f"System Response: {interaction['system_response']}\n")
                
                # Write metadata if available
                if 'metadata' in interaction:
                    f.write("Metadata:\n")
                    for key, value in interaction['metadata'].items():
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
            "timestamp": self.session_id.split("_", 1)[0]
        }

# Create a singleton instance
session_manager = None

def get_session_manager():
    """Get or create the session manager instance.
    
    Returns:
        SessionManager: The session manager instance
    """
    global session_manager
    if session_manager is None:
        session_manager = SessionManager()
    return session_manager