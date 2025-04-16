import os
import sys
import json
from session_manager import get_session_manager
from personalized_learning_logger import get_learning_logger

def test_session_manager():
    """Test the session manager functionality."""
    print("Testing Session Manager...")
    
    # Get the session manager
    session_manager = get_session_manager()
    
    # Get session info
    session_info = session_manager.get_session_info()
    print(f"Session ID: {session_info['session_id']}")
    print(f"Fake Name: {session_info['fake_name']}")
    print(f"Session Directory: {session_info['session_dir']}")
    
    # Test saving a profile
    test_profile = {
        "name": "Test User",
        "age": "25",
        "education_level": "Master's Degree",
        "major": "Computer Science",
        "work_exp": "2 years",
        "hobbies": "Reading, Coding",
        "strongest_subject": "Programming",
        "challenging_subject": "Statistics",
        "proficiency_level": "Intermediate"
    }
    
    profile_path = session_manager.save_profile(test_profile, "Test User")
    print(f"Profile saved to: {profile_path}")
    
    # Test saving knowledge test results
    test_results = "Test results for knowledge test\nScore: 4/5"
    results_path = session_manager.save_knowledge_test_results(test_results)
    print(f"Knowledge test results saved to: {results_path}")
    
    # Test saving UEQ responses
    test_ueq = "UEQ responses for the test\nQ1: 5\nQ2: 4"
    ueq_path = session_manager.save_ueq_responses(test_ueq)
    print(f"UEQ responses saved to: {ueq_path}")
    
    # Test learning logger
    learning_logger = get_learning_logger()
    learning_logger.log_interaction(
        interaction_type="test",
        user_input="Test question",
        system_response="Test answer",
        metadata={"test": True}
    )
    log_path = learning_logger.save_logs()
    print(f"Learning logs saved to: {log_path}")
    
    # Verify directory structure
    print("\nVerifying directory structure:")
    session_dir = session_info['session_dir']
    
    expected_dirs = [
        os.path.join(session_dir, "profile"),
        os.path.join(session_dir, "knowledge_test"),
        os.path.join(session_dir, "learning_logs"),
        os.path.join(session_dir, "ueq")
    ]
    
    for directory in expected_dirs:
        if os.path.exists(directory):
            print(f"✓ {directory} exists")
        else:
            print(f"✗ {directory} does not exist")
    
    # Verify files
    print("\nVerifying files:")
    expected_files = [
        os.path.join(session_dir, "profile", "original_profile.txt"),
        os.path.join(session_dir, "profile", "pseudonymized_profile.txt"),
        os.path.join(session_dir, "knowledge_test", "knowledge_test_results.txt"),
        os.path.join(session_dir, "ueq", "ueq_responses.txt")
    ]
    
    for file in expected_files:
        if os.path.exists(file):
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} does not exist")

if __name__ == "__main__":
    test_session_manager()