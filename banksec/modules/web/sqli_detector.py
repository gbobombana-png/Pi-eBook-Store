import urllib.request
import urllib.parse
import urllib.error
import ssl
import time

# SQL injection test payloads (detection only, no exploitation)
PAYLOADS = {
    "error_based": [
        "'", "\"", "' OR '1'='1", "' OR 1=1--", "\" OR \"1\"=\"1",
        "1' AND 1=CONVERT(int,(SELECT TOP 1 name FROM sysobjects))--",
        "' AND 1=2 UNION SELECT NULL--",
        "1 AND SLEEP(0)--",
    ],
    "time_based": [
        "1' AND SLEEP(3)--", "1; WAITFOR DELAY '0:0:3'--",
        "1' AND (SELECT * FROM (SELECT(SLEEP(3)))a)--",
    ],
    "blind": [
        "1' AND '1'='1", "1' AND '1'='2",
        "1 AND 1=1", "1 AND 1=2",
    ],
}

ERROR_SIGNATURES = [
    "sql syntax", "mysql_fetch", "ora-", "oracle error",
    "microsoft sql", "unclosed quotation", "syntax error",
    "unterminated string", "pg_query", "warning: pg_",
    "sqlite3.operationalerror", "jdbc", "odbc", "db2 sql",
    "sql server", "operationalerror", "sqlstate", "sqlite",
]

COMMON_PARAMS = ["id", "user", "username", "pass", "password", "search", "q",
                 "query", "account", "card", "number", "ref", "token", "page",
                 "cat", "category", "product", "order", "sort", "filter"]

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def _fetch(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Security-Audit)"})
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout)
        return resp.read().decode(errors="ignore"), resp.status, dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.read().decode(errors="ignore"), e.code, {}
    except Exception:
        return "", 0, {}


class SQLiDetector:
    def __init__(self, logger):
        self.logger = logger

    def _has_sqli_error(self, body):
        body_lower = body.lower()
        for sig in ERROR_SIGNATURES:
            if sig in body_lower:
                return sig
        return None

    def _test_param(self, base_url, param, scheme):
        findings = []

        # Error-based
        for payload in PAYLOADS["error_based"]:
            url = f"{base_url}?{param}={urllib.parse.quote(payload)}"
            body, status, _ = _fetch(url)
            sig = self._has_sqli_error(body)
            if sig:
                self.logger.vuln("CRITICAL", f"SQL Injection (error-based): {param}",
                                f"URL: {url[:100]} | Signature: {sig}")
                findings.append({
                    "severity": "CRITICAL",
                    "title": f"SQL Injection detected in parameter: {param}",
                    "detail": f"Error-based SQLi. URL: {url[:120]} | DB error: {sig}"
                })
                return findings  # confirmed, no need to keep testing

        # Time-based (blind)
        for payload in PAYLOADS["time_based"]:
            url = f"{base_url}?{param}={urllib.parse.quote(payload)}"
            t0 = time.time()
            body, status, _ = _fetch(url, timeout=10)
            elapsed = time.time() - t0
            if elapsed >= 2.5:
                self.logger.vuln("HIGH", f"SQL Injection (time-based blind): {param}",
                                f"URL: {url[:100]} | Delay: {elapsed:.1f}s")
                findings.append({
                    "severity": "HIGH",
                    "title": f"Blind SQL Injection (time-based): {param}",
                    "detail": f"Response delayed {elapsed:.1f}s with payload: {payload[:60]}"
                })
                return findings

        return findings

    def run(self, host, scheme="https", port=443, paths=None):
        self.logger.section("SQL Injection Detection")
        findings = []

        if paths is None:
            paths = ["/login", "/search", "/api/user", "/api/account", "/api/v1/user",
                    "/account", "/profile", "/card", "/transaction", "/transfer",
                    "/admin", "/admin/login", "/api/login", "/api/auth"]

        base = f"{scheme}://{host}" if port in (80, 443) else f"{scheme}://{host}:{port}"

        for path in paths:
            url = base + path
            self.logger.debug(f"Testing SQLi on {url}")

            for param in COMMON_PARAMS[:6]:  # test top 6 params per path
                found = self._test_param(url, param, scheme)
                findings.extend(found)

                if len(findings) >= 5:  # cap findings to avoid hammering
                    self.logger.warning("SQLi cap reached, stopping")
                    return findings

        # Check for UNION-based on homepage
        url = f"{base}/"
        body, _, _ = _fetch(f"{url}?id=1 UNION SELECT NULL,NULL--")
        if self._has_sqli_error(body):
            findings.append({
                "severity": "CRITICAL",
                "title": "UNION-based SQL Injection on root path",
                "detail": f"UNION SELECT returned SQL error on {url}"
            })

        if not findings:
            self.logger.success("No SQL injection detected on tested endpoints")

        return findings
