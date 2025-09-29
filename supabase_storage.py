# SPDX-License-Identifier: MIT
"""Supabase storage integration for interview data persistence.

Uploads all original local session files to Supabase Storage at session completion,
maintaining the exact same file structure and content as stored locally.
"""

import json
import os
import streamlit as st
from datetime import datetime
from supabase import create_client
from pathlib import Path
import traceback


class SupabaseStorage:
    """Handles uploading all original local session files to Supabase Storage."""
    
    def __init__(self):
        """Initialize Supabase client with credentials from Streamlit secrets."""
        try:
            self.supabase = create_client(
                st.secrets["supabase"]["url"],
                st.secrets["supabase"]["service_key"]  # Use service key for uploads
            )
            self.bucket_name = "interview-results"
            self.connected = True
        except Exception as e:
            st.error(f"Failed to connect to Supabase: {e}")
            self.connected = False
    
    def upload_session_files(self, session_manager) -> bool:
        """Upload all local session files to Supabase Storage, maintaining original structure."""
        if not self.connected:
            st.error("Supabase not connected - cannot save data")
            return False
            
        try:
            session_info = session_manager.get_session_info()
            session_id = session_info["session_id"]
            session_dir = Path(session_manager.session_dir)
            
            if not session_dir.exists():
                st.error(f"Session directory not found: {session_dir}")
                return False
            
            uploaded_files = []
            failed_uploads = []
            
            # Walk through all files in the session directory
            for file_path in session_dir.rglob("*"):
                if file_path.is_file():
                    # Calculate relative path from session directory
                    relative_path = file_path.relative_to(session_dir)
                    
                    # Create Supabase path: sessions/{session_id}/{relative_path}
                    supabase_path = f"sessions/{session_id}/{relative_path}"
                    
                    # Read file content
                    try:
                        if file_path.suffix.lower() in ['.json', '.txt']:
                            # Text files - read as UTF-8
                            content = file_path.read_text(encoding='utf-8')
                            content_type = "application/json" if file_path.suffix.lower() == '.json' else "text/plain"
                            file_data = content.encode('utf-8')
                        else:
                            # Binary files
                            content_type = "application/octet-stream"
                            file_data = file_path.read_bytes()
                        
                        # Upload to Supabase
                        result = self.supabase.storage.from_(self.bucket_name).upload(
                            path=supabase_path,
                            file=file_data,
                            file_options={"content-type": content_type}
                        )
                        
                        if result.error:
                            failed_uploads.append(f"{relative_path}: {result.error}")
                        else:
                            uploaded_files.append(str(relative_path))
                            
                    except Exception as e:
                        failed_uploads.append(f"{relative_path}: {str(e)}")
            
            # Report results
            if uploaded_files:
                st.success(f"🎉 Successfully uploaded {len(uploaded_files)} files to cloud storage!")
                st.success("✅ All session data has been preserved for research analysis.")
                st.info(f"Session ID: {session_id}")
                
                # Show uploaded files in expander
                with st.expander(f"📁 View uploaded files ({len(uploaded_files)} files)"):
                    for file_name in sorted(uploaded_files):
                        st.text(f"✅ {file_name}")
            
            if failed_uploads:
                st.warning(f"⚠️ {len(failed_uploads)} files failed to upload:")
                with st.expander("View failed uploads"):
                    for failure in failed_uploads:
                        st.text(f"❌ {failure}")
            
            return len(uploaded_files) > 0
                
        except Exception as e:
            st.error(f"Error uploading session files to Supabase: {e}")
            st.error(f"Traceback: {traceback.format_exc()}")
            return False


# Global instance for easy access
_storage_instance = None

def get_supabase_storage() -> SupabaseStorage:
    """Get or create the Supabase storage instance."""
    global _storage_instance
    
    if _storage_instance is None:
        _storage_instance = SupabaseStorage()
    
    return _storage_instance