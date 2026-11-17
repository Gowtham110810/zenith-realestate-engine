import os
import re
import sqlite3
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
import central_core
import discovery_engine

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
SENDER_EMAIL = "zenith.ai.gowtham@gmail.com"
DAILY_EMAIL_LIMIT = 5


def get_smtp_password():
    pwd = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not pwd:
        try:
            import streamlit as st
            pwd = st.secrets.get("GMAIL_APP_PASSWORD", "")
        except Exception:
            pass
    return pwd.strip().replace(" ", "")


def get_today_sent_count():
    central_core.init_databases()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    conn = sqlite3.connect(central_core.REALESTATE_DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM outreach_logs WHERE sent_date = ?", (today_str,))
    count = cur.fetchone()[0]
    conn.close()
    return count


def is_already_contacted(target_email: str):
    central_core.init_databases()
    conn = sqlite3.connect(central_core.REALESTATE_DB)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM outreach_logs WHERE target_email = ?", (target_email.lower().strip(),))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def extract_emails(html_text: str):
    emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html_text))
    return [
        e.lower() for e in emails
        if not e.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".css", ".js", ".svg", ".webp"))
        and "example.com" not in e.lower()
        and "sentry.io" not in e.lower()
    ]


def hunt_leads(category: str, city: str):
    central_core.init_databases()
    urls = discovery_engine.deep_discover_urls(category, city)
    leads = []

    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code >= 400:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            emails = extract_emails(resp.text)
            if not emails:
                continue

            primary_email = emails[0]
            if is_already_contacted(primary_email):
                continue

            title = soup.find("title")
            agency_name = title.get_text(strip=True).split("|")[0].split("-")[0][:45].strip() if title else "Real Estate Team"

            pitch = (
                f"Hi {agency_name} Team,\n\n"
                f"I came across your property portfolio in {city}. I know that writing fresh MagicBricks/99acres descriptions, "
                f"WhatsApp buyer broadcasts, and Instagram captions for every new listing takes hours away from actual site visits and closing deals.\n\n"
                f"I built an AI Real Estate Marketing Engine that takes basic property bullet points (BHK, location, price, amenities) "
                f"and generates a complete luxury portal listing, WhatsApp broadcast pitch, and Instagram ad script in 10 seconds—sent straight to your Telegram.\n\n"
                f"Would you be open to a 7-day free trial to test it on your current listings? Reply 'YES' and I will send you a live sample today.\n\n"
                f"Best regards,\nGowtham | Zenith AI\n{SENDER_EMAIL}"
            )

            leads.append({
                "agency_name": agency_name,
                "url": url,
                "emails": emails,
                "pitch": pitch
            })
        except Exception:
            continue
    return leads


def send_email(agency_name: str, url: str, target_email: str, subject: str, body: str):
    central_core.init_databases()
    target_email = target_email.lower().strip()
    if get_today_sent_count() >= DAILY_EMAIL_LIMIT:
        return False, "Daily limit of 5 emails reached."
    if is_already_contacted(target_email):
        return False, "Already contacted."

    password = get_smtp_password()
    if not password:
        return False, "Missing GMAIL_APP_PASSWORD in Streamlit Secrets."

    msg = MIMEMultipart()
    msg["From"] = f"Gowtham | Zenith AI <{SENDER_EMAIL}>"
    msg["To"] = target_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
        server.starttls()
        server.login(SENDER_EMAIL, password)
        server.send_message(msg)
        server.quit()

        now_utc = datetime.now(timezone.utc)
        conn = sqlite3.connect(central_core.REALESTATE_DB)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO outreach_logs (agency_name, url, target_email, subject, pitch, sent_date, sent_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (agency_name, url, target_email, subject, body, now_utc.strftime("%Y-%m-%d"), now_utc.isoformat())
        )
        conn.commit()
        conn.close()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)
