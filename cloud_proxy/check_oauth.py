#!/usr/bin/env python3
"""
Check OAuth client health and provide renewal instructions
Run this periodically to ensure OAuth client is valid
"""

import os
import sys
import requests
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OAUTH_CLIENT_ID = os.getenv('TAILSCALE_OAUTH_CLIENT_ID')
OAUTH_CLIENT_SECRET = os.getenv('TAILSCALE_OAUTH_CLIENT_SECRET')
TAILNET = os.getenv('TAILSCALE_TAILNET', 'your-tailnet.ts.net')

def check_oauth_health():
    """Test if OAuth credentials are valid"""

    if not OAUTH_CLIENT_ID or not OAUTH_CLIENT_SECRET:
        logger.error("OAuth credentials not found in environment")
        logger.error("Set TAILSCALE_OAUTH_CLIENT_ID and TAILSCALE_OAUTH_CLIENT_SECRET")
        return False

    # Get OAuth token
    try:
        token_response = requests.post(
            'https://api.tailscale.com/api/v2/oauth/token',
            auth=(OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET),
            data={'grant_type': 'client_credentials'},
            timeout=10
        )

        if token_response.status_code != 200:
            logger.error(f"OAuth client invalid: {token_response.status_code}")
            logger.error(f"Response: {token_response.text}")
            print_renewal_instructions()
            return False

        token = token_response.json()['access_token']

        # Test API access
        devices_response = requests.get(
            f'https://api.tailscale.com/api/v2/tailnet/{TAILNET}/devices',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )

        if devices_response.status_code == 200:
            devices = devices_response.json()
            logger.info("OAuth client is healthy!")
            logger.info(f"Tailnet: {TAILNET}")
            logger.info(f"Devices: {len(devices.get('devices', []))}")
            return True
        else:
            logger.warning(f"OAuth token works but API access failed: {devices_response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Error checking OAuth health: {e}")
        print_renewal_instructions()
        return False

def print_renewal_instructions():
    """Print instructions for renewing OAuth client"""
    print("\n" + "="*60)
    print("📋 HOW TO RENEW TAILSCALE OAUTH CLIENT")
    print("="*60)
    print()
    print("1. Go to: https://login.tailscale.com/admin/settings/oauth")
    print()
    print("2. Find your existing OAuth client named 'cloud-proxy' or create new:")
    print("   - Click 'Generate OAuth Client'")
    print("   - Name: cloud-proxy")
    print("   - Scopes: 'Devices: Write' or 'Write auth keys'")
    print("   - Click 'Generate client'")
    print()
    print("3. Copy the Client ID and Client Secret")
    print()
    print("4. Update Cloud Run environment variables:")
    print()
    print("   gcloud run services update dev-proxy \\")
    print("     --region=us-central1 \\")
    print("     --update-env-vars TAILSCALE_OAUTH_CLIENT_ID=YOUR_CLIENT_ID,\\")
    print("TAILSCALE_OAUTH_CLIENT_SECRET=YOUR_CLIENT_SECRET")
    print()
    print("5. Verify deployment:")
    print("   python3 check_oauth.py")
    print()
    print("="*60)
    print()

if __name__ == '__main__':
    logger.info(f"Checking Tailscale OAuth health at {datetime.now()}")

    is_healthy = check_oauth_health()

    if not is_healthy:
        sys.exit(1)

    sys.exit(0)
