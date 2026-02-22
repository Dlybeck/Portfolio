#!/bin/bash
set -e

echo "🔍 Verifying OpenHands Fix"
echo "=========================="

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
echo "Tailscale IPv4: $TS_IP"
BASE_URL="http://${TS_IP}:3000"

echo ""
echo "1. Testing URL extraction..."
RESPONSE=$(curl -s -H "Host: opencode.davidlybeck.com" "${BASE_URL}/api/conversations")

echo "$RESPONSE" | python3 -c "
import sys, json, re

try:
    data = json.load(sys.stdin)
    cache = {}
    url_re = re.compile(r'(?:http://|ws://|wss://)?(?:localhost|127\\.0\\.0\\.1):(\\d+)')
    
    def search(obj):
        if isinstance(obj, dict):
            # Handle pagination
            if 'results' in obj:
                search(obj['results'])
                return
            
            # Get conversation ID
            conv_id = None
            for field in ['conversation_id', 'id', 'conversationId', 'conversationID']:
                if field in obj:
                    conv_id = obj[field]
                    break
            
            # Get URL  
            found_url = None
            for k, v in obj.items():
                if isinstance(v, str):
                    m = url_re.search(v)
                    if m:
                        found_url = v
                        break
            
            if conv_id and found_url:
                m = url_re.search(found_url)
                if m:
                    port = m.group(1)
                    cache[conv_id] = f'http://localhost:{port}'
                    print(f'✅ Found: {conv_id} → localhost:{port}')
                    print(f'   URL field value: {found_url}')
            
            # Recursive
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    search(v)
                    
        elif isinstance(obj, list):
            for item in obj:
                search(item)
    
    print('Searching API response...')
    search(data)
    
    print('')
    if cache:
        print(f'📊 Found {len(cache)} conversations with agent URLs:')
        for cid, url in cache.items():
            print(f'   {cid[:8]}... → {url}')
    else:
        print('❌ No agent URLs found')
        print('   First 500 chars of response:')
        print(str(data)[:500])
        
except Exception as e:
    print(f'Error: {e}')
"

echo ""
echo "2. Testing port 48431..."
echo "   Listening:"
sudo ss -tlnp 2>/dev/null | grep ":48431 " || echo "   Not found"
echo "   Binding address:"
sudo ss -tlnp 2>/dev/null | grep ":48431 " | grep -o "0.0.0.0:\\|127.0.0.1:" || echo "   Unknown"

echo ""
echo "3. Quick WebSocket test concept..."
echo "   Conversation IDs found above should work with:"
echo "   wss://opencode.davidlybeck.com/sockets/events/{CONVERSATION_ID}"
echo ""
echo "📋 If URLs found but WebSocket still fails:"
echo "   - Check Cloud Run logs for WebSocket errors"
echo "   - Ensure agent server binds to 0.0.0.0"
echo "   - Test SOCKS5: curl --socks5 localhost:1055 http://\${TS_IP}:48431/"
