import sys
import datetime

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
MAGENTA= "\033[95m"
WHITE  = "\033[97m"

class Logger:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.findings = []

    def _ts(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def info(self, msg):
        print(f"{BLUE}[{self._ts()}] [*]{RESET} {msg}")

    def success(self, msg):
        print(f"{GREEN}[{self._ts()}] [+]{RESET} {BOLD}{msg}{RESET}")

    def warning(self, msg):
        print(f"{YELLOW}[{self._ts()}] [!]{RESET} {msg}")

    def error(self, msg):
        print(f"{RED}[{self._ts()}] [-]{RESET} {msg}")

    def vuln(self, severity, title, detail=""):
        colors = {"CRITICAL": RED, "HIGH": MAGENTA, "MEDIUM": YELLOW, "LOW": CYAN, "INFO": WHITE}
        c = colors.get(severity, WHITE)
        print(f"{c}[{self._ts()}] [VULN:{severity}]{RESET} {BOLD}{title}{RESET}")
        if detail:
            print(f"    {detail}")
        self.findings.append({"severity": severity, "title": title, "detail": detail, "time": self._ts()})

    def debug(self, msg):
        if self.verbose:
            print(f"{CYAN}[{self._ts()}] [DBG]{RESET} {msg}")

    def banner(self, text):
        width = 60
        print(f"\n{BOLD}{BLUE}{'='*width}{RESET}")
        print(f"{BOLD}{BLUE}  {text}{RESET}")
        print(f"{BOLD}{BLUE}{'='*width}{RESET}\n")

    def section(self, text):
        print(f"\n{BOLD}{CYAN}--- {text} ---{RESET}")
