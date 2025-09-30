# SPDX-License-Identifier: MIT
"""Authentication system for the AI Learning Platform.

Manages secure login with different credential types for study participants
and research team members. Organizes data collection by credential type.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from typing import Dict, Optional
import streamlit as st


@dataclass
class CredentialConfig:
    """Configuration for a specific credential type."""
    username: str
    password_hash: str
    study_condition: str  # "personalised", "generic", "dev", "fast_test", "dev_fast_test"
    description: str
    folder_prefix: str  # for organizing data in Supabase
    dev_mode: bool = False
    fast_test_mode: bool = False
    upload_enabled: bool = False


class AuthenticationManager:
    """Manages authentication and session state for the learning platform."""
    
    def __init__(self):
        self.credentials = self._initialize_credentials()
    
    def _hash_password(self, password: str) -> str:
        """Create secure hash of password with salt."""
        salt = "cancer_biology_study_2025"  # Study-specific salt
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def _initialize_credentials(self) -> Dict[str, CredentialConfig]:
        """Initialize all available credentials for the study."""
        return {
            # Study participant credentials
            "personalised_p001": CredentialConfig(
                username="personalised_p001",
                password_hash=self._hash_password("PersonalisedCohort2025!"),
                study_condition="personalised",
                description="Personalised Learning Cohort Participant",
                folder_prefix="personalised_cohort",
                dev_mode=False,
                fast_test_mode=False,
                upload_enabled=False
            ),
            "personalised_p002": CredentialConfig(
                username="personalised_p002", 
                password_hash=self._hash_password("PersonalisedCohort2025!"),
                study_condition="personalised",
                description="Personalised Learning Cohort Participant",
                folder_prefix="personalised_cohort",
                dev_mode=False,
                fast_test_mode=False,
                upload_enabled=False
            ),
            "personalised_p003": CredentialConfig(
                username="personalised_p003",
                password_hash=self._hash_password("PersonalisedCohort2025!"),
                study_condition="personalised", 
                description="Personalised Learning Cohort Participant",
                folder_prefix="personalised_cohort",
                dev_mode=False,
                fast_test_mode=False,
                upload_enabled=False
            ),
            "generic_g001": CredentialConfig(
                username="generic_g001",
                password_hash=self._hash_password("GenericCohort2025!"),
                study_condition="generic",
                description="Generic Learning Cohort Participant", 
                folder_prefix="generic_cohort",
                dev_mode=False,
                fast_test_mode=False,
                upload_enabled=False
            ),
            "generic_g002": CredentialConfig(
                username="generic_g002",
                password_hash=self._hash_password("GenericCohort2025!"),
                study_condition="generic",
                description="Generic Learning Cohort Participant",
                folder_prefix="generic_cohort", 
                dev_mode=False,
                fast_test_mode=False,
                upload_enabled=False
            ),
            "generic_g003": CredentialConfig(
                username="generic_g003",
                password_hash=self._hash_password("GenericCohort2025!"),
                study_condition="generic",
                description="Generic Learning Cohort Participant",
                folder_prefix="generic_cohort",
                dev_mode=False,
                fast_test_mode=False,
                upload_enabled=False
            ),
            
            # Research team credentials  
            "dev_researcher": CredentialConfig(
                username="dev_researcher",
                password_hash=self._hash_password("DevMode2025Research!"),
                study_condition="personalised",  # Default for dev mode
                description="Development Mode - Full Access",
                folder_prefix="dev_testing",
                dev_mode=True,
                fast_test_mode=False,
                upload_enabled=True
            ),
            "fast_demo": CredentialConfig(
                username="fast_demo",
                password_hash=self._hash_password("FastDemo2025!"),
                study_condition="personalised",  # Default for demo
                description="Fast Test Mode - Demo Access", 
                folder_prefix="demo_testing",
                dev_mode=False,
                fast_test_mode=True,
                upload_enabled=False
            ),
            "dev_fast_test": CredentialConfig(
                username="dev_fast_test",
                password_hash=self._hash_password("DevFastTest2025!"),
                study_condition="personalised",  # Default for combined mode
                description="Development + Fast Test Mode",
                folder_prefix="dev_fast_testing",
                dev_mode=True,
                fast_test_mode=True,
                upload_enabled=True
            ),
            
            # Special admin credential
            "admin_furkan": CredentialConfig(
                username="admin_furkan",
                password_hash=self._hash_password("AdminAccess2025Furkan!"),
                study_condition="personalised",  # Default admin setting
                description="Administrator Access",
                folder_prefix="admin_testing",
                dev_mode=True,
                fast_test_mode=False,
                upload_enabled=True
            )
        }
    
    def authenticate(self, username: str, password: str) -> Optional[CredentialConfig]:
        """Authenticate user and return credential config if valid."""
        if username not in self.credentials:
            return None
        
        credential = self.credentials[username]
        password_hash = self._hash_password(password)
        
        if password_hash == credential.password_hash:
            return credential
        return None
    
    def is_authenticated(self) -> bool:
        """Check if current session has valid authentication."""
        return (
            st.session_state.get("authenticated", False) and
            st.session_state.get("credential_config") is not None
        )
    
    def get_current_config(self) -> Optional[CredentialConfig]:
        """Get current authenticated user's credential configuration."""
        if self.is_authenticated():
            return st.session_state.get("credential_config")
        return None
    
    def logout(self) -> None:
        """Clear authentication and reset session."""
        # Clear authentication state
        st.session_state["authenticated"] = False
        st.session_state["credential_config"] = None
        
        # Clear session data to prevent data leakage between users
        session_keys_to_clear = [
            "current_page", "profile_completed", "learning_completed", 
            "test_completed", "ueq_completed", "completion_processed",
            "upload_completed", "responses", "messages", "profile_text", 
            "profile_dict", "exported_images", "transcription_text",
            "selected_slide", "debug_logs", "condition_chosen",
            "use_personalisation", "consent_given", "consent_logged",
            "show_review", "gemini_chat", "_page_timer"
        ]
        
        for key in session_keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def get_study_condition_override(self) -> Optional[bool]:
        """Get study condition override for special modes.
        
        Returns:
            True for personalised, False for generic, None for user choice
        """
        config = self.get_current_config()
        if not config:
            return None
            
        # For dev modes, allow dynamic choice via sidebar
        if config.dev_mode:
            return st.sidebar.selectbox(
                "🔧 Study Condition (Dev Mode)",
                options=[True, False],
                format_func=lambda x: "Personalised" if x else "Generic",
                key="dev_condition_override"
            )
        
        # For participant credentials, use fixed condition
        return config.study_condition == "personalised"
    
    def get_available_usernames(self) -> Dict[str, str]:
        """Get list of available usernames for display purposes."""
        return {
            username: config.description 
            for username, config in self.credentials.items()
        }


# Global authentication manager instance
_auth_manager = None

def get_auth_manager() -> AuthenticationManager:
    """Get singleton authentication manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthenticationManager()
    return _auth_manager