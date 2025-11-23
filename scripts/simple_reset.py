#!/usr/bin/env python3
"""
Simple credential reset - bypasses validation for emergency access
"""
import os
import sys
import pyotp
import qrcode
from passlib.context import CryptContext
from dotenv import set_key

# Simple password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def simple_reset():
    """Reset with a simple 16-char password"""

    # Use a simple 16-character password
    simple_password = "Admin123!@#Pass"

    print(f"Setting password to: {simple_password}")
    print(f"Password length: {len(simple_password)} characters")
    print(f"Password bytes: {len(simple_password.encode('utf-8'))} bytes")

    try:
        # Hash password
        password_hash = pwd_context.hash(simple_password)
        print(f"✅ Password hashed successfully")

        # Generate TOTP secret
        totp_secret = pyotp.random_base32()
        print(f"✅ TOTP secret generated")

        # Update .env
        set_key(".env", "DASHBOARD_PASSWORD_HASH", password_hash)
        set_key(".env", "TOTP_SECRET", totp_secret)
        print(f"✅ .env updated")

        # Generate QR code
        totp = pyotp.TOTP(totp_secret)
        provisioning_uri = totp.provisioning_uri(name="admin", issuer_name="Dev Dashboard")

        img = qrcode.make(provisioning_uri)
        img.save("generated/new_totp_qr.png")
        print(f"✅ QR code saved as: generated/new_totp_qr.png")

        print("\n" + "="*50)
        print("SUCCESS! Credentials reset")
        print("="*50)
        print(f"Username: admin")
        print(f"Password: {simple_password}")
        print(f"\nNext steps:")
        print(f"1. Scan generated/new_totp_qr.png with Google Authenticator")
        print(f"2. Login with the credentials above")
        print(f"3. Change password after logging in if needed")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_reset()
