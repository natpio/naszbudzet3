import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Nasz Budżet", page_icon="💎", layout="wide")

# --- SUPER NOWOCZESNA STYLIZACJA (GLASSMORPHISM) ---
st.markdown("""
    <style>
    /* Globalne tło - nowoczesny gradient */
    .stApp { 
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        font-family: 'Inter', sans-serif;
    }
    /* Główne nagłówki */
    h1 { color: #2c3e50; font-weight: 800; letter-spacing: -1px; }
    
    /* Stylizacja Metryk (Karty) */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        transition: transform 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
    }
    [data-testid="stMetricValue"] { 
        font-size: 2.2rem; 
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #1cb5e0, #000046);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Przyciski */
    .stButton>button { 
        background: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
        color: white; 
        border: none;
        border-radius: 12px; 
        font-weight: bold; 
        height: 3em; 
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(79, 172, 254, 0.6);
    }
    
    /* Panele boczne i zakładki */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z GOOGLE SHEETS ---
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
        gc = gspread.authorize(credentials)
        return gc.open_by_url(creds["spreadsheet"])
    except Exception as e:
        st.error(f"Błąd połączenia: {e}")
        return None

sh = init_connection()

# --- FUNKCJE POMOCNICZE ---
def load_df(sheet_name):
    try:
        data = sh.worksheet(sheet_name).get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def save_df(sheet_name, df):
    try:
        sheet = sh.worksheet(sheet_name)
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.fillna("").values.tolist())
        st.toast(f"✅ Zaktualizowano bazę: {sheet_name}!")
    except Exception as e:
        st.error(f"Błąd zapisu: {e}")

# --- AUTOMATYZACJA 800+ ---
def sync_recurring_benefits():
    df = load_df("Przychody")
    current_month = datetime.now().strftime("%Y-%m")
    
    if df.empty or 'Źródło' not in df.columns or 'Data' not in df.columns:
        if st.sidebar.button("✨ Zainicjuj 800+ w tym miesiącu"):
            sh.worksheet("Przychody").append_row([
                datetime.now().strftime("%Y-%m-%d"), "Świadczenie 800+", "Konto", 1600.0
            ])
            st.rerun()
        return

    mask = (df['Źródło'] == "Świadczenie 800+") & (df['Data'].astype(str).str.startswith(current_month))
    if not mask.any():
        if st.sidebar.button("✨ Dodaj 800+ za ten miesiąc"):
            sh.worksheet("Przychody").append_row([
                datetime.now().strftime("%Y-%m-%d"), "Świadczenie 800+", "Konto", 1600.0
            ])
            st.toast("Dzieciaczki zasiliły budżet! 👶💰")
            st.rerun()

# --- INTERFEJS ---
st.sidebar.markdown("## 💎 Nasze Centrum")
sync_recurring_benefits()
st.sidebar.markdown("---")
menu = st.sidebar.radio("Nawigacja:", ["🏠 Kokpit", "📥 Wpływy", "💸 Wydatki", "📅 Raty"])

if menu == "🏠 Kokpit":
    st.markdown("<h1>Witajcie w domu! ☕</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #7f8c8d; font-size: 1.1rem;'>Oto jak wygląda Wasz wspólny budżet w tym miesiącu.</p>", unsafe_allow_html=True)
    st.write("")
    
    prz = load_df("Przychody")
    wyd = load_df("Wydatki")
    raty = load_df("Raty")
    
    total_in = pd.to_numeric(prz["Kwota"], errors='coerce').sum() if not prz.empty else 0
    total_out = pd.to_numeric(wyd["Kwota"], errors='coerce').sum() if not wyd.empty else 0
    total_raty = pd.to_numeric(raty["Kwota raty"], errors='coerce').sum() if not raty.empty else 0
    
    zostaje = total_in - total_out - total_raty
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wspólne Wpływy", f"{total_in:,.2f} zł")
    c2.metric("Wydaliśmy", f"{total_out:,.2f} zł")
    c3.metric("Raty & Zobowiązania", f"{total_raty:,.2f} zł")
    c4.metric("Wolne Środki", f"{zostaje:,.2f} zł")

    st.markdown("---")
    
    colA, colB = st.columns(2)
    with colA:
        if not wyd.empty:
            st.subheader("Na co idą pieniądze? 🛒")
            wydatki_kat = wyd.groupby("Kategoria")["Kwota"].sum().reset_index()
            st.bar_chart(wydatki_kat, x="Kategoria", y="Kwota", color="#ff7675")
        else:
            st.info("Brak wydatków, by pokazać wykres.")
            
    with colB:
        if not prz.empty:
            st.subheader("Stan środków 💳")
            kasa = prz.groupby("Typ")["Kwota"].sum().reset_index()
            st.bar_chart(kasa, x="Typ", y="Kwota", color="#74b9ff")

elif menu == "📥 Wpływy":
    st.markdown("<h1>Zasilenie konta 📥</h1>", unsafe_allow_html=True)
    
    with st.container():
        with st.form("form_p", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            zrodlo = col1.text_input("Skąd te pieniądze? (np. Wypłata, Sprzedaż)")
            forma = col2.selectbox("Gdzie?", ["Konto", "Gotówka", "Oszczędnościowe"])
            ile = col3.number_input("Ile?", min_value=0.0, step=50.0)
            if st.form_submit_button("➕ Dodaj do puli"):
                if zrodlo:
                    sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d"), zrodlo, forma, ile])
                    st.rerun()

    st.write("### Historia Wpływów")
    df_p = load_df("Przychody")
    if not df_p.empty:
        ed_p = st.data_editor(df_p, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zapisz zmiany w Tabeli"):
            save_df("Przychody", ed_p)

elif menu == "💸 Wydatki":
    st.markdown("<h1>Zarządzanie Wydatkami 💸</h1>", unsafe_allow_html=True)
    
    with st.container():
        with st.form("form_w", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nazwa = col1.text_input("Co kupiliśmy / opłaciliśmy?")
            kwota = col2.number_input("Kwota", min_value=0.0, step=10.0)
            
            col3, col4 = st.columns(2)
            rodzaj = col3.selectbox("Typ kosztu", ["Zmienny (np. zakupy)", "Stały (np. czynsz)"])
            kat = col4.selectbox("Kategoria", ["Dom i Rachunki", "Jedzenie", "Transport", "Dzieci", "Przyjemności", "Zdrowie", "Inne"])
            
            if st.form_submit_button("🛒 Zapisz wydatek"):
                if nazwa:
                    sh.worksheet("Wydatki").append_row([datetime.now().strftime("%Y-%m-%d"), nazwa, kat, rodzaj, kwota])
                    st.rerun()

    st.write("### Nasze Wydatki")
    df_w = load_df("Wydatki")
    if not df_w.empty:
        ed_w = st.data_editor(df_w, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zapisz edycję wydatków"):
            save_df("Wydatki", ed_w)

elif menu == "📅 Raty":
    st.markdown("<h1>Harmonogram Rat 📅</h1>", unsafe_allow_html=True)
    st.info("Trzymamy rękę na pulsie. Lista naszych stałych obciążeń finansowych.")
    
    df_r = load_df("Raty")
    if df_r.empty:
        df_r = pd.DataFrame(columns=["Nazwa banku/kredytu", "Dzień płatności", "Kwota raty", "Pozostało do spłaty", "Data końcowa"])
    
    ed_r = st.data_editor(df_r, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Zaktualizuj bazę rat"):
        save_df("Raty", ed_r)
