import socket
import urllib.request

_tor_enabled = False

def enable_tor():
    global _tor_enabled
    _tor_enabled = True
    # Patch socket pour forcer tout le trafic via Tor SOCKS5
    try:
        import socks
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
        socket.socket = socks.socksocket
        print("[+] Tor activé via PySocks (127.0.0.1:9050)")
    except ImportError:
        # Fallback: urllib proxy handler
        proxy = urllib.request.ProxyHandler({
            "http":  "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050",
        })
        opener = urllib.request.build_opener(proxy)
        urllib.request.install_opener(opener)
        print("[+] Tor activé via urllib proxy (127.0.0.1:9050)")
    _tor_enabled = True

def is_tor():
    return _tor_enabled

def get_requests_proxies():
    if _tor_enabled:
        return {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
    return {}
