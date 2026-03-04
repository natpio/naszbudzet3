import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import io

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Retro Budżet Domowy", page_icon="💄", layout="centered")

# --- STYLIZACJA RETRO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pacifico&family=Special+Elite&display=swap');
    .stApp { background-color: #fce4ec; background-image: radial-gradient(#f06292 2px, transparent 2px); background-size: 35px 35px; }
    h1, h2, h3 { font-family: 'Pacifico', cursive !important; color: #d81b60 !important; text-align: center; }
    div.stButton > button {
        background-color: #d81b60 !important; color: white !important;
        border-radius: 25px !important; font-family: 'Special Elite', cursive;
        width: 100%; box-shadow: 4px 4px 0px #880e4f;
    }
    .stMetric { background-color: white; padding: 15px; border-radius: 15px; border: 2px solid #d81b60; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJA NAPRAWCZA DLA KLUCZA (ULTRA AGRESYWNA) ---
def fix_pem_format(key_string):
    if not key_string:
        return None
    
    # 1. Usuwamy znaki spoza zakresu ASCII (to one powodują błąd InvalidByte)
    clean_ascii = "".join(char for char in key_string if ord(char) < 128)
    
    # 2. Standaryzujemy znaki nowej linii
    clean_lines = clean_ascii.replace("\\n", "\n").splitlines()
    
    # 3. Czyścimy każdą linię z białych znaków i odrzucamy puste
    processed_lines = [line.strip() for line in clean_lines if line.strip()]
    
    # 4. Składamy w czysty format PEM
    return "\n".join(processed_lines)

# --- POŁĄCZENIE Z GOOGLE ---
@st.cache_resource
def connect_to_gsheets():
    try:
        s = st.secrets["connections"]["gsheets"]
        
        # Naprawa klucza przed wysłaniem do Google
        final_key = fix_pem_format(s["private_key"])
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds_info = {
            "type": "service_account",
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": final_key,
            "client_email": s["client_email"],
            "client_id": s["client_id"],
            "auth_uri": s["auth_uri"],
            "token_uri": s["token_uri"],
            "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
            "client_x509_cert_url": s["client_x509_cert_url"],
        }
        
        credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
        gc = gspread.authorize(credentials)
        return gc.open_by_url(s["spreadsheet"])
    except Exception as e:
        st.error(f"❌ Krytyczny błąd autoryzacji: {e}")
        return None

sh = connect_to_gsheets()

def load_data(name):
    if sh:
        try:
            return pd.DataFrame(sh.worksheet(name).get_all_records())
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# --- INTERFEJS ---
with st.sidebar:
    st.markdown("# 💄 Menu")
    view = st.radio("Wybierz:", ["Podsumowanie", "Wydatki", "Przychody", "Raty", "Zakupy"])

if view == "Podsumowanie":
    st.title("👗 Salon Budżetowy")
    df_wyd = load_data("Wydatki")
    df_prz = load_data("Przychody")
    df_osz = load_data("Oszczednosci")
    
    # Prosta analityka
    in_sum = pd.to_numeric(df_prz["Kwota"], errors='coerce').sum() if not df_prz.empty else 0
    out_sum = pd.to_numeric(df_wyd["Kwota"], errors='coerce').sum() if not df_wyd.empty else 0
    save_sum = pd.to_numeric(df_osz["Suma"], errors='coerce').iloc[-1] if not df_osz.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Wpływy", f"{in_sum:,.2f} zł")
    col2.metric("Wydatki", f"{out_sum:,.2f} zł")
    col3.metric("Skarbonka", f"{save_sum:,.2f} zł")
    
    st.markdown("### Ostatnie operacje")
    st.dataframe(df_wyd.tail(10), use_container_width=True)

elif view == "Wydatki":
    st.title("🛍️ Dodaj Wydatek")
    with st.form("form_exp", clear_on_submit=True):
        item = st.text_input("Nazwa")
        price = st.number_input("Kwota", min_value=0.0)
        cat = st.selectbox("Kat.", ["Jedzenie", "Dom", "Transport", "Rozrywka", "Inne"])
        if st.form_submit_button("DODAJ"):
            if sh:
                sh.worksheet("Wydatki").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), item, price, cat, "Zmienny"])
                st.success("Zapisano! ✨")

elif view == "Przychody":
    st.title("💵 Dodaj Przychód")
    with st.form("form_inc", clear_on_submit=True):
        source = st.text_input("Źródło")
        amount = st.number_input("Kwota", min_value=0.0)
        if st.form_submit_button("ZAPISZ"):
            if sh:
                sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), source, amount])
                st.success("Dodano do budżetu! 🍒")

elif view == "Raty":
    st.title("📅 Raty i Opłaty")
    st.dataframe(load_data("Raty"), use_container_width=True)
    st.dataframe(load_data("Koszty_Stale"), use_container_width=True)

elif view == "Zakupy":
    st.title("📝 Lista Zakupów")
    df_zak = load_data("Zakupy")
    new_item = st.text_input("Co kupić?")
    if st.button("DODAJ DO LISTY"):
        if sh and new_item:
            sh.worksheet("Zakupy").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), new_item])
            st.rerun()
    if not df_zak.empty:
        for p in df_zak["Produkt"]:
            st.write(f"🔘 {p}")
