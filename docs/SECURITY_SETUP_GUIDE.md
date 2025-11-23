# 🔐 Security Setup Guide - Tailscale + 2FA

This guide will help you set up secure remote access to your dev dashboard using **Tailscale VPN** and **2FA authentication**.

---

## 📋 Prerequisites

- macOS (your Mac)
- Homebrew installed
- Internet connection
- Smartphone (for Google Authenticator)

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Tailscale on Mac

```bash
# Install Tailscale via Homebrew
brew install tailscale

# Start Tailscale and authenticate
sudo tailscale up
```

This will give you a login URL. Open it in your browser and authenticate with:
- Google account
- GitHub account
- Microsoft account

**After authentication:**
- Tailscale will assign your Mac a permanent IP like `100.x.x.x`
- This IP is only accessible within your private Tailscale network

### Step 2: Install Tailscale on Your Phone

**iOS:**
https://apps.apple.com/app/tailscale/id1470499037

**Android:**
https://play.google.com/store/apps/details?id=com.tailscale.ipn

Login with the **same account** you used on your Mac.

### Step 3: Verify Connection

On your Mac:
```bash
tailscale status
```

You should see:
- Your Mac's Tailscale IP (100.x.x.x)
- Your phone's Tailscale IP (once installed)

**Test connection from your phone:**
- Open Safari/Chrome on your phone
- Navigate to: `http://100.x.x.x:8080` (use your Mac's Tailscale IP)
- You should see connection attempt (might be refused for now, that's okay)

---

## 🔑 Configure Dashboard Authentication

### Step 1: Run Security Setup Script

```bash
cd /Users/dlybeck/Documents/Portfolio

# Make script executable
chmod +x setup_security.py

# Run setup
python3 setup_security.py
```

This will:
1. ✅ Generate secure JWT secret key
2. ✅ Create your dashboard username/password
3. ✅ Generate TOTP 2FA secret
4. ✅ Create QR code for Google Authenticator
5. ✅ Save everything to `.env` file

**Example output:**
```
🔐 Dev Dashboard Security Setup
================================================

📝 Generating JWT secret key...
✅ Generated: a1b2c3d4e5f6...

👤 Enter dashboard username (default: admin): admin

🔑 Password requirements:
  - At least 16 characters
  - Must contain: uppercase, lowercase, numbers, special characters

Enter dashboard password: MySecureP@ssw0rd2025!

✅ Password hashed

📱 Generating 2FA (TOTP) secret...
✅ Generated TOTP secret: JBSWY3DPEHPK3PXP

📷 Generating QR code for Google Authenticator...
✅ QR code saved to: generated/totp_qr.png

💾 Creating .env file...
✅ Created .env file
```

### Step 2: Set Up Google Authenticator

**Install Google Authenticator:**
- iOS: https://apps.apple.com/app/google-authenticator/id388497605
- Android: https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2

**Add your dashboard:**
1. Open Google Authenticator app
2. Tap "+" to add account
3. Choose "Scan QR code"
4. Scan `generated/totp_qr.png` (open the image on your computer)

**Alternative (manual entry):**
1. Choose "Enter setup key"
2. Account name: "Dev Dashboard"
3. Key: (the TOTP_SECRET from setup output)
4. Type: Time-based

You should now see a 6-digit code that changes every 30 seconds.

---

## 🔧 Install Dependencies

```bash
cd /Users/dlybeck/Documents/Portfolio

# Install Python dependencies
pip3 install -r requirements.txt
```

**Dependencies installed:**
- `python-jose` - JWT tokens
- `passlib[bcrypt]` - Password hashing
- `pyotp` - 2FA TOTP
- `anthropic` - Claude AI
- `websockets` - Terminal WebSockets
- `ptyprocess` - Terminal sessions
- And more...

---

## ✅ Verify Configuration

### Check .env file

```bash
cat .env
```

Should contain:
```
SECRET_KEY=<long random string>
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD_HASH=$2b$12$...
TOTP_SECRET=<base32 string>
ANTHROPIC_API_KEY=<your key>
```

### Test Security Module

```bash
python3 -c "from core.security import validate_security_config; validate_security_config()"
```

Should output:
```
✅ Security configuration validated
```

---

## 🌐 Access Your Dashboard

### From Your Mac (Local)

```bash
# Start the dashboard
python3 main.py
```

Open browser: `http://localhost:8080/dev`

### From Your Phone (via Tailscale)

1. **Get your Mac's Tailscale IP:**
   ```bash
   tailscale status | grep "$(hostname)"
   ```

   Example output: `100.101.102.103`

2. **On your phone (connected to Tailscale):**
   - Open browser
   - Navigate to: `http://100.101.102.103:8080/dev`

3. **Login:**
   - Username: `admin` (or what you set)
   - Password: (your password)
   - 2FA Code: (from Google Authenticator app)

---

## 🔒 Security Features Enabled

✅ **Network Layer:**
- Only accessible via Tailscale VPN
- End-to-end encrypted tunnel
- No public internet exposure

✅ **Authentication:**
- Strong password requirements (16+ chars)
- Bcrypt password hashing
- Time-based 2FA (TOTP)
- JWT tokens (30 min expiration)

✅ **Rate Limiting:**
- Max 3 login attempts
- 15 minute lockout after failed attempts

✅ **Session Security:**
- Automatic logout after 10 min idle
- Token refresh mechanism
- Max 3 devices per user

✅ **Command Safety:**
- Dangerous commands blocked
- Destructive operations require confirmation
- All commands logged

---

## 🛠️ Troubleshooting

### Can't connect to Tailscale IP from phone

**Check:**
```bash
# On Mac - verify Tailscale is running
tailscale status

# Should show "online"
```

**Fix:**
```bash
# Restart Tailscale
sudo tailscale down
sudo tailscale up
```

### Login fails with "Account locked"

Wait 15 minutes, or reset manually:
```bash
# Restart the dashboard server (clears rate limiting)
```

### "2FA code invalid"

**Check:**
1. Phone time is synced (Settings → General → Date & Time → Set Automatically)
2. Using the correct account in Google Authenticator
3. Enter code quickly (changes every 30 seconds)

### Dashboard not starting

**Check .env configuration:**
```bash
python3 -c "from core.security import validate_security_config; validate_security_config()"
```

**Check dependencies:**
```bash
pip3 list | grep -E "fastapi|jose|passlib|pyotp"
```

---

## 📱 Mobile Tips

### Save Tailscale IP for Quick Access

**iOS:**
1. Open Safari
2. Navigate to `http://100.x.x.x:8080/dev`
3. Tap Share → Add to Home Screen
4. Now you have a one-tap icon

**Android:**
1. Open Chrome
2. Navigate to URL
3. Menu → Add to Home screen

### Using on Cellular Data

Tailscale works over cellular! You can access your Mac from:
- ✅ Coffee shops
- ✅ Work
- ✅ Anywhere with internet

**No port forwarding needed!**

---

## 🔐 Security Best Practices

### DO:
✅ Use a unique, strong password (16+ chars)
✅ Keep Google Authenticator secure
✅ Logout when done using dashboard
✅ Regularly review login logs
✅ Keep Tailscale updated

### DON'T:
❌ Share your .env file
❌ Commit .env to git (already in .gitignore)
❌ Reuse passwords from other services
❌ Disable 2FA
❌ Share your TOTP secret

---

## 🚨 Emergency Procedures

### Lost Phone / 2FA Access

**Option 1: Reset TOTP secret**
```bash
# Generate new TOTP secret
python3 -c "import pyotp; print(pyotp.random_base32())"

# Update .env file with new secret
# Re-run setup to generate new QR code
python3 setup_security.py
```

**Option 2: Temporary 2FA bypass** (use carefully)
```python
# Edit core/security.py
# Comment out TOTP verification temporarily
# Re-enable after regaining access
```

### Suspected Security Breach

**Immediately:**
1. Stop the dashboard server
2. Regenerate all secrets:
   ```bash
   python3 setup_security.py
   ```
3. Review logs for suspicious activity
4. Change all passwords

### Forgot Password

```bash
# Generate new password hash
python3 -c "from core.security import hash_password_for_env; print(hash_password_for_env('NewP@ssw0rd2025!'))"

# Update DASHBOARD_PASSWORD_HASH in .env
```

---

## 📊 Monitoring & Logs

### View Login Attempts

```bash
# Check dashboard logs
tail -f logs/dashboard.log | grep "login"
```

### Failed Login Alerts

Configure email alerts in `.env`:
```
ALERT_EMAIL=your@email.com
ALERT_ON_FAILED_LOGIN=true
ALERT_ON_NEW_DEVICE=true
```

---

## 🎯 Next Steps

After setup is complete:

1. ✅ Test login from phone via Tailscale
2. ✅ Test 2FA with Google Authenticator
3. ✅ Verify terminal access works
4. ✅ Test AI assistant features
5. ✅ Configure auto-start (optional)

---

## 🔗 Useful Links

- [Tailscale Documentation](https://tailscale.com/kb/)
- [Google Authenticator](https://support.google.com/accounts/answer/1066447)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Password Guidelines](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

**Questions or issues?** Check `DEV_DASHBOARD_PLAN.md` for architecture details.

**Last Updated:** 2025-10-01
