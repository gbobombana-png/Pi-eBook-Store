import socket
from modules.network.port_scanner import PortScanner
from modules.network.ssl_analyzer import SSLAnalyzer
from modules.network.protocol_detector import ProtocolDetector
from modules.web.sqli_detector import SQLiDetector
from modules.web.xss_detector import XSSDetector
from modules.web.auth_tester import AuthTester
from modules.web.api_scanner import APIScanner
from modules.crypto.cipher_audit import CipherAuditor
from modules.atm.xfs_analyzer import XFSAnalyzer
from modules.atm.pin_security import PINSecurityAuditor

SCAN_MODES = {
    "full":    ["ports", "ssl", "protocols", "sqli", "xss", "auth", "api", "cipher", "atm", "pin"],
    "network": ["ports", "ssl", "protocols", "cipher"],
    "web":     ["sqli", "xss", "auth", "api"],
    "atm":     ["ports", "protocols", "atm", "pin"],
    "quick":   ["ports", "ssl", "auth"],
}


class Scanner:
    def __init__(self, logger, threads=50):
        self.logger = logger
        self.threads = threads

    def _resolve(self, host):
        try:
            ip = socket.gethostbyname(host)
            self.logger.success(f"Resolved {host} → {ip}")
            return ip
        except Exception as e:
            self.logger.error(f"Cannot resolve {host}: {e}")
            return None

    def run(self, host, mode="full", port_range=None, ssl_port=443):
        self.logger.banner(f"BankSec Audit — Target: {host}")
        all_findings = []

        ip = self._resolve(host)
        if not ip:
            return all_findings

        modules = SCAN_MODES.get(mode, SCAN_MODES["full"])
        self.logger.info(f"Scan mode: {mode.upper()} | Modules: {', '.join(modules)}")

        open_ports = []

        # Determine scheme from target
        scheme = "https"
        web_port = ssl_port

        # 1. Port scanning
        if "ports" in modules:
            scanner = PortScanner(self.logger, threads=self.threads)
            findings, open_ports = scanner.run(host, port_range)
            all_findings.extend(findings)

            # Adjust scheme if only HTTP available
            if 443 not in open_ports and 8443 not in open_ports:
                if 80 in open_ports or 8080 in open_ports:
                    scheme = "http"
                    web_port = 80 if 80 in open_ports else 8080

        # 2. SSL/TLS analysis
        if "ssl" in modules:
            ssl_port_to_use = ssl_port if ssl_port in open_ports else (
                8443 if 8443 in open_ports else (443 if 443 in open_ports else None)
            )
            if ssl_port_to_use:
                analyzer = SSLAnalyzer(self.logger)
                findings = analyzer.run(host, ssl_port_to_use)
                all_findings.extend(findings)
            else:
                self.logger.warning("No SSL port found, skipping SSL analysis")

        # 3. Banking protocol detection
        if "protocols" in modules:
            detector = ProtocolDetector(self.logger)
            findings = detector.run(host, open_ports)
            all_findings.extend(findings)

        # 4. SQL Injection
        if "sqli" in modules:
            detector = SQLiDetector(self.logger)
            findings = detector.run(host, scheme=scheme, port=web_port)
            all_findings.extend(findings)

        # 5. XSS
        if "xss" in modules:
            detector = XSSDetector(self.logger)
            findings = detector.run(host, scheme=scheme, port=web_port)
            all_findings.extend(findings)

        # 6. Authentication
        if "auth" in modules:
            tester = AuthTester(self.logger)
            findings = tester.run(host, scheme=scheme, port=web_port)
            all_findings.extend(findings)

        # 7. API security
        if "api" in modules:
            scanner = APIScanner(self.logger)
            findings = scanner.run(host, scheme=scheme, port=web_port)
            all_findings.extend(findings)

        # 8. Cipher audit
        if "cipher" in modules:
            ssl_target = ssl_port if ssl_port in open_ports else (443 if 443 in open_ports else None)
            if ssl_target:
                auditor = CipherAuditor(self.logger)
                findings = auditor.run(host, ssl_target)
                all_findings.extend(findings)

        # 9. ATM XFS analysis
        if "atm" in modules:
            analyzer = XFSAnalyzer(self.logger)
            findings = analyzer.run(host, open_ports)
            all_findings.extend(findings)

        # 10. PIN security
        if "pin" in modules:
            auditor = PINSecurityAuditor(self.logger)
            findings = auditor.run(host, open_ports, scheme=scheme, port=web_port)
            all_findings.extend(findings)

        # Summary
        self.logger.banner("Scan Complete")
        counts = {}
        for f in all_findings:
            sev = f["severity"]
            counts[sev] = counts.get(sev, 0) + 1

        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            cnt = counts.get(sev, 0)
            if cnt > 0:
                self.logger.info(f"  {sev:<10}: {cnt} finding(s)")

        return all_findings
