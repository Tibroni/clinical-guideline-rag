import streamlit as st

HIDE_PAGES_NAV_CSS = """
<style>
    [data-testid="stSidebarNav"] { display: none !important; }
</style>
"""

HIDE_LANDING_SIDEBAR_CSS = """
<style>
    section[data-testid="stSidebar"] { display: none !important; }
    section[data-testid="stSidebarCollapsedControl"] { display: none !important; }
    [data-testid="stMain"] > div { padding-left: 1rem !important; padding-right: 1rem !important; }
</style>
"""

HIDE_STREAMLIT_TOOLBAR_CSS = """
<style>
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    header[data-testid="stHeader"] { visibility: hidden !important; height: 0 !important; }
    .stApp > header + div[data-testid="stAppViewContainer"] {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    .block-container { padding-top: 2rem !important; }
</style>
"""

LANDING_DETAIL_CSS = """
<style>
    .landing-detail-grid {
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        gap: 1rem !important;
        align-items: stretch !important;
        width: 100% !important;
        margin-bottom: 20px !important;
    }
    .landing-detail-col {
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
    }
    .landing-detail-heading {
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: var(--white) !important;
        line-height: 1.3 !important;
    }
    .landing-detail-card {
        flex: 1 1 auto !important;
        display: flex !important;
        flex-direction: column !important;
        margin-bottom: 0 !important;
        box-sizing: border-box !important;
    }
    .landing-detail-card .tech-table {
        flex: 1 1 auto !important;
        height: 100% !important;
    }
    .landing-detail-card .tech-table tr {
        height: calc(100% / 6) !important;
    }
    .landing-detail-card .workflow-table tr {
        height: calc(100% / 5) !important;
    }
    .landing-detail-card .tech-table td {
        vertical-align: top !important;
    }
    .landing-detail-card .tech-table.workflow-table td.workflow-key,
    .landing-detail-card .tech-table.workflow-table .workflow-key-label {
        font-family: var(--font-mono) !important;
        font-size: 0.7rem !important;
        font-weight: 700 !important;
        color: #F44174 !important;
        letter-spacing: 0.08em !important;
    }
    .landing-detail-card .tech-table.workflow-table td.workflow-key {
        width: 35% !important;
    }
    .tech-table.workflow-table code {
        color: #F44174 !important;
        background-color: rgba(244, 65, 116, 0.12) !important;
        border: 1px solid rgba(244, 65, 116, 0.25) !important;
        border-radius: 4px !important;
        padding: 0.1em 0.35em !important;
    }
    @media (max-width: 768px) {
        .landing-detail-grid {
            grid-template-columns: 1fr !important;
        }
    }
</style>
"""

def inject_styles(*, hide_sidebar: bool = False):
    st.markdown("""
<!-- Film Grain Overlay -->
<svg class="grain-overlay" aria-hidden="true" style="position: fixed; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 9999; opacity: 0.03; mix-blend-mode: overlay;">
  <filter id="site-noise">
    <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="4" stitchTiles="stitch" />
  </filter>
  <rect width="100%" height="100%" filter="url(#site-noise)" />
</svg>

<style>
    @import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@100..900&display=swap');
    
    :root {
      /* Core Colors */
      --neutral-primary: #050505;
      --neutral-primary-soft: #0A0A0A;
      --neutral-primary-medium: #111111;
      --neutral-primary-strong: #1A1A1A;
      
      --neutral-secondary-medium: #111111;
      --neutral-secondary-strong: #1A1A1A;
      --neutral-tertiary-soft: #0E0E0E;
      --neutral-tertiary-medium: #1A1A1A;
      
      --brand: #F44174;
      --brand-softer: #1A0810;
      --brand-soft: #3D0E1F;
      --brand-strong: #FF5A89;
      
      /* Status Colors */
      --success-soft: #061A14;
      --success: #00CC88;
      --success-medium: #0A2E22;
      --success-strong: #009966;
      
      --danger-soft: #1A0508;
      --danger: #FF3355;
      --danger-medium: #3D0A14;
      --danger-strong: #CC2244;
      
      --warning-soft: #1A0E04;
      --warning: #FF8833;
      --warning-medium: #331A08;
      --warning-strong: #DD5511;

      --disabled: #111111;

      /* Text Colors */
      --white: #FFFFFF;
      --black: #0A0A0A;
      --heading: #EDEDED;
      --body: #888888;
      --body-subtle: #666666;
      --fg-brand: #F44174;
      --fg-brand-strong: #FFB0C7;
      --fg-disabled: #444444;

      /* Borders */
      --border-default: #1A1A1A;
      --border-default-medium: #222222;
      --border-default-strong: #333333;
      --border-brand: #F44174;
      --border-brand-subtle: #3D0E1F;
      --border-success: #065F46;
      --border-success-subtle: #0A2E22;
      --border-danger: #CC2244;
      --border-danger-subtle: #3D0A14;
      --border-warning: #FF8833;
      --border-warning-subtle: #331A08;

      /* Semantic aliases to map to the new tokens */
      --bg-color: var(--neutral-primary);
      --card-bg: var(--neutral-primary-soft);
      --card-bg-hover: var(--neutral-secondary-medium);
      --border-color: var(--border-default);
      --border-glow: rgba(244, 65, 116, 0.4);
      --text-primary: var(--white);
      --text-secondary: var(--body);
      --text-muted: var(--body-subtle);
      --primary-accent: var(--brand);
      --primary-accent-hover: var(--brand-strong);
      --accent-dim: var(--brand-softer);
      --transition-smooth: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      --font-sans: 'Geist Mono', ui-monospace, monospace;
      --font-mono: 'Geist Mono', ui-monospace, monospace;
    }
    
    /* Main Layout */
    .stApp {
        background-color: var(--neutral-primary) !important;
        background-image: radial-gradient(circle at 50% 0%, rgba(244, 65, 116, 0.08) 0%, transparent 60%) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-sans) !important;
    }
    
    .block-container {
        max-width: 1100px !important;
        padding-top: 4rem !important;
        padding-bottom: 6rem !important;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-sans) !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        color: var(--heading) !important;
        margin-top: 0 !important;
    }
    
    p, li, label {
        font-family: var(--font-sans) !important;
        font-weight: 400 !important;
        color: var(--body) !important;
    }
    
    .app-eyebrow {
        font-family: var(--font-mono) !important;
        font-size: 0.65rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.2em !important;
        color: var(--text-muted) !important;
        margin-bottom: 0.5rem !important;
        display: block;
    }
    
    .main-title {
        font-family: var(--font-sans) !important;
        font-size: clamp(2rem, 5vw, 2.75rem) !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        color: var(--heading) !important;
        margin-bottom: 0.2rem !important;
    }
    
    .subtitle {
        color: var(--body) !important;
        font-size: 1.05rem !important;
        font-weight: 400 !important;
        margin-bottom: 2rem !important;
        max-width: 800px;
        line-height: 1.7 !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: var(--neutral-primary-soft) !important;
        border-right: 1px solid var(--border-color) !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: var(--heading) !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: var(--body) !important;
    }
    
    /* Cards */
    .glass-card {
        background: var(--neutral-primary-soft) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: 12px !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.12) !important; /* shadow-xs */
        transition: var(--transition-smooth) !important;
    }
    /* Interactive Card hover */
    .interactive-card:hover {
        background: var(--neutral-secondary-medium) !important;
        border-color: var(--border-default-strong) !important;
        cursor: pointer;
    }
    
    .glow-card {
        background: var(--neutral-primary-soft) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid var(--border-default) !important;
        border-top: 2px solid var(--brand) !important;
        border-radius: 12px !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.12), 0 0 15px rgba(244, 65, 116, 0.1) !important;
    }
    
    /* Form Buttons styling */
    div[data-testid="stButton"] button, button[kind="primary"]:not([data-baseweb="tab"]), button[kind="secondary"]:not([data-baseweb="tab"]) {
        border-radius: 9999px !important;
        font-family: var(--font-mono) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.12em !important;
        font-size: 0.7rem !important;
        font-weight: 500 !important;
        padding: 10px 24px !important;
        transition: var(--transition-smooth) !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.12) !important; /* shadow-xs */
    }
    /* Primary buttons (Outlined Brand Variant) */
    button[kind="primary"]:not([data-baseweb="tab"]), div[data-testid="stButton"] button[kind="primary"] {
        background-color: transparent !important;
        border: 1px solid var(--brand) !important;
        color: var(--brand) !important;
    }
    button[kind="primary"]:not([data-baseweb="tab"]):hover, div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: var(--brand-softer) !important;
        border-color: var(--brand-strong) !important;
    }
    button[kind="primary"]:not([data-baseweb="tab"]) *, div[data-testid="stButton"] button[kind="primary"] * {
        color: var(--brand) !important;
    }
    button[kind="primary"]:not([data-baseweb="tab"]):hover *, div[data-testid="stButton"] button[kind="primary"]:hover * {
        color: var(--brand-strong) !important;
    }
    /* Secondary buttons */
    button[kind="secondary"]:not([data-baseweb="tab"]), div[data-testid="stButton"] button[kind="secondary"] {
        background-color: var(--neutral-secondary-medium) !important;
        border: 1px solid var(--border-default-medium) !important;
        color: var(--body) !important;
    }
    button[kind="secondary"]:not([data-baseweb="tab"]):hover, div[data-testid="stButton"] button[kind="secondary"]:hover {
        background-color: var(--neutral-tertiary-medium) !important;
        border-color: var(--border-default-strong) !important;
        color: var(--heading) !important;
    }
    button[kind="secondary"]:not([data-baseweb="tab"]) *, div[data-testid="stButton"] button[kind="secondary"] * {
        color: var(--body) !important;
    }
    button[kind="secondary"]:not([data-baseweb="tab"]):hover *, div[data-testid="stButton"] button[kind="secondary"]:hover * {
        color: var(--heading) !important;
    }
    
    /* Streamlit Tabs */
    button[data-baseweb="tab"] {
        font-family: var(--font-mono) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.12em !important;
        font-weight: 600 !important;
        color: var(--body) !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 0px !important;
        border-bottom: 2px solid transparent !important;
        padding: 12px 18px !important;
        transition: var(--transition-smooth) !important;
    }
    button[data-baseweb="tab"]:hover {
        color: var(--heading) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--brand) !important;
        border-bottom: 2px solid var(--brand) !important;
    }
    div[data-baseweb="tab-list"] {
        border-bottom: 1px solid var(--border-default) !important;
        background-color: transparent !important;
    }
    
    /* Sidebar buttons overrides for compact sizing */
    section[data-testid="stSidebar"] button {
        padding: 6px 16px !important;
        font-size: 0.65rem !important;
    }
    
    /* Form inputs */
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea, div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: var(--neutral-secondary-medium) !important;
        border: 1px solid var(--border-default-medium) !important;
        border-radius: 12px !important; /* radius: 12px base */
        color: var(--heading) !important;
        font-family: var(--font-sans) !important;
        font-size: 0.95rem !important;
        transition: var(--transition-smooth) !important;
    }
    div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus, div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus {
        border-color: var(--brand) !important;
        box-shadow: 0 0 0 1px var(--brand) !important;
    }
    
    /* Toggles and Checkboxes */
    div[data-testid="stCheckbox"] [data-baseweb="checkbox"]:has(input[type="checkbox"]:checked) > div:first-of-type,
    div[data-testid="stCheckbox"] [data-baseweb="checkbox"]:has(input[type="checkbox"]:checked) > span:first-of-type {
        background-color: var(--brand) !important;
    }
    div[data-testid="stCheckbox"] [data-baseweb="checkbox"] input[type="checkbox"] + div,
    div[data-testid="stCheckbox"] [data-baseweb="checkbox"] input[type="checkbox"] + span,
    div[data-testid="stCheckbox"] [data-testid="stWidgetLabel"],
    div[data-testid="stCheckbox"] [data-testid="stWidgetLabel"] p {
        background-color: transparent !important;
        background: transparent !important;
    }
    div[data-testid="stCheckbox"] label {
        align-items: center !important;
    }
    div[data-testid="stCheckbox"] [data-testid="stWidgetLabel"] p {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Badges */
    .status-badge {
        font-family: var(--font-mono) !important;
        font-size: 0.6rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        padding: 4px 10px !important;
        border-radius: 8px !important; /* default radius is 8px */
        display: inline-block !important;
    }
    .status-success {
        background-color: var(--success-soft) !important;
        color: var(--fg-success-strong) !important;
        border: 1px solid var(--border-success-subtle) !important;
    }
    .status-warning {
        background-color: var(--warning-soft) !important;
        color: var(--fg-warning) !important;
        border: 1px solid var(--border-warning-subtle) !important;
    }
    .status-error {
        background-color: var(--danger-soft) !important;
        color: var(--fg-danger-strong) !important;
        border: 1px solid var(--border-danger-subtle) !important;
    }
    
    /* Citation Link */
    .citation-link {
      background: var(--brand-softer) !important;
      padding: 2px 8px !important;
      border-radius: 9999px !important;
      border: 1px solid var(--border-brand-subtle) !important;
      font-size: 0.75rem !important;
      font-weight: 600 !important;
      color: var(--fg-brand-strong) !important;
      text-decoration: none !important;
      font-family: var(--font-mono) !important;
      display: inline-block !important;
      margin: 2px 4px !important;
      transition: var(--transition-smooth) !important;
    }

    .citation-link:hover {
      color: var(--white) !important;
      background: var(--brand-soft) !important;
      border-color: var(--brand) !important;
    }
    
    /* Expanders */
    div[data-testid="stExpander"] {
        background: var(--neutral-primary-soft) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.12) !important;
        margin-bottom: 15px !important;
    }
    div[data-testid="stExpander"] summary {
        font-family: var(--font-sans) !important;
        font-weight: 600 !important;
        color: var(--heading) !important;
        padding: 14px 16px !important;
    }
    
    /* Tables styling */
    table {
        width: 100% !important;
        border-collapse: collapse !important;
        margin: 1rem 0 !important;
        font-family: var(--font-sans) !important;
        font-size: 0.9rem !important;
    }
    th {
        background-color: var(--neutral-primary-medium) !important;
        color: var(--white) !important;
        font-family: var(--font-mono) !important;
        text-transform: uppercase !important;
        font-size: 0.7rem !important;
        letter-spacing: 0.1em !important;
        padding: 12px 16px !important;
        border: 1px solid var(--border-default) !important;
        text-align: left !important;
    }
    td {
        padding: 12px 16px !important;
        border: 1px solid var(--border-default) !important;
        color: var(--body) !important;
        background-color: rgba(255, 255, 255, 0.02) !important;
    }
    tr:hover td {
        background-color: rgba(255, 255, 255, 0.04) !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.03); }
    ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.15); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--brand); }
    
    /* Widget Labels Override */
    div[data-testid="stWidgetLabel"] p {
        font-family: var(--font-mono) !important;
        font-size: 0.65rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.12em !important;
        color: var(--text-muted) !important;
        margin-bottom: 0.35rem !important;
    }
    
    /* File Uploader styling */
    div[data-testid="stFileUploader"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        box-shadow: none !important;
    }
    div[data-testid="stFileUploader"] section {
        background: var(--neutral-primary-soft) !important;
        border: 1px dashed var(--border-default) !important;
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.12) !important; /* shadow-xs */
        transition: var(--transition-smooth) !important;
    }
    div[data-testid="stFileUploader"] section:hover {
        border-color: var(--brand) !important;
        background: var(--neutral-secondary-medium) !important;
    }
    div[data-testid="stFileUploader"] button {
        background-color: transparent !important;
        border: 1px solid var(--border-default) !important;
        color: var(--white) !important;
        border-radius: 12px !important;
        font-family: var(--font-mono) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.12em !important;
        font-size: 0.65rem !important;
        font-weight: 500 !important;
        padding: 8px 16px !important;
        transition: var(--transition-smooth) !important;
    }
    div[data-testid="stFileUploader"] button:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-color: var(--brand) !important;
    }
    
    /* Dividers styling */
    hr {
        margin: 2rem 0 !important;
        border: none !important;
        border-top: 1px solid var(--border-default) !important;
        opacity: 0.8 !important;
    }
    
    /* Status Row for Sidebar */
    .status-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 14px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid var(--border-default);
        border-radius: 8px;
        margin-bottom: 10px;
        font-family: var(--font-sans);
        font-size: 0.85rem;
        transition: var(--transition-smooth);
    }
    .status-row:hover {
        background: rgba(255, 255, 255, 0.04);
        border-color: var(--border-default-strong);
    }
    .status-row strong {
        font-family: var(--font-mono);
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-secondary);
    }
    
    /* Alert cards override */
    div[data-testid="stAlert"] {
        background-color: var(--neutral-primary-soft) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: 12px !important;
        color: var(--white) !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.12) !important;
    }
    div[data-testid="stAlert"] [role="img"] {
        filter: grayscale(1) brightness(1.5) !important;
    }

    /* Technical Stack Table Override */
    .tech-table {
        width: 100% !important;
        border-collapse: collapse !important;
        margin: 0 !important;
    }
    .tech-table tr {
        border-bottom: 1px solid var(--border-default) !important;
    }
    .tech-table tr:last-child {
        border-bottom: none !important;
    }
    .tech-table td {
        padding: 12px 0 !important;
        border: none !important;
        background-color: transparent !important;
        font-size: 0.85rem !important;
        color: var(--body) !important;
    }
    .tech-table td.tech-key {
        font-family: var(--font-mono) !important;
        font-size: 0.7rem !important;
        font-weight: 700 !important;
        color: var(--brand) !important;
        letter-spacing: 0.08em !important;
        width: 35% !important;
    }
    .landing-detail-card .tech-table.workflow-table td.workflow-key,
    .landing-detail-card .tech-table.workflow-table .workflow-key-label {
        font-family: var(--font-mono) !important;
        font-size: 0.7rem !important;
        font-weight: 700 !important;
        color: #F44174 !important;
        letter-spacing: 0.08em !important;
    }
    .landing-detail-card .tech-table.workflow-table td.workflow-key {
        width: 35% !important;
    }
    .tech-table.workflow-table code {
        color: #F44174 !important;
        background-color: rgba(244, 65, 116, 0.12) !important;
        border: 1px solid rgba(244, 65, 116, 0.25) !important;
        border-radius: 4px !important;
        padding: 0.1em 0.35em !important;
    }
    .tech-table tr:hover td {
        background-color: transparent !important;
    }
</style>
""", unsafe_allow_html=True)
    st.markdown(HIDE_PAGES_NAV_CSS, unsafe_allow_html=True)
    st.markdown(HIDE_STREAMLIT_TOOLBAR_CSS, unsafe_allow_html=True)
    if hide_sidebar:
        st.markdown(HIDE_LANDING_SIDEBAR_CSS, unsafe_allow_html=True)
        st.markdown(LANDING_DETAIL_CSS, unsafe_allow_html=True)
