# SPDX-License-Identifier: MIT
"""Centralized configuration for the AI Learning Platform.

This module contains all configurable text, course information, and platform settings.
Modify these variables to adapt the platform for different courses or studies.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CourseConfig:
    """Configuration for the current course/study topic."""
    
    # Core course information
    course_title: str = "Introduction to Cancer Biology"
    course_short_name: str = "Cancer Biology"  # Used in shorter contexts
    subject_area: str = "Biology"  # General subject area
    
    # File and content references
    transcription_filename: str = "turbo_transcription_Introduction to Cancer Biology.txt"
    video_filename: str = "Introduction to Cancer Biology.mp4"
    slides_directory: str = "fixed"  # Subdirectory in uploads/ppt/
    
    # Study-specific settings
    total_slides: int = 27  # Expected number of slides
    session_duration_minutes: int = 60  # Expected session duration


@dataclass  
class PlatformConfig:
    """Configuration for platform text and interface."""
    
    # Platform branding
    platform_name: str = "AI Learning Platform"
    platform_subtitle: str = "Personalized Learning Experience"
    
    # Study information
    study_title: str = "AI-Generated Personalized Learning Study"
    study_organization: str = "KU Leuven"
    study_year: str = "2025"
    
    # Interface labels
    learning_section_name: str = "Learning Experience"  # Used in navigation
    explanation_generator_title: str = "Explanation Generator"
    
    # Session components
    session_components: List[str] = None
    
    def __post_init__(self):
        if self.session_components is None:
            self.session_components = [
                "Student Profile Survey",
                self.learning_section_name,
                "Knowledge Assessment", 
                "User Experience Questionnaire"
            ]


@dataclass
class UITextConfig:
    """Configuration for all user-facing text and messages."""
    
    # Welcome and introduction text
    welcome_title: str = "🎓 {platform_name}"
    welcome_subtitle: str = "Welcome – what this session is about"
    
    study_description: str = (
        "You are taking part in our {study_organization} study on **AI‑generated, "
        "personalized learning explanations**. We are studying whether tailoring "
        "explanations to a learner's background affects their understanding of the "
        "material compared to providing general explanations."
    )
    
    session_topic_intro: str = "In today's session, it will be about **{course_title}**."
    
    # Navigation and progress text
    nav_home: str = "🏠 Home"
    nav_profile: str = "Student Profile Survey"
    nav_learning: str = "{learning_section_name}"
    nav_knowledge: str = "Knowledge Test"
    nav_ueq: str = "User Experience Survey"
    
    # Content status messages
    content_loaded_slides: str = "✅ {total_slides} slides loaded"
    content_loaded_transcription: str = "✅ Transcription loaded"
    content_loaded_profile: str = "✅ Student profile loaded"
    
    content_info_box: str = (
        "📚 **{course_title}**\\n\\n"
        "Using pre-loaded course materials:\\n"
        "- {total_slides} lecture slides\\n" 
        "- Complete audio transcription"
    )
    
    # Study steps and instructions
    steps_table_header: str = "What will happen? – step by step"
    start_instruction: str = 'When you are ready, click **"Start the Student Profile Survey"** below.'
    completion_thanks: str = "Thank you for helping us improve adaptive learning experiences!"
    
    # Study role and data info
    your_role_text: str = (
        "* Work through the steps **in the order shown** (use the sidebar).\\n"
        "* Give honest answers – there are no right or wrong responses.\\n"
        "* **Ask questions any time** – just speak to the facilitator."
    )
    
    data_recording_text: str = (
        "We log your inputs and the system's responses to analyse the tutor's effectiveness.\\n"
        "Your name is replaced by a random code; you may stop at any moment without penalty."
    )
    
    # Completion and progress messages
    completion_title: str = "🎉 Interview Complete!"
    completion_description: str = (
        "You have successfully completed all components of the {course_short_name} "
        "learning interview"
    )
    
    # Error and warning messages
    warning_complete_profile: str = "Please complete the Student Profile Survey first."
    warning_complete_learning: str = "Please complete the {learning_section_name} section first."
    warning_complete_knowledge: str = "Please complete the Knowledge Test first."
    warning_complete_all: str = "Please complete all interview components first."


@dataclass
class AuthConfig:
    """Configuration for authentication and security text."""
    
    # Login page text
    login_title: str = "🔬 {platform_name}"
    login_subtitle: str = "🔐 Secure Access"
    
    login_description: str = (
        "Welcome to the **{platform_name}** research study.\\n\\n"
        "Please enter your assigned credentials to access the platform."
    )
    
    # Credential organization
    password_salt: str = "ai_learning_study_2025"  # Used for password hashing
    
    # Session security
    session_timeout_message: str = "Session expired. Please log in again."
    logout_success_message: str = "Successfully logged out. Thank you for participating!"


class Config:
    """Main configuration class that combines all config sections."""
    
    def __init__(self):
        self.course = CourseConfig()
        self.platform = PlatformConfig() 
        self.ui_text = UITextConfig()
        self.auth = AuthConfig()
        
        # Apply course configuration to platform settings
        self._apply_course_config()
    
    def _apply_course_config(self):
        """Apply course-specific settings to other configuration sections."""
        # Update UI text with course information
        for attr_name in dir(self.ui_text):
            if not attr_name.startswith('_'):
                attr_value = getattr(self.ui_text, attr_name)
                if isinstance(attr_value, str) and '{' in attr_value:
                    try:
                        formatted_value = attr_value.format(
                            platform_name=self.platform.platform_name,
                            course_title=self.course.course_title,
                            course_short_name=self.course.course_short_name,
                            study_organization=self.platform.study_organization,
                            learning_section_name=self.platform.learning_section_name,
                            total_slides=self.course.total_slides,
                            **self.__dict__
                        )
                        setattr(self.ui_text, attr_name, formatted_value)
                    except (KeyError, ValueError):
                        # If formatting fails, keep original text
                        pass
    
    def get_course_display_name(self, context: str = "full") -> str:
        """Get appropriate course name for different contexts."""
        if context == "full":
            return self.course.course_title
        elif context == "short":
            return self.course.course_short_name
        elif context == "subject":
            return self.course.subject_area
        else:
            return self.course.course_title
    
    def get_file_paths(self) -> Dict[str, str]:
        """Get standardized file paths for course content."""
        return {
            "transcription": f"transcriptions/{self.course.transcription_filename}",
            "video": f"uploads/video/{self.course.video_filename}",
            "slides_dir": f"uploads/ppt/{self.course.slides_directory}/picture"
        }
    
    def update_course(self, **kwargs) -> None:
        """Update course configuration dynamically."""
        for key, value in kwargs.items():
            if hasattr(self.course, key):
                setattr(self.course, key, value)
        
        # Reapply configuration after updates
        self._apply_course_config()


# Global configuration instance
_config_instance = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


# Quick access functions for common use cases
def get_course_title(context: str = "full") -> str:
    """Get course title in specified context."""
    return get_config().get_course_display_name(context)

def get_platform_name() -> str:
    """Get platform name."""
    return get_config().platform.platform_name

def get_ui_text(text_key: str) -> str:
    """Get UI text by key."""
    return getattr(get_config().ui_text, text_key, text_key)

def get_file_path(file_type: str) -> str:
    """Get file path by type."""
    return get_config().get_file_paths().get(file_type, "")


# Example usage and easy course switching
def switch_to_machine_learning():
    """Example: Switch platform to Machine Learning course."""
    config = get_config()
    config.update_course(
        course_title="Introduction to Machine Learning",
        course_short_name="Machine Learning", 
        subject_area="Computer Science",
        transcription_filename="turbo_transcription_Introduction to Machine Learning.txt",
        video_filename="Introduction to Machine Learning.mp4",
        total_slides=30
    )

def switch_to_physics():
    """Example: Switch platform to Physics course."""
    config = get_config()
    config.update_course(
        course_title="Quantum Physics Fundamentals",
        course_short_name="Quantum Physics",
        subject_area="Physics", 
        transcription_filename="turbo_transcription_Quantum Physics Fundamentals.txt",
        video_filename="Quantum Physics Fundamentals.mp4",
        total_slides=25
    )


# Global configuration instance
config = get_config()