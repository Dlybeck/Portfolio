#!/bin/bash
set -e

echo "🔍 Testing OpenHands API Response Format"
echo "======================================="

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
echo "Tailscale IPv4: $TS_IP"

echo ""
echo "1. Testing /api/conversations endpoint..."
API_RESPONSE=$(curl -s -H "Host: opencode.davidlybeck.com" "http://${TS_IP}:3000/api/conversations?limit=2" 2>&1 || echo "FAILED")

echo "Response length: ${#API_RESPONSE} characters"
echo ""
echo "2. Full response (first 1000 chars):"
echo "------------------------------------"
echo "${API_RESPONSE:0:1000}"
echo "..."
if [ ${#API_RESPONSE} -gt 1000 ]; then
    echo "(truncated, full response is ${#API_RESPONSE} chars)"
fi

echo ""
echo "3. JSON structure analysis..."
echo "$API_RESPONSE" | python3 -c "
import sys, json, re

try:
    data = json.load(sys.stdin)
    print('✅ JSON parsed successfully')
    print(f'Type: {type(data)}')
    
    def find_urls(obj, path=''):
        urls = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f'{path}.{k}' if path else k
                if isinstance(v, str) and ('url' in k.lower() or 'localhost' in v or re.search(r':\\d+/', v)):
                    urls.append((new_path, v))
                elif isinstance(v, (dict, list)):
                    urls.extend(find_urls(v, new_path))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                urls.extend(find_urls(item, f'{path}[{i}]'))
        return urls
    
    if isinstance(data, list):
        print(f'List length: {len(data)}')
        if data:
            print('\\nFirst conversation structure:')
            first = data[0]
            print(f'  Keys: {list(first.keys())}')
            
            # Find ALL URL-like fields
            print('\\nSearching for URL fields...')
            all_urls = find_urls(data)
            if all_urls:
                print('Found URL fields:')
                for path, url in all_urls:
                    print(f'  {path}: {url}')
                    
                    # Check if it looks like an agent URL
                    if 'localhost' in url and re.search(r':\\d+', url):
                        print(f'    ⚡ Looks like agent URL!')
                        match = re.search(r'localhost:(\\d+)', url)
                        if match:
                            port = match.group(1)
                            print(f'    Port: {port}')
            else:
                print('❌ No URL fields found at all')
                
    elif isinstance(data, dict):
        print(f'Dict keys: {list(data.keys())}')
        all_urls = find_urls(data)
        if all_urls:
            print('Found URL fields:')
            for path, url in all_urls:
                print(f'  {path}: {url}')
        else:
            print('❌ No URL fields found')
            
except json.JSONDecodeError as e:
    print(f'❌ JSON decode error: {e}')
    print('Response might be HTML or error page')
    # Try to see what we got
    sample = sys.stdin.read()[:200] if not isinstance(data, str) else data[:200]
    print(f'Sample: {sample}')
except Exception as e:
    print(f'❌ Error: {e}')
" 2>/dev/null || echo "Python analysis failed"

echo ""
echo "4. Checking for agent server ports manually..."
echo "   Looking for ports 36xxx-39xxx..."
sudo ss -tlnp 2>/dev/null | grep -E ":(36[0-9]{3}|37[0-9]{3}|38[0-9]{3}|39[0-9]{3})" | head -10

echo ""
echo "📋 What this means:"
echo "=================="
echo "If API returns conversations but no URLs:"
echo "1. Agent URLs might be in different field (not 'url')"
echo "2. OpenHands v1.3 might use different response format"
echo "3. Need to update _extract_agent_urls() in openhands_web_proxy.py"
