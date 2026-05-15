import urllib.request
import urllib.parse
import urllib.error
import ssl
import json
import time

DEFAULT_CREDS = [
    ("admin", "admin"), ("admin", "password"), ("admin", "123456"),
    ("admin", "admin123"), ("root", "root"), ("root", "toor"),
    ("administrator", "administrator"), ("test", "test"),
    ("user", "user"), ("demo", "demo"), ("guest", "guest"),
    ("operator", "operator"), ("manager", "manager"),
    ("atm", "atm"), ("bank", "bank"), ("system", "system"),
    ("admin", ""), ("", ""),
]

LOGIN_PATHS = [
    "/login", "/admin", "/admin/login", "/wp-admin", "/administrator",
    "/api/login", "/api/auth", "/api/v1/auth", "/api/v1/login",
    "/user/login", "/account/login", "/signin", "/auth/signin",
    "/panel", "/console", "/management",
]

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def _post(url, data, timeout=8):
    try:
        payload = json.dumps(data).encode() if isinstance(data, dict) else urllib.parse.urlencode(data).encode()
        ctype = "application/json" if isinstance(data, dict) else "application/x-www-form-urlencoded"
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": ctype,
            "User-Agent": "Mozilla/5.0 (Security-Audit)"
        })
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout)
        return resp.read().decode(errors="ignore"), resp.status
    except urllib.error.HTTPError as e:
        return e.read().decode(errors="ignore"), e.code
    except Exception as e:
        return "", 0


def _get(url, timeout=5):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Security-Audit)"})
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout)
        return resp.read().decode(errors="ignore"), resp.status, dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.read().decode(errors="ignore"), e.code, {}
    except Exception:
        return "", 0, {}


class AuthTester:
    def __init__(self, logger):
        self.logger = logger

    def _detect_login_page(self, body):
        indicators = ["password", "login", "username", "sign in", "connexion", "mot de passe"]
        body_lower = body.lower()
        return any(i in body_lower for i in indicators)

    def _check_https_enforcement(self, host, port):
        findings = []
        http_url = f"http://{host}:{port if port != 80 else 80}/"
        body, status, headers = _get(http_url)
        location = headers.get("Location", "")
        if status in (200, 201) and not location.startswith("https"):
            findings.append({
                "severity": "HIGH",
                "title": "HTTP not redirected to HTTPS",
                "detail": f"http://{host}:{port}/ returns HTTP 200 without HTTPS redirect (PCI-DSS 4.2.1)"
            })
            self.logger.vuln("HIGH", "HTTP not redirected to HTTPS")
        elif location.startswith("https"):
            self.logger.success("HTTP → HTTPS redirect in place")
        return findings

    def _check_lockout(self, url, scheme):
        findings = []
        self.logger.info("Testing brute-force protection...")
        fail_count = 0
        for i in range(6):
            _, status = _post(url, {"username": "admin", "password": f"wrongpass{i}"})
            if status in (429, 423, 403):
                self.logger.success(f"Brute-force protection active (HTTP {status} after {i+1} attempts)")
                return findings
            if status in (200, 302):
                fail_count += 1
            time.sleep(0.3)

        if fail_count >= 5:
            findings.append({
                "severity": "HIGH",
                "title": "No brute-force protection on login",
                "detail": f"Login at {url} accepted 6+ failed attempts without lockout or CAPTCHA"
            })
            self.logger.vuln("HIGH", "No brute-force protection", f"URL: {url}")
        return findings

    def _test_default_creds(self, url, scheme):
        findings = []
        self.logger.info(f"Testing {len(DEFAULT_CREDS)} default credential pairs...")

        for user, pwd in DEFAULT_CREDS[:10]:  # limit to 10 to avoid account lockout
            body, status = _post(url, {"username": user, "password": pwd})
            body_low = body.lower()
            # Success indicators
            if status in (200, 302) and any(x in body_low for x in
                    ["dashboard", "welcome", "logout", "sign out", "profile", "account"]):
                findings.append({
                    "severity": "CRITICAL",
                    "title": f"Default credentials work: {user}:{pwd}",
                    "detail": f"Successfully authenticated at {url} with default credentials!"
                })
                self.logger.vuln("CRITICAL", f"Default creds accepted: {user}:{pwd}", url)
                return findings
            time.sleep(0.5)

        return findings

    def _check_security_headers(self, host, scheme, port):
        findings = []
        url = f"{scheme}://{host}:{port}/"
        _, _, headers = _get(url)

        required_headers = {
            "X-Frame-Options": "Clickjacking protection",
            "X-Content-Type-Options": "MIME-type sniffing protection",
            "Content-Security-Policy": "XSS/injection protection",
            "X-XSS-Protection": "Browser XSS filter",
            "Referrer-Policy": "Referrer information leakage",
        }

        dangerous_headers = {
            "Server": "Reveals server version",
            "X-Powered-By": "Reveals technology stack",
            "X-AspNet-Version": "Reveals .NET version",
        }

        for header, purpose in required_headers.items():
            if header not in headers and header.lower() not in {k.lower() for k in headers}:
                findings.append({
                    "severity": "MEDIUM",
                    "title": f"Missing security header: {header}",
                    "detail": f"{purpose} not configured"
                })
                self.logger.vuln("MEDIUM", f"Missing header: {header}")

        for header, risk in dangerous_headers.items():
            val = headers.get(header, headers.get(header.lower(), ""))
            if val:
                findings.append({
                    "severity": "LOW",
                    "title": f"Information disclosure header: {header}: {val}",
                    "detail": risk
                })
                self.logger.vuln("LOW", f"Info disclosure: {header}: {val[:60]}")

        return findings

    def run(self, host, scheme="https", port=443):
        self.logger.section("Authentication & Access Control")
        findings = []

        base = f"{scheme}://{host}" if port in (80, 443) else f"{scheme}://{host}:{port}"

        # HTTPS enforcement
        findings.extend(self._check_https_enforcement(host, 80))

        # Security headers
        findings.extend(self._check_security_headers(host, scheme, port))

        # Find active login page
        login_url = None
        for path in LOGIN_PATHS:
            url = base + path
            body, status, _ = _get(url)
            if status == 200 and self._detect_login_page(body):
                self.logger.success(f"Login page found: {url}")
                login_url = url
                break

        if login_url:
            findings.extend(self._check_lockout(login_url, scheme))
            findings.extend(self._test_default_creds(login_url, scheme))
        else:
            self.logger.info("No standard login page found")

        return findings
