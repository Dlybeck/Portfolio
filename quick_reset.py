#!/usr/bin/env python3
import sys
import os
import pyotp
import qrcode
from dotenv import dotenv_values, set_key
from core.security import get_password_hash

ENV_FILE = ".env"

def quick_reset(password):
    """Quick credential reset with provided password"""

    # Check password length in bytes
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        print(f"❌ Error: Password is {len(password_bytes)} bytes (max 72 bytes)")
        print("Please use a shorter password")
        return False

    try:
        # Generate credentials
        password_hash = get_password_hash(password)
        totp_secret = pyotp.random_base32()

        # Load config
        if not os.path.exists(ENV_FILE):
            print(f"❌ Error: {ENV_FILE} not found")
            return False

        config = dotenv_values(ENV_FILE)
        username = config.get("DASHBOARD_USERNAME", "admin")

        # Update .env
        set_key(ENV_FILE, "DASHBOARD_PASSWORD_HASH", password_hash)
        set_key(ENV_FILE, "TOTP_SECRET", totp_secret)

        # Generate QR code
        totp = pyotp.TOTP(totp_secret)
        provisioning_uri = totp.provisioning_uri(name=username, issuer_name="Dev Dashboard")

        qr_filename = "new_totp_qr.png"
        img = qrcode.make(provisioning_uri)
        img.save(qr_filename)

        print(f"✅ Credentials updated successfully!")
        print(f"✅ QR code saved as: {qr_filename}")
        print(f"✅ Password length: {len(password_bytes)} bytes (OK)")
        print(f"\nUsername: {username}")
        print(f"\nNext steps:")
        print(f"1. Open {qr_filename} and scan with Google Authenticator")
        print(f"2. Delete old 'Dev Dashboard' entry from authenticator")
        print(f"3. Login with new password + 2FA code")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 quick_reset.py 'YourNewPassword'")
        print("Password must be 16+ chars with uppercase, lowercase, numbers, special chars")
        sys.exit(1)

    password = sys.argv[1]

    if len(password) < 16:
        print("❌ Password must be at least 16 characters")
        sys.exit(1)

    success = quick_reset(password)
    sys.exit(0 if success else 1)
