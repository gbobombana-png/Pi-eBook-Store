#!/data/data/com.termux/files/usr/bin/bash
# Tor anonymization setup for Termux

echo "[*] Installation des paquets..."
pkg install -y tor proxychains-ng curl 2>/dev/null

echo "[*] Configuration de Tor..."
mkdir -p ~/.tor_data
cat > $PREFIX/etc/tor/torrc << 'EOF'
SocksPort 9050
SocksPolicy accept 127.0.0.1
Log notice file /data/data/com.termux/files/home/.tor_data/tor.log
DataDirectory /data/data/com.termux/files/home/.tor_data
DNSPort 5353
AutomapHostsOnResolve 1
VirtualAddrNetworkIPv4 10.192.0.0/10
ExcludeExitNodes {ru},{cn},{ir},{kp}
StrictNodes 1
EOF

echo "[*] Configuration de proxychains..."
cat > $PREFIX/etc/proxychains.conf << 'EOF'
strict_chain
proxy_dns
remote_dns_subnet 224
tcp_read_time_out 15000
tcp_connect_time_out 8000
[ProxyList]
socks5 127.0.0.1 9050
EOF

echo "[+] Setup terminé. Lance: bash ~/Pi-eBook-Store/tor_setup/tor_start.sh"
