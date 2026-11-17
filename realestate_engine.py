import os
import sqlite3
from datetime import datetime, timezone
import requests
import central_core


def get_telegram_credentials():
    central_core.init_databases()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    try:
        import streamlit as st
        if not token:
            token = st.secrets.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not chat_id:
            chat_id = str(st.secrets.get("TELEGRAM_CHAT_ID", "")).strip()
    except Exception:
        pass

    conn = sqlite3.connect(central_core.REALESTATE_DB)
    cur = conn.cursor()
    if not token:
        cur.execute("SELECT value FROM settings WHERE key = 'telegram_token'")
        row = cur.fetchone()
        if row:
            token = row[0]
    if not chat_id:
        cur.execute("SELECT value FROM settings WHERE key = 'telegram_chat_id'")
        row = cur.fetchone()
        if row:
            chat_id = row[0]
    conn.close()
    return token, chat_id


def save_telegram_credentials(token, chat_id):
    central_core.init_databases()
    conn = sqlite3.connect(central_core.REALESTATE_DB)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('telegram_token', ?)", (token.strip(),))
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('telegram_chat_id', ?)", (str(chat_id).strip(),))
    conn.commit()
    conn.close()


def auto_detect_chat_id(token: str):
    """Fetches the latest Chat ID from the last user who messaged the Telegram bot."""
    token = token.strip()
    if not token:
        return None, "Please enter a valid Bot Token first."
    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        resp = requests.get(url, timeout=10).json()
        if not resp.get("ok"):
            return None, resp.get("description", "Invalid Bot Token.")
        results = resp.get("result", [])
        if not results:
            return None, "No messages found. Send 'Hello' to your bot on Telegram first, then click Auto-Detect."
        for update in reversed(results):
            msg = update.get("message") or update.get("channel_post")
            if msg and "chat" in msg:
                chat_id = str(msg["chat"]["id"])
                first_name = msg["chat"].get("first_name", "User")
                return chat_id, f"Detected Chat ID for {first_name}: {chat_id}"
        return None, "Could not extract Chat ID from recent updates."
    except Exception as e:
        return None, str(e)


def send_telegram_alert(message: str):
    token, chat_id = get_telegram_credentials()
    if not token or not chat_id:
        return False, "Telegram Token or Chat ID missing."
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message[:4000]}
        resp = requests.post(url, json=payload, timeout=10).json()
        if resp.get("ok"):
            return True, "Marketing package pushed to Telegram!"
        return False, resp.get("description", "Telegram API Error")
    except Exception as e:
        return False, str(e)


def generate_property_marketing_pack(property_title, location, price, specs, highlights):
    prompt = f"""
    You are an elite luxury real estate copywriter in India.
    Create a complete 4-part marketing package for the following property:
    - Property Title/Type: {property_title}
    - Location: {location}
    - Price: {price}
    - Configuration/Specs: {specs}
    - Key Amenities & Highlights: {highlights}

    Format your output clearly into these exact 4 sections:

    1. PORTAL LISTING DESCRIPTION (MagicBricks / 99acres / Housing.com)
    Write a high-converting, SEO-optimized 150-word property description highlighting lifestyle, connectivity, and investment value.

    2. WHATSAPP BROADCAST PITCH
    Write a punchy, bulleted message formatted for WhatsApp buyer broadcast lists with urgent call-to-action for site visits.

    3. INSTAGRAM & FACEBOOK CAPTION
    Write a visually engaging social media hook, lifestyle body copy, and 10 targeted local real estate hashtags.

    4. HIGH-CONVERTING META AD SCRIPT
    Provide Primary Text, Headline, and Call-To-Action for a paid lead-generation campaign.
    """
    pack = central_core.call_gemini(prompt)
    if "Error:" in pack:
        pack = (
            f"1. PORTAL LISTING: Premium {specs} {property_title} available in {location} at {price}. Features: {highlights}.\n\n"
            f"2. WHATSAPP BROADCAST: Hot Listing in {location}! {property_title} ({specs}) for {price}. Key highlights: {highlights}. Reply to book a site visit today!\n\n"
            f"3. INSTAGRAM CAPTION: Step into luxury in {location}. {specs} {property_title} now available at {price}. DM for private tour! #RealEstateIndia #{location.replace(' ', '')}Property\n\n"
            f"4. META AD: Headline: Own Your Dream Home in {location} | Price: {price} | Click Learn More to Schedule a Visit."
        )

    central_core.init_databases()
    conn = sqlite3.connect(central_core.REALESTATE_DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO listings (property_title, location, price, specs, marketing_pack, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (property_title, location, price, specs, pack, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()
    return pack
