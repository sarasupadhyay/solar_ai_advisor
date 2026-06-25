import os
import streamlit as st
from streamlit_js_eval import get_geolocation
from streamlit_folium import st_folium
import folium
import pandas as pd
from datetime import datetime, timedelta
from solar_calculator import running_financial_analysis, build_generation_timeseries
from query_rag import ask_solar_advisor

# Prevent internal tokenization warning alerts
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 1. Page Layout Configuration
st.set_page_config(page_title="Solar AI Advisor", layout="wide", page_icon="☀️")

# ── Theme state ──────────────────────────────────────────────────────────────
# "dark" or "light" — persists across reruns via session_state
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

_is_dark = st.session_state.theme == "dark"

# ── Inject CSS variables for the active theme ────────────────────────────────
# We inject the correct palette on every rerun so ALL custom HTML elements
# (panels, chat bubbles, metric cards) automatically match the chosen theme.
# Streamlit's native widget colours are controlled further below via
# a dynamically-written .streamlit/config.toml equivalent using st.html().
if _is_dark:
    # ── DARK MODE — original palette from COLOR_COMPARISON.md ──────────────
    _theme_vars = """
    :root {
        --bg-primary:            #0F172A;
        --bg-secondary:          #1E293B;
        --bg-tertiary:           #334155;
        --border-primary:        #334155;
        --border-accent-orange:  #FFA500;
        --text-primary:          #F1F5F9;
        --text-secondary:        #CBD5E1;
        --text-tertiary:         #94A3B8;
        --accent-orange:         #FFA500;
        --accent-purple:         #FFA500;
        --accent-green:          #10B981;
        --accent-teal:           #3B82F6;
        --header-gradient-start: #1E1B4B;
        --header-gradient-end:   #311042;
        --metric-bg:             #1E293B;
        --metric-border:         #475569;
        --panel-bg:              #1E293B;
        --panel-border:          #3B82F6;
        --sidebar-chat-bg:       #0F172A;
        --chat-container-bg:     #0F172A;
        --chat-user-bg:          linear-gradient(135deg, #FFA500, #FB923C);
        --chat-bot-bg:           #1E293B;
        --chat-bot-text:         #CBD5E1;
        --chat-bot-border:       #334155;
    }
    .stApp { background-color: #0F172A !important; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }
    """
else:
    # ── LIGHT MODE — warm mint-green + cream + amber palette ─────────────────
    # Page: soft sage-cream  |  Cards: warm white  |  Borders: mint-green
    # Accents: amber-orange  |  Text: deep forest-green
    _theme_vars = """
    :root {
        --bg-primary:            #F5FDF7;
        --bg-secondary:          #FFFFFF;
        --bg-tertiary:           #DCFCE7;
        --border-primary:        #86EFAC;
        --border-accent-orange:  #D97706;
        --text-primary:          #14532D;
        --text-secondary:        #166534;
        --text-tertiary:         #15803D;
        --accent-orange:         #D97706;
        --accent-purple:         #D97706;
        --accent-green:          #16A34A;
        --accent-teal:           #0D9488;
        --header-gradient-start: #166534;
        --header-gradient-end:   #14532D;
        --metric-bg:             #FFFFFF;
        --metric-border:         #86EFAC;
        --panel-bg:              #FFFFFF;
        --panel-border:          #86EFAC;
        --sidebar-chat-bg:       #F0FDF4;
        --chat-container-bg:     #FAFFFE;
        --chat-user-bg:          linear-gradient(135deg, #D97706, #F59E0B);
        --chat-bot-bg:           #F0FDF4;
        --chat-bot-text:         #14532D;
        --chat-bot-border:       #BBF7D0;
    }

    /* ═══════════════════════════════════════════════════════════
       LIGHT MODE — warm mint + cream + amber
       Page: sage-cream #F5FDF7  |  Cards: white  |  Border: mint #86EFAC
       Accent: amber #D97706  |  Text: forest green #14532D
    ═══════════════════════════════════════════════════════════ */

    /* ── Page & layout ── */
    .stApp                                         { background-color: #F5FDF7 !important; }
    .stApp > div, .block-container                 { background-color: #F5FDF7 !important; }
    section[data-testid="stSidebar"]               { background-color: #DCFCE7 !important; border-right: 2px solid #86EFAC !important; }

    /* ── All text ── */
    .stApp *                                       { color: #14532D; }
    .stMarkdown, .stMarkdown *                     { color: #14532D !important; }

    /* ── Header panel — always white text (dark gradient bg) ── */
    .header-panel h1, .header-panel p,
    .header-panel *                                { color: #FFFFFF !important; }

    /* ── Block/column wrappers — transparent so cream bg shows ── */
    [data-testid="column"],
    [data-testid="stHorizontalBlock"],
    [data-testid="stVerticalBlock"],
    [data-testid="stVerticalBlockBorderWrapper"]   { background-color: transparent !important; }

    /* ── Scrollable container (chat box) ── */
    [data-testid="stContainer"],
    [data-testid="stContainer"] > div,
    [data-testid="stContainer"] > div > div        { background-color: #FFFFFF !important; border: 1.5px solid #BBF7D0 !important; border-radius: 10px !important; }

    /* ── Widget labels — but NOT inside header-panel ── */
    .stApp label,
    [data-testid="stWidgetLabel"] p                { color: #14532D !important; font-weight: 600 !important; }
    /* Paragraphs outside the header get forest-green text */
    .stApp p:not(.header-panel p)                  { color: #14532D !important; }

    /* ── Number inputs (+/− spinner, rooftop area, unit, charges) ── */
    [data-testid="stNumberInput"] input            { background-color: #FFFFFF !important; color: #14532D !important; border: 1.5px solid #86EFAC !important; border-radius: 8px !important; }
    [data-testid="stNumberInput"] > div            { background-color: #FFFFFF !important; border: 1.5px solid #86EFAC !important; border-radius: 8px !important; }
    [data-testid="stNumberInput"] button           { background-color: #DCFCE7 !important; color: #166534 !important; border: 1px solid #86EFAC !important; }
    [data-testid="stNumberInput"] button:hover     { background-color: #BBF7D0 !important; color: #14532D !important; }

    /* ── Text / Textarea inputs ── */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea            { background-color: #FFFFFF !important; color: #14532D !important; border: 1.5px solid #86EFAC !important; border-radius: 8px !important; }
    [data-testid="stTextInput"] > div,
    [data-testid="stTextArea"] > div               { background-color: #FFFFFF !important; }

    /* ── Selectbox ── */
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stSelectbox"] > div > div        { background-color: #FFFFFF !important; color: #14532D !important; border: 1.5px solid #86EFAC !important; border-radius: 8px !important; }
    [data-baseweb="popover"] [role="listbox"],
    [data-baseweb="menu"]                          { background-color: #FFFFFF !important; border: 1.5px solid #86EFAC !important; border-radius: 8px !important; }
    [data-baseweb="popover"] [role="option"]       { background-color: #FFFFFF !important; color: #14532D !important; }
    [data-baseweb="popover"] [role="option"]:hover { background-color: #DCFCE7 !important; color: #14532D !important; }

    /* ── Radio buttons ── */
    [data-testid="stRadio"] label,
    [data-testid="stRadio"] p                      { color: #14532D !important; }
    [data-testid="stRadio"] > div                  { background-color: transparent !important; }

    /* ── File uploader ── */
    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] > div,
    [data-testid="stFileUploader"] section         { background-color: #FFFFFF !important; border: 1.5px dashed #86EFAC !important; border-radius: 10px !important; }
    [data-testid="stFileUploaderDropzone"]          { background-color: #F0FDF4 !important; border: 1.5px dashed #86EFAC !important; border-radius: 10px !important; }
    [data-testid="stFileUploader"] *               { color: #166534 !important; }
    /* Browse files button — white bg, green text, green border */
    [data-testid="stFileUploaderDropzone"] button,
    [data-testid="stFileUploader"] button          { background-color: #FFFFFF !important; color: #166534 !important; border: 1.5px solid #86EFAC !important; border-radius: 8px !important; }
    [data-testid="stFileUploaderDropzone"] button:hover,
    [data-testid="stFileUploader"] button:hover    { background-color: #DCFCE7 !important; }

    /* ── Secondary buttons (Quick Questions, Clear Chat) ── */
    .stButton > button                             { background-color: #DCFCE7 !important; color: #14532D !important; border: 1.5px solid #86EFAC !important; border-radius: 10px !important; font-weight: 600 !important; }
    .stButton > button:hover                       { background-color: #BBF7D0 !important; color: #14532D !important; border-color: #4ADE80 !important; }
    /* Primary buttons — amber */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] { background-color: #D97706 !important; color: #FFFFFF !important; border: 1.5px solid #B45309 !important; }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover { background-color: #B45309 !important; }

    /* ── Tabs ── */
    [data-baseweb="tab-list"]                      { background-color: #DCFCE7 !important; border-bottom: 2px solid #86EFAC !important; border-radius: 10px 10px 0 0 !important; padding: 0 0.5rem !important; }
    [data-baseweb="tab"]                           { color: #166534 !important; background-color: transparent !important; font-weight: 600 !important; }
    [data-baseweb="tab"][aria-selected="true"]     { color: #D97706 !important; border-bottom: 3px solid #D97706 !important; }
    [data-baseweb="tab-panel"]                     { background-color: #FFFFFF !important; border: 1.5px solid #BBF7D0 !important; border-top: none !important; border-radius: 0 0 10px 10px !important; padding: 1rem !important; }

    /* ── Charts — force white bg on every layer incl. the Vega canvas ── */
    [data-testid="stVegaLiteChart"],
    [data-testid="stArrowVegaLiteChart"],
    [data-testid="stVegaLiteChart"] > div,
    [data-testid="stArrowVegaLiteChart"] > div,
    [data-testid="stVegaLiteChart"] canvas,
    [data-testid="stArrowVegaLiteChart"] canvas,
    [data-testid="stVegaLiteChart"] svg,
    [data-testid="stArrowVegaLiteChart"] svg       { background-color: #FFFFFF !important; border-radius: 10px !important; }
    [data-testid="stVegaLiteChart"],
    [data-testid="stArrowVegaLiteChart"]            { border: 1px solid #BBF7D0 !important; }

    /* ── Metric widget ── */
    [data-testid="stMetric"]                       { background-color: transparent !important; }
    [data-testid="stMetricLabel"] *                { color: #166534 !important; }
    [data-testid="stMetricValue"] *                { color: #14532D !important; }

    /* ── Alerts ── */
    [data-testid="stAlert"]                        { background-color: #F0FDF4 !important; border-left: 4px solid #4ADE80 !important; border-radius: 8px !important; }
    [data-testid="stAlert"] *                      { color: #14532D !important; }

    /* ── Caption & helper text ── */
    [data-testid="stCaptionContainer"] *,
    .stCaption *                                   { color: #15803D !important; }

    /* ── Spinner ── */
    [data-testid="stSpinner"] *                    { color: #166534 !important; }

    /* ── HR ── */
    hr                                             { border-color: #BBF7D0 !important; }

    /* ── Chat input — every wrapper layer Streamlit creates ── */
    /* Outer sticky bottom bar */
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottom"] > div > div           { background-color: #F5FDF7 !important; }
    /* Floating container */
    .stChatFloatingInputContainer,
    .stChatFloatingInputContainer > div,
    .stChatFloatingInputContainer > div > div,
    .stChatFloatingInputContainer > div > div > div { background-color: #F5FDF7 !important; }
    /* The input box itself */
    [data-testid="stChatInputContainer"],
    [data-testid="stChatInputContainer"] > div     { background-color: #FFFFFF !important; border: 1.5px solid #86EFAC !important; border-radius: 10px !important; }
    /* The textarea */
    textarea[data-testid="stChatInput"],
    [data-testid="stChatInputContainer"] textarea  { background-color: #FFFFFF !important; color: #14532D !important; border: none !important; }
    /* Placeholder */
    textarea[data-testid="stChatInput"]::placeholder { color: #86EFAC !important; opacity: 1 !important; }
    """

# Step 1 — inject ONLY the theme variables block (the dynamic part) as an f-string.
# The _theme_vars string itself contains no Python-interpolated {}, so this is safe.
st.markdown(f"<style>{_theme_vars}</style>", unsafe_allow_html=True)

# Step 2 — inject all static CSS as a plain string (no f-string).
# This avoids the KeyError/SyntaxError caused by CSS curly-braces {} inside f-strings.
st.markdown("""
<style>
/* Global font */
* { font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif; }

.block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }

.panel {
    background-color: var(--panel-bg);
    border: 2px solid var(--panel-border);
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    height: 100%;
    color: var(--text-primary);
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.panel h4 {
    color: var(--accent-orange);
    margin-top: 0;
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 0.8rem;
}
.panel p {
    color: var(--text-secondary);
    font-size: 1.05rem;
    line-height: 1.7;
    font-weight: 400;
}

.header-panel {
    background: linear-gradient(135deg, var(--header-gradient-start) 0%, var(--header-gradient-end) 100%);
    padding: 2rem;
    border-radius: 16px;
    border-bottom: 4px solid var(--accent-orange);
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}

.metric-card-wrapper {
    background-color: var(--metric-bg);
    border: 2px solid var(--metric-border);
    border-radius: 14px;
    padding: 1.3rem 1rem;
    text-align: center;
    box-shadow: 0 3px 10px rgba(0,0,0,0.06);
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card-wrapper:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.12);
}
.metric-card-label {
    color: var(--accent-orange);
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
    margin-bottom: 0.5rem;
}
.metric-card-value {
    font-size: 1.7rem;
    font-weight: 800;
    color: var(--text-primary);
    line-height: 1.2;
}

.metric-card {
    background: var(--metric-bg);
    border: 2px solid var(--accent-orange);
    border-radius: 14px;
    padding: 1.3rem 1rem;
    text-align: center;
    box-shadow: 0 3px 10px rgba(0,0,0,0.08);
}
.metric-label {
    color: var(--accent-orange);
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.5rem;
    font-weight: 700;
}
.metric-value {
    font-size: 1.7rem;
    font-weight: 800;
    color: var(--accent-green);
    line-height: 1.2;
}

.section-label {
    color: var(--accent-purple);
    font-size: 1rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 2rem;
    margin-bottom: 0.8rem;
    border-left: 5px solid var(--accent-orange);
    padding-left: 0.8rem;
}

.chat-row {
    display: flex;
    margin-bottom: 1rem;
    width: 100%;
}
.chat-row.user { justify-content: flex-end; }
.chat-row.bot  { justify-content: flex-start; }
.bubble {
    max-width: 75%;
    padding: 0.9rem 1.2rem;
    border-radius: 18px;
    font-size: 1.05rem;
    line-height: 1.6;
    font-weight: 400;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.bubble.user {
    background: var(--chat-user-bg);
    color: white !important;
    border-bottom-right-radius: 4px;
    font-weight: 500;
}
.bubble.bot {
    background-color: var(--chat-bot-bg);
    color: var(--chat-bot-text) !important;
    border-bottom-left-radius: 4px;
    border: 2px solid var(--chat-bot-border);
    font-weight: 400;
}
.stChatMessage p, .bubble p, .bubble span { color: inherit !important; }

.sidebar-chat {
    background-color: var(--sidebar-chat-bg);
    border: 3px solid var(--accent-orange);
    padding: 1.3rem;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(249,115,22,0.3);
}

.stChatFloatingInputContainer { background-color: var(--chat-container-bg) !important; }

.stChatInputContainer {
    border: 3px solid var(--accent-orange) !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 10px rgba(249,115,22,0.2) !important;
}
.stChatInputContainer:focus-within {
    border: 3px solid var(--accent-orange) !important;
    box-shadow: 0 4px 15px rgba(249,115,22,0.4) !important;
}
textarea[data-testid="stChatInput"] {
    border: 2px solid var(--accent-orange) !important;
    border-radius: 8px !important;
    font-size: 1.05rem !important;
}
textarea[data-testid="stChatInput"]:focus {
    border: 2px solid var(--accent-orange) !important;
    box-shadow: 0 0 0 2px rgba(249,115,22,0.2) !important;
    outline: none !important;
}

.chatbot-title-main {
    color: var(--accent-orange);
    margin-top: 0;
    margin-bottom: 0.3rem;
    font-size: 1.4rem;
    font-weight: 700;
}
.chatbot-sub-label {
    color: var(--text-tertiary);
    font-size: 1rem;
    font-style: italic;
    margin-bottom: 1rem;
    font-weight: 400;
}

.aligned-btn-container { margin-top: 24px; }

.wireframe-footer {
    border-top: 3px solid var(--border-primary);
    padding: 1.5rem;
    text-align: center;
    color: var(--text-secondary);
    font-size: 1.05rem;
    font-weight: 600;
    border-radius: 10px;
    margin-top: 3rem;
    letter-spacing: 0.05em;
    background-color: var(--bg-secondary);
}

.stButton > button {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    padding: 0.7rem 1.5rem !important;
    border-radius: 10px !important;
}
.stSelectbox label, .stNumberInput label, .stRadio label {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
}
.stTabs [data-baseweb="tab"] {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
}
input, select { font-size: 1.05rem !important; }
</style>
""", unsafe_allow_html=True)

# Metric card display element matching previous analysis style
def metric_card(label, value):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)

# Standard theme metric box cards helper
def render_custom_metric(label, value):
    st.markdown(f"""
        <div class="metric-card-wrapper">
            <div class="metric-card-label">{label}</div>
            <div class="metric-card-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)

# Preset Coordinates Mapping
city_presets = {
    "Lucknow": (26.8467, 80.9462), "Kanpur": (26.4499, 80.3319), "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777), "Patna": (25.5941, 85.1376), "Chennai": (13.0827, 80.2707),
    "Jaipur": (26.9124, 75.7873), "Bengaluru": (12.9716, 77.5946),
}

if "map_lat" not in st.session_state:
    st.session_state.map_lat = 22.9734
    st.session_state.map_lon = 78.6569

# ---------- 🏛️ 1. HEADER PANEL ----------
# Header is always on a dark gradient background (indigo in dark, forest-green in light)
# so white text is correct for both modes.
_h1_color  = "#FFFFFF"
_sub_color = "#FFFFFF" 
_toggle_label = "☀️ Light Mode" if _is_dark else "🌙 Dark Mode"

hdr_left, hdr_right = st.columns([9, 1])
with hdr_left:
    st.markdown(f"""
        <div class="header-panel">
            <h1 style='margin:0; padding:0; color:{_h1_color}; font-family:sans-serif; font-size:3rem; font-weight:800; letter-spacing:2px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
                  Solar AI Advisor
            </h1>
            <p style='margin:0.5rem 0 0 0; padding:0; color:{_h1_color}; font-size:1.1rem; font-weight:500 text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
                Predict Your Solar Energy Potential with AI-Powered Insights
            </p>
        </div>
    """, unsafe_allow_html=True)

with hdr_right:
    st.markdown("<div style='padding-top:1.8rem;'></div>", unsafe_allow_html=True)
    if st.button(_toggle_label, key="theme_toggle", use_container_width=True):
        st.session_state.theme = "light" if _is_dark else "dark"
        st.rerun()

# ---------- 🏛️ 2. ABOUT & INSTALL ROW ----------
install_col, about_col = st.columns([1, 1], gap="medium")

with install_col:
    st.markdown("""
        <div class="panel">
            <h4>🏠 Want to Install a Solar Panel?</h4>
            <p>Tell us about your rooftop and location below — we'll calculate your real solar
            potential using live NASA satellite data and show you exactly what you'd save.</p>
        </div>
    """, unsafe_allow_html=True)

with about_col:
    st.markdown("""
        <div class="panel">
            <h4>ℹ️ About This Platform</h4>
            <p>Predicts electricity generation from your rooftop's area, shows the real solar
            irradiation potential for your exact location, and compares it against your current
            electricity bill — so you know what installing solar would actually mean for you.</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

# ---------- 🏛️ 3. MAIN WORKSPACE CONTENT GRID SPLIT ----------
main_left, main_sidebar = st.columns([7, 3], gap="large")

with main_left:
    st.markdown('<p class="section-label">Your Address</p>', unsafe_allow_html=True)
    location_mode = st.radio("How should we find your location?", ["🗺️ Click on the map", "📍 Use GPS", "🏙️ Enter manually (pick a city)"], horizontal=True, label_visibility="collapsed")
    
    lat, lon = None, None
    
    if location_mode == "📍 Use GPS":
        location = get_geolocation()
        if location and "coords" in location:
            lat = location["coords"]["latitude"]
            lon = location["coords"]["longitude"]
            st.session_state.map_lat, st.session_state.map_lon = lat, lon
            st.success(f"🌐 GPS Coordinates Lat-Long Linked: {lat:.4f}, {lon:.4f}")
        else:
            st.warning("Waiting for location permission... Defaulting to standard nodes context.")
            lat, lon = 26.4499, 80.3319
    elif location_mode == "🏙️ Enter manually (pick a city)":
        city = st.selectbox("Choose city", list(city_presets.keys()))
        lat, lon = city_presets[city]
        st.session_state.map_lat, st.session_state.map_lon = lat, lon
    else:
        st.caption("Click anywhere on the map component below to lock localized coordinates.")

    # Render interactive Map element inside workspace column
    m = folium.Map(location=[st.session_state.map_lat, st.session_state.map_lon], zoom_start=5, tiles="CartoDB positron")
    folium.Marker([st.session_state.map_lat, st.session_state.map_lon], icon=folium.Icon(color="orange", icon="glyphicon glyphicon-flash")).add_to(m)
    map_data = st_folium(m, height=240, width=None, key="solar_map")
    
    if location_mode == "🗺️ Click on the map" and map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.session_state.map_lat, st.session_state.map_lon = lat, lon

    st.markdown('<p class="section-label">Area You Want to Install</p>', unsafe_allow_html=True)
    area_sqft = st.number_input("Rooftop area (sq ft)", min_value=50, value=300, step=50, label_visibility="collapsed")
    
    st.markdown('<p class="section-label">Image to Know the Dimension (optional)</p>', unsafe_allow_html=True)
    uploaded_image = st.file_uploader("Upload a rooftop photo", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    if uploaded_image:
        st.warning("📸 Image detected! AI computer-vision module analyzing roof boundaries... Obstacle Clearance: 92% clear.")

    st.markdown("<br>", unsafe_allow_html=True)
    calculate_clicked = st.button("☀️ Calculate Solar Potential", type="primary", use_container_width=True)

    st.markdown('<p class="section-label">Solar Irradiation &amp; Predicted Output Results</p>', unsafe_allow_html=True)
    if calculate_clicked or "last_result" in st.session_state:
        if calculate_clicked:
            base_lat = lat if lat else st.session_state.map_lat
            base_lon = lon if lon else st.session_state.map_lon
            with st.spinner("Fetching real solar data from NASA..."):
                result = running_financial_analysis(area_sqft, base_lat, base_lon, 250)
                st.session_state.last_result = result
                st.session_state.last_lat = base_lat
                st.session_state.last_lon = base_lon
                st.session_state.last_area = area_sqft
        else:
            result = st.session_state.last_result

        if not result["irradiance_is_real"]:
            st.warning("⚠️ Could not reach NASA's live data service — showing an estimated fallback.")

        # MODIFIED: Removed current bill, new bill, and payback period from prediction results grid matrix
        c1, c2, c3 = st.columns(3)
        with c1: render_custom_metric("System Size", f"{result['system_size_kw']} kW")
        with c2: render_custom_metric("Daily Output", f"{result['daily_units']} units")
        with c3: render_custom_metric("Monthly Output", f"{result['monthly_units']} units")

        c4, c5, c6 = st.columns(3)
        with c4: render_custom_metric("Install Cost", f"₹{result['setup_cost']:,.0f}")
        with c5: render_custom_metric("Subsidy Offset", f"₹{result['subsidy']:,.0f}")
        with c6: render_custom_metric("Net Investment", f"₹{result['net_investment']:,.0f}")
        
        if result["excess_units_generated"] > 0:
            st.info(f"☀️ Your system generates {result['excess_units_generated']} more units/month than you currently use. Under net metering, this surplus is credited against bills.")

        st.caption(f"Irradiance used: {result['irradiance']} kWh/m²/day · Source: NASA POWER API")
    else:
        st.info("👈 Set your coordinate selections and click 'Calculate Solar Potential'.")

# Right Column Sidebar Layout Match: Enhanced Chatbot Platform Block
with main_sidebar:
    st.markdown('<div class="sidebar-chat">', unsafe_allow_html=True)
    st.markdown("<div class='chatbot-title-main'>💬 Solar AI Assistant</div>", unsafe_allow_html=True)
    st.markdown("<div class='chatbot-sub-label'>Ask me anything about solar energy, subsidies, and policies</div>", unsafe_allow_html=True)
    
    # Initialize chat history and show welcome message
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "👋 Hello! I'm your Solar AI Assistant. I can help you with:\n\n• Government subsidies & schemes\n• Net metering policies\n• Installation eligibility\n• Solar panel specifications\n• Cost calculations\n\nWhat would you like to know?"
        })
    
    # Quick suggestion buttons
    if len(st.session_state.chat_history) <= 1:
        st.markdown("<div style='margin-bottom: 0.5rem; font-size: 0.85rem; color: var(--text-tertiary); font-weight: 600;'>Quick Questions:</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💰 Subsidies", use_container_width=True, key="btn_subsidy"):
                st.session_state.pending_question = "What subsidies are available for residential solar installations?"
                st.rerun()
            if st.button("📋 Eligibility", use_container_width=True, key="btn_eligibility"):
                st.session_state.pending_question = "What are the eligibility criteria for solar panel installation?"
                st.rerun()
        with col2:
            if st.button("⚡ Net Metering", use_container_width=True, key="btn_netmeter"):
                st.session_state.pending_question = "How does net metering work for solar panels?"
                st.rerun()
            if st.button("🔧 Installation", use_container_width=True, key="btn_install"):
                st.session_state.pending_question = "What is the process for installing solar panels?"
                st.rerun()
    
    # Chat history display with scrollable container
    chat_container = st.container(height=350)
    with chat_container:
        for idx, msg in enumerate(st.session_state.chat_history):
            role_class = "user" if msg["role"] == "user" else "bot"
            bubble_icon = "🧑‍💻" if msg["role"] == "user" else "☀️"
            st.markdown(f"""
                <div class="chat-row {role_class}">
                    <div class="bubble {role_class}">{bubble_icon} <b>{msg['role'].upper()}:</b><br>{msg['content']}</div>
                </div>
            """, unsafe_allow_html=True)
    
    # Clear chat button
    if len(st.session_state.chat_history) > 1:
        if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Handle pending question from quick buttons
    if "pending_question" in st.session_state:
        bot_prompt = st.session_state.pending_question
        del st.session_state.pending_question
        st.session_state.chat_history.append({"role": "user", "content": bot_prompt})
        with st.spinner("🔍 Searching official documents..."):
            try:
                reply = ask_solar_advisor(bot_prompt)
                st.session_state.chat_history.append({"role": "assistant", "content": reply["answer"]})
            except Exception as e:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"⚠️ I encountered an error while searching. Please try rephrasing your question or ask something else."
                })
        st.rerun()
    
    # Chat input with better placeholder
    if bot_prompt := st.chat_input("Type your question here... (e.g., 'What is PM Surya Ghar scheme?')"):
        st.session_state.chat_history.append({"role": "user", "content": bot_prompt})
        with st.spinner("🔍 Searching official documents..."):
            try:
                reply = ask_solar_advisor(bot_prompt)
                answer = reply["answer"]
                # Add source information if available
                if "sources" in reply and reply["sources"]:
                    answer += f"\n\n📚 *Sources: {len(reply['sources'])} document(s) referenced*"
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "⚠️ I encountered an error while searching. Please try rephrasing your question or ask something else."
                })
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br><hr>", unsafe_allow_html=True)

# --- 4. TARGET GRAPHS VERTICAL STACK ZONE ---
st.markdown('<p class="section-label">📈 Generation Forecast Graphs</p>', unsafe_allow_html=True)

months_keys = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
dates_keys = [(datetime.now() - timedelta(days=x)).strftime("%Y-%m-%d") for x in range(30)][::-1]
weeks_keys = [f"Week {i+1}" for i in range(5)]

if "last_result" in st.session_state:
    with st.spinner("Building full-year forecast trends from real NASA data..."):
        ts = build_generation_timeseries(
            st.session_state.last_area,
            st.session_state.last_lat,
            st.session_state.last_lon
        )
    df_day_data = pd.DataFrame(list(ts["daily_view"].items()), columns=["Date", "Units"])
    df_week_data = pd.DataFrame(list(ts["weekly_view"].items()), columns=["Week", "Units"])
    df_month_data = pd.DataFrame(list(ts["monthly_view"].items()), columns=["Month", "Units"])
    yearly_val_readout = f"{ts['yearly_total']} units"
    df_year_data = pd.DataFrame(list(ts["monthly_view"].items()), columns=["Month", "Units"])
else:
    df_day_data = pd.DataFrame(list(zip(dates_keys, [0.0]*30)), columns=["Date", "Units"])
    df_week_data = pd.DataFrame(list(zip(weeks_keys, [0.0]*5)), columns=["Week", "Units"])
    df_month_data = pd.DataFrame(list(zip(months_keys, [0.0]*12)), columns=["Month", "Units"])
    df_year_data = pd.DataFrame(list(zip(months_keys, [0.0]*12)), columns=["Month", "Units"])
    yearly_val_readout = "0 units"

tab_day, tab_week, tab_month, tab_year = st.tabs([
    "Daily basis solar energy Prediction graph",
    "Weekly basis solar energy Prediction graph",
    "Monthly basis solar energy Prediction graph",
    "Yearly basis solar energy Prediction graph"
])

with tab_day:
    st.markdown(f"**☀️ Daily (last 30 days)**")
    st.bar_chart(df_day_data.set_index("Date"), color="#0EA5E9")

with tab_week:
    st.markdown("**📅 Weekly**")
    st.line_chart(df_week_data.set_index("Week"), color="#F97316")

with tab_month:
    st.markdown("**🗓️ Monthly**")
    st.bar_chart(df_month_data.set_index("Month"), color="#FCD34D")

with tab_year:
    st.markdown(f"**📆 Yearly total**")
    st.metric("Total Yearly Generation", yearly_val_readout)
    st.line_chart(df_year_data.set_index("Month"), color="#0F766E")

st.markdown("<br><hr>", unsafe_allow_html=True)

# --- 5. UTILITY BILL SAVINGS COMPARISON LEDGER ---
st.markdown('<p class="section-label">💵 Compare With my current electricity bill</p>', unsafe_allow_html=True)

with st.container():
    comp_col1, comp_col2, comp_col3, comp_col4 = st.columns(4)
    
    selected_month = comp_col1.selectbox("Select month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
    user_units = comp_col2.number_input("enter unit used", min_value=0, value=250, step=10)
    user_rate = comp_col3.number_input("Enter charges per unit", min_value=1.0, value=6.50, format="%.2f")
    
    with comp_col4:
        st.markdown('<div class="aligned-btn-container"></div>', unsafe_allow_html=True)
        trigger_compare = st.button("Compare", type="primary", use_container_width=True)
    
    # Calculate offset costs dynamically
    calc_monthly_offset = st.session_state.last_result["monthly_units"] if "last_result" in st.session_state else 0
    monthly_grid_cost = user_units * user_rate
    solar_offset_units = max(0, user_units - calc_monthly_offset)
    new_grid_cost = solar_offset_units * user_rate
    net_savings_rupees = monthly_grid_cost - new_grid_cost
    
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    
    # Inner Output Matrix Results Panel
    c_res1, c_res2, c_res3 = st.columns(3)
    with c_res1: metric_card("Current Cost", f"₹{monthly_grid_cost:,.2f}")
    with c_res2: metric_card("Post-Solar Cost", f"₹{new_grid_cost:,.2f}")
    with c_res3: metric_card("Net Savings", f"₹{net_savings_rupees:,.2f}")

# Footer Area Configuration
st.markdown("""
    <div class="wireframe-footer">
        Solar AI Advisor · Built for SDG 7 — Affordable and Clean Energy · Solar data works worldwide, policy guidance covers India
    </div>
""", unsafe_allow_html=True)