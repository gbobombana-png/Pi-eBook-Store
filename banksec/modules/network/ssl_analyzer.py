import ssl
import socket
import datetime

WEAK_PROTOCOLS = ["SSLv2", "SSLv3", "TLSv1", "TLSv1.1"]
WEAK_CIPHERS = ["RC4", "DES", "3DES", "NULL", "EXPORT", "anon", "MD5"]

PROTOCOL_MAP = {
    ssl.PROTOCOL_TLS_CLIENT: "TLS",
}


def _try_protocol(host, port, protocol_version):
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        if protocol_version == "SSLv2":
            return False
        elif protocol_version == "SSLv3":
            ctx.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_2 | ssl.OP_NO_TLSv1_3
            return False
        elif protocol_version == "TLSv1":
            ctx.minimum_version = ssl.TLSVersion.TLSv1
            ctx.maximum_version = ssl.TLSVersion.TLSv1
        elif protocol_version == "TLSv1.1":
            ctx.minimum_version = ssl.TLSVersion.TLSv1_1
            ctx.maximum_version = ssl.TLSVersion.TLSv1_1
        else:
            return False
        with socket.create_connection((host, port), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                return True
    except Exception:
        return False


class SSLAnalyzer:
    def __init__(self, logger):
        self.logger = logger

    def run(self, host, port=443):
        self.logger.section("SSL/TLS Analysis")
        findings = []

        # Get certificate
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with socket.create_connection((host, port), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()

            self.logger.success(f"SSL connected: {version} | Cipher: {cipher[0]}")

            # Check TLS version
            if version in ("TLSv1", "TLSv1.1", "SSLv3"):
                findings.append({
                    "severity": "HIGH",
                    "title": f"Weak TLS version negotiated: {version}",
                    "detail": "TLS 1.0/1.1 are deprecated. Use TLS 1.2+ (PCI-DSS requirement)"
                })
                self.logger.vuln("HIGH", f"Weak TLS: {version}")
            else:
                self.logger.success(f"TLS version OK: {version}")

            # Check cipher strength
            for weak in WEAK_CIPHERS:
                if weak.lower() in cipher[0].lower():
                    findings.append({
                        "severity": "HIGH",
                        "title": f"Weak cipher in use: {cipher[0]}",
                        "detail": f"Cipher contains {weak} which is cryptographically broken"
                    })
                    self.logger.vuln("HIGH", f"Weak cipher: {cipher[0]}")
                    break

            # Certificate expiry
            if cert:
                exp_str = cert.get("notAfter", "")
                if exp_str:
                    exp_date = datetime.datetime.strptime(exp_str, "%b %d %H:%M:%S %Y %Z")
                    days_left = (exp_date - datetime.datetime.utcnow()).days
                    if days_left < 0:
                        findings.append({
                            "severity": "CRITICAL",
                            "title": "SSL Certificate EXPIRED",
                            "detail": f"Certificate expired {abs(days_left)} days ago"
                        })
                        self.logger.vuln("CRITICAL", "SSL Certificate expired")
                    elif days_left < 30:
                        findings.append({
                            "severity": "HIGH",
                            "title": f"SSL Certificate expires in {days_left} days",
                            "detail": "Renew immediately to avoid service disruption"
                        })
                        self.logger.vuln("HIGH", f"Certificate expires soon: {days_left} days")
                    else:
                        self.logger.success(f"Certificate valid for {days_left} more days")

                # Check signature algorithm (SHA-1 is broken)
                sig_alg = cert.get("signatureAlgorithm", "")
                if "sha1" in sig_alg.lower():
                    findings.append({
                        "severity": "HIGH",
                        "title": "Certificate uses SHA-1 signature",
                        "detail": "SHA-1 is cryptographically broken. Browsers distrust these certs."
                    })
                    self.logger.vuln("HIGH", "SHA-1 certificate signature")

                # Check SAN
                san = cert.get("subjectAltName", [])
                if not san:
                    findings.append({
                        "severity": "MEDIUM",
                        "title": "No Subject Alternative Name (SAN)",
                        "detail": "Modern browsers require SAN for HTTPS validation"
                    })

        except ssl.SSLError as e:
            findings.append({
                "severity": "HIGH",
                "title": f"SSL Error on port {port}",
                "detail": str(e)
            })
            self.logger.warning(f"SSL error: {e}")
        except ConnectionRefusedError:
            self.logger.warning(f"Port {port} closed or no SSL")
            return findings
        except Exception as e:
            self.logger.warning(f"SSL analysis error: {e}")

        # Test for weak protocol acceptance
        self.logger.info("Testing weak protocol acceptance...")
        for proto in ["TLSv1", "TLSv1.1"]:
            if _try_protocol(host, port, proto):
                findings.append({
                    "severity": "HIGH",
                    "title": f"Server accepts deprecated {proto}",
                    "detail": "Disable TLS 1.0 and 1.1 in server config (PCI-DSS 6.4.1)"
                })
                self.logger.vuln("HIGH", f"Server accepts {proto}")

        # Check HSTS header
        try:
            import urllib.request
            req = urllib.request.Request(f"https://{host}:{port}/", headers={"User-Agent": "BankSec/1.0"})
            ctx2 = ssl.create_default_context()
            ctx2.check_hostname = False
            ctx2.verify_mode = ssl.CERT_NONE
            resp = urllib.request.urlopen(req, context=ctx2, timeout=5)
            hsts = resp.headers.get("Strict-Transport-Security", "")
            if not hsts:
                findings.append({
                    "severity": "MEDIUM",
                    "title": "Missing HSTS header",
                    "detail": "Strict-Transport-Security header not set. Enables downgrade attacks."
                })
                self.logger.vuln("MEDIUM", "Missing HSTS header")
            else:
                self.logger.success(f"HSTS present: {hsts[:60]}")
        except Exception:
            pass

        return findings
