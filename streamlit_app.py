import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Retro Budżet", page_icon="💄", layout="centered")

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

# --- FUNKCJA NAPRAWCZA DLA KLUCZA ---
def get_clean_key(raw_key):
    # Zamień tekstowe \n na rzeczywiste znaki nowej linii
    key = raw_key.replace("\\n", "\n")
    # Usuń ewentualne spacje i cudzysłowy, które Streamlit mógł dodać przy parsowaniu TOML
    lines = key.split("\n")
    clean_lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(clean_lines)

# --- POŁĄCZENIE ---
@st.cache_resource
def init_connection():
    try:
        # Pobieramy sekcję gsheets jako słownik
        creds = st.secrets["connections"]["gsheets"]
        
        # Kluczowe: ręczne wyczyszczenie klucza przed wysłaniem do biblioteki google-auth
        fixed_key = get_clean_key(creds["private_key"])
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Budujemy obiekt poświadczeń od zera
        credentials = Credentials.from_service_account_info(
            {
                "type": "service_account",
                "project_id": creds["project_id"],
                "private_key_id": creds["private_key_id"],
                "private_key": fixed_key,
                "client_email": creds["client_email"],
                "client_id": creds["client_id"],
                "auth_uri": creds["auth_uri"],
                "token_uri": creds["token_uri"],
                "auth_provider_x509_cert_url": creds["auth_provider_x509_cert_url"],
                "client_x509_cert_url": creds["client_x509_cert_url"],
            },
            scopes=scopes
        )
        
        gc = gspread.authorize(credentials)
        return gc.open_by_url(creds["spreadsheet"])
    except Exception as e:
        st.error(f"❌ Krytyczny błąd autoryzacji: {e}")
        return None

sh = init_connection()

def load_data(sheet_name):
    if sh:
        try:
            return pd.DataFrame(sh.worksheet(sheet_name).get_all_records())
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# --- INTERFEJS ---
with st.sidebar:
    st.markdown("# 💄 Menu")
    view = st.radio("Sekcja:", ["Salon", "Wydatki", "Przychody", "Raty", "Zakupy"])

if view == "Salon":
    st.title("👗 Salon")
    df_wyd = load_data("Wydatki")
    df_prz = load_data("Przychody")
    df_osz = load_data("Oszczednosci")
    
    in_sum = pd.to_numeric(df_prz["Kwota"], errors='coerce').sum() if not df_prz.empty else 0
    out_sum = pd.to_numeric(df_wyd["Kwota"], errors='coerce').sum() if not df_wyd.empty else 0
    
    col1, col2 = st.columns(2)
    col1.metric("Wpływy", f"{in_sum:,.2f} zł")
    col2.metric("Wydatki", f"{out_sum:,.2f} zł")
    st.dataframe(df_wyd.tail(10), use_container_width=True)

elif view == "Wydatki":
    st.title("🛍️ Wydatek")
    with st.form("f1", clear_on_submit=True):
        n = st.text_input("Nazwa")
        k = st.number_input("Kwota", min_value=0.0)
        cat = st.selectbox("Kat.", ["Jedzenie", "Dom", "Transport", "Rozrywka", "Inne"])
        if st.form_submit_button("ZAPISZ"):
            if sh:
                sh.worksheet("Wydatki").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), n, k, cat, "Zmienny"])
                st.success("Zapisano! ✨")

elif view == "Przychody":
    st.title("💵 Przychód")
    with st.form("f2", clear_on_submit=True):
        s = st.text_input("Źródło")
        a = st.number_input("Kwota", min_value=0.0)
        if st.form_submit_button("DODAJ"):
            if sh:
                sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), s, a])
                st.success("Dodano! 🍒")

elif view == "Raty":
    st.title("📅 Raty")
    st.dataframe(load_data("Raty"), use_container_width=True)

elif view == "Zakupy":
    st.title("📝 Lista")
    df_zak = load_data("Zakupy")
    new = st.text_input("Co kupić?")
    if st.button("DODAJ"):
        if sh and new:
            sh.worksheet("Zakupy").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), new])
            st.rerun()
    if not df_zak.empty:
        for p in df_zak["Produkt"]:
            st.write(f"🔘 {p}")
