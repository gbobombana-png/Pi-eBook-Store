import socket
import ssl
import urllib.request
import urllib.error

HSM_PORTS = [5000, 1500, 9000, 9001, 1501, 4002]
HSM_SIGNATURES = [b"HSM", b"Thales", b"nCipher", b"SafeNet", b"Utimaco", b"ATALLA"]

PCI_PIN_REQUIREMENTS = {
    "PIN_BLOCK_FORMAT": "ISO 9564-1 Format 0/3 required; Format 2 (old) deprecated",
    "KEY_LENGTH": "Minimum 128-bit (AES) or 112-bit (3DES) zone encryption keys",
    "KEY_MANAGEMENT": "Dual control and split knowledge for key loading (PCI PIN §12.3)",
    "HSM_VALIDATION": "FIPS 140-2 Level 3 minimum for HSM devices",
    "AUDIT_LOG": "All key management events must be logged (PCI PIN §14)",
}

DUKPT_SIGNATURES = ["DUKPT", "KSN", "BDK", "IKSN", "dukpt"]
AES_WEAK_MODES = ["ECB"]  # ECB mode for PIN blocks is forbidden


def _check_port(host, port, timeout=4):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def _probe_hsm(host, port, timeout=5):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.send(b"\x00\x02NC")  # Thales HSM status command
        data = sock.recv(256)
        sock.close()
        return data
    except Exception:
        return b""


def _fetch(url, timeout=8):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Security-Audit)"})
        resp = urllib.request.urlopen(req, context=ctx, timeout=timeout)
        return resp.read().decode(errors="ignore")
    except Exception:
        return ""


class PINSecurityAuditor:
    def __init__(self, logger):
        self.logger = logger

    def _detect_hsm(self, host, open_ports):
        findings = []
        hsm_found = False

        for port in open_ports:
            if port in HSM_PORTS:
                data = _probe_hsm(host, port)
                for sig in HSM_SIGNATURES:
                    if sig in data:
                        self.logger.success(f"HSM detected on port {port}: {sig.decode()}")
                        hsm_found = True
                        if port not in [5000]:  # standard HSM port
                            findings.append({
                                "severity": "MEDIUM",
                                "title": f"HSM on non-standard port: {port}",
                                "detail": f"HSM ({sig.decode()}) detected on port {port}. Verify firewall rules."
                            })
                        break

                if not hsm_found and port in HSM_PORTS:
                    findings.append({
                        "severity": "HIGH",
                        "title": f"Possible HSM port open without identification: {port}",
                        "detail": "Port typically used for HSM but signature not recognized. Manual investigation required."
                    })

        if not hsm_found:
            findings.append({
                "severity": "INFO",
                "title": "No HSM detected on known ports",
                "detail": "Hardware Security Module not found on standard ports. "
                         "Verify HSM is present and properly firewalled, or using non-standard port."
            })
            self.logger.info("No HSM detected on standard ports")

        return findings, hsm_found

    def _check_pin_security_headers(self, host, scheme="https", port=443):
        findings = []
        base = f"{scheme}://{host}:{port}"

        # Check for PIN-related endpoint exposure
        pin_paths = ["/api/pin", "/api/pin/change", "/api/pin/verify",
                    "/api/card/pin", "/api/v1/pin", "/pin/change"]

        for path in pin_paths:
            body = _fetch(f"{base}{path}")
            if body and len(body) > 20:
                # Check if PIN transmitted in cleartext
                if any(kw in body.lower() for kw in ["pin", "password", "passcode"]):
                    findings.append({
                        "severity": "CRITICAL",
                        "title": f"PIN endpoint exposed: {path}",
                        "detail": "PIN management endpoint publicly accessible. "
                                 "Verify authentication and encryption requirements."
                    })
                    self.logger.vuln("CRITICAL", f"PIN endpoint accessible: {path}")

        return findings

    def _audit_key_management_compliance(self):
        findings = []
        self.logger.info("Generating PCI PIN key management compliance checklist...")

        compliance_items = [
            ("CRITICAL", "DUKPT key management", "Verify DUKPT (ANSI X9.24) used for PEDs, not static keys"),
            ("HIGH", "Key ceremony documentation", "All key loading events must use dual control/split knowledge"),
            ("HIGH", "HSM FIPS 140-2 validation", "Verify HSM devices hold FIPS 140-2 Level 3 certification"),
            ("HIGH", "PIN block format", "Confirm ISO 9564-1 Format 0 or Format 3 used (not Format 2)"),
            ("MEDIUM", "EPP certification", "PCI-approved EPP device list compliance"),
            ("MEDIUM", "Key rotation schedule", "Zone keys must rotate at least annually (PCI PIN §12.3)"),
            ("MEDIUM", "Audit log completeness", "All key events logged with timestamp, operator, reason"),
            ("LOW", "Key destruction policy", "Superseded keys must be destroyed (zeroized) immediately"),
        ]

        for sev, title, detail in compliance_items:
            findings.append({"severity": sev, "title": f"[MANUAL CHECK] {title}", "detail": detail})
            self.logger.vuln(sev, f"Manual audit required: {title}", detail)

        return findings

    def run(self, host, open_ports, scheme="https", port=443):
        self.logger.section("PIN Security & HSM Audit")
        findings = []

        findings_hsm, hsm_found = self._detect_hsm(host, open_ports)
        findings.extend(findings_hsm)

        findings.extend(self._check_pin_security_headers(host, scheme, port))

        # PCI PIN compliance checklist (manual verification items)
        findings.extend(self._audit_key_management_compliance())

        # Summary
        self.logger.info("PCI PIN security requirements reference:")
        for req, desc in PCI_PIN_REQUIREMENTS.items():
            self.logger.info(f"  {req}: {desc}")

        return findings
