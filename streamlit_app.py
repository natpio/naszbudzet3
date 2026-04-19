import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import calendar

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
    /* Podświetlenie dziennego limitu */
    .daily-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; 
        padding: 25px; 
        border-radius: 20px;
        text-align: center; 
        margin-bottom: 20px; 
        box-shadow: 0 10px 20px rgba(118, 75, 162, 0.3);
    }
    .daily-box.highlight {
        background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
        box-shadow: 0 10px 20px rgba(0, 114, 255, 0.3);
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
        for col in df_to_save.select_dtypes(include=['datetime64']).columns:
            df_to_save[col] = df_to_save[col].dt.strftime('%Y-%m-%d')
        sheet.update([df_to_save.columns.values.tolist()] + df_to_save.fillna("").values.tolist())
        st.toast(f"✅ Zapisano zmiany w tabeli: {sheet_name}")
    except Exception as e:
        st.error(f"Błąd zapisu: {e}")

# --- AUTOMATYZACJA KOSZTÓW ---
def run_monthly_billing(month_date):
    wydatki_df = load_df("Wydatki")
    
    if wydatki_df.empty or 'Data' not in wydatki_df.columns or 'Data końca' not in wydatki_df.columns:
        return
        
    month_str = month_date.strftime("%Y-%m")
    
    already_billed = wydatki_df[
        (wydatki_df['Data'].dt.strftime("%Y-%m") == month_str) & 
        (wydatki_df['Nazwa'].astype(str).str.contains("AUTOMAT:"))
    ]
    
    if already_billed.empty:
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
selected_month = st.sidebar.date_input("Wybierz miesiąc do analizy", date.today().replace(day=1))
run_monthly_billing(selected_month)
st.sidebar.markdown("---")
menu = st.sidebar.radio("Nawigacja:", ["🏠 Kokpit", "📥 Wpływy", "💸 Wydatki", "📅 Raty", "🐷 Oszczędności"])

def filter_month(df):
    if df.empty or 'Data' not in df.columns: return df
    return df[df['Data'].dt.strftime("%Y-%m") == selected_month.strftime("%Y-%m")]

# --- WIDOKI ---
if menu == "🏠 Kokpit":
    st.markdown(f"<h1>Bilans: {selected_month.strftime('%B %Y')} ☕</h1>", unsafe_allow_html=True)
    
    prz_m = filter_month(load_df("Przychody"))
    wyd_m = filter_month(load_df("Wydatki"))
    osz_m = filter_month(load_df("Oszczednosci"))
    raty = load_df("Raty")
    osz_all = load_df("Oszczednosci")
    
    # Obliczenia miesięczne
    suma_wplywow = prz_m['Kwota'].sum() if not prz_m.empty else 0
    suma_wydatkow = wyd_m['Kwota'].sum() if not wyd_m.empty else 0
    suma_rat = pd.to_numeric(raty['Kwota raty'], errors='coerce').sum() if not raty.empty else 0
    wplaty_osz_m = osz_m[osz_m['Typ'] == 'Wpłata']['Kwota'].sum() if not osz_m.empty and 'Typ' in osz_m.columns else 0
    
    # Wolne środki = Wpływy - Wydatki - Raty - Wpłaty na oszczędności (w tym miesiącu)
    do_konca_miesiaca = suma_wplywow - suma_wydatkow - suma_rat - wplaty_osz_m
    
    # Obliczenia całkowitych oszczędności (historycznie)
    if not osz_all.empty and 'Typ' in osz_all.columns:
        total_savings = osz_all[osz_all['Typ'] == 'Wpłata']['Kwota'].sum() - osz_all[osz_all['Typ'] == 'Wypłata']['Kwota'].sum()
    else:
        total_savings = 0

    # Obliczanie Dni
    dzis = date.today()
    if dzis.month == selected_month.month and dzis.year == selected_month.year:
        dni_w_miesiacu = calendar.monthrange(dzis.year, dzis.month)[1]
        pozostalo_dni = dni_w_miesiacu - dzis.day + 1
    else:
        pozostalo_dni = calendar.monthrange(selected_month.year, selected_month.month)[1]

    dzienna_stawka = do_konca_miesiaca / pozostalo_dni if pozostalo_dni > 0 and do_konca_miesiaca > 0 else 0

    # Sekcja Licznika Dziennego
    st.write("### Wskaźniki przetrwania")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
            <div class='daily-box'>
                <p style='margin:0; font-size: 1.1rem; opacity: 0.9;'>Zostało na koncie (na życie)</p>
                <h2 style='margin:0; font-size: 3.5rem; font-weight: 800;'>{do_konca_miesiaca:,.2f} zł</h2>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class='daily-box highlight'>
                <p style='margin:0; font-size: 1.1rem; opacity: 0.9;'>Bezpieczny limit na dziś (przez {pozostalo_dni} dni)</p>
                <h2 style='margin:0; font-size: 3.5rem; font-weight: 800;'>{dzienna_stawka:,.2f} zł</h2>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Łączne Wpływy", f"{suma_wplywow:,.2f} zł")
    col2.metric("Wydatki + Raty", f"{(suma_wydatkow + suma_rat):,.2f} zł")
    col3.metric("Wysłano na 🐷 w tym m-cu", f"{wplaty_osz_m:,.2f} zł")

    st.markdown("---")
    st.markdown(f"### 🐷 Nasz Fundusz Całkowity: **<span style='color:#27ae60;'>{total_savings:,.2f} zł</span>**", unsafe_allow_html=True)
    
    colA, colB = st.columns(2)
    with colA:
        if not wyd_m.empty:
            st.write("#### Na co poszły pieniądze?")
            wydatki_kat = wyd_m.groupby("Kategoria")["Kwota"].sum().reset_index()
            st.bar_chart(wydatki_kat, x="Kategoria", y="Kwota", color="#ff7675")
    with colB:
        if not prz_m.empty:
            st.write("#### Gdzie są nasze środki?")
            kasa = prz_m.groupby("Typ")["Kwota"].sum().reset_index()
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
