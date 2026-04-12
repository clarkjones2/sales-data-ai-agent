"""
Generate a Markdown KPI digest from digest_config.json.

Optional: email via SMTP if environment variables are set:
  SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASSWORD,
  DIGEST_FROM_EMAIL, DIGEST_TO_EMAIL (comma-separated)

Schedule with cron, e.g. weekly:
  0 9 * * 1 cd /path/to/project && python scheduled_digest.py
"""
from __future__ import annotations

import json
import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

from data_quality import format_data_quality_markdown, run_data_quality_report
from database_tools import DatabaseQueryTool

_PROJECT = Path(__file__).resolve().parent
load_dotenv(_PROJECT / ".env")


def _load_config() -> dict:
    p = _PROJECT / "digest_config.json"
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def run_digest(
    db_path: str | None = None,
    out_dir: str | None = None,
    send_email: bool = True,
) -> Path:
    cfg = _load_config()
    db_tool = DatabaseQueryTool(db_path)
    out = Path(out_dir or (_PROJECT / "exports"))
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = out / f"digest_{stamp}.md"

    lines = [
        f"# {cfg.get('title', 'Digest')}",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
        "## KPIs",
        "",
    ]

    for block in cfg.get("queries", []):
        title = block["title"]
        sql = block["sql"].strip()
        r = db_tool.query_database(sql, max_rows=500)
        lines.append(f"### {title}")
        lines.append("")
        if r.get("success") and r.get("data"):
            lines.append("```")
            lines.append(json.dumps(r["data"], indent=2, default=str))
            lines.append("```")
        else:
            lines.append(f"_Error: {r.get('message', r)}_")
        lines.append("")

    dq = run_data_quality_report(db_tool.db_path)
    lines.append("## Data quality snapshot")
    lines.append("")
    lines.append(format_data_quality_markdown(dq))

    text = "\n".join(lines)
    report_path.write_text(text, encoding="utf-8")
    print(f"Wrote {report_path}")

    if send_email and os.environ.get("SMTP_HOST") and os.environ.get("DIGEST_TO_EMAIL"):
        _send_email(report_path.read_text(encoding="utf-8"), cfg.get("title", "Digest"))

    return report_path


def _send_email(body: str, subject_prefix: str) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    from_addr = os.environ.get("DIGEST_FROM_EMAIL", user)
    to_raw = os.environ["DIGEST_TO_EMAIL"]
    recipients = [x.strip() for x in to_raw.split(",") if x.strip()]

    msg = EmailMessage()
    msg["Subject"] = f"{subject_prefix} — {datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = from_addr
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port) as server:
        server.starttls(context=context)
        if user:
            server.login(user, password)
        server.send_message(msg)
    print(f"Emailed digest to {recipients}")


if __name__ == "__main__":
    run_digest()
