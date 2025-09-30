#!/usr/bin/env python3
"""
Quick Supabase test script - run this anytime to check if uploads will work.

Usage:
    python test_supabase.py

This will test:
- Supabase connection
- Bucket existence/creation
- Upload capability
"""

import sys
import os
from pathlib import Path

# Add project directory to path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set up a mock streamlit secrets for testing
class MockSecrets:
    def __init__(self):
        self.secrets = {
            "supabase": {
                "url": "https://bbnmgwiiyvnksftwxxuc.supabase.co",
                "service_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJibm1nd2lpeXZua3NmdHd4eHVjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTE2OTE4MCwiZXhwIjoyMDc0NzQ1MTgwfQ.Fx8W2cqMp-whkaT5aq9BSx3GcCZMlayCjy9wSLS0bGM"
            }
        }
    
    def __getitem__(self, key):
        return self.secrets[key]

# Mock streamlit
class MockStreamlit:
    def __init__(self):
        self.secrets = MockSecrets()
    
    def error(self, msg):
        print(f"ERROR: {msg}")
    
    def success(self, msg):
        print(f"SUCCESS: {msg}")

# Replace streamlit with mock
sys.modules['streamlit'] = MockStreamlit()
import streamlit as st

def main():
    print("🚀 Testing Supabase Upload Configuration...")
    print("-" * 50)
    
    try:
        from supabase_storage import SupabaseStorage
        
        # Create storage instance
        storage = SupabaseStorage()
        
        # Run manual test
        success = storage.manual_test()
        
        if success:
            print("\n🎉 All tests passed! Uploads should work.")
            return 0
        else:
            print("\n❌ Tests failed. Check the errors above.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\nTest completed with exit code: {exit_code}")
    sys.exit(exit_code)