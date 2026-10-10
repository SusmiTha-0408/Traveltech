import streamlit as st
import time
import textwrap
import folium
from streamlit_folium import st_folium

from mock_data import (
    generate_buses,
    generate_dynamic_last_mile,
    generate_dynamic_disruption_recovery,
    reverse_geocode,
    parse_travel_query,
    resolve_city_profile,
    add_minutes_to_time_str
)
from translations import (
    LANGUAGES,
    t,
    get_translated_city,
    get_default_query,
    get_ai_rationale_list
)

# Page Configuration
st.set_page_config(
    page_title="TBS RoamAgent - Multimodal Travel Concierge",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Polished Pastel Styling (Light Mint Green #e8f5e9 & Blossom Pink #fce4ec)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Sans+Telugu:wght@400;600;700&family=Noto+Sans+Malayalam:wght@400;600;700&family=Noto+Sans+Devanagari:wght@400;600;700&family=Noto+Sans+Tamil:wght@400;600;700&family=Noto+Sans+Kannada:wght@400;600;700&family=Noto+Sans+Bengali:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Noto Sans Telugu', 'Noto Sans Malayalam', 'Noto Sans Devanagari', 'Noto Sans Tamil', 'Noto Sans Kannada', 'Noto Sans Bengali', sans-serif;
    }

    .stApp {
        background: linear-gradient(145deg, #f7fbf8 0%, #fffbfd 45%, #fbf5f8 100%);
        color: #2c3e50;
    }

    /* Container panels */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #dceedb !important;
        box-shadow: 0 4px 16px rgba(44, 62, 80, 0.04) !important;
        padding: 0.2rem !important;
    }

    /* Polished Header Banner with Pastel Gradient */
    .main-header {
        background: linear-gradient(135deg, #e8f5e9 0%, #ffffff 50%, #fce4ec 100%);
        border: 1.5px solid #dceedb;
        border-radius: 14px;
        padding: 1.2rem 1.6rem;
        color: #2c3e50;
        box-shadow: 0 6px 20px rgba(220, 238, 219, 0.45);
        margin-bottom: 1rem;
    }
    
    .main-header h1 {
        color: #1b5e20 !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
        margin: 0 !important;
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        color: #2c3e50 !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        margin-top: 0.25rem !important;
        margin-bottom: 0 !important;
    }

    /* Stepper Navigation Indicator */
    .wizard-nav-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #ffffff;
        border: 1px solid #dceedb;
        border-radius: 12px;
        padding: 0.75rem 1.1rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 10px rgba(44, 62, 80, 0.03);
        flex-wrap: wrap;
        gap: 0.4rem;
    }

    .step-pill-done {
        background: #e8f5e9;
        color: #1b5e20;
        border: 1px solid #a5d6a7;
        padding: 0.35rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
    }

    .step-pill-active {
        background: linear-gradient(135deg, #e8f5e9 0%, #fce4ec 100%);
        color: #1b5e20;
        border: 2px solid #2e7d32;
        padding: 0.38rem 0.85rem;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 800;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        box-shadow: 0 2px 8px rgba(46, 125, 50, 0.15);
    }

    .step-pill-future {
        background: #f8fafc;
        color: #94a3b8;
        border: 1px solid #e2e8f0;
        padding: 0.35rem 0.7rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
    }

    .step-arrow {
        color: #cbd5e1;
        font-weight: 800;
        font-size: 0.9rem;
    }

    /* Mode Indicators */
    .status-pill {
        display: inline-block;
        padding: 0.4rem 0.9rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    .pill-active {
        background-color: #e8f5e9;
        color: #1b5e20;
        border: 1px solid #a5d6a7;
    }
    
    .pill-alert {
        background-color: #fce4ec;
        color: #ad1457;
        border: 1px solid #f8bbd0;
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Pastel Badges */
    .metric-badge {
        background: #ffffff;
        border: 1px solid #dceedb;
        color: #2c3e50;
        border-radius: 8px;
        padding: 0.35rem 0.65rem;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        box-shadow: 0 1px 3px rgba(44, 62, 80, 0.03);
    }
    
    .metric-badge-mint {
        background: #e8f5e9;
        border: 1px solid #a5d6a7;
        color: #1b5e20;
        border-radius: 8px;
        padding: 0.35rem 0.65rem;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
    }

    .metric-badge-pink {
        background: #fce4ec;
        border: 1px solid #f8bbd0;
        color: #ad1457;
        border-radius: 8px;
        padding: 0.35rem 0.65rem;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
    }

    /* Leg Container */
    .leg-box {
        background-color: #fcfdfc;
        border: 1px solid #dceedb;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin: 0.6rem 0;
    }

    /* Disruption Alert Callout */
    .disruption-banner {
        background: linear-gradient(135deg, #fff0f3 0%, #fffbfd 100%);
        border: 1.5px solid #f8bbd0;
        border-left: 6px solid #ad1457;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 18px rgba(248, 187, 208, 0.3);
    }

    .readjustment-banner {
        background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%);
        border: 1.5px solid #a5d6a7;
        border-left: 6px solid #2e7d32;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 18px rgba(165, 214, 167, 0.3);
    }

    /* Visual Timeline Stepper */
    .timeline-container {
        display: flex;
        align-items: center;
        overflow-x: auto;
        padding: 0.9rem 1rem;
        background: #f7fbf8;
        border: 1px solid #dceedb;
        border-radius: 12px;
        gap: 0.5rem;
        margin: 1rem 0;
    }

    .timeline-node {
        background: #ffffff;
        color: #1b5e20;
        border: 1.5px solid #a5d6a7;
        padding: 0.4rem 0.85rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        white-space: nowrap;
    }

    .timeline-node-transfer {
        background: #fce4ec;
        color: #ad1457;
        border: 1px solid #f8bbd0;
        padding: 0.4rem 0.85rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        white-space: nowrap;
    }

    .timeline-node-dest {
        background: #e8f5e9;
        color: #2e7d32;
        border: 1.5px solid #81c784;
        padding: 0.4rem 0.85rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        white-space: nowrap;
    }

    .timeline-leg {
        background: #ffffff;
        color: #2c3e50;
        padding: 0.35rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.78rem;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        border: 1px solid #dceedb;
    }

    .timeline-arrow {
        color: #f8bbd0;
        font-weight: 800;
        font-size: 1.1rem;
        padding: 0 0.1rem;
    }

    .consent-box {
        background: #fff5f8;
        border: 2px solid #f8bbd0;
        border-radius: 14px;
        padding: 1.3rem 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 16px rgba(248, 187, 208, 0.25);
    }

    .ticket-wrapper {
        background: #ffffff;
        border: 2px solid #a5d6a7;
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 8px 25px rgba(165, 214, 167, 0.25);
        margin: 1rem 0;
    }

    .ticket-header {
        background: linear-gradient(135deg, #e8f5e9 0%, #ffffff 50%, #fce4ec 100%);
        border-bottom: 1.5px solid #dceedb;
        padding: 1.2rem 1.6rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .ticket-body {
        padding: 1.4rem 1.6rem;
        display: flex;
        justify-content: space-between;
        gap: 1.2rem;
        flex-wrap: wrap;
        background: #ffffff;
    }

    .ticket-perforation {
        border-top: 2px dashed #dceedb;
        margin: 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper: Render QR Code SVG Mockup
def render_qr_svg_mockup(token_label="AUTO-DISPATCH-VZG-EV42", otp="5821"):
    return (
        '<div style="background: #ffffff; padding: 14px; border-radius: 12px; border: 1.5px solid #dceedb; display: inline-block; text-align: center; box-shadow: 0 4px 14px rgba(44, 62, 80, 0.05);">'
        '<svg width="130" height="130" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="100" height="100" fill="#ffffff"/>'
        '<rect x="5" y="5" width="26" height="26" fill="#1b5e20" rx="4"/>'
        '<rect x="9" y="9" width="18" height="18" fill="#ffffff" rx="2"/>'
        '<rect x="13" y="13" width="10" height="10" fill="#2e7d32" rx="1"/>'
        '<rect x="69" y="5" width="26" height="26" fill="#1b5e20" rx="4"/>'
        '<rect x="73" y="9" width="18" height="18" fill="#ffffff" rx="2"/>'
        '<rect x="77" y="13" width="10" height="10" fill="#2e7d32" rx="1"/>'
        '<rect x="5" y="69" width="26" height="26" fill="#1b5e20" rx="4"/>'
        '<rect x="9" y="73" width="18" height="18" fill="#ffffff" rx="2"/>'
        '<rect x="13" y="77" width="10" height="10" fill="#2e7d32" rx="1"/>'
        '<rect x="36" y="10" width="5" height="5" fill="#2c3e50"/>'
        '<rect x="46" y="10" width="5" height="5" fill="#ad1457"/>'
        '<rect x="56" y="10" width="5" height="5" fill="#2c3e50"/>'
        '<rect x="10" y="36" width="5" height="5" fill="#2c3e50"/>'
        '<rect x="10" y="46" width="5" height="5" fill="#ad1457"/>'
        '<rect x="10" y="56" width="5" height="5" fill="#2c3e50"/>'
        '<rect x="38" y="24" width="6" height="6" fill="#2e7d32"/>'
        '<rect x="48" y="24" width="6" height="6" fill="#ad1457"/>'
        '<rect x="58" y="24" width="6" height="6" fill="#2e7d32"/>'
        '<rect x="35" y="35" width="6" height="6" fill="#2c3e50"/>'
        '<rect x="45" y="35" width="8" height="8" fill="#1b5e20"/>'
        '<rect x="58" y="35" width="6" height="6" fill="#ad1457"/>'
        '<rect x="70" y="35" width="6" height="6" fill="#2c3e50"/>'
        '<rect x="80" y="35" width="6" height="6" fill="#2e7d32"/>'
        '<rect x="35" y="48" width="6" height="6" fill="#ad1457"/>'
        '<rect x="45" y="48" width="6" height="6" fill="#2c3e50"/>'
        '<rect x="55" y="48" width="6" height="6" fill="#1b5e20"/>'
        '<rect x="68" y="48" width="8" height="6" fill="#ad1457"/>'
        '<rect x="82" y="48" width="6" height="6" fill="#2c3e50"/>'
        '<rect x="35" y="60" width="6" height="6" fill="#2e7d32"/>'
        '<rect x="45" y="60" width="6" height="6" fill="#ad1457"/>'
        '<rect x="58" y="60" width="6" height="6" fill="#2c3e50"/>'
        '<rect x="70" y="60" width="6" height="6" fill="#1b5e20"/>'
        '<rect x="38" y="75" width="6" height="6" fill="#ad1457"/>'
        '<rect x="48" y="75" width="6" height="6" fill="#2e7d32"/>'
        '<rect x="58" y="75" width="6" height="6" fill="#ad1457"/>'
        '<rect x="70" y="75" width="6" height="6" fill="#2c3e50"/>'
        '<rect x="80" y="75" width="6" height="6" fill="#2e7d32"/>'
        '<rect x="45" y="86" width="6" height="6" fill="#1b5e20"/>'
        '<rect x="58" y="86" width="6" height="6" fill="#ad1457"/>'
        '<rect x="70" y="86" width="6" height="6" fill="#2c3e50"/>'
        '<rect x="82" y="86" width="6" height="6" fill="#2e7d32"/>'
        '</svg>'
        f'<div style="font-size: 0.72rem; font-weight: 700; color: #1b5e20; margin-top: 6px; letter-spacing: 0.5px;">{token_label}</div>'
        f'<div style="font-size: 0.7rem; font-weight: 800; color: #ad1457; margin-top: 2px;">OTP: {otp}</div>'
        '</div>'
    )

# Helper: Render Route Stepper HTML
def render_route_stepper(steps, lang="en"):
    html_parts = ['<div class="timeline-container">']
    for item in steps:
        if "node" in item:
            node_name = item.get("node_te") if lang == "te" and "node_te" in item else item.get("node", "")
            node_name = get_translated_city(node_name, lang)
            time_str = item.get("time", "")
            node_type = item.get("type", "origin")
            
            if node_type == "origin":
                icon = "📍"
                css_class = "timeline-node"
            elif node_type == "transfer":
                icon = "🔄"
                css_class = "timeline-node-transfer"
            else:
                icon = "🏁"
                css_class = "timeline-node-dest"
                
            time_badge = f' ({time_str})' if time_str else ''
            html_parts.append(f'<div class="{css_class}"><span>{icon}</span><span><b>{node_name}</b>{time_badge}</span></div>')
        elif "transit" in item:
            transit_name = item.get("transit_te") if lang == "te" and "transit_te" in item else item.get("transit", "")
            dur = item.get("duration", "")
            dur_badge = f' <span style="opacity: 0.8; font-size: 0.72rem;">[{dur}]</span>' if dur else ''
            html_parts.append(f'<span class="timeline-arrow">➔</span><div class="timeline-leg"><span>{transit_name}</span>{dur_badge}</div><span class="timeline-arrow">➔</span>')
    html_parts.append('</div>')
    return "".join(html_parts)

# Helper: Wizard Progress Stepper Bar
def render_wizard_stepper_bar(step_num, lang="en"):
    step_defs = [
        (1, t("wizard_step_1", lang)),
        (2, t("wizard_step_2", lang)),
        (3, t("wizard_step_3", lang)),
        (4, t("wizard_step_4", lang)),
        (5, t("wizard_step_5", lang)),
        (6, t("wizard_step_6", lang)),
    ]
    parts = ['<div class="wizard-nav-bar">']
    for idx, (s_num, s_label) in enumerate(step_defs):
        if s_num < step_num:
            parts.append(f'<span class="step-pill-done">✓ {s_label}</span>')
        elif s_num == step_num:
            parts.append(f'<span class="step-pill-active">● {s_label}</span>')
        else:
            parts.append(f'<span class="step-pill-future">○ Step {s_num}</span>')
        if idx < len(step_defs) - 1:
            parts.append('<span class="step-arrow">➔</span>')
    parts.append('</div>')
    return "".join(parts)

# Initialize Session State
if "wizard_step" not in st.session_state:
    st.session_state.wizard_step = 1

if "user_name" not in st.session_state:
    st.session_state.user_name = "Susmitha D"

if "user_phone" not in st.session_state:
    st.session_state.user_phone = "+91 98480 23456"

if "lang" not in st.session_state:
    st.session_state.lang = "en"

if "origin" not in st.session_state:
    st.session_state.origin = "Kerala (Kochi)"

if "destination" not in st.session_state:
    st.session_state.destination = "Duvvada, Visakhapatnam"

if "dest_coords" not in st.session_state:
    st.session_state.dest_coords = [17.7042, 83.1524]

if "last_clicked_coords" not in st.session_state:
    st.session_state.last_clicked_coords = None

if "selected_luggage" not in st.session_state:
    st.session_state.selected_luggage = 2

if "selected_budget" not in st.session_state:
    st.session_state.selected_budget = 1500

if "selected_comfort" not in st.session_state:
    st.session_state.selected_comfort = "Sleeper"

if "deadline_choice" not in st.session_state:
    st.session_state.deadline_choice = "09:00 AM"

if "available_buses" not in st.session_state:
    st.session_state.available_buses = []

if "selected_bus" not in st.session_state:
    st.session_state.selected_bus = None

if "auto_booking" not in st.session_state:
    st.session_state.auto_booking = None

if "payment_mode" not in st.session_state:
    st.session_state.payment_mode = "UPI (GPay / PhonePe / Paytm)"

if "payment_done" not in st.session_state:
    st.session_state.payment_done = False

if "chaos_active" not in st.session_state:
    st.session_state.chaos_active = False

if "delay_minutes" not in st.session_state:
    st.session_state.delay_minutes = 45

if "booking_status" not in st.session_state:
    st.session_state.booking_status = None

curr_lang = st.session_state.lang
curr_step = st.session_state.wizard_step

# =========================================================================
# TOP HEADER BAR: TITLE & TOP-RIGHT LANGUAGE SELECTOR
# =========================================================================
col_head_l, col_head_r = st.columns([3.3, 1.7])
with col_head_l:
    header_subtitle = t("header_subtitle", curr_lang)
    header_html = (
        '<div class="main-header">'
        f'<h1>{t("app_title", curr_lang)}</h1>'
        f'<p>{header_subtitle}</p>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

with col_head_r:
    with st.container(border=True):
        st.markdown(f'<div style="font-weight: 700; color: #1b5e20; font-size: 0.88rem; margin-bottom: 0.2rem;">{t("lang_selector_title", curr_lang)}</div>', unsafe_allow_html=True)
        lang_labels = list(LANGUAGES.values())
        lang_keys = list(LANGUAGES.keys())
        current_idx = lang_keys.index(curr_lang) if curr_lang in lang_keys else 0
        
        selected_lang_label = st.selectbox(
            label="Select Preferred Language",
            options=lang_labels,
            index=current_idx,
            label_visibility="collapsed"
        )
        new_lang_key = lang_keys[lang_labels.index(selected_lang_label)]
        if new_lang_key != st.session_state.lang:
            st.session_state.lang = new_lang_key
            st.rerun()

# Render Wizard Progress Stepper Bar
st.markdown(render_wizard_stepper_bar(curr_step, curr_lang), unsafe_allow_html=True)

# =========================================================================
# STEP 1: ONBOARDING SCREEN
# =========================================================================
if curr_step == 1:
    st.markdown("### 👋 Step 1: Onboarding & Passenger Login")
    
    with st.container(border=True):
        st.markdown("""
        <div style="background: linear-gradient(135deg, #e8f5e9 0%, #ffffff 50%, #fce4ec 100%); padding: 1.2rem; border-radius: 10px; margin-bottom: 1.2rem; border: 1px solid #dceedb;">
            <b style="color: #1b5e20; font-size: 1.15rem;">Welcome to TBS RoamAgent Multimodal Concierge</b>
            <p style="color: #2c3e50; font-size: 0.92rem; margin: 0.3rem 0 0 0;">
                Your autonomous travel companion that seamlessly connects intercity buses with local autos, 
                and automatically mitigates highway delays in real-time.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        c_name, c_phone = st.columns(2)
        with c_name:
            user_name_input = st.text_input("Full Name (ప్రయాణీకుడి పేరు):", value=st.session_state.user_name)
        with c_phone:
            user_phone_input = st.text_input("Mobile Phone (ఫోన్ నంబర్):", value=st.session_state.user_phone)
            
        st.session_state.user_name = user_name_input
        st.session_state.user_phone = user_phone_input

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="display: flex; gap: 0.6rem; flex-wrap: wrap; margin-bottom: 1rem;">
            <span class="metric-badge-mint">🛡️ Smart Delay Auto-Readjustment</span>
            <span class="metric-badge-pink">⚡ Zero No-Show Local Auto Guarantee</span>
            <span class="metric-badge">🧳 Luggage-Aware Fleet Matching</span>
            <span class="metric-badge-mint">💳 Seamless UPI & Card Payments</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button(t("onboarding_next_btn", curr_lang), type="primary", use_container_width=True):
            if not user_name_input.strip() or not user_phone_input.strip():
                st.error("Please enter your name and phone number to continue.")
            else:
                st.session_state.wizard_step = 2
                st.rerun()

# =========================================================================
# STEP 2: MAIN SEARCH DASHBOARD (INTERACTIVE FOLIUM MAP + DYNAMIC ROUTING)
# =========================================================================
elif curr_step == 2:
    st.markdown("### 🗺️ Step 2: Main Search Dashboard & Interactive Map Pin")
    
    with st.container(border=True):
        st.markdown(f'<div style="font-size: 0.9rem; color: #1b5e20; font-weight: 700; margin-bottom: 0.6rem;">👤 Passenger: {st.session_state.user_name} ({st.session_state.user_phone})</div>', unsafe_allow_html=True)
        
        # Interactive Folium Map Section
        st.markdown("""
        <div style="background: linear-gradient(135deg, #e8f5e9 0%, #ffffff 50%, #fce4ec 100%); padding: 0.8rem 1.2rem; border-radius: 10px; border: 1px solid #dceedb; margin-bottom: 0.8rem;">
            <b style="color: #1b5e20; font-size: 0.95rem;">📍 Interactive Destination Pin Selection</b>
            <div style="font-size: 0.82rem; color: #2c3e50;">
                Click anywhere on the map of India to set your <b>Final Destination</b> pin (e.g. Duvvada, RK Beach, Hyderabad, Gajuwaka).
                The AI will reverse-geocode coordinates and dynamically generate intercity buses & local transit!
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_map, col_details = st.columns([3.2, 1.8])
        
        with col_map:
            # Create Folium Map centered around destination coordinates or India/Andhra Pradesh
            center_lat, center_lng = st.session_state.dest_coords if st.session_state.dest_coords else (17.7042, 83.1524)
            m = folium.Map(location=[center_lat, center_lng], zoom_start=8, tiles="OpenStreetMap")
            
            # Place marker at selected coordinates
            if st.session_state.dest_coords:
                folium.Marker(
                    location=st.session_state.dest_coords,
                    popup=f"Selected Destination: {st.session_state.destination}",
                    tooltip=f"🏁 {st.session_state.destination}",
                    icon=folium.Icon(color="green", icon="flag", prefix="glyphicon")
                ).add_to(m)

            # Render Folium Map in Streamlit and capture clicks
            map_data = st_folium(m, height=360, width=None, returned_objects=["last_clicked"])

            # Detect Map Click and reverse-geocode dynamically
            if map_data and map_data.get("last_clicked"):
                click_lat = round(map_data["last_clicked"]["lat"], 5)
                click_lng = round(map_data["last_clicked"]["lng"], 5)
                prev_click = st.session_state.get("last_clicked_coords")
                
                # Check if click is new
                if not prev_click or (abs(prev_click[0] - click_lat) > 0.0001 or abs(prev_click[1] - click_lng) > 0.0001):
                    st.session_state.last_clicked_coords = (click_lat, click_lng)
                    st.session_state.dest_coords = [click_lat, click_lng]
                    resolved_place = reverse_geocode(click_lat, click_lng)
                    st.session_state.destination = resolved_place
                    st.rerun()

        with col_details:
            st.markdown("##### 📍 Location Controls:")
            origin_input = st.text_input("Current Location (Origin):", value=st.session_state.origin)
            dest_input = st.text_input("Final Destination (Type or Click Map):", value=st.session_state.destination)
            
            st.session_state.origin = origin_input
            if dest_input != st.session_state.destination:
                st.session_state.destination = dest_input

            if st.session_state.dest_coords:
                st.markdown(f"""
                <div style="background: #e8f5e9; border: 1px solid #a5d6a7; border-radius: 8px; padding: 0.6rem; margin-top: 0.5rem;">
                    <b style="color: #1b5e20; font-size: 0.8rem;">🎯 Pin Coordinates:</b>
                    <div style="font-size: 0.76rem; color: #2c3e50;">
                        Lat: {st.session_state.dest_coords[0]:.4f}, Lng: {st.session_state.dest_coords[1]:.4f}<br>
                        Status: <b>Locked for Last-Mile Dispatch</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br><b>⚡ Quick Presets:</b>", unsafe_allow_html=True)
            p1, p2 = st.columns(2)
            with p1:
                if st.button("📍 Duvvada", use_container_width=True):
                    st.session_state.destination = "Duvvada, Visakhapatnam"
                    st.session_state.dest_coords = [17.7042, 83.1524]
                    st.rerun()
                if st.button("🌊 RK Beach", use_container_width=True):
                    st.session_state.destination = "Visakhapatnam (RK Beach)"
                    st.session_state.dest_coords = [17.7120, 83.3330]
                    st.rerun()
            with p2:
                if st.button("🏙️ Hyderabad", use_container_width=True):
                    st.session_state.destination = "Hyderabad Hitec City"
                    st.session_state.dest_coords = [17.4470, 78.3760]
                    st.rerun()
                if st.button("📍 Vijayawada", use_container_width=True):
                    st.session_state.destination = "Vijayawada Benz Circle"
                    st.session_state.dest_coords = [16.5000, 80.6400]
                    st.rerun()

        st.markdown("---")
        
        # Trip Constraints
        c_lug, c_bud, c_dead = st.columns(3)
        with c_lug:
            luggage_val = st.slider("Luggage Count (Heavy Bags):", 1, 4, st.session_state.selected_luggage)
            st.session_state.selected_luggage = luggage_val
        with c_bud:
            budget_val = st.slider("Total Budget (₹):", 500, 3000, st.session_state.selected_budget, 50)
            st.session_state.selected_budget = budget_val
        with c_dead:
            deadline_val = st.select_slider("Arrival Deadline:", ["07:30 AM", "08:00 AM", "08:30 AM", "09:00 AM", "09:30 AM", "10:00 AM"], value=st.session_state.deadline_choice)
            st.session_state.deadline_choice = deadline_val

        # Conversational NLP input
        st.markdown("---")
        st.markdown("##### 💬 Natural Language Prompt:")
        prompt_val = st.text_input(
            "Travel Prompt", 
            value=get_default_query(origin=st.session_state.origin, dest=st.session_state.destination, deadline=st.session_state.deadline_choice, luggage=st.session_state.selected_luggage, budget=st.session_state.selected_budget, lang=curr_lang), 
            label_visibility="collapsed"
        )
        
        c_back, c_search = st.columns([1, 2.5])
        with c_back:
            if st.button("← Back to Login", use_container_width=True):
                st.session_state.wizard_step = 1
                st.rerun()
        with c_search:
            if st.button(t("search_routes_btn", curr_lang), type="primary", use_container_width=True):
                # Dynamically generate buses between ANY two locations
                st.session_state.available_buses = generate_buses(
                    source=st.session_state.origin,
                    destination=st.session_state.destination,
                    budget=st.session_state.selected_budget,
                    luggage=st.session_state.selected_luggage,
                    comfort=st.session_state.selected_comfort
                )
                st.session_state.wizard_step = 3
                st.rerun()

# =========================================================================
# STEP 3: INTERCITY BUS SELECTION (DYNAMIC BUSES)
# =========================================================================
elif curr_step == 3:
    st.markdown(f"### 🚍 Step 3: Available Intercity Buses ({st.session_state.origin} ➔ {st.session_state.destination})")
    
    # Ensure buses exist
    if not st.session_state.available_buses:
        st.session_state.available_buses = generate_buses(
            source=st.session_state.origin,
            destination=st.session_state.destination,
            budget=st.session_state.selected_budget,
            luggage=st.session_state.selected_luggage
        )

    for b in st.session_state.available_buses:
        with st.container(border=True):
            c_info, c_btn = st.columns([3.5, 1.2])
            with c_info:
                st.markdown(f'<span class="metric-badge-mint">{b["badge"]}</span> <span class="metric-badge">📡 {b["telematics"]}</span>', unsafe_allow_html=True)
                st.markdown(f'<h4 style="margin: 0.3rem 0; color: #1b5e20;">{b["operator"]}</h4>', unsafe_allow_html=True)
                st.markdown(f'<b>Departs:</b> {b["departure"]} ➔ <b>Arrives:</b> {b["arrival"]} ({b["duration"]})')
                st.markdown(f'<div style="font-size: 0.85rem; color: #475569;">🛏️ {b["berth"]} • 🧳 Fits {st.session_state.selected_luggage} heavy bags in boot space</div>', unsafe_allow_html=True)
            with c_btn:
                st.markdown(f'<div style="text-align: right; font-size: 1.8rem; font-weight: 800; color: #1b5e20;">₹{b["cost"]}</div>', unsafe_allow_html=True)
                if st.button(f"Select Bus (₹{b['cost']}) ➔", key=f"sel_{b['id']}", type="primary", use_container_width=True):
                    st.session_state.selected_bus = b
                    # Dynamically calculate last-mile transport immediately
                    st.session_state.auto_booking = generate_dynamic_last_mile(
                        selected_bus=b,
                        destination=st.session_state.destination,
                        luggage=st.session_state.selected_luggage,
                        budget=st.session_state.selected_budget,
                        coords=st.session_state.get("dest_coords")
                    )
                    st.session_state.wizard_step = 4
                    st.rerun()

    c_b3, _ = st.columns([1, 3])
    with c_b3:
        if st.button("← Back to Search Criteria", use_container_width=True):
            st.session_state.wizard_step = 2
            st.rerun()

# =========================================================================
# STEP 4: SMART LAST-MILE AUTO-BOOKING (AI AGENT DYNAMIC DISPATCH)
# =========================================================================
elif curr_step == 4:
    st.markdown(f"### 🛺 Step 4: Smart Last-Mile Dispatch (AI Agent)")
    
    sel_bus = st.session_state.selected_bus
    if not sel_bus:
        st.session_state.wizard_step = 3
        st.rerun()

    if not st.session_state.auto_booking:
        st.session_state.auto_booking = generate_dynamic_last_mile(
            selected_bus=sel_bus,
            destination=st.session_state.destination,
            luggage=st.session_state.selected_luggage,
            budget=st.session_state.selected_budget,
            coords=st.session_state.get("dest_coords")
        )

    auto_data = st.session_state.auto_booking

    with st.container(border=True):
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #e8f5e9 0%, #ffffff 50%, #fce4ec 100%); padding: 1.2rem; border-radius: 12px; border: 1.5px solid #81c784; margin-bottom: 1.2rem;">
            <div style="display: flex; align-items: center; gap: 0.6rem;">
                <span style="font-size: 1.8rem;">🤖</span>
                <div>
                    <b style="color: #1b5e20; font-size: 1.1rem;">AI Agent Autonomous Last-Mile Coordination</b>
                    <p style="color: #2c3e50; font-size: 0.9rem; margin: 0.2rem 0 0 0;">
                        {auto_data['rationale']}
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c_auto_info, c_auto_driver = st.columns(2)
        with c_auto_info:
            st.markdown(f"""
            <div class="leg-box">
                <span style="background: #e8f5e9; color: #1b5e20; font-weight: 700; font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: 6px;">
                    PRE-COORDINATED LAST-MILE TRANSIT
                </span>
                <h4 style="margin: 0.4rem 0 0.2rem 0; color: #1b5e20;">{auto_data['mode']}</h4>
                <div style="font-size: 0.88rem; color: #2c3e50;">
                    • <b>Pickup Location:</b> {auto_data['pickup_loc']}<br>
                    • <b>Scheduled Pickup:</b> {auto_data['pickup_time']} (Luggage transfer buffer)<br>
                    • <b>Drop Location:</b> {auto_data['drop_loc']}<br>
                    • <b>Arrival ETA:</b> {auto_data['drop_time']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c_auto_driver:
            st.markdown(f"""
            <div class="leg-box">
                <span style="background: #fce4ec; color: #ad1457; font-weight: 700; font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: 6px;">
                    VERIFIED DRIVER & VEHICLE
                </span>
                <h4 style="margin: 0.4rem 0 0.2rem 0; color: #ad1457;">Driver: {auto_data['driver_name']}</h4>
                <div style="font-size: 0.88rem; color: #2c3e50;">
                    • <b>Vehicle No:</b> {auto_data['vehicle_no']}<br>
                    • <b>Fleet Synchronization:</b> Standby protocol active at drop bay<br>
                    • <b>Luggage Handling:</b> Boot and carrier space verified<br>
                    • <b>Safety Guarantee:</b> Zero surge pricing & zero cancellation fee
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Transparent Fare Breakdown
        bus_cost = sel_bus["cost"]
        auto_cost = auto_data["cost"]
        total_fare = auto_data["total_fare"]

        st.markdown(f"#### 💳 {t('fare_breakdown_title', curr_lang)}")
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #dceedb; border-radius: 12px; padding: 1.2rem; margin-bottom: 1.2rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                <span>🚍 Intercity Bus ({sel_bus['operator']})</span>
                <b>₹{bus_cost}</b>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                <span>🛺 Pre-coordinated {auto_data['mode']} ({auto_data['pickup_loc']} ➔ {st.session_state.destination})</span>
                <b>₹{auto_cost}</b>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; color: #1b5e20;">
                <span>🛡️ RoamAgent Zero-Disruption Insurance & Fleet Sync Guarantee</span>
                <b>₹0 (FREE)</b>
            </div>
            <hr style="margin: 0.5rem 0; border: none; border-top: 1px dashed #dceedb;">
            <div style="display: flex; justify-content: space-between; font-size: 1.2rem; font-weight: 800; color: #1b5e20;">
                <span>Total Multimodal Journey Fare:</span>
                <span>₹{total_fare}</span>
            </div>
            <div style="font-size: 0.8rem; color: #15803D; margin-top: 0.2rem;">
                ✓ Fits comfortably within your ₹{st.session_state.selected_budget} budget cap.
            </div>
        </div>
        """, unsafe_allow_html=True)

        c_b4, c_pay = st.columns([1, 2.5])
        with c_b4:
            if st.button("← Back to Bus Selection", use_container_width=True):
                st.session_state.wizard_step = 3
                st.rerun()
        with c_pay:
            if st.button(t("proceed_payment_btn", curr_lang), type="primary", use_container_width=True):
                st.session_state.wizard_step = 5
                st.rerun()

# =========================================================================
# STEP 5: PAYMENT GATEWAY
# =========================================================================
elif curr_step == 5:
    st.markdown(f"### 💳 Step 5: {t('payment_gateway_title', curr_lang)}")
    
    total_amount = st.session_state.auto_booking.get("total_fare", 1400) if st.session_state.auto_booking else 1400
    
    with st.container(border=True):
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #e8f5e9 0%, #ffffff 50%, #fce4ec 100%); padding: 1rem 1.4rem; border-radius: 12px; border: 1px solid #dceedb; margin-bottom: 1.2rem; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <b style="color: #1b5e20; font-size: 1.05rem;">{st.session_state.origin} ➔ {st.session_state.destination}</b>
                <div style="color: #64748B; font-size: 0.85rem;">Multimodal Booking: Intercity Bus + {st.session_state.auto_booking.get('mode', 'Local Auto') if st.session_state.auto_booking else 'Local Transit'}</div>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 0.8rem; color: #64748B;">TOTAL TO PAY</span>
                <div style="font-size: 1.8rem; font-weight: 800; color: #1b5e20;">₹{total_amount}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        pay_tab1, pay_tab2, pay_tab3 = st.tabs([
            "📱 UPI (GPay / PhonePe / Paytm)", 
            "💳 Credit / Debit Card", 
            "💵 Pay on Arrival"
        ])

        with pay_tab1:
            st.markdown("##### Pay via Instant UPI:")
            col_upi_id, col_upi_qr = st.columns([2.5, 1.5])
            with col_upi_id:
                upi_input = st.text_input("Enter Virtual Payment Address (UPI ID):", value=f"{st.session_state.user_name.lower().replace(' ', '')}@okaxis")
                st.caption("Supports Google Pay, PhonePe, Paytm, CRED, BHIM & all bank UPI apps.")
            with col_upi_qr:
                st.markdown(f"""
                <div style="background: #ffffff; border: 1.5px solid #dceedb; border-radius: 10px; padding: 0.8rem; text-align: center;">
                    <div style="font-size: 1.8rem;">📲</div>
                    <b style="color: #1b5e20; font-size: 0.82rem;">Scan & Pay ₹{total_amount}</b>
                    <div style="font-size: 0.72rem; color: #64748B;">UPI Dynamic Auto-Pay Active</div>
                </div>
                """, unsafe_allow_html=True)

        with pay_tab2:
            st.markdown("##### Pay via Card:")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.text_input("Card Number:", value="4532 •••• •••• 8821")
                st.text_input("Cardholder Name:", value=st.session_state.user_name.upper())
            with col_c2:
                st.text_input("Expiry Date:", value="08/28")
                st.text_input("CVV:", value="•••", type="password")

        with pay_tab3:
            st.markdown("##### Pay on Arrival:")
            auto_cost = st.session_state.auto_booking.get("cost", 80) if st.session_state.auto_booking else 80
            st.info(f"ℹ️ Pay ₹{auto_cost} in cash or UPI directly to driver {st.session_state.auto_booking.get('driver_name', 'Ramesh K.')} upon arrival at destination. Intercity bus ticket billed on boarding check-in.")

        st.markdown("<br>", unsafe_allow_html=True)
        c_b5, c_pay_now = st.columns([1, 2.5])
        with c_b5:
            if st.button("← Back to Transit Details", use_container_width=True):
                st.session_state.wizard_step = 4
                st.rerun()
        with c_pay_now:
            pay_btn_text = t("pay_now_btn", curr_lang, amount=total_amount)
            if st.button(pay_btn_text, type="primary", use_container_width=True):
                with st.spinner("Processing Payment & Reserving Multi-Fleet Inventory..."):
                    time.sleep(1.2)
                st.session_state.payment_done = True
                st.session_state.wizard_step = 6
                st.success("Payment Successful! Generating Boarding Pass...")
                st.rerun()

# =========================================================================
# STEP 6: LIVE ITINERARY & DISRUPTION ENGINE (DYNAMIC AUTO-READJUSTMENT)
# =========================================================================
elif curr_step == 6:
    st.markdown("### 🎫 Step 6: Live Itinerary & Disruption Engine")
    
    sel_bus = st.session_state.selected_bus or {
        "operator": "KSRTC SWIFT Deluxe Multi-Axle Volvo Sleeper",
        "departure_time": "04:30 PM",
        "arrival_time": "06:00 AM",
        "arrival_point": f"{st.session_state.destination} Central RTC Complex",
        "cost": 1320
    }
    
    last_mile = st.session_state.auto_booking or generate_dynamic_last_mile(
        selected_bus=sel_bus,
        destination=st.session_state.destination,
        luggage=st.session_state.selected_luggage,
        budget=st.session_state.selected_budget,
        coords=st.session_state.get("dest_coords")
    )

    # Active Disruption Recovery Model
    recovery_plan = generate_dynamic_disruption_recovery(
        selected_bus=sel_bus,
        last_mile=last_mile,
        origin=st.session_state.origin,
        destination=st.session_state.destination,
        delay_minutes=st.session_state.delay_minutes
    )

    # Disruption Simulator Controls Bar
    with st.container(border=True):
        col_ctl_text, col_ctl_btn = st.columns([3, 2])
        with col_ctl_text:
            if not st.session_state.chaos_active:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 0.6rem;">
                    <span class="status-pill pill-active">🟢 OPTIMAL FLOW</span>
                    <span style="font-weight: 700; color: #1b5e20;">All Journey Legs Synchronized on Schedule</span>
                </div>
                <div style="font-size: 0.85rem; color: #475569; margin-top: 0.2rem;">
                    Bus ETA at {last_mile['pickup_loc']}: {sel_bus['arrival_time']} • Standby: {last_mile['pickup_time']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 0.6rem;">
                    <span class="status-pill pill-alert">🚨 DELAY DETECTED</span>
                    <span style="font-weight: 800; color: #ad1457;">+{st.session_state.delay_minutes}-Min Highway Delay • Auto Rescheduled to {recovery_plan['rescheduled_auto_pickup']}</span>
                </div>
                <div style="font-size: 0.85rem; color: #880e4f; margin-top: 0.2rem;">
                    Bus delayed to {recovery_plan['delayed_bus_arrival']}. RoamAgent synchronized driver to {recovery_plan['rescheduled_auto_pickup']}.
                </div>
                """, unsafe_allow_html=True)
        with col_ctl_btn:
            if not st.session_state.chaos_active:
                if st.button("🚨 Simulate 45-min Highway Delay", type="primary", use_container_width=True):
                    st.session_state.chaos_active = True
                    st.session_state.booking_status = None
                    st.rerun()
            else:
                if st.button("🔄 Reset to Scheduled Timings", use_container_width=True):
                    st.session_state.chaos_active = False
                    st.session_state.booking_status = None
                    st.rerun()

    # If Highway Delay is triggered: display Smart Auto-Readjustment workflow
    if st.session_state.chaos_active:
        st.markdown(f"""
        <div class="disruption-banner">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <span class="status-pill pill-alert">🚨 REAL-TIME TELEMATICS INCIDENT DETECTED</span>
                    <h3 style="color: #ad1457; margin: 0.4rem 0 0.2rem 0; font-size: 1.35rem;">
                        45-Minute Highway Congestion & Bottleneck Detected on Route to {st.session_state.destination}
                    </h3>
                    <p style="color: #880e4f; margin: 0; font-size: 0.9rem;">
                        Intercity bus {sel_bus.get('operator', '')} delayed by 45 mins. Scheduled arrival shifted from {recovery_plan['original_bus_arrival']} to {recovery_plan['delayed_bus_arrival']}.
                    </p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 2.2rem; font-weight: 800; color: #ad1457;">+{recovery_plan['delay_minutes']} min</div>
                    <div style="font-size: 0.78rem; font-weight: 700; color: #880e4f;">HIGHWAY DELAY</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Highlight callout banner
        st.markdown(f"""
        <div class="readjustment-banner">
            <div style="display: flex; align-items: center; gap: 0.8rem;">
                <span style="font-size: 2rem;">⚡</span>
                <div>
                    <div style="color: #1b5e20; font-weight: 800; font-size: 1.15rem;">
                        {recovery_plan['reschedule_highlight_en']}
                    </div>
                    <div style="color: #2e7d32; font-size: 0.88rem; margin-top: 0.2rem;">
                        {recovery_plan['webhook_confirmation']}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Comparison cards
        c_unrec, c_rec = st.columns(2)
        with c_unrec:
            st.markdown(f"""
            <div style="background: #fff5f8; border: 2px solid #f8bbd0; border-radius: 12px; padding: 1.1rem;">
                <b style="color: #ad1457; font-size: 1rem;">❌ Without RoamAgent Coordination</b>
                <div style="font-size: 0.85rem; color: #880e4f; margin-top: 0.5rem;">
                    • Local driver cancels after standard 10-minute wait timeout at {recovery_plan['original_auto_pickup']}.<br>
                    • Traveler stranded with {st.session_state.selected_luggage} heavy bags at {last_mile['pickup_loc']}.<br>
                    • Forced to rebook in morning peak surge ➔ arrival delayed by over 90+ minutes.
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c_rec:
            st.markdown(f"""
            <div style="background: #f0fdf4; border: 2px solid #a5d6a7; border-radius: 12px; padding: 1.1rem;">
                <b style="color: #1b5e20; font-size: 1rem;">✅ With RoamAgent Smart Auto-Reschedule</b>
                <div style="font-size: 0.85rem; color: #1b5e20; margin-top: 0.5rem;">
                    • Local pickup rescheduled automatically from {recovery_plan['original_auto_pickup']} to {recovery_plan['rescheduled_auto_pickup']}.<br>
                    • Driver standby at {last_mile['pickup_loc']} with luggage assistance guaranteed.<br>
                    • Arrives at {st.session_state.destination} smoothly at {recovery_plan['rescheduled_arrival']} (Zero Extra Charge).
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Consent Gate
        st.markdown(f"#### 🛡️ {t('consent_gate_title', curr_lang)}")
        st.markdown("""
        <div class="consent-box">
            <div style="color: #ad1457; font-size: 0.92rem; font-weight: 700;">
                ⚠️ Consent Required: The agent will not modify driver dispatch without explicit traveler authorization.
            </div>
            <p style="color: #2c3e50; font-size: 0.86rem; margin: 0.3rem 0 0 0;">
                Please review the rescheduled auto dispatch timings above and authorize fleet synchronization:
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_c_app, col_c_rej = st.columns([2.5, 1.5])
        with col_c_app:
            if st.button("✅ Approve Delay & Auto Reschedule", type="primary", use_container_width=True):
                st.session_state.booking_status = "approved"
        with col_c_rej:
            if st.button("❌ Reject", use_container_width=True):
                st.session_state.booking_status = "rejected"

        if st.session_state.booking_status == "approved":
            st.balloons()
            st.success(f"🎉 DELAY APPROVED & LOCAL TRANSIT AUTONOMOUSLY RESCHEDULED TO {recovery_plan['rescheduled_auto_pickup']}!")
        elif st.session_state.booking_status == "rejected":
            st.warning("⚠️ Traveler rejected auto-rescheduling. Warning: Driver will cancel wait timeout due to highway delay.")

    # Render Visual Timeline Stepper
    timeline_steps = recovery_plan["timeline_steps"] if st.session_state.chaos_active else [
        {"node": st.session_state.origin, "time": sel_bus.get("departure_time", "04:30 PM"), "type": "origin"},
        {"transit": f"🚍 {sel_bus.get('operator', 'Intercity Bus')}", "duration": sel_bus.get("duration", "13h 30m")},
        {"node": last_mile.get("pickup_loc", "Transit Hub"), "time": sel_bus.get("arrival_time", "06:00 AM"), "type": "transfer"},
        {"transit": f"🛺 {last_mile.get('mode', 'EV Auto')}", "duration": "25m Smooth Run"},
        {"node": st.session_state.destination, "time": last_mile.get("drop_time", "06:40 AM"), "type": "destination"}
    ]
    st.markdown(render_route_stepper(timeline_steps, curr_lang), unsafe_allow_html=True)

    # FINAL BOARDING PASS (Intercity Bus PNR + Local Auto Dispatch Code)
    st.markdown("#### 🎫 Digital Boarding Pass & Multi-Fleet Pass")
    col_tkt, col_qr = st.columns([2.6, 1.2])
    
    bus_pnr = recovery_plan["pnr"]
    auto_code = recovery_plan["auto_dispatch_code"]
    auto_otp = recovery_plan["auto_otp"]
    driver_info = recovery_plan["driver_name"]
    eta_time = recovery_plan["rescheduled_arrival"] if st.session_state.chaos_active else last_mile.get("drop_time", "06:40 AM")
    auto_time = f"{recovery_plan['rescheduled_auto_pickup']} (Rescheduled)" if st.session_state.chaos_active else f"{last_mile.get('pickup_time', '06:15 AM')} (Scheduled)"
    status_badge = "CONFIRMED & RESCHEDULED" if st.session_state.chaos_active else "CONFIRMED & ON-TIME"

    with col_tkt:
        ticket_html = (
            '<div class="ticket-wrapper">'
            '<div class="ticket-header">'
            '<div>'
            '<div style="font-size: 0.75rem; letter-spacing: 1px; color: #1b5e20; font-weight: 700; text-transform: uppercase;">TBS ROAMAGENT MULTIMODAL BOARDING PASS</div>'
            f'<h3 style="margin: 0; font-size: 1.35rem; color: #1b5e20;">{st.session_state.origin} ➔ {st.session_state.destination}</h3>'
            '</div>'
            '<div style="text-align: right;">'
            f'<span style="background: #e8f5e9; color: #1b5e20; border: 1px solid #a5d6a7; padding: 0.35rem 0.8rem; border-radius: 9999px; font-weight: 700; font-size: 0.82rem;">{status_badge}</span>'
            '</div>'
            '</div>'
            '<div class="ticket-body">'
            '<div style="flex: 1; min-width: 140px;">'
            '<span style="color: #64748B; font-size: 0.78rem; text-transform: uppercase; font-weight: 600;">INTERCITY BUS PNR</span><br>'
            f'<b style="font-size: 1.25rem; color: #1b5e20; letter-spacing: 0.5px;">{bus_pnr}</b><br>'
            f'<span style="font-size: 0.76rem; color: #64748B;">{sel_bus.get("berth", "AC Sleeper Berth")}</span>'
            '</div>'
            '<div style="flex: 1; min-width: 140px;">'
            '<span style="color: #64748B; font-size: 0.78rem; text-transform: uppercase; font-weight: 600;">LOCAL TRANSIT CODE</span><br>'
            f'<b style="font-size: 1.25rem; color: #ad1457; letter-spacing: 0.5px;">{auto_code}</b><br>'
            f'<span style="font-size: 0.76rem; color: #ad1457; font-weight: 700;">Security OTP: {auto_otp}</span>'
            '</div>'
            '<div style="flex: 1; min-width: 130px;">'
            '<span style="color: #64748B; font-size: 0.78rem; text-transform: uppercase; font-weight: 600;">FINAL DESTINATION ETA</span><br>'
            f'<b style="font-size: 1.25rem; color: #2e7d32;">{eta_time}</b><br>'
            '<span style="font-size: 0.76rem; color: #1b5e20;">✅ On-Time Delivery</span>'
            '</div>'
            '</div>'
            '<div class="ticket-perforation"></div>'
            '<div style="padding: 1.1rem 1.6rem; background: #ffffff;">'
            '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.8rem;">'
            '<div>'
            '<span style="color: #64748B; font-size: 0.78rem; font-weight: 600;">PASSENGER & CONTACT:</span><br>'
            f'<b style="color: #2c3e50; font-size: 0.9rem;">{st.session_state.user_name}</b> ({st.session_state.user_phone})<br>'
            f'<span style="font-size: 0.8rem; color: #64748B;">Luggage: {st.session_state.selected_luggage} Heavy Suitcases Verified</span>'
            '</div>'
            '<div>'
            '<span style="color: #64748B; font-size: 0.78rem; font-weight: 600;">ASSIGNED DRIVER & STAND:</span><br>'
            f'<b style="color: #1b5e20; font-size: 0.9rem;">{driver_info}</b><br>'
            f'<span style="font-size: 0.8rem; color: #ad1457; font-weight: 600;">Pickup: {auto_time} at {last_mile["pickup_loc"]}</span>'
            '</div>'
            '</div>'
            '</div>'
            '</div>'
        )
        st.markdown(ticket_html, unsafe_allow_html=True)

    with col_qr:
        qr_box_html = (
            '<div style="text-align: center; margin-top: 1rem;">'
            '<h5 style="margin: 0 0 0.4rem 0; color: #1b5e20;">🛺 Transit QR Pass</h5>'
            + render_qr_svg_mockup(token_label=auto_code, otp=auto_otp) +
            f'<div style="font-size: 0.75rem; color: #64748B; margin-top: 0.4rem;">Show to {driver_info} at {last_mile["pickup_loc"]}<br>Direct luggage handling verified</div>'
            '</div>'
        )
        st.markdown(qr_box_html, unsafe_allow_html=True)

    # Downloadable Dossier
    dossier_text = f"""======================================================================
TBS ROAMAGENT MULTIMODAL TRAVEL DOSSIER
PNR: {bus_pnr} | SAMARTHA HACKATHON EDITION
======================================================================
Passenger: {st.session_state.user_name} ({st.session_state.user_phone})
Route: {st.session_state.origin} -> {st.session_state.destination}
Journey Status: {status_badge}
Final Destination Arrival: {eta_time}
Total Multimodal Fare: ₹{last_mile.get('total_fare', 1400)} (Zero Disruption Guarantee Active)

----------------------------------------------------------------------
LEG 1: INTERCITY BUS
----------------------------------------------------------------------
Operator: {sel_bus.get('operator', 'Intercity Volvo')}
Bus PNR: {bus_pnr}
Seat/Berth: {sel_bus.get('berth', 'AC Sleeper Berth')}
Pickup: {st.session_state.origin}
Drop: {last_mile.get('pickup_loc')}
Luggage: {st.session_state.selected_luggage} Heavy Suitcases Verified in Boot

----------------------------------------------------------------------
LEG 2: LOCAL TRANSIT ({last_mile.get('mode', 'Smart Local EV Auto')})
----------------------------------------------------------------------
Dispatch Code: {auto_code}
Security OTP: {auto_otp}
Assigned Driver: {driver_info}
Pickup Stand: {last_mile.get('pickup_loc')}
Pickup Time: {auto_time}
Drop Location: {st.session_state.destination} ({eta_time})
Driver Wait Fee: ₹0 (Zero No-Show Guarantee Applied)
======================================================================
"""
    st.download_button(
        label="📥 Download Boarding Pass Dossier (TBS_Boarding_Pass.txt)",
        data=dossier_text,
        file_name="TBS_Boarding_Pass.txt",
        mime="text/plain",
        type="primary",
        use_container_width=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Plan Another Journey / Start Over", use_container_width=True):
        st.session_state.wizard_step = 2
        st.session_state.chaos_active = False
        st.session_state.booking_status = None
        st.rerun()

# Footer
st.markdown("<br><hr>", unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)
with f1:
    st.caption("🛡️ **TBS RoamAgent** | SAMARTHA Hackathon Prototype")
with f2:
    st.caption(f"🚀 Active Wizard Step: {curr_step} of 6")
with f3:
    st.caption("📡 Telematics Fleet Engine v3.0 Active")
