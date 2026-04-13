"""
API integration tests -- tests the FastAPI action router against a live Google Sheet.
Run: python test_api.py

Requires: .env configured with valid SPREADSHEET_ID + credentials.json
"""

import sys
import os
import json
import uuid
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# ============================================================
# CONFIG
# ============================================================
BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8000")

TEST_ID = uuid.uuid4().hex[:6]
TEST_EMAIL = f"testuser_{TEST_ID}@test.com"
TEST_PASSWORD = "TestPassword123!"
TEST_NAME = f"Test User {TEST_ID}"
TEST_USERNAME = f"testuser_{TEST_ID}"


def post_action(action: str, payload: dict = {}) -> dict:
    resp = requests.post(f"{BASE_URL}/", json={"action": action, "payload": payload})
    return resp.status_code, resp.json()


def assert_success(status, body, test_name):
    if status == 200 and body.get("success"):
        print(f"  [PASS] {test_name}")
        return True
    else:
        detail = body.get("detail", body)
        print(f"  [FAIL] {test_name} -- HTTP {status}: {detail}")
        return False


def assert_fail(status, body, test_name, expected_msg=None):
    if status == 400:
        detail = body.get("detail", "")
        if expected_msg and expected_msg.lower() not in detail.lower():
            print(f"  [FAIL] {test_name} -- Expected '{expected_msg}' in '{detail}'")
            return False
        print(f"  [PASS] {test_name} (correctly rejected)")
        return True
    else:
        print(f"  [FAIL] {test_name} -- Expected 400, got HTTP {status}")
        return False


# ============================================================
# TEST SUITES
# ============================================================

def test_health():
    print("\n" + "=" * 60)
    print("TEST: Health Endpoint")
    print("=" * 60)
    resp = requests.get(f"{BASE_URL}/health")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  [PASS] Health OK -- Status: {data.get('status')}")
        stats = data.get("stats", {})
        if stats:
            print(f"     Users: {stats.get('total_users', 0)}, Active: {stats.get('active_users', 0)}")
    else:
        print(f"  [FAIL] Health failed -- HTTP {resp.status_code}")


def test_auth_flow():
    """Register -> Login -> Duplicate check -> Missing fields -> Wrong password."""
    print("\n" + "=" * 60)
    print("TEST: Authentication Flow")
    print("=" * 60)

    # Register
    s, b = post_action("register", {
        "name": TEST_NAME,
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "username": TEST_USERNAME,
    })
    assert_success(s, b, "Register new user")

    # Login
    s, b = post_action("login", {"email": TEST_EMAIL, "password": TEST_PASSWORD})
    ok = assert_success(s, b, "Login with correct credentials")
    profile = None
    if ok:
        profile = b.get("data", {})
        has_pw = "password_hash" in profile
        print(f"  [{'FAIL' if has_pw else 'PASS'}] password_hash not in response")
        print(f"     User ID: {profile.get('user_id', 'N/A')}")

    # Duplicate email
    s, b = post_action("register", {"name": "Dup", "email": TEST_EMAIL, "password": "x"})
    assert_fail(s, b, "Reject duplicate email", "already registered")

    # Missing fields
    s, b = post_action("register", {"email": TEST_EMAIL})
    assert_fail(s, b, "Reject missing fields", "required")

    # Wrong password
    s, b = post_action("login", {"email": TEST_EMAIL, "password": "wrong"})
    assert_fail(s, b, "Reject wrong password", "Invalid")

    return profile


def test_profile_updates(user_id: str):
    """Update profile, domains, locations, experience, salary."""
    print("\n" + "=" * 60)
    print("TEST: Profile & Preferences Updates")
    print("=" * 60)

    # Update domains (job titles)
    s, b = post_action("updateDomains", {
        "user_id": user_id,
        "domains": "python developer;data analyst;backend engineer",
    })
    assert_success(s, b, "Update domains (job titles)")

    # Update profile with locations + preferences
    s, b = post_action("updateUserProfile", {
        "user_id": user_id,
        "location_1": "Mumbai",
        "location_2": "Bangalore",
        "location_3": "Delhi",
        "remote_jobs": "true",
        "experience_level": "intermediate",
        "min_salary": "800000",
    })
    assert_success(s, b, "Update locations + remote + experience + salary")

    # Verify by logging in again
    s, b = post_action("login", {"email": TEST_EMAIL, "password": TEST_PASSWORD})
    if s == 200:
        profile = b.get("data", {})
        checks = [
            ("Domains set", "python developer" in profile.get("domains", "")),
            ("Location 1", profile.get("location_1") == "Mumbai"),
            ("Location 2", profile.get("location_2") == "Bangalore"),
            ("Location 3", profile.get("location_3") == "Delhi"),
            ("Remote jobs", profile.get("remote_jobs", "").lower() == "true"),
            ("Experience", profile.get("experience_level") == "intermediate"),
            ("Min salary", profile.get("min_salary") == "800000"),
        ]
        for name, passed in checks:
            print(f"  [{'PASS' if passed else 'FAIL'}] Verify: {name}")

    # Non-existent user
    s, b = post_action("updateUserProfile", {"user_id": "fake-id-000", "name": "Ghost"})
    assert_fail(s, b, "Reject update for non-existent user", "not found")


def test_toggle_and_status(user_id: str):
    """Toggle status, unsubscribe, re-activate."""
    print("\n" + "=" * 60)
    print("TEST: Status Toggle & Unsubscribe")
    print("=" * 60)

    s, b = post_action("toggleUserStatus", {"user_id": user_id, "status": "paused"})
    assert_success(s, b, "Pause user")

    s, b = post_action("toggleUserStatus", {"user_id": user_id, "status": "active"})
    assert_success(s, b, "Re-activate user")

    s, b = post_action("unsubscribeUser", {"user_id": user_id})
    assert_success(s, b, "Unsubscribe user")

    s, b = post_action("toggleUserStatus", {"user_id": user_id, "status": "active"})
    assert_success(s, b, "Re-activate after unsubscribe")


def test_admin_flow():
    """Admin login, get users, system settings, stats, audit logs."""
    print("\n" + "=" * 60)
    print("TEST: Admin Flow")
    print("=" * 60)

    from config import settings
    s, b = post_action("adminLogin", {"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD})
    assert_success(s, b, "Admin login")

    s, b = post_action("adminLogin", {"email": "wrong", "password": "wrong"})
    assert_fail(s, b, "Reject wrong admin creds", "Invalid")

    s, b = post_action("getAllUsers")
    if assert_success(s, b, "Get all users"):
        users = b.get("data", [])
        print(f"     Total users: {len(users)}")
        leaked = any("password_hash" in u for u in users)
        print(f"  [{'FAIL' if leaked else 'PASS'}] No password_hash in any user response")

    s, b = post_action("getSystemSettings")
    if assert_success(s, b, "Get system settings"):
        print(f"     Settings: {b.get('data', {})}")

    s, b = post_action("updateSystemSettings", {"key": "system_enabled", "value": True})
    assert_success(s, b, "Update system setting")

    s, b = post_action("getSystemStats")
    if assert_success(s, b, "Get system stats"):
        print(f"     Stats: {b.get('data', {})}")

    s, b = post_action("getAuditLogs", {"limit": 5})
    assert_success(s, b, "Get audit logs")


def test_active_users_for_campaign():
    """Verify getActiveUsersForEmail returns properly filtered users."""
    print("\n" + "=" * 60)
    print("TEST: Active Users for Campaign")
    print("=" * 60)

    s, b = post_action("getActiveUsersForEmail")
    if assert_success(s, b, "Get active users"):
        users = b.get("data", [])
        print(f"     Active users: {len(users)}")
        all_active = all(u.get("status") == "active" for u in users)
        no_pw = not any("password_hash" in u for u in users)
        if users:
            print(f"  [{'PASS' if all_active else 'FAIL'}] All users are active")
            print(f"  [{'PASS' if no_pw else 'FAIL'}] No password_hash leaked")


def test_unsubscribe_html():
    """Test the GET /unsubscribe endpoint returns HTML."""
    print("\n" + "=" * 60)
    print("TEST: Unsubscribe HTML Page")
    print("=" * 60)

    resp = requests.get(f"{BASE_URL}/unsubscribe?user_id=nonexistent-id-000")
    if resp.status_code == 200 and "html" in resp.headers.get("content-type", "").lower():
        print(f"  [PASS] Returns HTML (even for bad user_id)")
    else:
        print(f"  [FAIL] Expected HTML response, got {resp.status_code}")


def test_invalid_action():
    """Ensure unknown actions return 400."""
    print("\n" + "=" * 60)
    print("TEST: Invalid Action Handling")
    print("=" * 60)

    s, b = post_action("totallyFakeAction", {})
    assert_fail(s, b, "Reject unknown action", "Invalid action")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  JOB AUTOMATION -- API INTEGRATION TEST SUITE")
    print(f"  Target: {BASE_URL}")
    print("=" * 60)

    try:
        requests.get(f"{BASE_URL}/health", timeout=30)
    except requests.ConnectionError:
        print(f"\n[ERROR] Cannot connect to {BASE_URL}")
        print("   Start the server first: uvicorn main:app --reload")
        sys.exit(1)

    test_health()
    test_invalid_action()

    profile = test_auth_flow()
    user_id = profile.get("user_id") if profile else None

    if user_id:
        test_profile_updates(user_id)
        test_toggle_and_status(user_id)
        test_active_users_for_campaign()

    test_admin_flow()
    test_unsubscribe_html()

    print("\n" + "=" * 60)
    print("  ALL API TESTS COMPLETE")
    print("=" * 60)
