"""
Minimal helper: send the contents of results/scan_summary.txt
to every address listed in email.txt.

Usage (blocking):
    from email_summary import send_summary_email
    send_summary_email()
"""

import smtplib, os
from email.message import EmailMessage
from pathlib import Path
from common_helpers import base_dir
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_suffix('.env'))      # ← new line

EMAIL_SENDER   = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")
SMTP_SERVER    = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", 587))
SUBJECT        = os.getenv("SUBJECT", "Báo cáo kết quả quét GitHub")

SUMMARY_FILE   = base_dir() / "results" / "scan_summary.txt"
EMAIL_LIST_FILE= base_dir() / "email.txt"


# ─── helpers ─────────────────────────────────────────────────────────────────
def _load_recipients() -> list[str]:
    if not EMAIL_LIST_FILE.exists():
        print("⚠️  Không tìm thấy email.txt – bỏ qua bước gửi mail.")
        return []
    lines = [ln.strip() for ln in EMAIL_LIST_FILE.read_text(encoding="utf-8").splitlines()]
    return [ln for ln in lines if ln]

def _load_report() -> str | None:
    if not SUMMARY_FILE.exists():
        print("⚠️  Không tìm thấy scan_summary.txt – không có gì để gửi.")
        return None
    return SUMMARY_FILE.read_text(encoding="utf-8")

# ─── public API ─────────────────────────────────────────────────────────────
def send_summary_email():
    recipients = _load_recipients()
    if not recipients:
        return

    body = _load_report()
    if body is None:
        return

    msg = EmailMessage()
    msg["Subject"] = SUBJECT
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = ", ".join(recipients)
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"📧 Đã gửi báo cáo đến {len(recipients)} địa chỉ.")
    except Exception as exc:
        print("❌ Lỗi gửi mail:", exc)
