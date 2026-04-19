import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import calendar

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Diner Budget", page_icon="🍔", layout="wide")

# --- STYLIZACJA AMERICAN DINER 50s ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lobster&family=Inter:wght@400;700;900&display=swap');

    /* Tło aplikacji - czarno-biała szachownica */
    .stApp {
        background-color: #ffffff;
        background-image:
          linear-gradient(45deg, #1a1a1a 25%, transparent 25%, transparent 75%, #1a1a1a 75%, #1a1a1a),
          linear-gradient(45deg, #1a1a1a 25%, transparent 25%, transparent 75%, #1a1a1a 75%, #1a1a1a);
        background-size: 60px 60px;
        background-position: 0 0, 30px 30px;
        background-attachment: fixed;
        font-family: 'Inter', sans-serif;
    }

    /* Główny kontener - Karta z Menu (kremowa jak milkshake waniliowy) */
    [data-testid="block-container"] {
        background-color: #fffdf5; 
        padding: 40px;
        border-radius: 15px;
        border: 5px solid #d90429;
        box-shadow: 12px 12px 0px #1a1a1a;
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    /* Nagłówki - Neonowy Lobster */
    h1, h2, h3 {
        font-family: 'Lobster', cursive !important;
        color: #d90429 !important;
        text-shadow: 2px 2px 0px #1a1a1a;
        letter-spacing: 2px;
    }

    /* Pasek boczny - Czerwony plastik / skóra */
    [data-testid="stSidebar"] {
        background-color: #d90429;
        background-image: linear-gradient(0deg, #961216 0%, #d90429 100%);
        border-right: 5px solid #1a1a1a;
    }
    
    /* Napisy w pasku bocznym */
    [data-testid="stSidebarNav"], [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #fffdf5 !important;
        font-weight: bold;
    }

    /* Karty Metryk i Hero - Czerwona Skórzana Loża z Chromem */
    div[data-testid="metric-container"], .hero-card {
        background: linear-gradient(to bottom, #bd1e24 0%, #8a0c10 100%);
        border: 4px solid #e2e8f0; /* Chrom */
        border-radius: 12px;
        padding: 20px;
        box-shadow: inset 0px 5px 15px rgba(0,0,0,0.5), 5px 5px 0px #1a1a1a;
        text-align: center;
    }

    /* Wartości w kartach metryk */
    [data-testid="stMetricValue"] {
        color: #fffdf5 !important;
        font-family: 'Lobster', cursive !important;
        text-shadow: 2px 2px 4px #000;
        font-size: 2.5rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #ffb703 !important; /* Musztardowy żółty */
        font-weight: 900 !important;
        text-transform: uppercase;
    }

    /* Stylizacja Hero Cards */
    .hero-card h2 {
        color: #fffdf5 !important;
        font-size: 3.5rem !important;
        margin: 10px 0;
    }
    .hero-card p {
        color: #ffb703 !important;
        font-weight: 900;
        text-transform: uppercase;
        margin:0;
        font-size: 1.1rem;
    }

    /* Przyciski - Retro Musztarda z grubym czarnym cieniem */
    .stButton>button {
        background-color: #ffb703;
        color: #1a1a1a !important;
        border: 3px solid #1a1a1a;
        border-radius: 8px;
        font-weight: 900;
        font-size: 1.1rem;
        text-transform: uppercase;
        box-shadow: 5px 5px 0px #1a1a1a;
        transition: all 0.1s;
    }
    .stButton>button:hover {
        transform: translate(2px, 2px);
        box-shadow: 2px 2px 0px #1a1a1a;
        background-color: #fb8500;
    }
    
    /* Ukrycie indexu tabel dla czystszego widoku */
    .stDataFrame { border: 2px solid #1a1a1a; border-radius: 8px; }
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
                "project_id": creds.get("project_id", "budzet"),
                "private_key": fixed_key,
                "client_email": creds["client_email"],
                "token_uri": creds["token_uri"],
            },
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(credentials).open_by_url(creds["spreadsheet"])
    except Exception as e:
        st.error(f"Błąd połączenia: {e}")
        return None

sh = init_connection()

# --- FUNKCJE BAZY ---
def load_df(sheet_name):
    try:
        data = sh.worksheet(sheet_name).get_all_records()
        df = pd.DataFrame(data)
        if not df.empty and 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        return df
    except: 
        return pd.DataFrame()

def save_df(sheet_name, df):
    sheet = sh.worksheet(sheet_name)
    sheet.clear()
    df_save = df.copy()
    if 'Data' in df_save.columns:
        df_save['Data'] = df_save['Data'].dt.strftime('%Y-%m-%d %H:%M:%S')
    sheet.update([df_save.columns.values.tolist()] + df_save.fillna("").values.tolist())
    st.toast(f"🍒 Zaktualizowano szafę grającą: {sheet_name}!")

# --- NAWIGACJA BOCZNA ---
st.sidebar.markdown("<h2 style='color:white !important; text-shadow:none;'>🍔 Diner Menu</h2>", unsafe_allow_html=True)
miesiące = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
wybrany_m = st.sidebar.selectbox("Wybierz Miesiąc:", miesiące, index=datetime.now().month - 1)
wybrany_rok = st.sidebar.selectbox("Wybierz Rok:", [2024, 2025, 2026], index=2)

m_idx = miesiące.index(wybrany_m) + 1
selected_date = date(wybrany_rok, m_idx, 1)

st.sidebar.markdown("---")
menu = st.sidebar.radio("Co podać?", ["🏠 Kasa Główna (Kokpit)", "🍟 Zamówienia (Wydatki)", "🗓️ Rachunki za Lokal (Stałe)", "💵 Utarg (Przychody)", "🎸 Jukebox (Oszczędności)"])

# --- WIDOKI ---
if menu == "🏠 Kasa Główna (Kokpit)":
    st.title(f"Zestawienie: {wybrany_m} {wybrany_rok} 🥤")
    
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
    if dzis.month == m_idx and dzis.year == wybrany_rok:
        pozostalo_dni = ostatni_dzien - dzis.day + 1
    elif selected_date < dzis:
        pozostalo_dni = 0
    else:
        pozostalo_dni = ostatni_dzien
        
    dniowka = wolne / pozostalo_dni if pozostalo_dni > 0 and wolne > 0 else 0

    c_h1, c_h2 = st.columns(2)
    with c_h1:
        st.markdown(f"<div class='hero-card'><p>Zostało w kasie (na życie)</p><h2>{wolne:,.2f} zł</h2></div>", unsafe_allow_html=True)
    with c_h2:
        st.markdown(f"<div class='hero-card'><p>Dniówka na szejki ({pozostalo_dni} dni)</p><h2>{dniowka:,.2f} zł</h2></div>", unsafe_allow_html=True)

    st.write("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Łączny Utarg", f"{s_prz:,.2f} zł")
    col2.metric("Opłaty za lokal", f"{s_zobowiazania:,.2f} zł")
    col3.metric("Dzisiejsze frytki", f"{s_codzienne:,.2f} zł")
    col4.metric("Wrzucono do szafy", f"{w_osz:,.2f} zł")

elif menu == "🍟 Zamówienia (Wydatki)":
    st.title("🍟 Zamówienia na wynos (Wydatki)")
    st.info("Kasa rejestruje datę i godzinę automatycznie! Wpisz tylko kwotę.")
    
    with st.form("quick_add", clear_on_submit=True):
        c1, c2, c3 = st.columns([2,1,1])
        nazwa = c1.text_input("Co było na rachunku?")
        kwota = c2.number_input("Kwota", min_value=0.0, step=5.0)
        kat = c3.selectbox("Kategoria", ["Jedzenie", "Dom", "Transport", "Zdrowie", "Rozrywka", "Inne"])
        if st.form_submit_button("⚡ ZAPISZ PARAGON"):
            if kwota > 0 and nazwa:
                teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sh.worksheet("Wydatki").append_row([teraz, nazwa, kat, kwota])
                st.success("Zamówienie przyjęte!")
                st.rerun()

    df_w = load_df("Wydatki")
    if not df_w.empty:
        st.write("### Ostatnie paragony z kasy")
        ed_w = st.data_editor(df_w.sort_values("Data", ascending=False), hide_index=True, use_container_width=True)
        if st.button("💾 Zapisz poprawki w księdze"): 
            save_df("Wydatki", ed_w)

elif menu == "🗓️ Rachunki za Lokal (Stałe)":
    st.title("🗓️ Rachunki za Lokal (Zobowiązania)")
    st.markdown("Czynsz, dostawcy, raty. Opłaty stałe, które pobierają się same co miesiąc.")
    
    t1, t2 = st.tabs(["📋 Baza opłat", "➕ Nowa umowa"])
    
    with t2:
        with st.form("add_zob", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nazwa dostawcy (np. Netflix, Prąd, Rata)")
            k = c2.number_input("Kwota stała", min_value=0.0)
            typ = st.selectbox("Typ", ["Subskrypcja", "Koszt Stały", "Rata Kredytu"])
            if st.form_submit_button("Podpisz umowę"):
                if n and k > 0:
                    sh.worksheet("Zobowiazania").append_row([n, typ, k])
                    st.rerun()
                
    with t1:
        df_z = load_df("Zobowiazania")
        if not df_z.empty:
            ed_z = st.data_editor(df_z, hide_index=True, num_rows="dynamic", use_container_width=True)
            if st.button("💾 Zaktualizuj rejestr stały"): 
                save_df("Zobowiazania", ed_z)

elif menu == "💵 Utarg (Przychody)":
    st.title("💵 Dzisiejszy Utarg (Przychody)")
    with st.form("add_prz", clear_on_submit=True):
        c1, c2 = st.columns(2)
        zrodlo = c1.text_input("Skąd ten hajs? (np. Pensja)")
        kwota = c2.number_input("Ile zarobiliśmy?", min_value=0.0)
        forma = st.selectbox("Forma zapłaty", ["Konto", "Gotówka w kasie"])
        if st.form_submit_button("Wrzuć do kasy"):
            if zrodlo and kwota > 0:
                sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), zrodlo, forma, kwota])
                st.rerun()

    df_p = load_df("Przychody")
    if not df_p.empty:
        st.write("### Historia księgowa")
        ed_p = st.data_editor(df_p.sort_values("Data", ascending=False), hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Nadpisz księgi"): 
            save_df("Przychody", ed_p)

elif menu == "🎸 Jukebox (Oszczędności)":
    st.title("🎸 Jukebox (Oszczędności)")
    st.markdown("Wrzuć monetę do szafy na lepsze czasy!")
    with st.form("add_osz", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        cel = c1.text_input("Na jaki cel?")
        kwota = c2.number_input("Ile wrzucasz?", min_value=0.0)
        akcja = c3.selectbox("Rodzaj operacji", ["Wpłata", "Wypłata"])
        if st.form_submit_button("Wciśnij przycisk Play"):
            if cel and kwota > 0:
                sh.worksheet("Oszczednosci").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cel, kwota, akcja])
                st.rerun()

    df_o = load_df("Oszczednosci")
    if not df_o.empty:
        st.write("### Rozbita skarbonka")
        ed_o = st.data_editor(df_o.sort_values("Data", ascending=False), hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zabezpiecz szafę grającą"): 
            save_df("Oszczednosci", ed_o)
