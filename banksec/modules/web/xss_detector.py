import urllib.request
import urllib.parse
import urllib.error
import ssl

XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "'\"><script>alert(1)</script>",
    "<svg onload=alert(1)>",
    "javascript:alert(1)",
    "<body onload=alert(1)>",
    "\"><img src=x onerror=alert(1)>",
]

COMMON_PARAMS = ["q", "search", "query", "s", "keyword", "name", "msg",
                 "message", "comment", "input", "text", "value", "data",
                 "redirect", "url", "next", "return", "callback"]

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def _fetch(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Security-Audit)"})
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout)
        return resp.read().decode(errors="ignore"), resp.status
    except urllib.error.HTTPError as e:
        return e.read().decode(errors="ignore"), e.code
    except Exception:
        return "", 0


class XSSDetector:
    def __init__(self, logger):
        self.logger = logger

    def _is_reflected(self, payload, body):
        return payload in body or urllib.parse.quote(payload) in body

    def run(self, host, scheme="https", port=443, paths=None):
        self.logger.section("Cross-Site Scripting (XSS) Detection")
        findings = []

        if paths is None:
            paths = ["/search", "/", "/contact", "/feedback", "/api/search",
                    "/api/v1/search", "/comment", "/forum", "/message"]

        base = f"{scheme}://{host}" if port in (80, 443) else f"{scheme}://{host}:{port}"

        for path in paths:
            for param in COMMON_PARAMS[:5]:
                for payload in XSS_PAYLOADS[:4]:  # limit iterations
                    encoded = urllib.parse.quote(payload)
                    url = f"{base}{path}?{param}={encoded}"
                    body, status = _fetch(url)

                    if body and self._is_reflected(payload, body):
                        findings.append({
                            "severity": "HIGH",
                            "title": f"Reflected XSS in parameter: {param}",
                            "detail": f"Path: {path} | Payload reflected: {payload[:60]}"
                        })
                        self.logger.vuln("HIGH", f"Reflected XSS: {path}?{param}=...",
                                        f"Payload: {payload[:60]}")
                        break  # one XSS per param is enough

        # Check for DOM-based XSS indicators in source
        body, _ = _fetch(f"{base}/")
        dom_xss_sinks = ["document.write(", "innerHTML =", "eval(", "setTimeout(",
                         "document.location", "window.location", "document.cookie"]
        for sink in dom_xss_sinks:
            if sink in body:
                findings.append({
                    "severity": "MEDIUM",
                    "title": f"Potential DOM XSS sink: {sink}",
                    "detail": f"Dangerous JavaScript function found in page source: {sink}"
                })
                self.logger.vuln("MEDIUM", f"DOM XSS sink found: {sink}")

        # Check for open redirect (common XSS escalation)
        redirect_payloads = ["https://evil.com", "//evil.com", "/\\evil.com"]
        for param in ["redirect", "url", "next", "return", "callback", "dest"]:
            for payload in redirect_payloads[:1]:
                url = f"{base}/login?{param}={urllib.parse.quote(payload)}"
                body, status = _fetch(url)
                if "evil.com" in body:
                    findings.append({
                        "severity": "MEDIUM",
                        "title": f"Open Redirect: {param}",
                        "detail": f"Redirect parameter reflects external URL: {payload}"
                    })
                    self.logger.vuln("MEDIUM", f"Open Redirect via {param}")

        if not findings:
            self.logger.success("No XSS detected on tested endpoints")

        return findings
