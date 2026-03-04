import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Retro Domowy Budżet", page_icon="💄", layout="centered")

# --- STYLIZACJA RETRO PIN-UP ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pacifico&family=Special+Elite&display=swap');
    .stApp {
        background-color: #fce4ec;
        background-image: radial-gradient(#f06292 2px, transparent 2px);
        background-size: 35px 35px;
    }
    h1, h2, h3 {
        font-family: 'Pacifico', cursive !important;
        color: #d81b60 !important;
        text-shadow: 2px 2px #ffffff;
        text-align: center;
    }
    div.stButton > button {
        background-color: #d81b60 !important;
        color: white !important;
        border-radius: 25px !important;
        border: 3px solid #880e4f !important;
        font-family: 'Special Elite', cursive;
        font-size: 1.2rem;
        width: 100%;
        box-shadow: 4px 4px 0px #880e4f;
    }
    [data-testid="stSidebar"] {
        background-color: #f8bbd0 !important;
        border-right: 5px solid #d81b60;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        border: 2px solid #d81b60;
        box-shadow: 5px 5px 0px #f06292;
    }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE (SYSTEMOWE - GSPREAD) ---
@st.cache_resource
def get_google_sheet():
    try:
        # Pobieramy dane z Twojej sekcji [connections.gsheets] w Secrets
        s = st.secrets["connections"]["gsheets"]
        
        # Definiujemy zakresy uprawnień
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Budujemy poświadczenia dokładnie tak, jak wymaga tego Google
        credentials = Credentials.from_service_account_info(
            {
                "type": "service_account",
                "project_id": s["project_id"],
                "private_key_id": s["private_key_id"],
                "private_key": s["private_key"].replace("\\n", "\n"),
                "client_email": s["client_email"],
                "client_id": s["client_id"],
                "auth_uri": s["auth_uri"],
                "token_uri": s["token_uri"],
                "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
                "client_x509_cert_url": s["client_x509_cert_url"],
            },
            scopes=scopes
        )
        
        # Autoryzacja i otwarcie arkusza
        gc = gspread.authorize(credentials)
        return gc.open_by_url(s["spreadsheet"])
    except Exception as e:
        st.error(f"Krytyczny błąd połączenia: {e}")
        return None

# Inicjalizacja arkusza
sh = get_google_sheet()

def fetch_data(sheet_name):
    if sh:
        try:
            worksheet = sh.worksheet(sheet_name)
            return pd.DataFrame(worksheet.get_all_records())
        except Exception as e:
            st.warning(f"Arkusz '{sheet_name}' nie został znaleziony.")
            return pd.DataFrame()
    return pd.DataFrame()

# --- NAWIGACJA ---
with st.sidebar:
    st.markdown("# 💄 Menu")
    st.image("https://www.freeiconspng.com/uploads/retro-pin-up-girl-png-10.png", width=150)
    choice = st.radio("Sekcja:", ["Salon", "Wydatki", "Przychody", "Zobowiązania", "Lista Zakupów"])

# --- WIDOKI ---

if choice == "Salon":
    st.title("👗 Salon")
    
    df_wyd = fetch_data("Wydatki")
    df_prz = fetch_data("Przychody")
    df_osz = fetch_data("Oszczednosci")
    
    t_in = pd.to_numeric(df_prz["Kwota"], errors='coerce').sum() if not df_prz.empty else 0
    t_out = pd.to_numeric(df_wyd["Kwota"], errors='coerce').sum() if not df_wyd.empty else 0
    t_save = pd.to_numeric(df_osz["Suma"], errors='coerce').iloc[-1] if not df_osz.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Wpływy", f"{t_in:,.2f} zł")
    c2.metric("Wydatki", f"{t_out:,.2f} zł")
    c3.metric("Oszczędności", f"{t_save:,.2f} zł")

    st.markdown("### Ostatnie wpisy")
    st.dataframe(df_wyd.tail(10), use_container_width=True)

elif choice == "Wydatki":
    st.title("🛍️ Dodaj Wydatek")
    with st.form("exp_form", clear_on_submit=True):
        nazwa = st.text_input("Co kupiłaś?")
        kwota = st.number_input("Kwota (PLN)", min_value=0.0, step=0.01)
        kat = st.selectbox("Kategoria", ["Jedzenie", "Dom", "Transport", "Rozrywka", "Inne"])
        typ = st.selectbox("Typ", ["Zmienny", "Stały"])
        
        if st.form_submit_button("ZAPISZ"):
            if sh:
                try:
                    wks = sh.worksheet("Wydatki")
                    wks.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nazwa, kwota, kat, typ])
                    st.success("Zapisano! ✨")
                except Exception as e:
                    st.error(f"Błąd zapisu: {e}")

elif choice == "Przychody":
    st.title("💵 Dodaj Przychód")
    with st.form("inc_form", clear_on_submit=True):
        nazwa_p = st.text_input("Źródło")
        kwota_p = st.number_input("Kwota", min_value=0.0)
        if st.form_submit_button("DODAJ"):
            if sh:
                sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nazwa_p, kwota_p])
                st.success("Budżet zasiliły nowe środki! 🍒")

elif choice == "Zobowiązania":
    st.title("📅 Raty i Koszty")
    st.markdown("### Raty")
    st.dataframe(fetch_data("Raty"), use_container_width=True)
    st.markdown("### Koszty Stałe")
    st.dataframe(fetch_data("Koszty_Stale"), use_container_width=True)

elif choice == "Lista Zakupów":
    st.title("📝 Lista zakupów")
    df_zak = fetch_data("Zakupy")
    new_prod = st.text_input("Co dopisać?")
    if st.button("DODAJ"):
        if sh and new_prod:
            sh.worksheet("Zakupy").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), new_prod])
            st.rerun()
    
    if not df_zak.empty:
        for p in df_zak["Produkt"]:
            st.write(f"🔘 {p}")
