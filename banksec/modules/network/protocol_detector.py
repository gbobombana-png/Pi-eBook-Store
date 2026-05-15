import socket

# Banking protocol signatures
SIGNATURES = {
    "ISO 8583": [b"\x00\x00\x02", b"\x60\x00", b"ISO0", b"ISO1", b"ISO2"],
    "NDC (Diebold ATM)": [b"EMF", b"TC ", b"TA ", b"127"],
    "XFS/CEN": [b"XFS", b"WFS_", b"FRM_"],
    "APACS": [b"APACS", b"\x02\x00\x00\x00"],
    "OPC-UA": [b"OPC-UA", b"HEL\x00", b"MSG\x00"],
    "Modbus": [b"\x00\x00\x00\x00\x00\x06"],
    "SWIFT": [b"{1:", b"{2:", b"SWIFT"],
    "FIX Protocol": [b"8=FIX", b"8=FIXT"],
}

ATM_PORTS = [4000, 1234, 4004, 4001, 4002]
POS_PORTS  = [4100, 4200, 8000, 8583]


def probe_port(host, port, payload=b"\x00\x00\x00\x10", timeout=3.0):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.send(payload)
        data = sock.recv(512)
        sock.close()
        return data
    except Exception:
        return b""


class ProtocolDetector:
    def __init__(self, logger):
        self.logger = logger

    def detect_in_banner(self, data):
        detected = []
        for proto, sigs in SIGNATURES.items():
            for sig in sigs:
                if sig in data:
                    detected.append(proto)
                    break
        return detected

    def run(self, host, open_ports):
        self.logger.section("Banking Protocol Detection")
        findings = []
        detected_protos = {}

        ports_to_probe = list(set(open_ports) & set(ATM_PORTS + POS_PORTS + [502, 102, 20000, 4840]))

        for port in ports_to_probe:
            self.logger.info(f"Probing port {port} for banking protocols...")
            data = probe_port(host, port)

            if data:
                protos = self.detect_in_banner(data)
                if protos:
                    detected_protos[port] = protos
                    for p in protos:
                        self.logger.vuln("HIGH", f"Banking protocol detected: {p} on port {port}",
                                        f"Raw: {data[:40].hex()}")
                        findings.append({
                            "severity": "HIGH",
                            "title": f"Exposed banking protocol: {p}",
                            "detail": f"Port {port} responds to {p} probes. Raw: {data[:40].hex()}"
                        })

        # Check ISO 8583 on standard ports
        if 443 in open_ports or 80 in open_ports:
            port = 443 if 443 in open_ports else 80
            data = probe_port(host, port, b"GET / HTTP/1.0\r\n\r\n")
            protos = self.detect_in_banner(data)
            for p in protos:
                findings.append({
                    "severity": "MEDIUM",
                    "title": f"Protocol signature {p} found on web port",
                    "detail": f"Port {port} returned banking protocol signature"
                })

        # ATM protocol exposure check
        atm_exposed = list(set(open_ports) & set(ATM_PORTS))
        if atm_exposed:
            findings.append({
                "severity": "CRITICAL",
                "title": f"ATM protocol ports exposed: {atm_exposed}",
                "detail": "XFS/NDC ports accessible externally. Major ATM security risk."
            })
            self.logger.vuln("CRITICAL", f"ATM ports exposed to network: {atm_exposed}")

        # SWIFT/FIX financial protocol check
        for port in [9200, 8080, 8443]:
            if port in open_ports:
                data = probe_port(host, port, b"GET / HTTP/1.0\r\nHost: " + host.encode() + b"\r\n\r\n")
                protos = self.detect_in_banner(data)
                for p in protos:
                    if p in ("SWIFT", "FIX Protocol"):
                        findings.append({
                            "severity": "CRITICAL",
                            "title": f"Financial messaging protocol exposed: {p}",
                            "detail": f"Port {port} — SWIFT/FIX exposure is catastrophic for banking"
                        })

        if not findings:
            self.logger.success("No dangerous banking protocols detected on exposed ports")

        return findings
