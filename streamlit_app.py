import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import calendar

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Midwest Budget PRO", page_icon="🏈", layout="wide", initial_sidebar_state="auto")

# --- STYLIZACJA: CHICAGO/DES MOINES + RWD + ZABÓJCA BIAŁEGO PASKA ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Roboto:wght@400;700;900&family=Oswald:wght@500;700&display=swap');

    /* =========================================================
       ZABÓJCA BIAŁEGO PASKA (100% Przezroczystości Headera)
       ========================================================= */
    [data-testid="stHeader"], header, .stAppHeader {
        background-color: transparent !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    
    /* Ukrycie prawego menu (Deploy, 3 kropki), zostaje tylko Hamburger Menu po lewej */
    [data-testid="stToolbar"] {
        display: none !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    .block-container {
        padding-top: 2rem !important; /* Mniejsze światło na górze */
    }

    /* =========================================================
       TŁO GŁÓWNE Z GITHUBA
       ========================================================= */
    .stApp {
        background-image: url('https://raw.githubusercontent.com/natpio/naszbudzet3/refs/heads/main/1776619317829.jpg');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family: 'Roboto', sans-serif;
    }
    
    .stApp::before {
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(26, 37, 44, 0.88); z-index: -1;
    }

    [data-testid="block-container"] {
        background-color: rgba(248, 250, 252, 0.95); 
        padding: 30px; border-radius: 8px; border: 8px solid #0f172a;
        box-shadow: 15px 15px 0px rgba(0,0,0,0.6);
        margin-bottom: 2rem;
    }

    h1, h2 { font-family: 'Bebas Neue', cursive !important; color: #c8102e !important; text-transform: uppercase; letter-spacing: 2px; }
    h3 { font-family: 'Oswald', sans-serif !important; color: #002244 !important; text-transform: uppercase; }

    /* =========================================================
       PASEK BOCZNY - PIŁKI
       ========================================================= */
    [data-testid="stSidebar"] {
        background-color: #002244; border-right: 8px solid #c83803;
        background-image: 
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 100 100'%3E%3Cellipse cx='50' cy='50' rx='35' ry='20' fill='%23c83803'/%3E%3Cpath d='M30,50 h40 M50,35 v30 M42,40 v20 M58,40 v20' stroke='%23f8fafc' stroke-width='2' fill='none'/%3E%3C/svg%3E"),
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='20' fill='%23f8fafc'/%3E%3Cpath d='M35,38 A22,22 0 0,0 65,62 M65,38 A22,22 0 0,1 35,62' stroke='%23c8102e' stroke-width='1.5' fill='none'/%3E%3C/svg%3E");
        background-size: 60px 60px, 50px 50px; background-position: 0 0, 30px 30px; background-repeat: repeat, repeat;
    }
    [data-testid="stSidebar"]::before {
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(0, 34, 68, 0.85); z-index: 0;
    }
    [data-testid="stSidebarNav"], [data-testid="stSidebar"] div, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { z-index: 1; position: relative; }
    [data-testid="stSidebarNav"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: #f8fafc !important; font-family: 'Oswald', sans-serif !important; font-weight: bold; }

    /* =========================================================
       HERO CARDS (Główne Liczniki)
       ========================================================= */
    .hero-card {
        background-color: #006b3d; border: 4px solid #ffffff; border-radius: 12px; padding: 25px; 
        box-shadow: 0 10px 20px rgba(0,0,0,0.4); text-align: center; color: white; margin-bottom: 20px;
    }
    
    .hero-card.interstate {
        background-color: #003882; border: 4px solid #ffffff; border-top: 15px solid #c8102e; 
        border-radius: 12px; padding: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.6); text-align: center; color: white; margin-bottom: 20px;
    }
    
    .hero-card.danger { background-color: #c8102e; border: 4px solid #ffffff; border-radius: 12px; padding: 25px; text-align: center; color: white; margin-bottom: 20px; }

    .hero-card h2, .hero-card.interstate h2, .hero-card.danger h2 { color: #ffffff !important; font-size: 3.5rem !important; margin: 5px 0; text-shadow: none; font-family: 'Bebas Neue', cursive !important; }
    .hero-card p, .hero-card.interstate p, .hero-card.danger p { font-weight: 900; font-size: 1.2rem; text-transform: uppercase; margin: 0; font-family: 'Roboto', sans-serif !important; }

    /* =========================================================
       METRYKI (Wpływy, Koszty, Odkłożono)
       ========================================================= */
    [data-testid="stMetric"] { 
        background-color: rgba(17, 34, 68, 0.95) !important; border: 3px solid #c83803 !important; 
        border-radius: 12px !important; padding: 15px !important; text-align: center !important; box-shadow: 0 8px 15px rgba(0,0,0,0.8) !important; 
    }
    [data-testid="stMetricValue"] div { font-family: 'Bebas Neue', cursive !important; color: #ffb612 !important; font-size: 2.5rem !important; text-shadow: 2px 2px 4px black !important; }
    [data-testid="stMetricLabel"] p { color: #ffffff !important; font-weight: 700 !important; text-transform: uppercase !important; font-family: 'Roboto', sans-serif !important; }

    /* Przycisk */
    .stButton>button {
        background-color: #002244; color: #ffffff !important; border: 3px solid #c83803; border-radius: 4px;
        font-weight: 900; font-family: 'Oswald', sans-serif; text-transform: uppercase; width: 100%;
    }

    .ticker-tape { background-color: #111; color: #ffb612; font-family: 'Roboto', monospace; font-weight: bold; padding: 10px; border: 4px solid #333; font-size: 1.2rem; margin-bottom: 30px; text-transform: uppercase; }

    /* --- MOBILE RWD --- */
    @media (max-width: 768px) {
        [data-testid="block-container"] { padding: 15px !important; border-width: 4px !important; margin-top: 0 !important; }
        .hero-card h2, .hero-card.interstate h2 { font-size: 2.2rem !important; }
        h1 { font-size: 2rem !important; }
        .stButton>button { font-size: 1rem !important; height: 3.5rem !important; }
        .ticker-tape { font-size: 0.9rem !important; padding: 5px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z BAZĄ ---
@st.cache_resource
def init_connection():
    try:
        creds = st.secrets["connections"]["gsheets"]
        fixed_key = creds["private_key"].replace("\\n", "\n").strip()
        credentials = Credentials.from_service_account_info(
            {
                "type": "service_account",
                "project_id": creds["project_id"],
                "private_key": fixed_key,
                "client_email": creds["client_email"],
                "token_uri": creds["token_uri"],
            },
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(credentials).open_by_url(creds["spreadsheet"])
    except Exception as e:
        st.error(f"Foul! Błąd silnika: {e}")
        return None

sh = init_connection()

def load_df(sheet_name):
    try:
        df = pd.DataFrame(sh.worksheet(sheet_name).get_all_records())
        if not df.empty and 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        return df
    except: return pd.DataFrame()

def save_df(sheet_name, df):
    sheet = sh.worksheet(sheet_name)
    sheet.clear()
    df_save = df.copy()
    if 'Data' in df_save.columns:
        df_save['Data'] = df_save['Data'].dt.strftime('%Y-%m-%d %H:%M:%S')
    sheet.update([df_save.columns.values.tolist()] + df_save.fillna("").values.tolist())
    st.toast(f"🏈 Touchdown! Wynik zapisany: {sheet_name}!", icon="🎯")

# --- NAWIGACJA (PLAYBOOK) ---
st.sidebar.markdown("<h1 style='color:white !important; font-size: 2.5rem;'>📋 PLAYBOOK</h1>", unsafe_allow_html=True)
miesiące = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
wybrany_m_nazwa = st.sidebar.selectbox("Miesiąc:", miesiące, index=datetime.now().month - 1)
wybrany_rok = st.sidebar.selectbox("Sezon:", [2024, 2025, 2026], index=2)
m_idx = miesiące.index(wybrany_m_nazwa) + 1
selected_date = date(wybrany_rok, m_idx, 1)

menu = st.sidebar.radio("Taktyka:", ["🏙️ L-Train (Kokpit)", "🛒 Zakupy (Codzienne)", "🏢 Stałe (Zobowiązania)", "📥 Wpływy", "🌽 Sejf"])

# --- WIDOKI ---
if menu == "🏙️ L-Train (Kokpit)":
    st.markdown("<h1 style='text-align:center;'>WINDY CITY SCOREBOARD</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='ticker-tape'><marquee scrollamount='8'>❄️ OSTRZEŻENIE: Zbliża się zamieć z nad Jeziora Michigan! ❄️ Twój bilans finansowy na sezon {wybrany_m_nazwa.upper()} {wybrany_rok} ❄️</marquee></div>", unsafe_allow_html=True)
    
    prz = load_df("Przychody")
    wyd_c = load_df("Wydatki")
    zob = load_df("Zobowiazania")
    osz = load_df("Oszczednosci")
    
    m_str = selected_date.strftime("%Y-%m")
    prz_m = prz[prz['Data'].dt.strftime("%Y-%m") == m_str] if not prz.empty else pd.DataFrame()
    wyd_m = wyd_c[wyd_c['Data'].dt.strftime("%Y-%m") == m_str] if not wyd_c.empty else pd.DataFrame()
    osz_m = osz[osz['Data'].dt.strftime("%Y-%m") == m_str] if not osz.empty else pd.DataFrame()
    
    s_prz = prz_m['Kwota'].sum() if not prz_m.empty else 0
    s_codzienne = wyd_m['Kwota'].sum() if not wyd_m.empty else 0
    s_zobowiazania = zob['Kwota'].sum() if not zob.empty else 0
    
    w_osz = osz_m[osz_m['Akcja'] == 'Wpłata']['Kwota'].sum() if (not osz_m.empty and 'Akcja' in osz_m.columns) else 0
    
    wolne = s_prz - s_codzienne - s_zobowiazania - w_osz
    
    ostatni_dzien = calendar.monthrange(wybrany_rok, m_idx)[1]
    dzis = date.today()
    if dzis.month == m_idx and dzis.year == wybrany_rok: pozostalo_dni = ostatni_dzien - dzis.day + 1
    elif selected_date < dzis: pozostalo_dni = 0
    else: pozostalo_dni = ostatni_dzien
        
    dniowka = wolne / pozostalo_dni if pozostalo_dni > 0 and wolne > 0 else 0

    c_h1, c_h2 = st.columns(2)
    with c_h1:
        st.markdown(f"<div class='hero-card'><p>I-80 FUNDS (W PORTFELU)</p><h2>{wolne:,.2f} zł</h2></div>", unsafe_allow_html=True)
    with c_h2:
        klasa = "hero-card danger" if dniowka < 50 else "hero-card interstate"
        st.markdown(f"<div class='{klasa}'><p>LIMIT NA DZIEŃ ({pozostalo_dni} DNI)</p><h2>{dniowka:,.2f} zł</h2></div>", unsafe_allow_html=True)

    st.write("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Wpływy", f"{s_prz:,.2f} zł")
    col2.metric("Stałe koszty", f"{s_zobowiazania:,.2f} zł")
    col3.metric("Odkłożono", f"{w_osz:,.2f} zł")

elif menu == "🛒 Zakupy (Codzienne)":
    st.markdown("<h1>🛒 Daily Scrimmage</h1>", unsafe_allow_html=True)
    st.info("Data i godzina wskoczą same. Wpisz tylko ile wydałeś.")
    with st.form("quick", clear_on_submit=True):
        c1, c2 = st.columns([2,1])
        n = c1.text_input("Co kupione?")
        k = c2.number_input("Kwota (zł)", min_value=0.0, step=1.0)
        if st.form_submit_button("🏈 ZAPISZ WYDATEK"):
            if k > 0 and n:
                teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sh.worksheet("Wydatki").append_row([teraz, n, "Codzienne", k])
                st.rerun()

    df_w = load_df("Wydatki")
    if not df_w.empty:
        ed_w = st.data_editor(df_w.sort_values("Data", ascending=False), hide_index=True, use_container_width=True)
        if st.button("💾 Zapisz zmiany"): save_df("Wydatki", ed_w)

elif menu == "🏢 Stałe (Zobowiązania)":
    st.markdown("<h1>🏢 Willis Tower Contracts</h1>", unsafe_allow_html=True)
    st.write("Subskrypcje, Raty, Czynsz. Wszystko co stałe.")
    df_z = load_df("Zobowiazania")
    with st.expander("➕ Dodaj nowe zobowiązanie"):
        with st.form("add_z", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nz = c1.text_input("Nazwa")
            kz = c2.number_input("Kwota", min_value=0.0)
            tz = st.selectbox("Typ", ["Subskrypcja", "Koszt Stały", "Rata"])
            if st.form_submit_button("Podpisz kontrakt"):
                if nz and kz > 0:
                    sh.worksheet("Zobowiazania").append_row([nz, tz, kz])
                    st.rerun()
    if not df_z.empty:
        ed_z = st.data_editor(df_z, hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zaktualizuj bazę"): save_df("Zobowiazania", ed_z)

elif menu == "📥 Wpływy":
    st.markdown("<h1>⚾ Box Office</h1>", unsafe_allow_html=True)
    with st.form("add_p", clear_on_submit=True):
        c1, c2 = st.columns(2)
        z = c1.text_input("Źródło")
        kw = c2.number_input("Kwota", min_value=0.0)
        if st.form_submit_button("💰 Dodaj wpływ"):
            if z and kw > 0:
                sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), z, "Konto", kw])
                st.rerun()
    df_p = load_df("Przychody")
    if not df_p.empty:
        ed_p = st.data_editor(df_p.sort_values("Data", ascending=False), hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Nadpisz"): save_df("Przychody", ed_p)

elif menu == "🌽 Sejf":
    st.markdown("<h1>🌽 Des Moines Vault</h1>", unsafe_allow_html=True)
    with st.form("add_o", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        cl = c1.text_input("Cel")
        kwo = c2.number_input("Kwota", min_value=0.0)
        ak = c3.selectbox("Akcja", ["Wpłata", "Wypłata"])
        if st.form_submit_button("🏦 Zamknij sejf"):
            if cl and kwo > 0:
                sh.worksheet("Oszczednosci").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cl, kwo, ak])
                st.rerun()
    df_o = load_df("Oszczednosci")
    if not df_o.empty:
        ed_o = st.data_editor(df_o.sort_values("Data", ascending=False), hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zapisz"): save_df("Oszczednosci", ed_o)
