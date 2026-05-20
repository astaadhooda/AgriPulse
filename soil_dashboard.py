import streamlit as st
import requests
import json
import time

# --- FIREBASE CONFIG ---
URL = "https://soil-ai-monitor-default-rtdb.asia-southeast1.firebasedatabase.app/.json"

st.set_page_config(page_title="SoilAI", page_icon="🌱", layout="centered")

# --- TOP NAVIGATION: LANGUAGE & THEME TOGGLE ---
col_lang, col_theme = st.columns([3, 1])

with col_lang:
    lang = st.radio("Language Selection", ["English", "ಕನ್ನಡ"], horizontal=True, label_visibility="collapsed")

with col_theme:
    theme_mode = st.selectbox("Theme", ["Dark Mode 🌙", "Light Mode ☀️"], label_visibility="collapsed")

# --- DYNAMIC APPLE DESIGN STYLING ---
if "Dark" in theme_mode:
    # Premium Dark Mode Theme Variables
    bg_overlay = "linear-gradient(rgba(0, 0, 0, 0.72), rgba(0, 0, 0, 0.85))"
    card_bg = "rgba(255, 255, 255, 0.07)"
    card_border = "rgba(255, 255, 255, 0.15)"
    text_primary = "#ffffff"
    text_secondary = "#86868b"
    text_muted = "#aaaaaa"
    dropdown_bg = "rgba(0, 0, 0, 0.4)"
    dropdown_border = "rgba(255, 255, 255, 0.2)"
    btn_bg = "#ffffff"
    btn_text = "#000000"
    live_block_bg = "rgba(255, 255, 255, 0.04)"
    ai_block_bg = "rgba(255, 255, 255, 0.12)"
    ai_block_border = "rgba(255, 255, 255, 0.1)"
else:
    # Premium Light Mode Theme Variables (Apple Design Studio style)
    bg_overlay = "linear-gradient(rgba(255, 255, 255, 0.45), rgba(255, 255, 255, 0.65))"
    card_bg = "rgba(255, 255, 255, 0.65)"
    card_border = "rgba(0, 0, 0, 0.08)"
    text_primary = "#1d1d1f"
    text_secondary = "#515154"
    text_muted = "#6e6e73"
    dropdown_bg = "rgba(255, 255, 255, 0.8)"
    dropdown_border = "rgba(0, 0, 0, 0.15)"
    btn_bg = "#1d1d1f"
    btn_text = "#ffffff"
    live_block_bg = "rgba(0, 0, 0, 0.03)"
    ai_block_bg = "rgba(0, 0, 0, 0.05)"
    ai_block_border = "rgba(0, 0, 0, 0.06)"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    .stApp {{
        background: {bg_overlay}, 
                    url('https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?q=80&w=2000&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        transition: background 0.3s ease;
    }}

    .glass-card {{
        background: {card_bg};
        border-radius: 35px;
        padding: 45px;
        border: 1px solid {card_border};
        backdrop-filter: blur(30px);
        -webkit-backdrop-filter: blur(30px);
        box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        margin-top: 15px;
        transition: all 0.3s ease;
    }}

    .title-text {{
        font-family: 'Inter', sans-serif;
        font-weight: 800; font-size: 2.8rem; line-height: 1.1;
        margin-bottom: 25px; color: {text_primary}; letter-spacing: -0.05em;
        text-align: center;
    }}

    /* Global Dynamic Form Elements Override */
    div[data-baseweb="select"] > div {{
        background-color: {dropdown_bg} !important;
        border-radius: 12px !important;
        border: 1px solid {dropdown_border} !important;
        color: {text_primary} !important;
    }}
    
    /* Ensure the values inside drop-downs conform to selected theme color */
    div[data-baseweb="select"] span {{
        color: {text_primary} !important;
    }}

    div.stButton > button:first-child {{
        background-color: {btn_bg}; color: {btn_text}; border-radius: 30px;
        height: 4em; width: 100%; border: none; font-weight: 700;
        font-size: 1.1rem; transition: 0.2s ease; margin-top: 20px;
    }}
    div.stButton > button:first-child:hover {{
        transform: scale(1.01);
        opacity: 0.9;
    }}
    
    .section-title {{
        font-weight: 700; color: {text_secondary}; font-size: 0.9rem; 
        text-transform: uppercase; letter-spacing: 0.08em; margin-top: 25px; margin-bottom: 10px;
    }}

    header, footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- TRANSLATIONS & DROPDOWN MAPPING ---
translations = {
    "English": {
        "title": "Soil Intelligence Expert.",
        "crops": ["Tomato", "Chilli"],
        "stages": ["Vegetative", "Flowering", "Fruiting"],
        "btn": "Analyze & Recommend",
        "n": "N", "p": "P", "k": "K",
        "live_lbl": "Live Sensor Readings",
        "ai_lbl": "AI Nutrient Recommendations"
    },
    "ಕನ್ನಡ": {
        "title": "ಮಣ್ಣಿನ ಬುದ್ಧಿವಂತಿಕೆ ತಜ್ಞ.",
        "crops": ["ಟೊಮೆಟೊ (Tomato)", "ಮೆಣಸಿನಕಾಯಿ (Chilli)"],
        "stages": ["ಸಸ್ಯಕ ಹಂತ (Vegetative)", "ಹೂಬಿಡುವ ಹಂತ (Flowering)", "ಕಾಯಿ ಬಿಡುವ ಹಂತ (Fruiting)"],
        "btn": "ವಿಶ್ಲೇಷಿಸಿ ಮತ್ತು ಶಿಫಾರಸು ಪಡೆಯಿರಿ",
        "n": "ಸಾರಜನಕ (N)", "p": "ರಂಜಕ (P)", "k": "ಪೊಟ್ಯಾಕಿಯಮ್ (K)",
        "live_lbl": "ಪ್ರಸ್ತುತ ಸೆನ್ಸಾರ್ ಡೇಟಾ",
        "ai_lbl": "AI ಪೌಷ್ಟಿಕಾಂಶ ಶಿಫಾರಸುಗಳು"
    }
}

crop_map = {"ಟೊಮೆಟೊ (Tomato)": "Tomato", "ಮೆಣಸಿನಕಾಯಿ (Chilli)": "Chilli", "Tomato": "Tomato", "Chilli": "Chilli"}
stage_map = {
    "ಸಸ್ಯಕ ಹಂತ (Vegetative)": "Vegetative", "ಹೂಬಿಡುವ ಹಂತ (Flowering)": "Flowering", "ಕಾಯಿ ಬಿಡುವ ಹಂತ (Fruiting)": "Fruiting",
    "Vegetative": "Vegetative", "Flowering": "Flowering", "Fruiting": "Fruiting"
}

t = translations[lang]

# The Main Interaction Plate
st.markdown(f"""
    <div class='glass-card'>
        <div class='title-text'>🌱 {t['title']}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-top:-60px;'>", unsafe_allow_html=True)
sel_crop_ui = st.selectbox("Crop Selector", t["crops"], label_visibility="collapsed")
sel_stage_ui = st.selectbox("Stage Selector", t["stages"], label_visibility="collapsed")

if st.button(t["btn"]):
    c_eng = crop_map[sel_crop_ui]
    s_eng = stage_map[sel_stage_ui]
    
    requests.patch(URL, data=json.dumps({"crop": c_eng, "stage": s_eng, "status": "requesting"}))
    
    with st.spinner(""):
        for _ in range(12):
            time.sleep(1)
            data = requests.get(URL).json()
            if data.get('status') == 'idle':
                st.session_state['recs'] = data.get('recommendations')
                st.session_state['sensors'] = data.get('current_sensors')
                break

# Results Section
if 'recs' in st.session_state:
    r = st.session_state['recs']
    s = st.session_state.get('sensors', {"n":0,"p":0,"k":0,"ph":7.0,"temp":25.0,"hum":60.0,"moist":50.0})
    
    # --- BLOCK 1: LIVE HARDWARE DATA ---
    st.markdown(f"<div class='section-title'>盒 {t['live_lbl']}</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; flex-wrap: wrap; margin-bottom: 20px;">
        <div style="text-align:center; background:{live_block_bg}; padding:12px; border-radius:14px; width:22%; margin:5px 0;">
            <small style="color:{text_secondary}; font-size:0.75rem;">Soil NPK</small><div style="color:{text_primary}; font-size:1.1rem; font-weight:600; margin-top:3px;">{int(s['n'])}-{int(s['p'])}-{int(s['k'])}</div>
        </div>
        <div style="text-align:center; background:{live_block_bg}; padding:12px; border-radius:14px; width:22%; margin:5px 0;">
            <small style="color:{text_secondary}; font-size:0.75rem;">Soil pH</small><div style="color:{text_primary}; font-size:1.1rem; font-weight:600; margin-top:3px;">{s['ph']}</div>
        </div>
        <div style="text-align:center; background:{live_block_bg}; padding:12px; border-radius:14px; width:22%; margin:5px 0;">
            <small style="color:{text_secondary}; font-size:0.75rem;">Moisture</small><div style="color:{text_primary}; font-size:1.1rem; font-weight:600; margin-top:3px;">{s['moist']}%</div>
        </div>
        <div style="text-align:center; background:{live_block_bg}; padding:12px; border-radius:14px; width:22%; margin:5px 0;">
            <small style="color:{text_secondary}; font-size:0.75rem;">Air Temp</small><div style="color:{text_primary}; font-size:1.1rem; font-weight:600; margin-top:3px;">{s['temp']}°C</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- BLOCK 2: AI TARGET RECOMMENDATIONS ---
    st.markdown(f"<div class='section-title'>🤖 {t['ai_lbl']}</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="display: flex; justify-content: space-around;">
        <div style="text-align:center; background:{ai_block_bg}; padding:20px; border-radius:20px; width:30%; border: 1px solid {ai_block_border};">
            <small style="color:{text_muted}; font-weight:600;">{t['n']}</small><h2 style="color:{text_primary}; margin:5px 0 0 0; font-size:1.8rem;">{r['N']}</h2><small style="color:{text_secondary}; font-size:0.7rem;">kg/ha</small>
        </div>
        <div style="text-align:center; background:{ai_block_bg}; padding:20px; border-radius:20px; width:30%; border: 1px solid {ai_block_border};">
            <small style="color:{text_muted}; font-weight:600;">{t['p']}</small><h2 style="color:{text_primary}; margin:5px 0 0 0; font-size:1.8rem;">{r['P']}</h2><small style="color:{text_secondary}; font-size:0.7rem;">kg/ha</small>
        </div>
        <div style="text-align:center; background:{ai_block_bg}; padding:20px; border-radius:20px; width:30%; border: 1px solid {ai_block_border};">
            <small style="color:{text_muted}; font-weight:600;">{t['k']}</small><h2 style="color:{text_primary}; margin:5px 0 0 0; font-size:1.8rem;">{r['K']}</h2><small style="color:{text_secondary}; font-size:0.7rem;">kg/ha</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)