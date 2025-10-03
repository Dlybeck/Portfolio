#!/bin/bash
# Tailscale diagnostics script
# Run this AFTER connecting Tailscale (while internet is broken)

OUTPUT_FILE="/Users/dlybeck/Documents/Portfolio/tailscale_diagnostics.txt"

echo "=== Tailscale Diagnostics ===" > "$OUTPUT_FILE"
echo "Generated: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "=== DNS Configuration ===" >> "$OUTPUT_FILE"
scutil --dns >> "$OUTPUT_FILE" 2>&1
echo "" >> "$OUTPUT_FILE"

echo "=== IPv4 Routes ===" >> "$OUTPUT_FILE"
netstat -rn -f inet >> "$OUTPUT_FILE" 2>&1
echo "" >> "$OUTPUT_FILE"

echo "=== IPv6 Routes ===" >> "$OUTPUT_FILE"
netstat -rn -f inet6 >> "$OUTPUT_FILE" 2>&1
echo "" >> "$OUTPUT_FILE"

echo "=== Network Interfaces ===" >> "$OUTPUT_FILE"
ifconfig >> "$OUTPUT_FILE" 2>&1
echo "" >> "$OUTPUT_FILE"

echo "=== Tailscale Status (if accessible) ===" >> "$OUTPUT_FILE"
/Applications/Tailscale.app/Contents/MacOS/Tailscale status >> "$OUTPUT_FILE" 2>&1
echo "" >> "$OUTPUT_FILE"

echo "=== Default Gateway ===" >> "$OUTPUT_FILE"
route -n get default >> "$OUTPUT_FILE" 2>&1
echo "" >> "$OUTPUT_FILE"

echo "=== Can Ping Google DNS? ===" >> "$OUTPUT_FILE"
ping -c 3 8.8.8.8 >> "$OUTPUT_FILE" 2>&1
echo "" >> "$OUTPUT_FILE"

echo "=== Can Resolve DNS? ===" >> "$OUTPUT_FILE"
nslookup google.com >> "$OUTPUT_FILE" 2>&1
echo "" >> "$OUTPUT_FILE"

echo "" >> "$OUTPUT_FILE"
echo "Diagnostics saved to: $OUTPUT_FILE"
echo "You can now disconnect Tailscale and we'll analyze the results."

cat "$OUTPUT_FILE"
