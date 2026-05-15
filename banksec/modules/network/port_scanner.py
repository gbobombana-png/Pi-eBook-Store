import socket
import concurrent.futures
import time

BANKING_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    80: "HTTP", 443: "HTTPS", 445: "SMB", 1433: "MSSQL",
    1521: "Oracle DB", 3306: "MySQL", 3389: "RDP",
    4000: "XFS CEN/ATM", 5000: "HSM", 7001: "WebLogic",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 8181: "HTTP-Alt2",
    9090: "WebSphere", 9200: "Elasticsearch", 27017: "MongoDB",
    5432: "PostgreSQL", 6379: "Redis", 11211: "Memcached",
    502: "Modbus", 102: "S7comm (PLC)", 20000: "DNP3",
    4840: "OPC-UA", 8728: "MikroTik API", 8729: "MikroTik API-SSL",
    1234: "NDC ATM", 2222: "SSH-Alt", 4444: "Metasploit",
    5900: "VNC", 8888: "HTTP-Alt3", 10000: "Webmin",
}

DANGEROUS_PORTS = {23, 21, 445, 4000, 1234, 5900, 4444, 9200, 6379, 11211, 27017}
CLEARTEXT_PORTS = {21, 23, 80, 502, 102, 20000}


def scan_port(host, port, timeout=2.0):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return port, result == 0
    except Exception:
        return port, False


def grab_banner(host, port, timeout=3.0):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
        banner = sock.recv(1024).decode(errors="ignore").strip()
        sock.close()
        return banner[:200] if banner else ""
    except Exception:
        return ""


class PortScanner:
    def __init__(self, logger, threads=50):
        self.logger = logger
        self.threads = threads

    def run(self, host, port_range=None):
        self.logger.section("Port Scanner")
        findings = []

        if port_range:
            start, end = map(int, port_range.split("-"))
            ports = list(range(start, end + 1))
        else:
            ports = list(BANKING_PORTS.keys())

        self.logger.info(f"Scanning {len(ports)} ports on {host} with {self.threads} threads...")
        open_ports = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as ex:
            futures = {ex.submit(scan_port, host, p): p for p in ports}
            for future in concurrent.futures.as_completed(futures):
                port, is_open = future.result()
                if is_open:
                    open_ports.append(port)

        open_ports.sort()
        self.logger.success(f"Found {len(open_ports)} open port(s): {open_ports}")

        for port in open_ports:
            service = BANKING_PORTS.get(port, "Unknown")
            banner = grab_banner(host, port)

            if port in DANGEROUS_PORTS:
                sev = "HIGH"
                detail = f"Port {port}/{service} is open and dangerous in a banking context"
                if banner:
                    detail += f" | Banner: {banner[:100]}"
                findings.append({"severity": sev, "title": f"Dangerous port open: {port}/{service}", "detail": detail})
                self.logger.vuln(sev, f"Dangerous port open: {port}/{service}", detail)
            elif port in CLEARTEXT_PORTS:
                findings.append({
                    "severity": "HIGH",
                    "title": f"Cleartext protocol: {port}/{service}",
                    "detail": f"Port {port} transmits data without encryption"
                })
                self.logger.vuln("HIGH", f"Cleartext protocol: {port}/{service}")
            else:
                self.logger.info(f"Open: {port}/{service}" + (f" | {banner[:80]}" if banner else ""))

        # Check for Telnet (critical in banking)
        if 23 in open_ports:
            findings.append({
                "severity": "CRITICAL",
                "title": "Telnet enabled (port 23)",
                "detail": "Telnet transmits credentials in plaintext. PCI-DSS prohibits its use."
            })
            self.logger.vuln("CRITICAL", "Telnet enabled", "PCI-DSS prohibits cleartext remote access")

        # Check for unauthenticated services
        if 9200 in open_ports:
            findings.append({
                "severity": "CRITICAL",
                "title": "Elasticsearch exposed (port 9200)",
                "detail": "Unauthenticated Elasticsearch can expose customer financial data"
            })

        if 6379 in open_ports:
            findings.append({
                "severity": "HIGH",
                "title": "Redis exposed (port 6379)",
                "detail": "Redis without auth can be used for RCE and data theft"
            })

        return findings, open_ports
