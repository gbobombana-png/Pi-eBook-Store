#!/usr/bin/env python3
"""
BankSec - Banking & ATM Security Audit Framework
Expert-level vulnerability detection for financial systems
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logger import Logger
from core.scanner import Scanner, SCAN_MODES
from core.reporter import Reporter
from core.proxy import enable_tor

BANNER = r"""
 ____              _    ____
| __ )  __ _ _ __ | | _/ ___|  ___  ___
|  _ \ / _` | '_ \| |/ /\___ \/ _ \/ __|
| |_) | (_| | | | |   <  ___) |  __/ (__
|____/ \__,_|_| |_|_|\_\|____/ \___|\___|

  Banking & ATM Security Audit Framework v1.1
  For authorized security testing only
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="BankSec — Banking & ATM Security Audit Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --target testphp.vulnweb.com --mode web
  python main.py --target 192.168.1.100 --mode atm --tor
  python main.py --target bank.example.com --mode full --format html --thesis
  python main.py --target 10.0.0.1 --mode network --port-range 1-10000
  python main.py --target bank.example.com --tor --thesis --format all
        """
    )
    parser.add_argument("--target",      required=True,  help="Target host or IP")
    parser.add_argument("--mode",        default="full", choices=list(SCAN_MODES.keys()),
                        help="Scan mode (default: full)")
    parser.add_argument("--port-range",  default=None,   metavar="START-END",
                        help="Custom port range (e.g. 1-65535)")
    parser.add_argument("--ssl-port",    default=443,    type=int,
                        help="SSL/TLS port to analyze (default: 443)")
    parser.add_argument("--output",      default="reports", help="Output directory for reports")
    parser.add_argument("--format",      default="all",  choices=["json", "txt", "html", "all"],
                        help="Report format (default: all)")
    parser.add_argument("--threads",     default=50,     type=int,
                        help="Thread count for port scanner (default: 50)")
    parser.add_argument("--verbose",     action="store_true", help="Verbose debug output")
    parser.add_argument("--tor",         action="store_true",
                        help="Route all traffic through Tor (127.0.0.1:9050)")
    parser.add_argument("--thesis",      action="store_true",
                        help="Thesis mode: add OWASP/CVE/PCI-DSS references to reports")
    return parser.parse_args()


def main():
    print(BANNER)
    args = parse_args()

    # Activer Tor si demandé
    if args.tor:
        enable_tor()

    logger = Logger(verbose=args.verbose)
    scanner = Scanner(logger, threads=args.threads)

    logger.info(f"Target  : {args.target}")
    logger.info(f"Mode    : {args.mode}")
    logger.info(f"Tor     : {'ACTIF' if args.tor else 'désactivé'}")
    logger.info(f"Thèse   : {'ACTIF' if args.thesis else 'désactivé'}")
    logger.info(f"Threads : {args.threads}")
    logger.info(f"Output  : {args.output}/")
    print()

    findings = scanner.run(
        host=args.target,
        mode=args.mode,
        port_range=args.port_range,
        ssl_port=args.ssl_port,
    )

    if findings:
        reporter = Reporter(
            target=args.target,
            findings=findings,
            output_dir=args.output,
            thesis_mode=args.thesis,
        )
        reporter.save(fmt=args.format)
    else:
        logger.success("No vulnerabilities found — target appears secure")

    return 0


if __name__ == "__main__":
    sys.exit(main())
