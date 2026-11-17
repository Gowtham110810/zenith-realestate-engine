import streamlit as st
import central_core
import realestate_engine
import realestate_lead_hunter

st.set_page_config(page_title="Zenith AI Real Estate Engine", page_icon="🏢", layout="wide")
central_core.init_databases()

if "re_leads" not in st.session_state:
    st.session_state.re_leads = []

if "smart_queue_re" not in st.session_state:
    st.session_state.smart_queue_re = [
        ("Luxury Real Estate Consultants", "Gurgaon", "High-ticket DLF/Golf Course Road brokers earning massive commissions."),
        ("Real Estate Brokers", "Hyderabad", "Booming Kokapet/Jubilee Hills luxury market needing constant listing copy."),
        ("Property Consultants", "Mumbai", "Fast-moving inventory where speed-to-market dictates broker commission."),
        ("Real Estate Agencies", "Bengaluru", "High volume of tech-corridor residential projects and villa listings."),
        ("Commercial Real Estate Brokers", "Pune", "High-retainer B2B brokers managing multiple office and retail spaces."),
        ("Luxury Villa Brokers", "Goa", "Holiday home and investment villa agencies relying heavily on Instagram marketing."),
        ("Real Estate Consultants", "Noida", "Rapidly expanding expressway luxury projects with fierce broker competition."),
        ("Property Dealers", "Chennai", "High-value OMR and ECR residential corridor specialists."),
        ("Real Estate Advisory", "Ahmedabad", "Growing commercial and luxury residential developments."),
        ("Realtors and Property Brokers", "Kolkata", "New Town and EM Bypass luxury apartment consultancies.")
    ]

st.title("🏢 AI Real Estate Marketing & Listing Engine")
st.caption("Rank 5 B2B SaaS: 10-Second Property Listing & Social Media Copywriter + Telegram Delivery + Broker Lead Hunter")

tab1, tab2, tab3 = st.tabs([
    "🏗️ 4-in-1 Property Marketing Generator",
    "📲 Telegram Bot Setup",
    "🎯 Auto-Pilot Broker Lead Hunter (5/Day Cap)"
])

with tab1:
    st.subheader("Turn Raw Property Specs into a Complete Marketing Campaign")
    with st.form("property_form"):
        col1, col2 = st.columns(2)
        prop_title = col1.text_input("Property Title / Project Type", value="Skyline Luxury Sky Villa")
        location = col2.text_input("Location / Neighborhood", value="Jubilee Hills, Hyderabad")
        price = col1.text_input("Asking Price", value="₹4.5 Crore")
        specs = col2.text_input("Configuration & Size", value="4 BHK | 4,200 Sq.Ft. | East Facing")
        highlights = st.text_area(
            "Key Amenities & Highlights",
            value="Private plunge pool, wrap-around deck, Italian marble flooring, 3 covered car parks, 5 mins from metro."
        )
        gen_btn = st.form_submit_button("✨ Generate Full Marketing Package & Push to Telegram")

    if gen_btn:
        with st.spinner("Writing Portal Listing, WhatsApp Pitch, Instagram Copy & Meta Ad..."):
            pack = realestate_engine.generate_property_marketing_pack(prop_title, location, price, specs, highlights)
            st.success("Complete Property Marketing Package Ready:")
            st.text_area("Copy & Paste Marketing Assets", value=pack, height=380)

            tg_message = f"🏢 NEW PROPERTY MARKETING PACK: {prop_title} ({location})\n\n{pack}"
            ok, msg = realestate_engine.send_telegram_alert(tg_message)
            if ok:
                st.toast("📲 Sent directly to Telegram!")
            else:
                st.warning(f"Telegram notice: {msg}")

with tab2:
    st.subheader("Connect Telegram Bot for Instant Mobile Copy Delivery")
    saved_token, saved_chat_id = realestate_engine.get_telegram_credentials()

    token_in = st.text_input("Telegram Bot Token", value=saved_token, type="password")
    col_a, col_b = st.columns([3, 1])
    chat_in = col_a.text_input("Telegram Chat ID", value=saved_chat_id)

    if col_b.button("🔍 Auto-Detect Chat ID"):
        detected_id, status_msg = realestate_engine.auto_detect_chat_id(token_in)
        if detected_id:
            realestate_engine.save_telegram_credentials(token_in, detected_id)
            st.success(status_msg)
            st.rerun()
        else:
            st.error(status_msg)

    if st.button("💾 Save & Test Connection"):
        realestate_engine.save_telegram_credentials(token_in, chat_in)
        ok, msg = realestate_engine.send_telegram_alert("🏢 Zenith Real Estate Marketing Engine Connected!")
        if ok:
            st.success("Test alert sent to your Telegram!")
        else:
            st.error(msg)

with tab3:
    st.subheader("Smart Real Estate Broker Discovery (zenith.ai.gowtham@gmail.com)")
    sent_today = realestate_lead_hunter.get_today_sent_count()
    remaining = max(0, realestate_lead_hunter.DAILY_EMAIL_LIMIT - sent_today)

    m1, m2, m3 = st.columns(3)
    m1.metric("Daily Limit", "5 Emails/Day")
    m2.metric("Sent Today", sent_today)
    m3.metric("Remaining Today", remaining)

    st.markdown("### 🧠 Smart Auto-Pilot Broker Queue")
    st.caption("Automatically targets high-commission real estate consultancies across India's top property markets.")

    if st.button("🚀 1-Click Smart Discover Brokers", use_container_width=True):
        if not st.session_state.smart_queue_re:
            st.warning("Queue complete! Refresh the page to reset the top 10 markets or use Manual Override below.")
        else:
            niche, city, logic = st.session_state.smart_queue_re.pop(0)
            st.info(f"**🧠 Targeting:** '{niche}' in '{city}' — *{logic}*")
            with st.spinner(f"Scanning independent broker websites in {city}..."):
                st.session_state.re_leads = realestate_lead_hunter.hunt_leads(niche, city)

            if not st.session_state.re_leads:
                st.warning(f"No uncontacted emails found for '{niche}' in '{city}'. Click Smart Discover again for the next market.")
            else:
                st.success(f"Found {len(st.session_state.re_leads)} real estate agency lead(s) in {city}!")

    with st.expander("Manual Override (Custom City or Niche)"):
        with st.form("manual_re_hunt"):
            c1, c2 = st.columns(2)
            m_niche = c1.text_input("Broker Category", value="Real Estate Consultants")
            m_city = c2.text_input("City", value="Hyderabad")
            m_btn = st.form_submit_button("🔍 Search Leads")
        if m_btn:
            with st.spinner("Scanning broker websites..."):
                st.session_state.re_leads = realestate_lead_hunter.hunt_leads(m_niche, m_city)

    leads = st.session_state.re_leads
    if leads:
        st.divider()
        if remaining > 0:
            if st.button(f"⚡ Auto-Send Top {min(len(leads), remaining)} Broker Pitches Now"):
                for idx, lead in enumerate(leads):
                    if realestate_lead_hunter.get_today_sent_count() >= realestate_lead_hunter.DAILY_EMAIL_LIMIT:
                        break
                    target_email = lead["emails"][0]
                    if realestate_lead_hunter.is_already_contacted(target_email):
                        continue
                    subject = f"Automate property listings & WhatsApp pitches for {lead['agency_name']}"
                    pitch_text = st.session_state.get(f"repitch_{idx}", lead["pitch"])
                    ok, msg = realestate_lead_hunter.send_email(
                        lead["agency_name"], lead["url"], target_email, subject, pitch_text
                    )
                    if ok:
                        st.toast(f"✅ Sent to {target_email}")
                    else:
                        st.error(f"❌ {target_email}: {msg}")
                st.rerun()
        else:
            st.warning("🔒 Daily limit of 5 outreach emails reached. Resets tomorrow.")

        for idx, lead in enumerate(leads):
            target_email = lead["emails"][0]
            already_sent = realestate_lead_hunter.is_already_contacted(target_email)
            badge = "✅ SENT" if already_sent else "🟢 READY"
            with st.expander(f"{badge} | #{idx+1}: {lead['agency_name']} ({lead['url']})", expanded=(idx < 5 and not already_sent)):
                st.write(f"**Email:** `{target_email}`")
                pitch = st.text_area("Pitch:", value=lead["pitch"], height=160, key=f"repitch_{idx}")
                if st.button("🚀 Send Individual Email", key=f"resend_{idx}", disabled=(already_sent or remaining == 0)):
                    subject = f"Automate property listings & WhatsApp pitches for {lead['agency_name']}"
                    ok, msg = realestate_lead_hunter.send_email(lead["agency_name"], lead["url"], target_email, subject, pitch)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
