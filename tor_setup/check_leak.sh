#!/data/data/com.termux/files/usr/bin/bash
# Test complet de fuite IP/DNS

echo "=== TEST ANTI-FUITE ==="
echo ""
echo "[1] Ton IP réelle:"
curl -s --connect-timeout 5 https://api.ipify.org
echo ""

echo "[2] IP via Tor (doit être différente):"
proxychains4 -q curl -s https://api.ipify.org 2>/dev/null
echo ""

echo "[3] Confirmation Tor:"
proxychains4 -q curl -s https://check.torproject.org/api/ip 2>/dev/null
echo ""

echo "[4] Test fuite DNS:"
proxychains4 -q curl -s "https://www.dnsleaktest.com/" 2>/dev/null | grep -o 'Your IP.*' | head -1
echo ""

echo "=== FIN DU TEST ==="
