
import os
from dotenv import load_dotenv
from core.security import authenticate_user, get_password_hash, DASHBOARD_USERNAME, DASHBOARD_PASSWORD_HASH, TOTP_SECRET
import pyotp

# Load environment variables from .env file
load_dotenv()

def run_auth_test():
    """
    Tests the authentication logic to diagnose login issues.
    """
    print("--- Starting Authentication Test ---")

    # --- Test Data ---
    # IMPORTANT: Replace with the actual password and a valid TOTP code you are using to test
    test_password = "REPLACE_WITH_ACTUAL_PASSWORD" 
    test_totp_code = "REPLACE_WITH_VALID_TOTP_CODE"

    # --- Sanity Checks ---
    print(f"Username from .env: {DASHBOARD_USERNAME}")
    if not DASHBOARD_PASSWORD_HASH:
        print("CRITICAL: DASHBOARD_PASSWORD_HASH is not set in the .env file.")
        return
    if not TOTP_SECRET:
        print("CRITICAL: TOTP_SECRET is not set in the .env file.")
        return
    
    print(f"Password hash loaded from .env: {DASHBOARD_PASSWORD_HASH[:5]}...{DASHBOARD_PASSWORD_HASH[-5:]}")
    print(f"TOTP secret loaded from .env: {TOTP_SECRET[:4]}...{TOTP_SECRET[-4:]}")

    # --- Test 1: Direct Password Verification ---
    print("\n--- Test 1: Direct Password Verification ---")
    try:
        is_password_correct = get_password_hash(test_password) == DASHBOARD_PASSWORD_HASH
        # This is a simplified check. The real verification is below.
        # We need to use pwd_context.verify for proper checking.
        from core.security import pwd_context
        is_password_correct = pwd_context.verify(test_password, DASHBOARD_PASSWORD_HASH)

        if is_password_correct:
            print("✅ SUCCESS: The provided password correctly matches the stored hash.")
        else:
            print("❌ FAILURE: The provided password does NOT match the stored hash.")
            # To help debug, let's generate what the hash *should* be
            expected_hash = get_password_hash(test_password)
            print(f"    - Expected Hash: {expected_hash}")
            print(f"    - Stored Hash:   {DASHBOARD_PASSWORD_HASH}")

    except Exception as e:
        print(f"ERROR during password verification: {e}")


    # --- Test 2: TOTP Code Verification ---
    print("\n--- Test 2: TOTP Code Verification ---")
    try:
        totp = pyotp.TOTP(TOTP_SECRET)
        is_totp_correct = totp.verify(test_totp_code, valid_window=1)
        if is_totp_correct:
            print("✅ SUCCESS: The provided TOTP code is valid.")
        else:
            print("❌ FAILURE: The provided TOTP code is NOT valid.")
            # For debugging, let's see what the current valid code is
            print(f"    - Current valid TOTP code is: {totp.now()}")
    except Exception as e:
        print(f"ERROR during TOTP verification: {e}")


    # --- Test 3: Full Authentication Function ---
    print("\n--- Test 3: Full authenticate_user() Function Call ---")
    try:
        # We expect this to fail if the password or TOTP is wrong.
        # The output will come from the print statements we added inside the function.
        authenticate_user(DASHBOARD_USERNAME, test_password, test_totp_code)
    except Exception as e:
        # The function itself raises HTTPException, which is expected on failure.
        # The important output is the print statements *within* the function.
        print(f"authenticate_user() raised an exception as expected on failure: {e.detail}")

    print("\n--- Test Complete ---")


if __name__ == "__main__":
    # IMPORTANT: You must edit this file and fill in the test_password and test_totp_code
    # before running this script.
    print("⚠️  Reminder: Make sure you have replaced the placeholder password and TOTP code in test_auth.py")
    # run_auth_test()
