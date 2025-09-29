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
    
    def test_connection(self) -> bool:
        """Test Supabase connection and bucket access."""
        if not self.connected:
            return False
            
        try:
            # Test bucket access
            bucket_list = self.supabase.storage.list_buckets()
            bucket_exists = any(bucket.name == self.bucket_name for bucket in bucket_list)
            
            if not bucket_exists:
                st.error(f"Bucket '{self.bucket_name}' not found")
                return False
                
            # Test upload
            test_path = f"connection_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            test_result = self.supabase.storage.from_(self.bucket_name).upload(
                path=test_path,
                file=b"Connection test",
                file_options={"content-type": "text/plain"}
            )
            
            if hasattr(test_result, 'error') and test_result.error:
                st.error(f"Upload test failed: {test_result.error}")
                return False
                
            # Clean up test file
            self.supabase.storage.from_(self.bucket_name).remove([test_path])
            return True
            
        except Exception as e:
            st.error(f"Connection test failed: {e}")
            return False
    
    def upload_session_files(self, session_manager) -> bool:
        """Upload all local session files to Supabase Storage, maintaining original structure."""
        if not self.connected:
            st.error("Supabase not connected - cannot save data")
            return False
            
        try:
            # Test connection and bucket access
            if not self.test_connection():
                st.error("Supabase connection test failed - uploads will not work")
                return False
                
            session_info = session_manager.get_session_info()
            session_id = session_info["session_id"]
            session_dir = Path(session_manager.session_dir)
            
            if not session_dir.exists():
                st.error(f"Session directory not found: {session_dir}")
                return False
            
            uploaded_files = []
            failed_uploads = []
            debug_info = []
            
            # Walk through all files in the session directory
            for file_path in session_dir.rglob("*"):
                if file_path.is_file():
                    # Calculate relative path from session directory
                    relative_path = file_path.relative_to(session_dir)
                    
                    # Create Supabase path: sessions/{session_id}/{relative_path}
                    # Convert Windows paths to forward slashes for Supabase
                    supabase_path = f"sessions/{session_id}/{relative_path}".replace("\\", "/")
                    
                    # Get file size for debugging
                    file_size = file_path.stat().st_size
                    debug_info.append(f"{relative_path}: {file_size} bytes")
                    
                    # Check file size (Supabase has limits)
                    if file_size > 50 * 1024 * 1024:  # 50MB limit
                        failed_uploads.append(f"{relative_path}: File too large ({file_size} bytes > 50MB)")
                        continue
                    
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
                        try:
                            # Try upload first
                            result = self.supabase.storage.from_(self.bucket_name).upload(
                                path=supabase_path,
                                file=file_data,
                                file_options={"content-type": content_type}
                            )
                            
                            # If upload fails due to file existing, try update instead
                            if hasattr(result, 'error') and result.error and "already exists" in str(result.error):
                                result = self.supabase.storage.from_(self.bucket_name).update(
                                    path=supabase_path,
                                    file=file_data,
                                    file_options={"content-type": content_type}
                                )
                            
                            if hasattr(result, 'error') and result.error:
                                error_msg = str(result.error)
                                failed_uploads.append(f"{relative_path}: {error_msg}")
                            else:
                                uploaded_files.append(str(relative_path))
                                
                        except Exception as upload_e:
                            failed_uploads.append(f"{relative_path}: Upload exception - {str(upload_e)}")
                            
                    except Exception as file_e:
                        failed_uploads.append(f"{relative_path}: File read error - {str(file_e)}")
            
            # Report results
            st.info(f"📊 Processing complete: {len(uploaded_files)} uploaded, {len(failed_uploads)} failed")
            
            if debug_info:
                with st.expander(f"🔍 Debug: File processing details ({len(debug_info)} files)"):
                    for info in debug_info:
                        st.text(info)
            
            if uploaded_files:
                st.success(f"🎉 Successfully uploaded {len(uploaded_files)} files to cloud storage!")
                st.success("✅ All session data has been preserved for research analysis.")
                st.info(f"Session ID: {session_id}")
                
                # Show uploaded files in expander
                with st.expander(f"📁 View uploaded files ({len(uploaded_files)} files)"):
                    for file_name in sorted(uploaded_files):
                        st.text(f"✅ {file_name}")
            
            if failed_uploads:
                st.error(f"⚠️ {len(failed_uploads)} files failed to upload:")
                with st.expander("❌ View failed uploads (click to expand)"):
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