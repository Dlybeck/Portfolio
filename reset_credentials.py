
import os
import getpass
import pyotp
import qrcode
from dotenv import dotenv_values, set_key

# Import password functions from the existing security module
from core.security import get_password_hash, validate_password_strength

ENV_FILE = ".env"

def secure_credential_reset():
    """
    Guides the user through securely resetting their dashboard password and 2FA secret.
    """
    print("--- Dev Dashboard Secure Credential Reset ---")

    # --- 1. Get and Validate New Password ---
    while True:
        try:
            print("\nPlease enter a new password for the dashboard.")
            print("Your password must be at least 16 characters and include uppercase, lowercase, numbers, and special characters.")
            new_password = getpass.getpass("New Password: ")
            confirm_password = getpass.getpass("Confirm New Password: ")

            if new_password != confirm_password:
                print("\n❌ Passwords do not match. Please try again.")
                continue

            is_valid, error_msg = validate_password_strength(new_password)
            if not is_valid:
                print(f"\n❌ Password is not strong enough: {error_msg}")
                continue
            
            print("\n✅ Password is strong and has been confirmed.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return

    # --- 2. Generate New Credentials ---
    try:
        # Bcrypt has a 72-byte limit - check and reject if too long
        password_bytes = new_password.encode('utf-8')
        if len(password_bytes) > 72:
            print("\n❌ Error: Your password exceeds the 72-byte limit for bcrypt.")
            print(f"   Your password is {len(password_bytes)} bytes.")
            print("   Please choose a shorter password (72 bytes max).")
            return

        new_password_hash = get_password_hash(new_password)
        new_totp_secret = pyotp.random_base32()
        print("✅ New password hash and 2FA secret generated.")
    except Exception as e:
        print(f"\n❌ Error generating new credentials: {e}")
        return

    # --- 3. Update .env File ---
    try:
        if not os.path.exists(ENV_FILE):
            print(f"\n❌ Error: The {ENV_FILE} file was not found in the current directory.")
            print("Please create one from .env.example before running this script.")
            return

        # Load existing .env to get username and other settings
        config = dotenv_values(ENV_FILE)
        username = config.get("DASHBOARD_USERNAME", "admin") # Default to admin if not set

        # Update the values
        set_key(ENV_FILE, "DASHBOARD_PASSWORD_HASH", new_password_hash)
        set_key(ENV_FILE, "TOTP_SECRET", new_totp_secret)
        print(f"✅ Successfully updated {ENV_FILE} with the new credentials.")

    except Exception as e:
        print(f"\n❌ Error updating the {ENV_FILE} file: {e}")
        return

    # --- 4. Generate New QR Code ---
    try:
        totp = pyotp.TOTP(new_totp_secret)
        provisioning_uri = totp.provisioning_uri(name=username, issuer_name="Dev Dashboard")
        
        qr_filename = "new_totp_qr.png"
        img = qrcode.make(provisioning_uri)
        img.save(qr_filename)
        
        print(f"\n✅ New 2FA QR code has been saved as: {qr_filename}")
    except Exception as e:
        print(f"\n❌ Error generating the new QR code: {e}")
        return

    # --- 5. Final Instructions ---
    print("\n--- Reset Complete! Next Steps: ---")
    print(f"1. Open the file '{qr_filename}' and scan it with your authenticator app (e.g., Google Authenticator).")
    print("2. Delete the old entry for 'Dev Dashboard' from your authenticator app.")
    print("3. You can now log in with your new password and the new 2FA code.")
    print("4. For security, please delete this script and the QR code image when you are done:")
    print(f"   rm {qr_filename} reset_credentials.py")

if __name__ == "__main__":
    secure_credential_reset()
