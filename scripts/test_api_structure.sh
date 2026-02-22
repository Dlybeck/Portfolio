#!/bin/bash
set -e

echo "🔍 Testing OpenHands API Structure"
echo "================================"

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
echo "Tailscale IPv4: $TS_IP"
BASE_URL="http://${TS_IP}:3000"

echo ""
echo "1. Fetching /api/conversations..."
RESPONSE=$(curl -s -H "Host: opencode.davidlybeck.com" "${BASE_URL}/api/conversations")
LEN=${#RESPONSE}
echo "Response length: $LEN chars"

if [ $LEN -eq 0 ]; then
    echo "Empty response!"
    exit 1
fi

echo ""
echo "2. Parsing JSON structure..."
echo "$RESPONSE" | python3 -c "
import sys, json, re

try:
    data = json.load(sys.stdin)
    print('✅ JSON parsed successfully')
    print(f'Type: {type(data).__name__}')
    
    if isinstance(data, dict):
        print(f'Dict keys: {list(data.keys())}')
        
        if 'results' in data:
            results = data['results']
            print(f'\\n📋 Results array length: {len(results)}')
            
            if results:
                print('\\n🔍 First conversation in results:')
                first = results[0]
                
                if isinstance(first, dict):
                    print(f'  Keys: {list(first.keys())}')
                    
                    # Show all fields
                    print('\\n  All fields:')
                    for key, value in first.items():
                        value_type = type(value).__name__
                        value_preview = str(value)[:80] if value else ''
                        print(f'    {key}: {value_type} = {value_preview}')
                    
                    # Look for URLs
                    print('\\n  🔗 Searching for URLs...')
                    url_count = 0
                    for key, value in first.items():
                        if isinstance(value, str):
                            # Look for localhost:PORT or 127.0.0.1:PORT
                            match = re.search(r'(localhost|127\\.0\\.0\\.1):(\\d+)', value)
                            if match:
                                url_count += 1
                                print(f'    Found: {key} = {value}')
                    
                    if url_count == 0:
                        print('    ❌ No URLs found')
                    
                    # Look for conversation ID
                    print('\\n  🆔 Searching for conversation ID...')
                    possible_ids = []
                    for key in first.keys():
                        if 'id' in key.lower() or 'conversation' in key.lower():
                            possible_ids.append(key)
                    
                    if possible_ids:
                        print(f'    Possible ID fields: {possible_ids}')
                        for field in possible_ids:
                            print(f'      {field}: {first.get(field)}')
                    else:
                        print('    ❌ No obvious ID fields found')
                else:
                    print(f'  Value (not dict): {first}')
            else:
                print('  Results array is empty')
        else:
            print('❌ No "results" key in response')
    else:
        print('Response is not a dict')
        
except json.JSONDecodeError as e:
    print(f'❌ JSON decode error: {e}')
    print('Response preview:')
    print(sys.stdin.read()[:200])
except Exception as e:
    print(f'❌ Error: {e}')
"

echo ""
echo "📋 Summary:"
echo "=========="
echo "Run this script and share output to see what fields exist."
