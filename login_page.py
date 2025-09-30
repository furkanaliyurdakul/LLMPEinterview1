# SPDX-License-Identifier: MIT
"""Login page for the AI Learning Platform.

Provides secure authentication interface and session management.
"""

from __future__ import annotations

import streamlit as st
from authentication import get_auth_manager, CredentialConfig
from config import config


def show_login_page() -> bool:
    """
    Display login page and handle authentication.
    
    Returns:
        True if user successfully authenticated, False otherwise
    """
    auth_manager = get_auth_manager()
    
    # Page configuration
    st.set_page_config(
        page_title=f"{config.platform.platform_name} - Login",
        page_icon="�",
        layout="wide"
    )
    
    # Header
    st.title(f"{config.platform.platform_name}")
    st.markdown("---")
    
    # Main login interface
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.header("Secure Access")
        st.markdown("""
        Welcome to the **{config.platform.platform_name}** research study.
        
        Please enter your assigned credentials to access the platform.
        
        **For study participants:**
        - Use the username and password provided by the research team
        - Your session will be automatically configured for your assigned study condition
        
        **For research team members:**
        - Use your development or demo credentials
        - Additional configuration options will be available
        """)
        
        # Login form
        with st.form("login_form", clear_on_submit=False):
            st.subheader("Login Credentials")
            
            username = st.text_input(
                "Username",
                placeholder="Enter your assigned username",
                help="Use the exact username provided to you"
            )
            
            password = st.text_input(
                "Password", 
                type="password",
                placeholder="Enter your password",
                help="Passwords are case-sensitive"
            )
            
            login_button = st.form_submit_button(
                "Access Platform",
                use_container_width=True,
                type="primary"
            )
            
            if login_button:
                if not username or not password:
                    st.error("❌ Please enter both username and password")
                else:
                    # Attempt authentication
                    with st.spinner("Verifying credentials..."):
                        credential_config = auth_manager.authenticate(username, password)
                        
                        if credential_config:
                            # Successful authentication
                            st.session_state["authenticated"] = True
                            st.session_state["credential_config"] = credential_config
                            
                            # Set study condition based on credentials
                            condition_override = auth_manager.get_study_condition_override()
                            if condition_override is not None:
                                st.session_state["use_personalisation"] = condition_override
                                st.session_state["condition_chosen"] = True
                            
                            # Configure special modes
                            st.session_state["dev_mode"] = credential_config.dev_mode
                            st.session_state["fast_test_mode"] = credential_config.fast_test_mode
                            
                            st.success(f"✅ Authentication successful! Welcome, {credential_config.description}")
                            st.info("🔄 Redirecting to platform...")
                            
                            # Force page refresh to load main application
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password. Please check your credentials and try again.")
    
    # Information panels
    st.markdown("---")
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.subheader("Study Information")
        st.markdown("""
        **Research Focus:**  
        Investigating the effectiveness of AI-generated personalized learning explanations for {config.course.subject_area.lower()} education.
        
        **Your Role:**  
        - Complete all platform components in sequence
        - Provide honest responses to all questions  
        - Engage with the learning materials naturally
        
        **Duration:** Approximately 60 minutes
        """)
    
    with col_info2:
        st.subheader("🔒 Privacy & Security")
        st.markdown("""
        **Data Protection:**  
        - All responses are pseudonymized
        - Data used only for academic research
        - GDPR compliant data handling
        
        **Session Security:**  
        - Automatic logout after session completion
        - Secure credential verification
        - Encrypted data transmission
        """)
    
    # Development information (only show for development)
    if st.secrets.get("environment", "production") == "development":
        st.markdown("---")
        with st.expander("🔧 Development Information", expanded=False):
            st.subheader("Available Credentials (Development Mode)")
            
            credentials_info = auth_manager.get_available_usernames()
            
            # Organize by type
            participant_creds = [(k, v) for k, v in credentials_info.items() if k.startswith(('personalised_', 'generic_'))]
            dev_creds = [(k, v) for k, v in credentials_info.items() if k.startswith(('dev_', 'fast_', 'admin_'))]
            
            col_dev1, col_dev2 = st.columns(2)
            
            with col_dev1:
                st.markdown("**Study Participant Credentials:**")
                for username, description in participant_creds:
                    st.code(f"{username} - {description}")
            
            with col_dev2:
                st.markdown("**Research Team Credentials:**")
                for username, description in dev_creds:
                    st.code(f"{username} - {description}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        <small>
        {config.platform.platform_name} | {config.platform.study_organization} Research Study {config.platform.study_year}<br>
        For technical support, contact the research team
        </small>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    return auth_manager.is_authenticated()


def show_logout_interface() -> None:
    """Show logout option in sidebar for authenticated users."""
    auth_manager = get_auth_manager()
    config = auth_manager.get_current_config()
    
    if config:
        st.sidebar.markdown("---")
        st.sidebar.subheader("👤 Session Info")
        st.sidebar.info(f"**User:** {config.description}")
        st.sidebar.info(f"**Mode:** {config.study_condition.title()}")
        
        if config.dev_mode:
            st.sidebar.warning("🔧 Development Mode Active")
        if config.fast_test_mode:
            st.sidebar.info("⚡ Fast Test Mode Active")
        
        if st.sidebar.button("🚪 Logout", type="secondary"):
            auth_manager.logout()
            st.rerun()


def require_authentication() -> CredentialConfig:
    """
    Require authentication and return current config.
    
    If not authenticated, shows login page and stops execution.
    If authenticated, returns the current credential configuration.
    """
    auth_manager = get_auth_manager()
    
    if not auth_manager.is_authenticated():
        # Show login page and stop execution
        show_login_page()
        st.stop()
    
    # Add logout interface to sidebar
    show_logout_interface()
    
    return auth_manager.get_current_config()