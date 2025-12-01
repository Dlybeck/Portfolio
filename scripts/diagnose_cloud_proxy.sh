#!/bin/bash
# Diagnose Cloud Run Proxy Issue
# This script mimics the backend logic to test connectivity to the Mac server from within the container environment

echo "=== CLOUD RUN DIAGNOSTIC SCRIPT ==="
echo "Target IP: ${MAC_SERVER_IP}"
echo "Target Port: ${MAC_SERVER_PORT}"
echo "SOCKS5 Proxy: ${SOCKS5_PROXY}"

# 1. Check SOCKS5 Proxy Connectivity
echo -e "\n[1] Checking SOCKS5 Proxy..."
# Assuming localhost:1055 is the proxy
nc -z -v 127.0.0.1 1055
if [ $? -eq 0 ]; then
    echo "✅ SOCKS5 proxy is listening on 127.0.0.1:1055"
else
    echo "❌ SOCKS5 proxy is NOT reachable"
fi

# 2. Check Route to Mac Server
echo -e "\n[2] Checking Route to Mac Server..."
# We can't ping via SOCKS, but we can check if we can reach it via curl/proxy
# Using python to test the exact library call used in the app
python3 -c "
import asyncio
import httpx
import os

async def test_proxy():
    proxy_url = os.environ.get('SOCKS5_PROXY', 'socks5://127.0.0.1:1055')
    target_url = f'http://{os.environ.get(\"MAC_SERVER_IP\")}:{os.environ.get(\"MAC_SERVER_PORT\")}/debug/health'
    
    print(f'Testing connection to {target_url} via {proxy_url}...')
    
    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=5.0) as client:
            resp = await client.get(target_url)
            print(f'Response Status: {resp.status_code}')
            print(f'Response Text: {resp.text}')
    except Exception as e:
        print(f'CONNECTION FAILED: {e}')

asyncio.run(test_proxy())
"

echo -e "\n=== END DIAGNOSTICS ==="
