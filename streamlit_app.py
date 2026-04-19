import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import calendar

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Midwest Budget", page_icon="🏈", layout="wide")

# --- STYLIZACJA: CHICAGO & DES MOINES (SPORTS & INDUSTRIAL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Roboto:wght@400;700;900&family=Oswald:wght@500;700&display=swap');

    /* Tło - Zimowe niebo nad Jeziorem Michigan i beton */
    .stApp {
        background-color: #2c3e50;
        background-image: linear-gradient(180deg, #1a252c 0%, #2c3e50 50%, #4ca1af 100%);
        font-family: 'Roboto', sans-serif;
        color: #e2e8f0;
    }

    /* Karta Główna - Stalowa konstrukcja jak L-Train */
    [data-testid="block-container"] {
        background-color: #f8fafc; 
        padding: 40px;
        border-radius: 8px;
        border: 10px solid #0f172a; /* Ciemna stal */
        box-shadow: 15px 15px 0px rgba(0,0,0,0.5);
        margin-top: 2rem;
        margin-bottom: 2rem;
        color: #0f172a;
    }

    /* Nagłówki - Sportowy Oswald i Bebas Neue */
    h1, h2 {
        font-family: 'Bebas Neue', cursive !important;
        color: #c8102e !important; /* Chicago Bulls Red */
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 2px 2px 0px #cbd5e1;
    }
    h3 {
        font-family: 'Oswald', sans-serif !important;
        color: #002244 !important; /* Chicago Bears Navy */
        text-transform: uppercase;
    }

    /* Pasek boczny - Cegły z Chicago i Kukurydza z Iowa */
    [data-testid="stSidebar"] {
        background-color: #002244; /* Bears Navy */
        border-right: 8px solid #c83803; /* Bears Orange */
    }
    [data-testid="stSidebarNav"], [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #f8fafc !important;
        font-family: 'Oswald', sans-serif;
        font-size: 1.1rem;
        letter-spacing: 1px;
    }

    /* KARTY METRYK - Tablica Wyników (Scoreboard np. na Wrigley Field) */
    div[data-testid="metric-container"] {
        background-color: #111;
        border: 4px solid #333;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0px 8px 15px rgba(0,0,0,0.8);
        text-align: center;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Bebas Neue', cursive !important;
        color: #ffb612 !important; /* Złoty (Iowa Capitol / Hawkeyes) */
        font-size: 3rem !important;
        text-shadow: 0 0 10px rgba(255, 182, 18, 0.5);
    }
    [data-testid="stMetricLabel"] {
        color: #fff !important;
        font-family: 'Roboto', sans-serif !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        font-size: 1rem !important;
        letter-spacing: 1px;
    }

    /* KARTY HERO - Tablice Autostradowe I-80 (Chicago -> Des Moines) */
    .hero-card {
        background-color: #006b3d; /* Zieleń autostradowa */
        border: 6px solid #ffffff;
        border-radius: 12px;
        padding: 30px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.5);
        text-align: center;
    }
    .hero-card.danger {
        background-color: #c8102e; /* Alert wietrznej zimy / Bulls Red */
    }
    .hero-card h2 {
        color: #ffffff !important;
        font-family: 'Bebas Neue', cursive !important;
        font-size: 4rem !important;
        margin: 10px 0;
        text-shadow: none;
    }
    .hero-card p {
        color: #ffffff !important;
        font-family: 'Roboto', sans-serif !important;
        font-weight: 900;
        font-size: 1.5rem;
        text-transform: uppercase;
        margin: 0;
    }

    /* PRZYCISKI - Masywne i sportowe */
    .stButton>button {
        background-color: #002244; /* Bears Navy */
        color: #ffffff !important;
        border: 4px solid #c83803; /* Bears Orange */
        border-radius: 4px;
        font-weight: 900;
        font-family: 'Oswald', sans-serif;
        font-size: 1.2rem;
        text-transform: uppercase;
        box-shadow: 4px 4px 0px #c83803;
        transition: all 0.1s;
    }
    .stButton>button:hover {
        transform: translate(2px, 2px);
        box-shadow: 2px 2px 0px #c83803;
        background-color: #00152b;
    }

    /* Tabele DataFrames */
    .stDataFrame {
        border: 3px solid #0f172a;
        border-radius: 4px;
    }
    
    /* Napis nad kokpitem */
    .ticker-tape {
        background-color: #111; color: #ffb612; font-family: 'Roboto', monospace; font-weight: bold;
        padding: 10px; border: 4px solid #333; font-size: 1.2rem; margin-bottom: 30px;
        text-transform: uppercase;
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
            {"type": "service_account", "project_id": creds.get("project_id", "budzet"),
             "private_key": fixed_key, "client_email": creds["client_email"], "token_uri": creds["token_uri"]},
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(credentials).open_by_url(creds["spreadsheet"])
    except Exception as e:
        st.error(f"Foul w obronie (Błąd): {e}")
        return None

sh = init_connection()

def load_df(sheet_name):
    try:
        df = pd.DataFrame(sh.worksheet(sheet_name).get_all_records())
        if not df.empty and 'Data' in df.columns: df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        return df
    except: return pd.DataFrame()

def save_df(sheet_name, df):
    sheet = sh.worksheet(sheet_name)
    sheet.clear()
    df_save = df.copy()
    if 'Data' in df_save.columns: df_save['Data'] = df_save['Data'].dt.strftime('%Y-%m-%d %H:%M:%S')
    sheet.update([df_save.columns.values.tolist()] + df_save.fillna("").values.tolist())
    st.toast(f"🏈 Touchdown! Wynik zapisany: {sheet_name}!", icon="🎯")

# --- MENU BOCZNE (Playbook) ---
st.sidebar.markdown("<h1 style='color:#ffffff !important; font-size: 3rem;'>📋 PLAYBOOK</h1>", unsafe_allow_html=True)
miesiące = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
wybrany_m = st.sidebar.selectbox("Miesiąc Rozgrywek:", miesiące, index=datetime.now().month - 1)
wybrany_rok = st.sidebar.selectbox("Sezon:", [2024, 2025, 2026], index=2)

m_idx = miesiące.index(wybrany_m) + 1
selected_date = date(wybrany_rok, m_idx, 1)

st.sidebar.markdown("---")
menu = st.sidebar.radio("Wybierz Taktykę:", [
    "🏙️ L-Train (Kokpit)", 
    "🌭 Deep Dish Pizza (Codzienne)", 
    "🏢 Willis Tower (Koszty Stałe)", 
    "⚾ Box Office (Przychody)", 
    "🌽 Des Moines Vault (Oszczędności)"
])

# --- WIDOKI ---
if menu == "🏙️ L-Train (Kokpit)":
    st.markdown("<h1 style='text-align:center;'>WINDY CITY SCOREBOARD</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='ticker-tape'><marquee scrollamount='8'>❄️ OSTRZEŻENIE: Zbliża się zamieć z nad Jeziora Michigan! ❄️ Twój bilans finansowy na sezon {wybrany_m.upper()} {wybrany_rok} ❄️</marquee></div>", unsafe_allow_html=True)
    
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
    w_osz = osz_m[osz_m['Akcja'] == 'Wpłata']['Kwota'].sum() if not osz_m.empty and 'Akcja' in osz_m.columns else 0
    
    wolne = s_prz - s_codzienne - s_zobowiazania - w_osz
    
    ostatni_dzien = calendar.monthrange(wybrany_rok, m_idx)[1]
    dzis = date.today()
    if dzis.month == m_idx and dzis.year == wybrany_rok: pozostalo_dni = ostatni_dzien - dzis.day + 1
    elif selected_date < dzis: pozostalo_dni = 0
    else: pozostalo_dni = ostatni_dzien
        
    dniowka = wolne / pozostalo_dni if pozostalo_dni > 0 and wolne > 0 else 0

    c_h1, c_h2 = st.columns(2)
    with c_h1:
        st.markdown(f"<div class='hero-card'><p>INTERSTATE 80 FUNDS (DO KOŃCA ZIMY)</p><h2>{wolne:,.2f} zł</h2></div>", unsafe_allow_html=True)
    with c_h2:
        klasa_karty = "hero-card danger" if dniowka < 50 else "hero-card"
        st.markdown(f"""
        <div class='{klasa_karty}'>
            <p>DNIÓWKA NA HOT DOGI (PRZEZ {pozostalo_dni} DNI)</p>
            <h2>{dniowka:,.2f} zł</h2>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Wypłata od Sponsorów", f"{s_prz:,.2f} zł")
    col2.metric("Opłaty za Stadion", f"{s_zobowiazania:,.2f} zł")
    col3.metric("Koszty na Mieście", f"{s_codzienne:,.2f} zł")
    col4.metric("Des Moines Vault", f"{w_osz:,.2f} zł")

elif menu == "🌭 Deep Dish Pizza (Codzienne)":
    st.markdown("<h1 style='text-align:center;'>🌭 Chicago Eats & Rides</h1>", unsafe_allow_html=True)
    st.write("### Życie w Wietrznym Mieście kosztuje. Wpisz kwotę, my nabijemy datę, Coachu!")
    
    with st.form("quick_add", clear_on_submit=True):
        c1, c2, c3 = st.columns([2,1,1])
        nazwa = c1.text_input("Na co poszła kasa?")
        kwota = c2.number_input("Ile? (zł)", min_value=0.0, step=1.0)
        kat = c3.selectbox("Sektor", ["Deep Dish & Hot Dogs (Jedzenie)", "Bilet na L-Train (Transport)", "Bulls Game (Rozrywka)", "Dom i Narzędzia", "Lekarz", "Inne"])
        if st.form_submit_button("🏈 PODAJ DALEJ (ZAPISZ)"):
            if kwota > 0 and nazwa:
                teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sh.worksheet("Wydatki").append_row([teraz, nazwa, kat, kwota])
                st.success("Zanotowane na tablicy!")
                st.rerun()

    df_w = load_df("Wydatki")
    if not df_w.empty:
        st.write("### Ostatnie zjazdy do bazy (Historia)")
        ed_w = st.data_editor(df_w.sort_values("Data", ascending=False), hide_index=True, use_container_width=True)
        if st.button("💾 Zapisz poprawki po weryfikacji wideo (VAR)"): save_df("Wydatki", ed_w)

elif menu == "🏢 Willis Tower (Koszty Stałe)":
    st.markdown("<h1 style='text-align:center;'>🏢 Willis Tower Leases</h1>", unsafe_allow_html=True)
    st.write("### Kontrakty długoterminowe. Czynsz, raty i abonamenty. Podstawa każdej franczyzy.")
    
    with st.form("add_zob", clear_on_submit=True):
        st.write("### 📝 Draft Nowego Kontraktu")
        c1, c2 = st.columns(2)
        n = c1.text_input("Dla kogo czek? (np. Netflix, Bank, Ubezpieczenie CROP)")
        k = c2.number_input("Rata miesięczna", min_value=0.0)
        typ = st.selectbox("Liga kosztów", ["Abonament (Subskrypcja)", "Koszty Stałe (Czynsz/Prąd)", "Rata Kredytu"])
        if st.form_submit_button("🔥 Podpisz Kontrakt"):
            if n and k > 0:
                sh.worksheet("Zobowiazania").append_row([n, typ, k])
                st.rerun()
                
    df_z = load_df("Zobowiazania")
    if not df_z.empty:
        st.write("### Aktywne Kontrakty Zawodnicze")
        ed_z = st.data_editor(df_z, hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Złóż podpis na zmianach"): save_df("Zobowiazania", ed_z)

elif menu == "⚾ Box Office (Przychody)":
    st.markdown("<h1 style='text-align:center;'>⚾ Box Office & Sponsors</h1>", unsafe_allow_html=True)
    with st.form("add_prz", clear_on_submit=True):
        c1, c2 = st.columns(2)
        zrodlo = c1.text_input("Kto kupił bilet / podpisał kontrakt?")
        kwota = c2.number_input("Wpływ na konto", min_value=0.0)
        forma = st.selectbox("Gdzie ląduje hajs?", ["Konto w Banku", "Walizka z gotówką"])
        if st.form_submit_button("💰 Odbierz Czek od Sponsora"):
            if zrodlo and kwota > 0:
                sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), zrodlo, forma, kwota])
                st.rerun()

    df_p = load_df("Przychody")
    if not df_p.empty:
        st.write("### Rejestr Sprzedaży Biletów")
        ed_p = st.data_editor(df_p.sort_values("Data", ascending=False), hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Przekaż do księgowości"): save_df("Przychody", ed_p)

elif menu == "🌽 Des Moines Vault (Oszczędności)":
    st.markdown("<h1 style='text-align:center;'>🌽 State Capitol Vault</h1>", unsafe_allow_html=True)
    st.write("### Kasa bezpieczna niczym w sejfie w Des Moines. Na trudne czasy pośród pól kukurydzy.")
    with st.form("add_osz", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        cel = c1.text_input("Na jaki cel w stanie Iowa?")
        kwota = c2.number_input("Ile ładujemy do sejfu?", min_value=0.0)
        akcja = c3.selectbox("Decyzja Trenera:", ["Wpłata (Bezpieczna Przystań)", "Wypłata (Zrywamy Lokatę)"])
        if st.form_submit_button("🏦 ZAMKNIJ DRZWI SKARBCA"):
            if cel and kwota > 0:
                czysta_akcja = "Wpłata" if "Wpłata" in akcja else "Wypłata"
                sh.worksheet("Oszczednosci").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cel, kwota, czysta_akcja])
                st.rerun()

    df_o = load_df("Oszczednosci")
    if not df_o.empty:
        st.write("### Rejestr Depozytów Stanowych")
        ed_o = st.data_editor(df_o.sort_values("Data", ascending=False), hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zabezpiecz Skarbiec"): save_df("Oszczednosci", ed_o)
