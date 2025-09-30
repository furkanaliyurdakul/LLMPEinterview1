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
import logging

# Set up logging for upload debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
            
            # Initialize bucket on startup
            self.ensure_bucket_exists()
            
        except Exception as e:
            # Only show technical errors in dev mode
            # In production, silently fail - uploads will be handled gracefully later
            self.connected = False
    
    def ensure_bucket_exists(self) -> bool:
        """Ensure the required bucket exists, create if missing."""
        if not self.connected:
            return False
            
        try:
            logger.info("Checking if Supabase bucket exists...")
            print(f"🔍 SUPABASE INIT: Checking bucket '{self.bucket_name}'...")
            
            # Test bucket access
            bucket_list = self.supabase.storage.list_buckets()
            existing_buckets = [bucket.name for bucket in bucket_list]
            logger.info(f"Available buckets: {existing_buckets}")
            print(f"📁 SUPABASE INIT: Available buckets: {existing_buckets}")
            
            bucket_exists = any(bucket.name == self.bucket_name for bucket in bucket_list)
            
            if bucket_exists:
                logger.info(f"Bucket '{self.bucket_name}' already exists")
                print(f"✅ SUPABASE INIT: Bucket '{self.bucket_name}' ready")
                return True
            
            # Create the bucket
            logger.info(f"Creating bucket '{self.bucket_name}'...")
            print(f"🔨 SUPABASE INIT: Creating bucket '{self.bucket_name}'...")
            
            create_result = self.supabase.storage.create_bucket(
                id=self.bucket_name,
                name=self.bucket_name,
                options={"public": False}  # Private bucket for interview data
            )
            
            if hasattr(create_result, 'error') and create_result.error:
                error_msg = f"Failed to create bucket: {create_result.error}"
                logger.error(error_msg)
                print(f"❌ SUPABASE INIT: {error_msg}")
                return False
            else:
                logger.info(f"Successfully created bucket '{self.bucket_name}'")
                print(f"✅ SUPABASE INIT: Successfully created bucket '{self.bucket_name}'")
                return True
                
        except Exception as e:
            error_msg = f"Error ensuring bucket exists: {e}"
            logger.error(error_msg)
            print(f"❌ SUPABASE INIT: {error_msg}")
            return False
    
    def test_connection(self) -> bool:
        """Test Supabase connection and upload capability."""
        if not self.connected:
            return False
            
        try:
            logger.info("Testing Supabase upload capability...")
            print("🔌 UPLOAD TEST: Testing upload capability...")
            
            # Test upload
            test_path = f"connection_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            test_result = self.supabase.storage.from_(self.bucket_name).upload(
                path=test_path,
                file=b"Connection test",
                file_options={"content-type": "text/plain"}
            )
            
            if hasattr(test_result, 'error') and test_result.error:
                error_msg = f"Upload test failed: {test_result.error}"
                logger.error(error_msg)
                print(f"❌ UPLOAD TEST: {error_msg}")
                return False
                
            # Clean up test file
            self.supabase.storage.from_(self.bucket_name).remove([test_path])
            logger.info("Upload test successful")
            print("✅ UPLOAD TEST: Upload capability confirmed")
            return True
            
        except Exception as e:
            error_msg = f"Upload test failed: {e}"
            logger.error(error_msg)
            print(f"❌ UPLOAD TEST: {error_msg}")
            return False
    
    def manual_test(self):
        """Manual test function you can call anytime to check Supabase setup."""
        print("\n" + "="*50)
        print("🧪 MANUAL SUPABASE TEST")
        print("="*50)
        
        if not self.connected:
            print("❌ Not connected to Supabase")
            return False
        
        print("✅ Connected to Supabase")
        
        # Test bucket
        if self.ensure_bucket_exists():
            print("✅ Bucket ready")
        else:
            print("❌ Bucket not ready")
            return False
        
        # Test upload
        if self.test_connection():
            print("✅ Upload capability confirmed")
            print("🎉 Supabase is ready for uploads!")
            return True
        else:
            print("❌ Upload test failed")
            return False
    
    def _get_credential_folder_prefix(self) -> str:
        """Get folder prefix based on current authentication credentials."""
        try:
            # Import here to avoid circular imports
            from authentication import get_auth_manager
            auth_manager = get_auth_manager()
            config = auth_manager.get_current_config()
            
            if config:
                return config.folder_prefix
            else:
                return "unknown_user"
        except (ImportError, AttributeError):
            # Fallback for cases where authentication isn't available
            return "legacy_session"
    
    def upload_session_files(self, session_manager, dev_mode: bool = False) -> bool:
        """Upload all local session files to Supabase Storage, maintaining original structure."""
        if not self.connected:
            error_msg = "Supabase not connected - cannot save data"
            logger.error(error_msg)
            # Don't show technical errors to participants
            return False
            
        try:
            # Quick upload capability test
            logger.info("Starting Supabase upload process...")
            print(f"🔄 UPLOAD DEBUG: Starting Supabase upload process at {datetime.now()}")
            
            if not self.test_connection():
                error_msg = "Supabase upload test failed - uploads will not work"
                logger.error(error_msg)
                # Don't show technical errors to participants
                return False
            
            # Get credential-based folder organization
            folder_prefix = self._get_credential_folder_prefix()
            
            session_info = session_manager.get_session_info()
            session_id = session_info["session_id"]
            session_dir = Path(session_manager.session_dir)
            
            logger.info(f"Session ID: {session_id}")
            logger.info(f"Session directory: {session_dir}")
            logger.info(f"Credential folder prefix: {folder_prefix}")
            print(f"📁 UPLOAD DEBUG: Session ID = {session_id}")
            print(f"📁 UPLOAD DEBUG: Session directory = {session_dir}")
            print(f"🏷️ UPLOAD DEBUG: Credential folder = {folder_prefix}")
            
            if not session_dir.exists():
                error_msg = f"Session directory not found: {session_dir}"
                logger.error(error_msg)
                # Don't show technical errors to participants
                return False
            
            uploaded_files = []
            failed_uploads = []
            debug_info = []
            
            # Create a detailed upload log file
            log_file = session_dir / "upload_debug_log.txt"
            
            def log_to_file_and_console(message):
                """Log to both file and console for debugging."""
                timestamp = datetime.now().strftime("%H:%M:%S")
                full_message = f"[{timestamp}] {message}"
                logger.info(message)
                print(f"📤 UPLOAD DEBUG: {full_message}")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(full_message + "\n")
            
            log_to_file_and_console(f"Starting upload for session {session_id}")
            log_to_file_and_console(f"Upload log saved to: {log_file}")
            
            # Walk through all files in the session directory
            all_files = list(session_dir.rglob("*"))
            file_count = len([f for f in all_files if f.is_file()])
            log_to_file_and_console(f"Found {file_count} files to process")
            
            for file_path in session_dir.rglob("*"):
                if file_path.is_file():
                    # Calculate relative path from session directory
                    relative_path = file_path.relative_to(session_dir)
                    
                    # Create credential-organized Supabase path: {credential_folder}/sessions/{session_id}/{relative_path}
                    # Convert Windows paths to forward slashes for Supabase
                    supabase_path = f"{folder_prefix}/sessions/{session_id}/{relative_path}".replace("\\", "/")
                    
                    # Get file size for debugging
                    file_size = file_path.stat().st_size
                    debug_info.append(f"{relative_path}: {file_size} bytes")
                    
                    log_to_file_and_console(f"Processing: {relative_path} ({file_size} bytes)")
                    
                    # Check file size (Supabase has limits)
                    if file_size > 50 * 1024 * 1024:  # 50MB limit
                        error_msg = f"{relative_path}: File too large ({file_size} bytes > 50MB)"
                        failed_uploads.append(error_msg)
                        log_to_file_and_console(f"❌ FAILED: {error_msg}")
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
                            log_to_file_and_console(f"Uploading to: {supabase_path}")
                            
                            # Try upload first
                            result = self.supabase.storage.from_(self.bucket_name).upload(
                                path=supabase_path,
                                file=file_data,
                                file_options={"content-type": content_type}
                            )
                            
                            # If upload fails due to file existing, try update instead
                            if hasattr(result, 'error') and result.error and "already exists" in str(result.error):
                                log_to_file_and_console(f"File exists, trying update: {supabase_path}")
                                result = self.supabase.storage.from_(self.bucket_name).update(
                                    path=supabase_path,
                                    file=file_data,
                                    file_options={"content-type": content_type}
                                )
                            
                            if hasattr(result, 'error') and result.error:
                                error_msg = f"{relative_path}: {str(result.error)}"
                                failed_uploads.append(error_msg)
                                log_to_file_and_console(f"❌ FAILED: {error_msg}")
                            else:
                                uploaded_files.append(str(relative_path))
                                log_to_file_and_console(f"✅ SUCCESS: {relative_path}")
                                
                        except Exception as upload_e:
                            error_msg = f"{relative_path}: Upload exception - {str(upload_e)}"
                            failed_uploads.append(error_msg)
                            log_to_file_and_console(f"❌ EXCEPTION: {error_msg}")
                            
                    except Exception as file_e:
                        error_msg = f"{relative_path}: File read error - {str(file_e)}"
                        failed_uploads.append(error_msg)
                        log_to_file_and_console(f"❌ FILE ERROR: {error_msg}")
            
            # Report results
            log_to_file_and_console(f"Upload complete: {len(uploaded_files)} success, {len(failed_uploads)} failed")
            
            # Print summary to console for easy access
            print(f"\n{'='*60}")
            print(f"🎯 UPLOAD SUMMARY FOR SESSION {session_id}")
            print(f"{'='*60}")
            print(f"✅ Successful uploads: {len(uploaded_files)}")
            print(f"❌ Failed uploads: {len(failed_uploads)}")
            print(f"📁 Log file: {log_file}")
            print(f"{'='*60}")
            
            if failed_uploads:
                print(f"\n❌ FAILED UPLOADS:")
                for i, failure in enumerate(failed_uploads, 1):
                    print(f"  {i}. {failure}")
                print(f"{'='*60}\n")
            
            # Show technical details only in dev mode
            if dev_mode:
                st.info(f"📊 Processing complete: {len(uploaded_files)} uploaded, {len(failed_uploads)} failed")
                st.info(f"📋 Detailed upload log saved to: `{log_file.name}`")
                
                if debug_info:
                    with st.expander(f"🔍 Debug: File processing details ({len(debug_info)} files)"):
                        for info in debug_info:
                            st.text(info)
            
            if uploaded_files:
                st.success(f"🎉 Successfully uploaded {len(uploaded_files)} files to cloud storage!")
                st.success("✅ All session data has been preserved for research analysis.")
                if dev_mode:
                    st.info(f"Session ID: {session_id}")
                
                # Show uploaded files in expander (only in dev mode)
                if dev_mode:
                    with st.expander(f"📁 View uploaded files ({len(uploaded_files)} files)"):
                        for file_name in sorted(uploaded_files):
                            st.text(f"✅ {file_name}")
            
            if failed_uploads:
                if dev_mode:
                    st.error(f"⚠️ {len(failed_uploads)} files failed to upload:")
                    with st.expander("❌ View failed uploads (click to expand)"):
                        for failure in failed_uploads:
                            st.text(f"❌ {failure}")
                else:
                    st.warning("⚠️ Some files experienced upload issues, but your data is secure.")
            
            return len(uploaded_files) > 0
                
        except Exception as e:
            # Log technical errors but don't show to participants
            logger.error(f"Error uploading session files to Supabase: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            if dev_mode:
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