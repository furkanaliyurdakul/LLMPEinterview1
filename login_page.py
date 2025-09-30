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
        Welcome to the platform.
        
        Please enter your credentials to access the system.
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
                    st.error("Please enter both username and password")
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
                            
                            st.success(f"Authentication successful! Welcome.")
                            st.info("Redirecting to platform...")
                            
                            # Force page refresh to load main application
                            st.rerun()
                        else:
                            st.error("Invalid username or password. Please check your credentials and try again.")
                            
                            # Show debug information if available
                            if "auth_debug" in st.session_state and st.session_state.auth_debug:
                                with st.expander("🔍 Debug Information (for development)", expanded=False):
                                    for debug_line in st.session_state.auth_debug[-20:]:  # Show last 20 lines
                                        st.code(debug_line, language=None)
                                    if st.button("Clear Debug Log"):
                                        st.session_state.auth_debug = []
                                        st.rerun()
    
    # Information panels
    st.markdown("---")
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.subheader("Platform Information")
        st.markdown("""
        **Usage Instructions:**  
        - Complete all platform components in sequence
        - Follow the navigation steps provided
        - Use the menu on the left to navigate
        """)
    
    with col_info2:
        st.subheader("Privacy & Security")
        st.markdown("""
        **Data Protection:**  
        - Secure data handling
        - Privacy-compliant processing
        
        **Session Security:**  
        - Secure login verification
        - Automatic session management
        """)
    

    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        <small>
        Learning Platform | 2025
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
        # Only show session info for non-participant users
        if config.username not in ["participant1", "participant2"]:
            st.sidebar.markdown("---")
            st.sidebar.subheader("Session Info")
            st.sidebar.info(f"**User:** {config.description}")
            st.sidebar.info(f"**Mode:** {config.study_condition.title()}")
            
            if config.dev_mode:
                st.sidebar.warning("Development Mode Active")
            if config.fast_test_mode:
                st.sidebar.info("Fast Test Mode Active")
        
        if st.sidebar.button("Logout", type="secondary"):
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