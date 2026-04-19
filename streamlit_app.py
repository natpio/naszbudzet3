import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Rodzinny Budżet PRO", page_icon="🏦", layout="wide")

# --- STYLIZACJA ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #1e3a8a; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .css-1kyx001 { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE ---
@st.cache_resource
def init_connection():
    creds = st.secrets["connections"]["gsheets"]
    key = creds["private_key"].replace("\\n", "\n").strip()
    credentials = Credentials.from_service_account_info(
        {
            "client_email": creds["client_email"],
            "private_key": key,
            "token_uri": creds["token_uri"],
            "project_id": creds.get("project_id", "budzet"),
        },
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(credentials).open_by_url(creds["spreadsheet"])

sh = init_connection()

def load_df(sheet_name):
    data = sh.worksheet(sheet_name).get_all_records()
    return pd.DataFrame(data) if data else pd.DataFrame()

def save_df(sheet_name, df):
    sheet = sh.worksheet(sheet_name)
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.fillna("").values.tolist())
    st.success(f"Zaktualizowano: {sheet_name}!")

# --- AUTOMATYZACJA 800+ ---
def sync_recurring_benefits():
    df = load_df("Przychody")
    current_month = datetime.now().strftime("%Y-%m")
    mask = (df['Źródło'] == "800+") & (df['Data'].str.startswith(current_month))
    
    if df.empty or not mask.any():
        if st.sidebar.button("🚨 Dodaj 800+ za ten miesiąc"):
            sh.worksheet("Przychody").append_row([
                datetime.now().strftime("%Y-%m-%d"), "Rodzina", "800+", "Konto", 1600.0
            ])
            st.rerun()

# --- INTERFEJS ---
sync_recurring_benefits()

menu = st.sidebar.selectbox("Menu", ["🏠 Dashboard", "💰 Przychody", "💸 Wydatki & Koszty", "📅 Raty & Kredyty"])

if menu == "🏠 Dashboard":
    st.title("📊 Przegląd Miesięczny")
    
    prz = load_df("Przychody")
    wyd = load_df("Wydatki")
    raty = load_df("Raty")
    
    total_in = pd.to_numeric(prz["Kwota"], errors='coerce').sum()
    total_out = pd.to_numeric(wyd["Kwota"], errors='coerce').sum()
    total_raty = pd.to_numeric(raty["Kwota raty"], errors='coerce').sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Przychody", f"{total_in:,.2f} zł")
    c2.metric("Wydatki", f"{total_out:,.2f} zł")
    c3.metric("Suma Rat", f"{total_raty:,.2f} zł")
    c4.metric("Zostaje", f"{(total_in - total_out - total_raty):,.2f} zł")

    st.subheader("Struktura Przychodu")
    st.bar_chart(prz.groupby("Osoba")["Kwota"].sum())

elif menu == "💰 Przychody":
    st.title("💰 Zarobki Natalii i Piotrka")
    
    with st.expander("➕ Szybkie dodawanie"):
        with st.form("add_prz"):
            col1, col2 = st.columns(2)
            osoba = col1.selectbox("Kto?", ["Natalia", "Piotrek", "Rodzina"])
            zrodlo = col2.text_input("Źródło (np. Pensja, Premia)")
            typ = col1.selectbox("Gdzie?", ["Konto", "Gotówka"])
            kwota = col2.number_input("Kwota", min_value=0.0)
            if st.form_submit_button("Dodaj"):
                sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d"), osoba, zrodlo, typ, kwota])
                st.rerun()

    df_p = load_df("Przychody")
    if not df_p.empty:
        st.info("💡 Możesz edytować komórki bezpośrednio w tabeli. Kliknij przycisk na dole, by zapisać.")
        ed_df = st.data_editor(df_p, num_rows="dynamic", use_container_width=True)
        if st.button("Zapisz zmiany w przychodach"):
            save_df("Przychody", ed_df)

elif menu == "💸 Wydatki & Koszty":
    st.title("💸 Koszty Stałe i Zmienne")
    df_w = load_df("Wydatki")
    
    tab1, tab2 = st.tabs(["Dodaj Nowy", "Lista i Edycja"])
    
    with tab1:
        with st.form("add_wyd"):
            n = st.text_input("Nazwa (Czynsz, Prąd, Biedronka...)")
            k = st.number_input("Kwota", min_value=0.0)
            t = st.selectbox("Rodzaj", ["Stały", "Zmienny"])
            kat = st.selectbox("Kategoria", ["Dom", "Jedzenie", "Transport", "Dzieci", "Przyjemności"])
            if st.form_submit_button("Zapisz wydatek"):
                sh.worksheet("Wydatki").append_row([datetime.now().strftime("%Y-%m-%d"), n, kat, t, k])
                st.rerun()
                
    with tab2:
        ed_w = st.data_editor(df_w, num_rows="dynamic", use_container_width=True)
        if st.button("Zapisz zmiany w wydatkach"):
            save_df("Wydatki", ed_w)

elif menu == "📅 Raty & Kredyty":
    st.title("📅 Harmonogram Spłat")
    df_r = load_df("Raty")
    
    st.warning("Pamiętaj o wpisywaniu daty spłaty, aby system mógł Ci o niej przypominać!")
    ed_r = st.data_editor(df_r, num_rows="dynamic", use_container_width=True)
    if st.button("Zaktualizuj bazę rat"):
        save_df("Raty", ed_r)
