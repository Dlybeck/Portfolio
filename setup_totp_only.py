#!/usr/bin/env python3
"""
Simple TOTP Setup - Just generate 2FA code
No username/password needed for single-user systems
"""

import pyotp
import qrcode
from pathlib import Path
from dotenv import set_key

def main():
    print("=" * 60)
    print("🔐 2FA Setup (Single-User Mode)")
    print("=" * 60)
    print()
    print("This will generate a 2FA code for Google Authenticator.")
    print("No username/password needed - just the 6-digit code!")
    print()

    # Generate TOTP secret
    totp_secret = pyotp.random_base32()
    print(f"📱 Generated TOTP secret: {totp_secret}")

    # Create TOTP URI
    totp = pyotp.TOTP(totp_secret)
    totp_uri = totp.provisioning_uri(name="Portfolio Dev", issuer_name="Dev Dashboard")

    # Generate QR code
    print("📷 Generating QR code...")
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save("totp_qr.png")
    print(f"✅ QR code saved to: totp_qr.png")

    # Update .env file
    env_file = Path(".env")
    if env_file.exists():
        set_key(".env", "TOTP_SECRET", totp_secret)
        print(f"✅ Updated .env file with TOTP_SECRET")
    else:
        print(f"⚠️  .env file not found - please add this line:")
        print(f"    TOTP_SECRET={totp_secret}")

    # Print setup instructions
    print()
    print("=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print()
    print("1. Open Google Authenticator on your phone")
    print("2. Tap '+' to add a new account")
    print("3. Scan the QR code: totp_qr.png")
    print()
    print("   OR manually enter this secret:")
    print(f"   {totp_secret}")
    print()
    print("4. Start the dev environment:")
    print("   ./start-local-dev.sh")
    print()
    print("5. For Cloud Run deployment:")
    print("   - Login page will show: Just enter your 6-digit code")
    print("   - No username or password needed!")
    print()
    print("6. For local development:")
    print("   - Authentication is optional")
    print("   - Just access http://localhost:8080/dev directly")
    print()

if __name__ == "__main__":
    main()
