import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Budżet Domowy PRO", page_icon="📊", layout="wide")

# --- STYLIZACJA PRO ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    h1, h2 { color: #2c3e50; font-family: 'Helvetica Neue', sans-serif; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #3498db; }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE ---
@st.cache_resource
def init_connection():
    creds = st.secrets["connections"]["gsheets"]
    key = creds["private_key"].replace("\\n", "\n").strip()
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(
        {
            "client_email": creds["client_email"],
            "private_key": key,
            "token_uri": creds["token_uri"],
            "project_id": creds.get("project_id", "budzet"),
        },
        scopes=scopes
    )
    gc = gspread.authorize(credentials)
    return gc.open_by_url(creds["spreadsheet"])

sh = init_connection()

def load_data(sheet_name):
    if sh:
        data = sh.worksheet(sheet_name).get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame()
    return pd.DataFrame()

# Funkcja do nadpisywania całego arkusza (dzięki temu działa edycja i usuwanie)
def save_data(sheet_name, df):
    if sh:
        sheet = sh.worksheet(sheet_name)
        sheet.clear()
        # Zapisujemy nagłówki + dane
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.toast(f"✅ Zapisano zmiany w: {sheet_name}")

# --- MENU BOCZNE ---
with st.sidebar:
    st.markdown("## 📊 Panel Sterowania")
    view = st.radio("Wybierz moduł:", ["Dashboard", "Przychody", "Wydatki i Koszty Stałe", "Kredyty i Raty"])

# --- WIDOKI ---
if view == "Dashboard":
    st.title("📈 Podsumowanie Finansów")
    df_prz = load_data("Przychody")
    df_wyd = load_data("Wydatki")
    
    in_sum = pd.to_numeric(df_prz["Kwota"], errors='coerce').sum() if not df_prz.empty else 0
    out_sum = pd.to_numeric(df_wyd["Kwota"], errors='coerce').sum() if not df_wyd.empty else 0
    bilans = in_sum - out_sum
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Łączne Przychody", f"{in_sum:,.2f} zł")
    col2.metric("Łączne Wydatki", f"{out_sum:,.2f} zł")
    col3.metric("Bilans", f"{bilans:,.2f} zł", delta=f"{bilans:,.2f} zł")

elif view == "Przychody":
    st.title("💵 Zarządzanie Przychodami")
    
    # Szybkie dodawanie
    st.subheader("⚡ Szybkie akcje")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ Dodaj 800+ (Dzieci)"):
            sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d"), "Rodzina", "800+", "Konto", 1600.0])
            st.success("Dodano 1600 zł z 800+!")
            st.rerun()
            
    # Edytor danych w czasie rzeczywistym
    st.subheader("Edytuj / Usuń Przychody")
    df_prz = load_data("Przychody")
    if not df_prz.empty:
        # data_editor pozwala na edycję w komórkach i usuwanie wierszy
        edited_df = st.data_editor(df_prz, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zapisz zmiany w Przychodach"):
            save_data("Przychody", edited_df)

elif view == "Wydatki i Koszty Stałe":
    st.title("💳 Koszty i Wydatki")
    
    # Formularz szybkiego dodawania kosztów stałych/zmiennych
    with st.expander("➕ Dodaj nowy wydatek", expanded=False):
        with st.form("form_wyd"):
            nazwa = st.text_input("Nazwa (np. Czynsz, Biedronka)")
            kwota = st.number_input("Kwota", min_value=0.0)
            typ = st.selectbox("Typ", ["Stały", "Zmienny"])
            kat = st.selectbox("Kategoria", ["Dom", "Jedzenie", "Transport", "Dzieci", "Rozrywka", "Inne"])
            if st.form_submit_button("Dodaj Wydatek"):
                sh.worksheet("Wydatki").append_row([datetime.now().strftime("%Y-%m-%d"), nazwa, kat, typ, kwota])
                st.success("Dodano wydatek!")
                st.rerun()

    st.subheader("Baza Wydatków (Edycja i Usuwanie)")
    df_wyd = load_data("Wydatki")
    if not df_wyd.empty:
        edited_wyd = st.data_editor(df_wyd, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zapisz zmiany w Wydatkach"):
            save_data("Wydatki", edited_wyd)

elif view == "Kredyty i Raty":
    st.title("📅 Harmonogram Rat")
    st.info("Tutaj wpiszcie swoje stałe obciążenia ratalne. Możesz bezpośrednio w tabeli dodawać nowe wiersze.")
    
    df_raty = load_data("Raty")
    # Jeśli arkusz jest pusty, tworzymy pusty schemat, żeby data_editor zadziałał
    if df_raty.empty:
        df_raty = pd.DataFrame(columns=["Nazwa banku/kredytu", "Dzień płatności", "Kwota raty", "Pozostało do spłaty", "Data końcowa"])
        
    edited_raty = st.data_editor(df_raty, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Zapisz stan rat"):
        save_data("Raty", edited_raty)
