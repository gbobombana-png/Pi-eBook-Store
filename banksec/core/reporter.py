import json
import datetime
import os

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
SEVERITY_COLOR = {
    "CRITICAL": "#c0392b", "HIGH": "#e67e22",
    "MEDIUM": "#f1c40f", "LOW": "#3498db", "INFO": "#95a5a6"
}

# Références académiques pour le mode thèse
THESIS_REFS = {
    "SQL Injection":        ("OWASP A03:2021", "CWE-89",  "PCI-DSS 6.2.4"),
    "XSS":                  ("OWASP A03:2021", "CWE-79",  "PCI-DSS 6.2.4"),
    "Reflected XSS":        ("OWASP A03:2021", "CWE-79",  "PCI-DSS 6.2.4"),
    "Blind SQL":            ("OWASP A03:2021", "CWE-89",  "PCI-DSS 6.2.4"),
    "Default credentials":  ("OWASP A07:2021", "CWE-521", "PCI-DSS 8.3.6"),
    "brute-force":          ("OWASP A07:2021", "CWE-307", "PCI-DSS 8.3.4"),
    "HSTS":                 ("OWASP A05:2021", "CWE-319", "PCI-DSS 4.2.1"),
    "TLS":                  ("OWASP A02:2021", "CWE-326", "PCI-DSS 4.2.1"),
    "SSL":                  ("OWASP A02:2021", "CWE-326", "PCI-DSS 4.2.1"),
    "cipher":               ("OWASP A02:2021", "CWE-327", "PCI-DSS 4.2.1"),
    "RC4":                  ("OWASP A02:2021", "CVE-2013-2566", "RFC 7465"),
    "Telnet":               ("OWASP A02:2021", "CWE-319", "PCI-DSS 2.2.7"),
    "BOLA":                 ("OWASP A01:2021", "CWE-639", "PCI-DSS 7.2"),
    "IDOR":                 ("OWASP A01:2021", "CWE-639", "PCI-DSS 7.2"),
    "Mass Assignment":      ("OWASP A08:2021", "CWE-915", "—"),
    "Swagger":              ("OWASP A05:2021", "CWE-200", "PCI-DSS 6.3.2"),
    "Elasticsearch":        ("OWASP A05:2021", "CWE-306", "PCI-DSS 7.2"),
    "ATM":                  ("OWASP A05:2021", "CWE-306", "PCI-DSS 12.3.3"),
    "XFS":                  ("OWASP A05:2021", "CWE-306", "PCI-DSS 12.3.3"),
    "PIN":                  ("PCI PIN §12",    "CWE-311", "PCI-DSS 3.5"),
    "HSM":                  ("PCI PIN §14",    "CWE-311", "PCI-DSS 3.5"),
    "WAF":                  ("OWASP A05:2021", "—",       "PCI-DSS 6.4.2"),
    "Struts":               ("OWASP A06:2021", "CVE-2017-5638", "—"),
    "WebLogic":             ("OWASP A06:2021", "CVE-2019-2725", "—"),
    "Certificate":          ("OWASP A02:2021", "CWE-298", "PCI-DSS 4.2.1"),
    "SHA-1":                ("OWASP A02:2021", "CWE-327", "PCI-DSS 4.2.1"),
    "Missing security header": ("OWASP A05:2021", "CWE-693", "PCI-DSS 6.4.1"),
    "Open Redirect":        ("OWASP A01:2021", "CWE-601", "—"),
    "DOM XSS":              ("OWASP A03:2021", "CWE-79",  "PCI-DSS 6.2.4"),
}

VULN_EXPLANATIONS = {
    "SQL Injection": "L'injection SQL permet à un attaquant d'interférer avec les requêtes d'une application vers sa base de données. Dans un contexte bancaire, cela peut mener à l'exfiltration de données clients, la modification de soldes, ou la suppression de transactions.",
    "XSS": "Le Cross-Site Scripting permet l'injection de scripts malveillants dans des pages web vues par d'autres utilisateurs. Dans le secteur bancaire, cela peut permettre le vol de sessions, la redirection vers des sites de phishing, ou la capture de credentials.",
    "TLS": "Les protocoles TLS/SSL chiffrés les communications entre le client et le serveur. Des versions obsolètes (TLS 1.0/1.1) présentent des vulnérabilités connues comme BEAST, POODLE, permettant des attaques de type Man-in-the-Middle sur les transactions financières.",
    "Default credentials": "L'utilisation d'identifiants par défaut est l'une des vulnérabilités les plus exploitées. Dans un environnement bancaire, elle peut donner accès à des interfaces d'administration critiques contrôlant des systèmes de paiement.",
    "BOLA": "Le Broken Object Level Authorization (IDOR) permet d'accéder aux données d'autres utilisateurs en manipulant les identifiants dans les requêtes API. En banque: accès aux comptes, relevés, ou cartes d'autres clients.",
    "ATM": "L'exposition des protocoles XFS/NDC sur le réseau constitue une vulnérabilité critique. Des attaques de type 'ATM Jackpot' peuvent être perpétrées à distance, forçant les distributeurs à distribuer du cash sans transaction légitime (ex: malware Tyupkin, PLOUTUS).",
}


def _get_thesis_ref(title):
    title_lower = title.lower()
    for keyword, refs in THESIS_REFS.items():
        if keyword.lower() in title_lower:
            return refs
    return None


def _get_explanation(title):
    title_lower = title.lower()
    for keyword, exp in VULN_EXPLANATIONS.items():
        if keyword.lower() in title_lower:
            return exp
    return None


class Reporter:
    def __init__(self, target, findings, output_dir="reports", thesis_mode=False):
        self.target = target
        self.findings = sorted(findings, key=lambda x: SEVERITY_ORDER.get(x["severity"], 9))
        self.output_dir = output_dir
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.thesis_mode = thesis_mode
        os.makedirs(output_dir, exist_ok=True)

    def _count_by_severity(self):
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for f in self.findings:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1
        return counts

    def save_json(self):
        path = os.path.join(self.output_dir, f"banksec_{self.timestamp}.json")
        data = {
            "target": self.target,
            "scan_time": self.timestamp,
            "summary": self._count_by_severity(),
            "findings": self.findings
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[+] JSON report: {path}")
        return path

    def save_txt(self):
        path = os.path.join(self.output_dir, f"banksec_{self.timestamp}.txt")
        counts = self._count_by_severity()
        with open(path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("  BankSec — Rapport d'Audit Sécurité Bancaire\n")
            f.write("=" * 60 + "\n")
            f.write(f"Cible   : {self.target}\n")
            f.write(f"Date    : {self.timestamp}\n\n")
            f.write("RÉSUMÉ\n" + "-" * 30 + "\n")
            for sev, cnt in counts.items():
                f.write(f"  {sev:<10}: {cnt}\n")
            f.write("\nFINDINGS\n" + "=" * 60 + "\n\n")
            for finding in self.findings:
                f.write(f"[{finding['severity']}] {finding['title']}\n")
                if finding.get("detail"):
                    f.write(f"  Détail : {finding['detail']}\n")
                if self.thesis_mode:
                    refs = _get_thesis_ref(finding['title'])
                    if refs:
                        f.write(f"  OWASP  : {refs[0]}\n")
                        f.write(f"  CWE    : {refs[1]}\n")
                        f.write(f"  PCI-DSS: {refs[2]}\n")
                    exp = _get_explanation(finding['title'])
                    if exp:
                        f.write(f"  Analyse: {exp}\n")
                f.write("\n")
        print(f"[+] TXT report: {path}")
        return path

    def save_html(self):
        path = os.path.join(self.output_dir, f"banksec_{self.timestamp}.html")
        counts = self._count_by_severity()
        rows = ""
        for f in self.findings:
            color = SEVERITY_COLOR.get(f["severity"], "#ccc")
            refs_html = ""
            exp_html = ""
            if self.thesis_mode:
                refs = _get_thesis_ref(f['title'])
                if refs:
                    refs_html = f'<br><small style="color:#aaa">📚 {refs[0]} | {refs[1]} | {refs[2]}</small>'
                exp = _get_explanation(f['title'])
                if exp:
                    exp_html = f'<br><small style="color:#88bbff;font-style:italic">{exp[:200]}...</small>'

            rows += f"""
            <tr>
                <td><span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-weight:bold">{f['severity']}</span></td>
                <td><strong>{f['title']}</strong>{refs_html}</td>
                <td style="font-size:0.9em">{f.get('detail','')}{exp_html}</td>
            </tr>"""

        summary_html = ""
        for sev, cnt in counts.items():
            if cnt > 0:
                color = SEVERITY_COLOR[sev]
                summary_html += f'<div style="display:inline-block;margin:5px;padding:10px 20px;background:{color};color:#fff;border-radius:8px;font-weight:bold">{sev}: {cnt}</div>'

        thesis_badge = '<span style="background:#9b59b6;color:#fff;padding:3px 10px;border-radius:4px;font-size:0.8em">MODE THÈSE</span>' if self.thesis_mode else ""

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>BankSec Report - {self.target}</title>
<style>
  body{{font-family:'Courier New',monospace;background:#0d1117;color:#e6edf3;margin:0;padding:20px}}
  .header{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px;margin-bottom:20px}}
  h1{{color:#58a6ff;margin:0 0 5px 0;font-size:1.8em}} h2{{color:#3fb950;border-bottom:1px solid #30363d;padding-bottom:5px}}
  table{{border-collapse:collapse;width:100%;margin-top:10px}}
  th{{background:#161b22;color:#58a6ff;padding:12px;text-align:left;border-bottom:2px solid #30363d}}
  td{{padding:10px 12px;border-bottom:1px solid #21262d;vertical-align:top}}
  tr:hover{{background:#161b22}}
  .risk-score{{font-size:3em;font-weight:bold;color:{SEVERITY_COLOR.get('CRITICAL','#c0392b')}}}
  code{{background:#161b22;padding:2px 6px;border-radius:4px;font-size:0.9em}}
</style>
</head>
<body>
<div class="header">
  <h1>🏦 BankSec — Rapport d'Audit Sécurité {thesis_badge}</h1>
  <p>Cible: <code>{self.target}</code> &nbsp;|&nbsp; Date: {self.timestamp}</p>
</div>

<h2>📊 Résumé Exécutif</h2>
<div>{summary_html}</div>

<h2>🔍 Findings Détaillés</h2>
<table>
  <tr><th width="120">Sévérité</th><th width="40%">Vulnérabilité</th><th>Détails & Analyse</th></tr>
  {rows}
</table>

<br><p style="color:#444;font-size:0.8em">Généré par BankSec v1.0 — Usage autorisé uniquement</p>
</body>
</html>"""
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"[+] HTML report: {path}")
        return path

    def save(self, fmt="all"):
        paths = []
        if fmt in ("json", "all"):
            paths.append(self.save_json())
        if fmt in ("txt", "all"):
            paths.append(self.save_txt())
        if fmt in ("html", "all"):
            paths.append(self.save_html())
        return paths
