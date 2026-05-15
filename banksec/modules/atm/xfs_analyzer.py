import socket
import struct
import time

# XFS/CEN standard port and common variants
XFS_PORTS = [4000, 4001, 4002, 4004, 9001, 12001]
NDC_PORTS = [1234, 4000, 4023, 5023]

# XFS WFSOpenService probe (simplified)
XFS_PROBE = b"\x00\x00\x00\x1c\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00"
# NDC ATM terminal command (EMF status request)
NDC_PROBE = b"EMF\x00"
# Generic ping probes
GENERIC_PROBES = [
    b"\x00\x00\x00\x04",
    b"PING\r\n",
    b"STATUS\r\n",
    b"\xff\xfd\x18",  # Telnet IAC negotiation
]

XFS_RESPONSE_SIGS = [b"XFS", b"WFS_", b"FRM_", b"SPI_", b"WOSA", b"CEN"]
NDC_RESPONSE_SIGS = [b"EMF", b"TC ", b"TA ", b"SDM"]

CRITICAL_XFS_COMMANDS = {
    "WFS_CMD_CDM_DISPENSE": "Cash dispense command — if accepted unauthenticated: ATM jackpot",
    "WFS_CMD_PIN_GET_DATA": "PIN capture command — could intercept PINs",
    "WFS_CMD_CAM_TAKE_PICTURE": "ATM camera control",
    "WFS_CMD_IDC_EJECT_CARD": "Card ejector — card trapping attack",
}


def _probe_port(host, port, payload, timeout=4.0):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.send(payload)
        time.sleep(0.5)
        data = sock.recv(1024)
        sock.close()
        return data
    except Exception:
        return b""


def _check_unauthenticated_xfs(host, port):
    for probe in GENERIC_PROBES:
        data = _probe_port(host, port, probe)
        if data:
            for sig in XFS_RESPONSE_SIGS:
                if sig in data:
                    return True, data
            for sig in NDC_RESPONSE_SIGS:
                if sig in data:
                    return True, data
    return False, b""


class XFSAnalyzer:
    def __init__(self, logger):
        self.logger = logger

    def _detect_xfs(self, host, port):
        data = _probe_port(host, port, XFS_PROBE)
        if data:
            for sig in XFS_RESPONSE_SIGS:
                if sig in data:
                    return True, "XFS", data
        return False, None, b""

    def _detect_ndc(self, host, port):
        data = _probe_port(host, port, NDC_PROBE)
        if data:
            for sig in NDC_RESPONSE_SIGS:
                if sig in data:
                    return True, "NDC", data
        return False, None, b""

    def run(self, host, open_ports):
        self.logger.section("ATM XFS/NDC Protocol Analysis")
        findings = []

        atm_ports_found = list(set(open_ports) & set(XFS_PORTS + NDC_PORTS))

        if not atm_ports_found:
            self.logger.info("No known ATM protocol ports open")
            return findings

        self.logger.warning(f"ATM protocol ports detected: {atm_ports_found}")

        for port in atm_ports_found:
            self.logger.info(f"Probing ATM protocols on port {port}...")

            # XFS detection
            detected, proto, raw = self._detect_xfs(host, port)
            if not detected:
                detected, proto, raw = self._detect_ndc(host, port)

            if detected:
                findings.append({
                    "severity": "CRITICAL",
                    "title": f"ATM {proto} protocol accessible on port {port}",
                    "detail": f"ATM control protocol exposed on network. Raw: {raw[:32].hex()}"
                })
                self.logger.vuln("CRITICAL", f"ATM {proto} protocol on port {port}",
                                f"Raw response: {raw[:32].hex()}")

                # Check unauthenticated access
                unauth, data = _check_unauthenticated_xfs(host, port)
                if unauth:
                    findings.append({
                        "severity": "CRITICAL",
                        "title": f"Unauthenticated ATM command access on port {port}",
                        "detail": "ATM responds to commands without authentication. "
                                 "Remote cash dispensing (ATM Jackpot) may be possible."
                    })
                    self.logger.vuln("CRITICAL",
                                    "Unauthenticated ATM access — potential jackpot attack vector",
                                    f"Response: {data[:32].hex()}")
            else:
                # Port open but protocol not identified
                findings.append({
                    "severity": "HIGH",
                    "title": f"Unknown service on ATM port {port}",
                    "detail": "Port associated with ATM protocols is open but protocol unidentified"
                })
                self.logger.vuln("HIGH", f"ATM port {port} open (unknown service)")

        # Network segmentation check
        if atm_ports_found:
            findings.append({
                "severity": "CRITICAL",
                "title": "ATM ports reachable from audit network",
                "detail": "ATM/XFS ports should ONLY be accessible from the bank's internal ATM network. "
                         "Network segmentation (VLAN/firewall) is missing or misconfigured. "
                         "PCI-DSS requirement 1.3.2 violated."
            })

        return findings
