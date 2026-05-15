import urllib.request
import urllib.parse
import urllib.error
import ssl
import json

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

SENSITIVE_ENDPOINTS = [
    "/api/users", "/api/accounts", "/api/cards", "/api/transactions",
    "/api/admin", "/api/v1/users", "/api/v1/accounts", "/api/v2/users",
    "/api/keys", "/api/secrets", "/api/config", "/api/debug",
    "/api/internal", "/api/private", "/api/export", "/api/dump",
    "/swagger.json", "/swagger-ui.html", "/swagger-ui/", "/api-docs",
    "/openapi.json", "/v1/api-docs", "/v2/api-docs", "/v3/api-docs",
    "/docs", "/redoc", "/graphql", "/graphiql", "/.env",
    "/config.json", "/settings.json", "/secrets.json", "/.git/config",
    "/backup.sql", "/database.sql", "/dump.sql", "/phpinfo.php",
    "/server-status", "/server-info", "/_status", "/health",
    "/metrics", "/actuator", "/actuator/env", "/actuator/beans",
    "/actuator/mappings", "/actuator/health",
]

BOLA_TEST_IDS = ["1", "2", "100", "999", "admin", "0", "-1", "null"]


def _fetch(url, timeout=8, method="GET", data=None, headers=None):
    try:
        h = {"User-Agent": "Mozilla/5.0 (Security-Audit)"}
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, data=data, headers=h, method=method)
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout)
        body = resp.read().decode(errors="ignore")
        return body, resp.status, dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.read().decode(errors="ignore"), e.code, {}
    except Exception:
        return "", 0, {}


class APIScanner:
    def __init__(self, logger):
        self.logger = logger

    def _check_swagger(self, base):
        findings = []
        swagger_paths = ["/swagger.json", "/swagger-ui.html", "/openapi.json",
                        "/api-docs", "/v2/api-docs", "/v3/api-docs"]
        for path in swagger_paths:
            body, status, _ = _fetch(base + path)
            if status == 200 and any(kw in body for kw in ["swagger", "openapi", "paths", "info"]):
                self.logger.vuln("MEDIUM", f"API Documentation exposed: {path}",
                                "Full API schema publicly accessible. Aids attackers.")
                findings.append({
                    "severity": "MEDIUM",
                    "title": f"API documentation publicly exposed: {path}",
                    "detail": "Swagger/OpenAPI docs accessible without authentication"
                })
        return findings

    def _check_sensitive_endpoints(self, base):
        findings = []
        for path in SENSITIVE_ENDPOINTS:
            body, status, headers = _fetch(base + path)
            if status == 200:
                content_type = headers.get("Content-Type", headers.get("content-type", ""))
                is_json = "json" in content_type or body.strip().startswith("{") or body.strip().startswith("[")

                severity = "HIGH" if any(kw in path for kw in
                    ["admin", "secret", "config", "env", "debug", "internal", "private",
                     "export", "dump", "actuator", "metrics"]) else "MEDIUM"

                if path.endswith((".env", ".sql", ".git/config", "phpinfo.php")):
                    severity = "CRITICAL"

                self.logger.vuln(severity, f"Sensitive endpoint accessible: {path}",
                               f"HTTP {status} | Content-Type: {content_type[:40]}")
                findings.append({
                    "severity": severity,
                    "title": f"Sensitive endpoint exposed: {path}",
                    "detail": f"HTTP {status} — accessible without authentication | {content_type[:60]}"
                })
        return findings

    def _check_bola(self, base, open_paths):
        findings = []
        self.logger.info("Testing BOLA/IDOR (Broken Object Level Authorization)...")

        for path in open_paths:
            if not any(p in path for p in ["/user", "/account", "/card", "/transaction"]):
                continue
            for test_id in BOLA_TEST_IDS[:4]:
                url = f"{base}{path}/{test_id}"
                body, status, _ = _fetch(url)
                if status == 200 and len(body) > 50:
                    findings.append({
                        "severity": "CRITICAL",
                        "title": f"BOLA/IDOR: {path}/{{id}} accessible",
                        "detail": f"Object ID {test_id} returned data without authorization check"
                    })
                    self.logger.vuln("CRITICAL", f"BOLA/IDOR on {path}/{test_id}")
                    break
        return findings

    def _check_mass_assignment(self, base):
        findings = []
        test_paths = ["/api/v1/user", "/api/user", "/api/account", "/api/register"]
        dangerous_fields = ["role", "admin", "is_admin", "permissions", "balance", "credit"]

        for path in test_paths:
            for field in dangerous_fields[:3]:
                payload = json.dumps({field: True, "admin": True, "role": "admin"}).encode()
                body, status, _ = _fetch(base + path, method="POST", data=payload,
                                         headers={"Content-Type": "application/json"})
                if status in (200, 201) and any(k in body for k in ["success", "created", "updated"]):
                    findings.append({
                        "severity": "HIGH",
                        "title": f"Mass Assignment vulnerability: {path}",
                        "detail": f"Server accepted privileged field '{field}' in request body"
                    })
                    self.logger.vuln("HIGH", f"Mass Assignment: {path}", f"Field: {field}")
        return findings

    def run(self, host, scheme="https", port=443):
        self.logger.section("API Security Scan")
        findings = []

        base = f"{scheme}://{host}" if port in (80, 443) else f"{scheme}://{host}:{port}"

        findings.extend(self._check_swagger(base))
        findings.extend(self._check_sensitive_endpoints(base))
        findings.extend(self._check_mass_assignment(base))

        # Collect open API paths for BOLA test
        open_paths = []
        for path in ["/api/v1/users", "/api/accounts", "/api/cards"]:
            _, status, _ = _fetch(base + path)
            if status == 200:
                open_paths.append(path)

        findings.extend(self._check_bola(base, open_paths))

        if not findings:
            self.logger.success("No critical API vulnerabilities detected")

        return findings
