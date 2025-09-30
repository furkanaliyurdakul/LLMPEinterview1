# SPDX-License-Identifier: MIT
"""Test script for the authentication system.

This script tests all credential types and verifies folder organization.
Run this locally to test before deployment.
"""

from authentication import get_auth_manager
from pathlib import Path
import os

def test_authentication_system():
    """Test all aspects of the authentication system."""
    
    print("🔐 Testing Authentication System")
    print("=" * 50)
    
    auth_manager = get_auth_manager()
    
    # Test 1: Check all credentials are defined
    print("\n1️⃣ Testing credential definitions...")
    credentials = auth_manager.get_available_usernames()
    
    expected_types = [
        "personalised_p001", "personalised_p002", "personalised_p003",
        "generic_g001", "generic_g002", "generic_g003", 
        "dev_researcher", "fast_demo", "dev_fast_test", "admin_furkan"
    ]
    
    print(f"✅ Found {len(credentials)} credential types")
    for username, description in credentials.items():
        print(f"   - {username}: {description}")
    
    missing_creds = set(expected_types) - set(credentials.keys())
    if missing_creds:
        print(f"❌ Missing credentials: {missing_creds}")
    else:
        print("✅ All expected credentials present")
    
    # Test 2: Test authentication with correct credentials  
    print("\n2️⃣ Testing authentication...")
    
    test_cases = [
        ("personalised_p001", "PersonalisedCohort2025!", True),
        ("generic_g001", "GenericCohort2025!", True),
        ("dev_researcher", "DevMode2025Research!", True),
        ("fast_demo", "FastDemo2025!", True),
        ("admin_furkan", "AdminAccess2025Furkan!", True),
        ("invalid_user", "wrong_password", False),
        ("personalised_p001", "wrong_password", False),
    ]
    
    for username, password, should_succeed in test_cases:
        result = auth_manager.authenticate(username, password)
        if should_succeed and result:
            print(f"✅ {username}: Authentication successful")
            print(f"   Study condition: {result.study_condition}")
            print(f"   Folder prefix: {result.folder_prefix}")
            print(f"   Dev mode: {result.dev_mode}")
            print(f"   Fast test: {result.fast_test_mode}")
        elif not should_succeed and not result:
            print(f"✅ {username}: Authentication correctly failed")
        else:
            print(f"❌ {username}: Unexpected result")
    
    # Test 3: Test folder organization
    print("\n3️⃣ Testing folder organization...")
    
    # Test different credential types
    test_credentials = [
        ("personalised_p001", "PersonalisedCohort2025!"),
        ("generic_g001", "GenericCohort2025!"),
        ("dev_researcher", "DevMode2025Research!"),
    ]
    
    for username, password in test_credentials:
        config = auth_manager.authenticate(username, password)
        if config:
            print(f"✅ {username}:")
            print(f"   Folder prefix: {config.folder_prefix}")
            print(f"   Expected structure: output/{config.folder_prefix}/YYYYMMDD_HHMMSS_FakeName/")
    
    # Test 4: Test credential types and features
    print("\n4️⃣ Testing credential features...")
    
    feature_tests = {
        "personalised_p001": {"study_condition": "personalised", "dev_mode": False, "upload_enabled": False},
        "generic_g001": {"study_condition": "generic", "dev_mode": False, "upload_enabled": False}, 
        "dev_researcher": {"study_condition": "personalised", "dev_mode": True, "upload_enabled": True},
        "fast_demo": {"study_condition": "personalised", "fast_test_mode": True, "upload_enabled": False},
        "dev_fast_test": {"dev_mode": True, "fast_test_mode": True, "upload_enabled": True},
    }
    
    for username, expected_features in feature_tests.items():
        config = auth_manager.authenticate(username, auth_manager.credentials[username].password_hash.replace(
            auth_manager._hash_password(""), ""
        ))
        # Note: We can't easily reverse the hash, so we'll use the stored config directly
        config = auth_manager.credentials[username]
        
        print(f"✅ {username}:")
        for feature, expected_value in expected_features.items():
            actual_value = getattr(config, feature)
            status = "✅" if actual_value == expected_value else "❌"
            print(f"   {status} {feature}: {actual_value} (expected: {expected_value})")

    print("\n🎉 Authentication System Test Complete!")
    print("=" * 50)


if __name__ == "__main__":
    test_authentication_system()