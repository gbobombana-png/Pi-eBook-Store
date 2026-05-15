import json
import datetime
import os

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
SEVERITY_COLOR = {
    "CRITICAL": "#c0392b", "HIGH": "#e67e22",
    "MEDIUM": "#f1c40f", "LOW": "#3498db", "INFO": "#95a5a6"
}

class Reporter:
    def __init__(self, target, findings, output_dir="reports"):
        self.target = target
        self.findings = sorted(findings, key=lambda x: SEVERITY_ORDER.get(x["severity"], 9))
        self.output_dir = output_dir
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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
            json.dump(data, f, indent=2)
        print(f"[+] JSON report: {path}")
        return path

    def save_txt(self):
        path = os.path.join(self.output_dir, f"banksec_{self.timestamp}.txt")
        counts = self._count_by_severity()
        with open(path, "w") as f:
            f.write(f"BankSec Audit Report\n")
            f.write(f"Target : {self.target}\n")
            f.write(f"Date   : {self.timestamp}\n")
            f.write("="*60 + "\n\n")
            f.write("SUMMARY\n")
            for sev, cnt in counts.items():
                f.write(f"  {sev:<10}: {cnt}\n")
            f.write("\n" + "="*60 + "\nFINDINGS\n" + "="*60 + "\n\n")
            for finding in self.findings:
                f.write(f"[{finding['severity']}] {finding['title']}\n")
                if finding.get("detail"):
                    f.write(f"  {finding['detail']}\n")
                f.write("\n")
        print(f"[+] TXT report: {path}")
        return path

    def save_html(self):
        path = os.path.join(self.output_dir, f"banksec_{self.timestamp}.html")
        counts = self._count_by_severity()
        rows = ""
        for f in self.findings:
            color = SEVERITY_COLOR.get(f["severity"], "#ccc")
            rows += f"""
            <tr>
                <td><span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-weight:bold">{f['severity']}</span></td>
                <td><strong>{f['title']}</strong></td>
                <td style="font-size:0.9em">{f.get('detail','')}</td>
            </tr>"""

        summary_html = ""
        for sev, cnt in counts.items():
            if cnt > 0:
                color = SEVERITY_COLOR[sev]
                summary_html += f'<div style="display:inline-block;margin:5px;padding:10px 20px;background:{color};color:#fff;border-radius:8px;font-weight:bold">{sev}: {cnt}</div>'

        html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>BankSec Report - {self.target}</title>
<style>
  body{{font-family:monospace;background:#1a1a2e;color:#eee;margin:20px}}
  h1{{color:#00d4ff}} h2{{color:#00ff88}}
  table{{border-collapse:collapse;width:100%;margin-top:20px}}
  th{{background:#16213e;color:#00d4ff;padding:10px;text-align:left}}
  td{{padding:8px 10px;border-bottom:1px solid #333}}
  tr:hover{{background:#16213e}}
</style></head>
<body>
<h1>BankSec Audit Report</h1>
<p>Target: <code>{self.target}</code> &nbsp;|&nbsp; Date: {self.timestamp}</p>
<h2>Summary</h2>{summary_html}
<h2>Findings</h2>
<table><tr><th>Severity</th><th>Title</th><th>Details</th></tr>{rows}</table>
</body></html>"""
        with open(path, "w") as fh:
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
