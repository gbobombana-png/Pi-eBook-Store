#!/data/data/com.termux/files/usr/bin/bash
pkill tor 2>/dev/null && echo "[+] Tor arrêté." || echo "[!] Tor n'était pas actif."
