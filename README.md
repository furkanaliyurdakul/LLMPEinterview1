# Personalized Learning Platform

## File Organization Structure

This platform uses a session-based file organization structure with pseudonymization for research purposes. Each session creates a unique directory with the following structure:

```
output/
  ├── [TIMESTAMP]_[FAKE_NAME]/  # Unique session directory
  │   ├── profile/               # Student profile data
  │   │   ├── original_profile.txt
  │   │   ├── original_profile.json
  │   │   ├── pseudonymized_profile.txt
  │   │   └── pseudonymized_profile.json
  │   ├── knowledge_test/        # Knowledge test results
  │   │   └── knowledge_test_results.txt
  │   ├── learning_logs/         # Logs of interactions with the learning tool
  │   │   └── learning_log_[TIMESTAMP].json
  │   └── ueq/                   # User Experience Questionnaire responses
  │       └── ueq_responses.txt
  └── [Other session directories...]
```

## Pseudonymization Approach

The system uses the following approach for pseudonymization:

1. When a new session starts, a unique session ID is generated using a timestamp and a randomly generated fake name.
2. The original student profile is saved with the real name and other identifying information.
3. A pseudonymized version of the profile is created by replacing the real name with the fake name.
4. All subsequent files (knowledge test results, learning logs, UEQ responses) are saved in the session directory and associated with the fake name.
5. The fake name serves as a unique identifier that links all files from the same session without revealing the student's real identity.

## Components

1. **Session Manager** (`session_manager.py`): Handles session creation, directory management, and pseudonymization.
2. **Profile Survey** (`testui_profilesurvey.py`): Collects student profile information.
3. **Personalized Learning** (`Gemini_UI.py`): Provides personalized learning experiences based on the student profile.
4. **Learning Logger** (`personalized_learning_logger.py`): Logs interactions with the personalized learning tool.
5. **Knowledge Test** (`testui_knowledgetest.py`): Assesses student knowledge after learning.
6. **UEQ Survey** (`testui_ueqsurvey.py`): Collects feedback about the user experience.
7. **Main Application** (`main.py`): Integrates all components with navigation.

## Usage

Run the main application to start a new session:

```
streamlit run main.py
```

Follow the navigation flow from Profile Survey to UEQ Survey. All data will be automatically saved in the session directory with pseudonymization.