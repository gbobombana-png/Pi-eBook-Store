#!/data/data/com.termux/files/usr/bin/bash
# Démarrage Tor + vérification anti-fuite

# Tuer les instances précédentes
pkill tor 2>/dev/null
sleep 1

echo "[*] Démarrage de Tor..."
tor -f $PREFIX/etc/tor/torrc &
TOR_PID=$!

# Attendre que Tor soit prêt
echo "[*] Connexion en cours..."
for i in $(seq 1 30); do
    if curl -s --socks5 127.0.0.1:9050 --connect-timeout 3 https://check.torproject.org/api/ip 2>/dev/null | grep -q '"IsTor":true'; then
        break
    fi
    sleep 2
    echo -n "."
done

echo ""
echo "[*] Vérification IP réelle (AVANT Tor):"
curl -s --connect-timeout 5 https://api.ipify.org 2>/dev/null || echo "Non disponible"

echo ""
echo "[*] Vérification IP via Tor (APRÈS):"
proxychains4 -q curl -s https://api.ipify.org 2>/dev/null

echo ""
echo "[*] Test anti-fuite DNS:"
proxychains4 -q curl -s https://check.torproject.org/api/ip 2>/dev/null

echo ""
echo "[+] Tor actif (PID: $TOR_PID)"
echo "[+] Utilise: proxychains4 <commande>"
echo "[+] Exemple: proxychains4 curl https://site.com"
echo ""
echo "Pour arrêter: bash tor_setup/tor_stop.sh"
