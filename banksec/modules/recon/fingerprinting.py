import urllib.request
import urllib.error
import ssl
import socket
import re

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# Signatures technologiques
TECH_SIGNATURES = {
    "WordPress":    ["wp-content", "wp-includes", "wp-json"],
    "Joomla":       ["joomla", "/components/com_", "Joomla!"],
    "Drupal":       ["Drupal", "/sites/default/", "drupal.js"],
    "Apache":       ["Apache/", "apache"],
    "Nginx":        ["nginx/", "Nginx"],
    "IIS":          ["Microsoft-IIS", "ASP.NET"],
    "PHP":          ["X-Powered-By: PHP", "PHPSESSID"],
    "Django":       ["csrfmiddlewaretoken", "django"],
    "Laravel":      ["laravel_session", "Laravel"],
    "jQuery":       ["jquery", "jQuery"],
    "Bootstrap":    ["bootstrap.min.css", "bootstrap.min.js"],
    "React":        ["react.js", "react-dom", "__REACT"],
    "Angular":      ["ng-version", "angular.js"],
    "Tomcat":       ["Apache Tomcat", "Tomcat"],
    "WebLogic":     ["WebLogic", "weblogic"],
    "WebSphere":    ["WebSphere", "websphere"],
    "Spring":       ["X-Application-Context", "spring"],
    "Struts":       ["struts", "action.do", ".action"],
}

WAF_SIGNATURES = {
    "Cloudflare":   ["cloudflare", "cf-ray", "__cfduid"],
    "AWS WAF":      ["awswaf", "x-amzn-requestid"],
    "F5 BIG-IP":    ["bigip", "f5-"],
    "Imperva":      ["imperva", "incapsula", "visid_incap"],
    "ModSecurity":  ["mod_security", "ModSecurity"],
    "Sucuri":       ["sucuri", "x-sucuri-id"],
    "Akamai":       ["akamai", "x-akamai"],
}


def _fetch(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout)
        body = resp.read(50000).decode(errors="ignore")
        headers = dict(resp.headers)
        return body, headers, resp.status
    except urllib.error.HTTPError as e:
        return e.read(10000).decode(errors="ignore"), dict(e.headers), e.code
    except Exception:
        return "", {}, 0


def _ttl_os(host):
    try:
        import subprocess
        result = subprocess.run(["ping", "-c", "1", "-W", "2", host],
                               capture_output=True, text=True, timeout=5)
        match = re.search(r"ttl=(\d+)", result.stdout, re.IGNORECASE)
        if match:
            ttl = int(match.group(1))
            if ttl <= 64:
                return f"Linux/Unix (TTL={ttl})"
            elif ttl <= 128:
                return f"Windows (TTL={ttl})"
            else:
                return f"Cisco/Network device (TTL={ttl})"
    except Exception:
        pass
    return "Unknown"


class Fingerprinter:
    def __init__(self, logger):
        self.logger = logger

    def _detect_tech(self, body, headers):
        detected = []
        combined = body.lower() + " ".join(f"{k}: {v}" for k, v in headers.items()).lower()
        for tech, sigs in TECH_SIGNATURES.items():
            for sig in sigs:
                if sig.lower() in combined:
                    detected.append(tech)
                    break
        return list(set(detected))

    def _detect_waf(self, body, headers):
        detected = []
        combined = body.lower() + " ".join(f"{k}: {v}" for k, v in headers.items()).lower()
        for waf, sigs in WAF_SIGNATURES.items():
            for sig in sigs:
                if sig.lower() in combined:
                    detected.append(waf)
                    break
        return list(set(detected))

    def _get_server_info(self, headers):
        info = {}
        for key in ["Server", "X-Powered-By", "X-AspNet-Version", "X-Generator",
                    "X-Drupal-Cache", "X-Varnish", "Via"]:
            val = headers.get(key, headers.get(key.lower(), ""))
            if val:
                info[key] = val
        return info

    def run(self, host, scheme="https", port=443):
        self.logger.section("Fingerprinting & Reconnaissance")
        findings = []

        base = f"{scheme}://{host}" if port in (80, 443) else f"{scheme}://{host}:{port}"

        # OS detection via TTL
        os_guess = _ttl_os(host)
        self.logger.info(f"OS estimé (TTL): {os_guess}")
        findings.append({"severity": "INFO", "title": f"OS fingerprint: {os_guess}",
                        "detail": "Basé sur l'analyse TTL des paquets ICMP"})

        # HTTP fingerprinting
        body, headers, status = _fetch(base + "/")
        if status == 0:
            body, headers, status = _fetch(f"http://{host}/")

        if body:
            # Technologies détectées
            techs = self._detect_tech(body, headers)
            if techs:
                self.logger.success(f"Technologies détectées: {', '.join(techs)}")
                findings.append({
                    "severity": "INFO",
                    "title": f"Stack technologique: {', '.join(techs)}",
                    "detail": "Technologies identifiées par analyse des headers et du contenu HTML"
                })

                # Vulnérabilités spécifiques aux technologies
                if "Struts" in techs:
                    findings.append({
                        "severity": "CRITICAL",
                        "title": "Apache Struts détecté — CVE-2017-5638 (Equifax breach)",
                        "detail": "Apache Struts vulnérable à RCE sans auth. Mettre à jour immédiatement."
                    })
                    self.logger.vuln("CRITICAL", "Apache Struts — CVE-2017-5638 risque")

                if "WebLogic" in techs:
                    findings.append({
                        "severity": "CRITICAL",
                        "title": "Oracle WebLogic détecté — CVE-2019-2725 (RCE)",
                        "detail": "WebLogic exposé à des RCE critiques. Patcher immédiatement."
                    })

                if "WordPress" in techs:
                    findings.append({
                        "severity": "MEDIUM",
                        "title": "WordPress détecté — vérifier /wp-login.php et xmlrpc.php",
                        "detail": "WordPress expose des endpoints d'auth et d'API par défaut"
                    })

            # WAF detection
            wafs = self._detect_waf(body, headers)
            if wafs:
                self.logger.success(f"WAF/Protection détecté: {', '.join(wafs)}")
                findings.append({
                    "severity": "INFO",
                    "title": f"WAF présent: {', '.join(wafs)}",
                    "detail": "Un pare-feu applicatif web est actif — protection supplémentaire"
                })
            else:
                findings.append({
                    "severity": "MEDIUM",
                    "title": "Aucun WAF détecté",
                    "detail": "Pas de Web Application Firewall identifié. Recommandé en environnement bancaire."
                })
                self.logger.vuln("MEDIUM", "Pas de WAF détecté")

            # Server info leakage
            server_info = self._get_server_info(headers)
            for key, val in server_info.items():
                findings.append({
                    "severity": "LOW",
                    "title": f"Information serveur exposée: {key}: {val}",
                    "detail": f"Le header {key} révèle des informations sur l'infrastructure"
                })
                self.logger.vuln("LOW", f"Header {key}: {val}")

        # Port/service spécifiques
        try:
            ip = socket.gethostbyname(host)
            self.logger.info(f"IP résolue: {ip}")
            findings.append({"severity": "INFO", "title": f"IP cible: {ip}", "detail": host})
        except Exception:
            pass

        return findings
