import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

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

# --- PANCERNE POŁĄCZENIE ---
@st.cache_resource
def connect_to_gsheets():
    try:
        # Pobieramy dane jako słownik bezpośrednio z obiektu Secrets
        s = st.secrets["connections"]["gsheets"]
        
        # Ekstrakcja klucza i wymuszenie poprawnego formatowania \n
        # To naprawia błąd InvalidByte(64, 91)
        raw_key = s["private_key"]
        clean_key = raw_key.replace("\\n", "\n")
        
        # Jeśli klucz został wklejony z cudzysłowami na końcach, usuwamy je
        clean_key = clean_key.strip('"').strip("'")

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds_info = {
            "type": "service_account",
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": clean_key,
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
    
    in_sum = pd.to_numeric(df_prz["Kwota"], errors='coerce').sum() if not df_prz.empty else 0
    out_sum = pd.to_numeric(df_wyd["Kwota"], errors='coerce').sum() if not df_wyd.empty else 0
    save_sum = pd.to_numeric(df_osz["Suma"], errors='coerce').iloc[-1] if not df_osz.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Wpływy", f"{in_sum:,.2f} zł")
    c2.metric("Wydatki", f"{out_sum:,.2f} zł")
    c3.metric("Skarbonka", f"{save_sum:,.2f} zł")
    
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
                st.success("Dodano! 🍒")

elif view == "Raty":
    st.title("📅 Raty i Opłaty")
    st.dataframe(load_data("Raty"), use_container_width=True)

elif view == "Zakupy":
    st.title("📝 Lista Zakupów")
    df_zak = load_data("Zakupy")
    new_item = st.text_input("Co kupić?")
    if st.button("DODAJ"):
        if sh and new_item:
            sh.worksheet("Zakupy").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), new_item])
            st.rerun()
    if not df_zak.empty:
        for p in df_zak["Produkt"]:
            st.write(f"🔘 {p}")
