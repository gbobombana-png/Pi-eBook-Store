import ssl
import socket

WEAK_CIPHER_PATTERNS = {
    "RC4":    "CRITICAL - RC4 stream cipher is completely broken (RFC 7465)",
    "DES":    "CRITICAL - DES (56-bit) cracked in <24h with brute force",
    "3DES":   "HIGH - Triple-DES vulnerable to SWEET32 birthday attack",
    "NULL":   "CRITICAL - NULL cipher provides no encryption whatsoever",
    "EXPORT": "CRITICAL - EXPORT ciphers intentionally weakened (FREAK/Logjam)",
    "anon":   "CRITICAL - Anonymous cipher: no server authentication (MITM trivial)",
    "MD5":    "HIGH - MD5 HMAC is cryptographically broken",
    "SHA1":   "MEDIUM - SHA-1 deprecated, use SHA-256+",
    "SEED":   "LOW - SEED (Korean cipher) not widely vetted",
    "IDEA":   "LOW - IDEA cipher is patent-encumbered and outdated",
    "ADH":    "CRITICAL - Anonymous Diffie-Hellman, no authentication",
    "AECDH":  "CRITICAL - Anonymous ECDH, no server authentication",
}

PERFECT_FORWARD_SECRECY_SUITES = ["ECDHE", "DHE"]
RECOMMENDED_CIPHERS = ["AES-256", "AES-128", "CHACHA20", "GCM", "CCM"]


def _get_all_ciphers(host, port):
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((host, port), timeout=8) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                return ssock.shared_ciphers() or []
    except Exception:
        return []


def _test_specific_cipher(host, port, cipher_name):
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers(cipher_name)
        with socket.create_connection((host, port), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                return True, ssock.cipher()
    except ssl.SSLError:
        return False, None
    except Exception:
        return False, None


class CipherAuditor:
    def __init__(self, logger):
        self.logger = logger

    def _check_pfs(self, ciphers):
        for cipher in ciphers:
            name = cipher[0] if isinstance(cipher, (list, tuple)) else cipher
            if any(pfs in name for pfs in PERFECT_FORWARD_SECRECY_SUITES):
                return True
        return False

    def run(self, host, port=443):
        self.logger.section("Cryptographic Cipher Audit")
        findings = []

        # Get negotiated ciphers
        ciphers = _get_all_ciphers(host, port)

        if not ciphers:
            self.logger.warning("Could not retrieve cipher list (no SSL on this port?)")
            return findings

        self.logger.info(f"Retrieved {len(ciphers)} cipher suite(s)")

        # Check for weak patterns
        for cipher in ciphers:
            name = cipher[0] if isinstance(cipher, (list, tuple)) else str(cipher)
            for pattern, explanation in WEAK_CIPHER_PATTERNS.items():
                if pattern.lower() in name.lower():
                    sev = "CRITICAL" if "CRITICAL" in explanation else "HIGH" if "HIGH" in explanation else "MEDIUM"
                    findings.append({
                        "severity": sev,
                        "title": f"Weak cipher suite supported: {name}",
                        "detail": explanation
                    })
                    self.logger.vuln(sev, f"Weak cipher: {name}", explanation)
                    break

        # Check PFS
        if not self._check_pfs(ciphers):
            findings.append({
                "severity": "HIGH",
                "title": "No Perfect Forward Secrecy (PFS) ciphers",
                "detail": "Without PFS (ECDHE/DHE), recording traffic today decrypts with future key compromise"
            })
            self.logger.vuln("HIGH", "No Perfect Forward Secrecy")
        else:
            self.logger.success("Perfect Forward Secrecy ciphers present (ECDHE/DHE)")

        # Test specific dangerous cipher suites
        dangerous_suites = [
            "RC4-MD5", "RC4-SHA", "DES-CBC-SHA", "NULL-SHA", "aNULL",
            "EXP-RC4-MD5", "EXP-DES-CBC-SHA"
        ]
        for suite in dangerous_suites:
            accepted, cipher_info = _test_specific_cipher(host, port, suite)
            if accepted:
                findings.append({
                    "severity": "CRITICAL",
                    "title": f"Server accepts critically weak cipher: {suite}",
                    "detail": f"Negotiated: {cipher_info}. This cipher provides no real security."
                })
                self.logger.vuln("CRITICAL", f"Server accepts: {suite}")

        # Summary
        good = [c[0] for c in ciphers if any(r in c[0] for r in RECOMMENDED_CIPHERS)]
        if good:
            self.logger.success(f"Strong ciphers present: {good[:3]}")

        return findings
