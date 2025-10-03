#!/usr/bin/env python3
"""
Custom credential reset - you choose the password
Usage: python3 custom_reset.py "YourPassword"
"""
import sys
import bcrypt
import pyotp
import qrcode
from dotenv import set_key

def custom_reset(password):
    """Reset with custom password"""

    # Check byte length
    password_bytes = password.encode('utf-8')
    byte_len = len(password_bytes)

    if byte_len > 72:
        print(f"❌ Password is {byte_len} bytes (max 72)")
        print("   Please use a shorter password")
        return False

    print(f"Resetting credentials...")
    print(f"Password length: {len(password)} chars, {byte_len} bytes")

    try:
        # Hash with bcrypt directly
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        print(f"✅ Password hashed")

        # Generate TOTP
        totp_secret = pyotp.random_base32()
        print(f"✅ TOTP generated")

        # Update .env
        set_key(".env", "DASHBOARD_PASSWORD_HASH", password_hash)
        set_key(".env", "TOTP_SECRET", totp_secret)
        print(f"✅ .env updated")

        # QR code
        totp = pyotp.TOTP(totp_secret)
        uri = totp.provisioning_uri(name="dlybeck", issuer_name="Dev Dashboard")
        img = qrcode.make(uri)
        img.save("new_totp_qr.png")
        print(f"✅ QR code saved: new_totp_qr.png")

        print("\n" + "="*50)
        print("✅ SUCCESS!")
        print("="*50)
        print(f"Username: dlybeck")
        print(f"Password: {password}")
        print(f"\nNext:")
        print(f"1. Scan new_totp_qr.png with Google Authenticator")
        print(f"2. Login with credentials above")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 custom_reset.py 'YourPassword'")
        print("\nPassword should be:")
        print("  - 16-50 characters (to stay under 72 bytes)")
        print("  - Mix of uppercase, lowercase, numbers, special chars")
        print("\nExample:")
        print('  python3 custom_reset.py "MySecure!Pass2024"')
        sys.exit(1)

    password = sys.argv[1]

    if len(password) < 16:
        print("❌ Password should be at least 16 characters")
        sys.exit(1)

    success = custom_reset(password)
    sys.exit(0 if success else 1)
