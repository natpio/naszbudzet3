import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Nasz Budżet PRO", page_icon="💎", layout="wide")

# --- SUPER NOWOCZESNA STYLIZACJA (GLASSMORPHISM) ---
st.markdown("""
    <style>
    .stApp { 
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        font-family: 'Inter', sans-serif;
    }
    h1 { color: #2c3e50; font-weight: 800; letter-spacing: -1px; }
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
        return gspread.authorize(credentials).open_by_url(creds["spreadsheet"])
    except Exception as e:
        st.error(f"Błąd połączenia: {e}")
        return None

sh = init_connection()

# --- FUNKCJE POMOCNICZE DO BAZY DANYCH ---
def load_df(sheet_name):
    try:
        data = sh.worksheet(sheet_name).get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            if 'Data' in df.columns:
                df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
            if 'Data końca' in df.columns:
                df['Data końca'] = pd.to_datetime(df['Data końca'], errors='coerce')
        return df
    except:
        return pd.DataFrame()

def save_df(sheet_name, df):
    try:
        sheet = sh.worksheet(sheet_name)
        sheet.clear()
        df_to_save = df.copy()
        # Formatowanie dat z powrotem na tekst przed zapisem
        for col in df_to_save.select_dtypes(include=['datetime64']).columns:
            df_to_save[col] = df_to_save[col].dt.strftime('%Y-%m-%d')
        sheet.update([df_to_save.columns.values.tolist()] + df_to_save.fillna("").values.tolist())
        st.toast(f"✅ Zapisano zmiany w tabeli: {sheet_name}")
    except Exception as e:
        st.error(f"Błąd zapisu: {e}")

# --- AUTOMATYZACJA KOSZTÓW ---
def run_monthly_billing(month_date):
    wydatki_df = load_df("Wydatki")
    
    # TARCZA: Jeśli arkusz jest pusty lub brakuje nagłówków, przerywamy automat
    if wydatki_df.empty or 'Data' not in wydatki_df.columns or 'Data końca' not in wydatki_df.columns:
        return
        
    month_str = month_date.strftime("%Y-%m")
    
    # Sprawdzenie czy już naliczono automat w tym miesiącu
    already_billed = wydatki_df[
        (wydatki_df['Data'].dt.strftime("%Y-%m") == month_str) & 
        (wydatki_df['Nazwa'].astype(str).str.contains("AUTOMAT:"))
    ]
    
    if already_billed.empty:
        # Znalezienie aktywnych subskrypcji i kosztów stałych
        aktywne = wydatki_df[
            ((wydatki_df['Typ'].astype(str).str.contains("Stały")) | (wydatki_df['Kategoria'] == "Subskrypcje")) &
            (wydatki_df['Data'] < month_date) &
            ((wydatki_df['Data końca'].isna()) | (wydatki_df['Data końca'] >= month_date)) &
            (~wydatki_df['Nazwa'].astype(str).str.contains("AUTOMAT:"))
        ].copy()
        
        if not aktywne.empty:
            if st.sidebar.button(f"🚀 Generuj subskrypcje i koszty na {month_str}"):
                for _, row in aktywne.iterrows():
                    new_row = [
                        month_date.strftime("%Y-%m-01"),
                        f"AUTOMAT: {row['Nazwa']}",
                        row['Kategoria'],
                        row['Typ'],
                        row['Kwota'],
                        row['Data końca'].strftime('%Y-%m-%d') if pd.notna(row['Data końca']) else ""
                    ]
                    sh.worksheet("Wydatki").append_row(new_row)
                st.rerun()

# --- SIDEBAR & NAWIGACJA ---
st.sidebar.markdown("## 💎 Nasze Centrum")
selected_month = st.sidebar.date_input("Wybierz miesiąc do analizy", datetime.now().replace(day=1))
run_monthly_billing(selected_month)
st.sidebar.markdown("---")
menu = st.sidebar.radio("Nawigacja:", ["🏠 Kokpit", "📥 Wpływy", "💸 Wydatki", "📅 Raty", "🐷 Oszczędności"])

def filter_month(df):
    if df.empty or 'Data' not in df.columns: return df
    return df[df['Data'].dt.strftime("%Y-%m") == selected_month.strftime("%Y-%m")]

# --- WIDOKI ---
if menu == "🏠 Kokpit":
    st.markdown(f"<h1>Bilans: {selected_month.strftime('%B %Y')} ☕</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #7f8c8d; font-size: 1.1rem;'>Witajcie! Oto podsumowanie Waszego budżetu w wybranym miesiącu.</p>", unsafe_allow_html=True)
    
    prz = filter_month(load_df("Przychody"))
    wyd = filter_month(load_df("Wydatki"))
    raty = load_df("Raty")
    osz = load_df("Oszczednosci")
    
    total_in = prz['Kwota'].sum() if not prz.empty else 0
    total_out = wyd['Kwota'].sum() if not wyd.empty else 0
    total_raty = pd.to_numeric(raty['Kwota raty'], errors='coerce').sum() if not raty.empty else 0
    
    # Obliczanie stanu oszczędności
    if not osz.empty and 'Typ' in osz.columns and 'Kwota' in osz.columns:
        wplaty = pd.to_numeric(osz[osz['Typ'] == 'Wpłata']['Kwota'], errors='coerce').sum()
        wyplaty = pd.to_numeric(osz[osz['Typ'] == 'Wypłata']['Kwota'], errors='coerce').sum()
        total_savings = wplaty - wyplaty
    else:
        total_savings = 0
        
    zostaje = total_in - total_out - total_raty
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wpływy", f"{total_in:,.2f} zł")
    c2.metric("Wydatki", f"{total_out:,.2f} zł")
    c3.metric("Raty stałe", f"{total_raty:,.2f} zł")
    c4.metric("Wolne Środki", f"{zostaje:,.2f} zł")

    st.markdown("---")
    st.subheader(f"🐷 Aktualny Fundusz Oszczędnościowy: {total_savings:,.2f} zł")
    
    colA, colB = st.columns(2)
    with colA:
        if not wyd.empty:
            st.write("#### Na co poszły pieniądze?")
            wydatki_kat = wyd.groupby("Kategoria")["Kwota"].sum().reset_index()
            st.bar_chart(wydatki_kat, x="Kategoria", y="Kwota", color="#ff7675")
    with colB:
        if not prz.empty:
            st.write("#### Gdzie są nasze środki?")
            kasa = prz.groupby("Typ")["Kwota"].sum().reset_index()
            st.bar_chart(kasa, x="Typ", y="Kwota", color="#74b9ff")

elif menu == "📥 Wpływy":
    st.markdown("<h1>Zasilenie konta 📥</h1>", unsafe_allow_html=True)
    
    with st.container():
        with st.form("form_p", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            zrodlo = col1.text_input("Skąd te pieniądze? (np. Wypłata, 800+)")
            forma = col2.selectbox("Gdzie trafiły?", ["Konto", "Gotówka"])
            ile = col3.number_input("Ile?", min_value=0.0, step=50.0)
            if st.form_submit_button("➕ Dodaj do puli"):
                if zrodlo:
                    sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d"), zrodlo, forma, ile])
                    st.rerun()

    st.write("### Pełna historia wpływów (Edytuj i Usuwaj)")
    df_p = load_df("Przychody")
    if not df_p.empty:
        ed_p = st.data_editor(df_p, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zapisz zmiany w Tabeli Wpływów"):
            save_df("Przychody", ed_p)

elif menu == "💸 Wydatki":
    st.markdown("<h1>Zarządzanie Wydatkami 💸</h1>", unsafe_allow_html=True)
    
    with st.container():
        with st.form("form_w", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nazwa = col1.text_input("Co kupiliśmy / opłaciliśmy?")
            kwota = col2.number_input("Kwota", min_value=0.0, step=10.0)
            
            col3, col4 = st.columns(2)
            rodzaj = col3.selectbox("Typ kosztu", ["Zmienny", "Stały"])
            kat = col4.selectbox("Kategoria", ["Dom i Rachunki", "Jedzenie", "Subskrypcje", "Transport", "Dzieci", "Przyjemności", "Zdrowie", "Inne"])
            
            data_konca = st.date_input("Data zakończenia (Wybierz TYLKO dla stałych kosztów i subskrypcji)", value=None)
            
            if st.form_submit_button("🛒 Zapisz wydatek"):
                if nazwa:
                    data_k_str = data_konca.strftime("%Y-%m-%d") if data_konca else ""
                    sh.worksheet("Wydatki").append_row([datetime.now().strftime("%Y-%m-%d"), nazwa, kat, rodzaj, kwota, data_k_str])
                    st.rerun()

    st.write("### Baza Wydatków (Edytuj, ustalaj daty wygaśnięcia)")
    df_w = load_df("Wydatki")
    if not df_w.empty:
        ed_w = st.data_editor(df_w, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zapisz edycję wydatków"):
            save_df("Wydatki", ed_w)

elif menu == "🐷 Oszczędności":
    st.markdown("<h1>Kasa Oszczędnościowa 🐷</h1>", unsafe_allow_html=True)
    
    with st.container():
        with st.form("osz_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            cel = col1.text_input("Na co to? (np. Poduszka, Remont)")
            kw = col2.number_input("Kwota", min_value=0.0, step=100.0)
            t = col3.selectbox("Akcja", ["Wpłata", "Wypłata"])
            if st.form_submit_button("Zapisz operację"):
                if cel:
                    sh.worksheet("Oszczednosci").append_row([datetime.now().strftime("%Y-%m-%d"), cel, kw, t])
                    st.rerun()
                
    df_o = load_df("Oszczednosci")
    if not df_o.empty:
        st.write("### Historia operacji oszczędnościowych")
        ed_o = st.data_editor(df_o, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zapisz zmiany oszczędności"):
            save_df("Oszczednosci", ed_o)

elif menu == "📅 Raty":
    st.markdown("<h1>Harmonogram Rat 📅</h1>", unsafe_allow_html=True)
    st.info("Trzymamy rękę na pulsie. Zapisuj tutaj kredyty, leasingi i spłaty ratalne.")
    
    df_r = load_df("Raty")
    if df_r.empty:
        df_r = pd.DataFrame(columns=["Nazwa banku/kredytu", "Dzień płatności", "Kwota raty", "Pozostało do spłaty", "Data końcowa"])
    
    ed_r = st.data_editor(df_r, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Zaktualizuj bazę rat"):
        save_df("Raty", ed_r)
