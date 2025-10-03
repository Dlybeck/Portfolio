#!/usr/bin/env python3
"""
Direct bcrypt reset - uses bcrypt library directly
"""
import bcrypt
import pyotp
import qrcode
from dotenv import set_key

def direct_reset():
    """Reset using bcrypt directly"""

    # Simple password - 16 characters
    password = "Admin123!@#Pass"

    print(f"Resetting credentials...")
    print(f"Password: {password}")
    print(f"Length: {len(password)} chars, {len(password.encode('utf-8'))} bytes")

    try:
        # Hash with bcrypt directly
        password_bytes = password.encode('utf-8')
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
        uri = totp.provisioning_uri(name="admin", issuer_name="Dev Dashboard")
        img = qrcode.make(uri)
        img.save("new_totp_qr.png")
        print(f"✅ QR code saved: new_totp_qr.png")

        print("\n" + "="*50)
        print("✅ SUCCESS!")
        print("="*50)
        print(f"Username: admin")
        print(f"Password: {password}")
        print(f"\nNext:")
        print(f"1. Scan new_totp_qr.png with Google Authenticator")
        print(f"2. Login with credentials above")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    direct_reset()
