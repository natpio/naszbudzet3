import streamlit as st
from streamlit_gsheets import GSheetsConnection
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

# --- POŁĄCZENIE (PANCERNA INICJALIZACJA) ---
try:
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        # Tworzymy kopię roboczą danych z Secrets
        full_conf = dict(st.secrets.connections.gsheets)
        
        # 1. Wyciągamy URL arkusza (będzie potrzebny w read/update, nie w st.connection)
        SHEET_URL = full_conf.get("spreadsheet")
        
        # 2. Naprawiamy klucz prywatny (zamiana tekstowego \n na znak nowej linii)
        if "private_key" in full_conf:
            full_conf["private_key"] = full_conf["private_key"].replace("\\n", "\n")
        
        # 3. Usuwamy klucze, które GSheetsConnection._connect() odrzuca jako 'unexpected'
        # Biblioteka sama zbuduje z nich obiekt credentials, jeśli przekażesz je poprawnie
        cleaned_conf = {k: v for k, v in full_conf.items() if k not in ["spreadsheet", "type", "project_id"]}
        
        # Inicjalizacja połączenia
        conn = st.connection("gsheets", type=GSheetsConnection, **cleaned_conf)
    else:
        st.error("Błąd: Nie znaleziono [connections.gsheets] w Secrets!")
        st.stop()
except Exception as e:
    st.error(f"Błąd inicjalizacji: {e}")
    st.stop()

def fetch_data(sheet_name):
    try:
        # Używamy pobranego SHEET_URL przy każdym zapytaniu
        return conn.read(spreadsheet=SHEET_URL, worksheet=sheet_name, ttl=0)
    except Exception as e:
        st.warning(f"Brak dostępu do zakładki '{sheet_name}'. Sprawdź nazwy w Google Sheets.")
        return pd.DataFrame()

# --- NAWIGACJA ---
with st.sidebar:
    st.markdown("# 💄 Menu Retro")
    st.image("https://www.freeiconspng.com/uploads/retro-pin-up-girl-png-10.png", width=150)
    choice = st.radio("Sekcja:", ["Salon (Podsumowanie)", "Dodaj Wydatek", "Dodaj Przychód", "Zobowiązania", "Lista Zakupów"])

# --- WIDOKI ---

if choice == "Salon (Podsumowanie)":
    st.title("👗 Twój Budżetowy Salon")
    
    df_wyd = fetch_data("Wydatki")
    df_prz = fetch_data("Przychody")
    df_osz = fetch_data("Oszczednosci")
    
    # Przeliczanie sum
    total_in = pd.to_numeric(df_prz["Kwota"], errors='coerce').sum() if not df_prz.empty else 0
    total_out = pd.to_numeric(df_wyd["Kwota"], errors='coerce').sum() if not df_wyd.empty else 0
    total_savings = pd.to_numeric(df_osz["Suma"], errors='coerce').iloc[-1] if not df_osz.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Wpływy", f"{total_in:,.2f} zł")
    col2.metric("Wydatki", f"{total_out:,.2f} zł")
    col3.metric("Oszczędności", f"{total_savings:,.2f} zł")

    st.markdown("### 📸 Ostatnie wpisy")
    if not df_wyd.empty:
        st.dataframe(df_wyd.tail(10).iloc[::-1], use_container_width=True)

elif choice == "Dodaj Wydatek":
    st.title("🛍️ Nowy Paragon")
    with st.form("exp_form", clear_on_submit=True):
        nazwa = st.text_input("Co kupiłaś?")
        kwota = st.number_input("Kwota (PLN)", min_value=0.0, step=0.01)
        kat = st.selectbox("Kategoria", ["Jedzenie", "Dom", "Transport", "Rozrywka", "Inne"])
        typ = st.selectbox("Typ", ["Zmienny", "Stały"])
        
        if st.form_submit_button("ZAPISZ"):
            new_row = pd.DataFrame([{
                "Data i Godzina": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Nazwa": nazwa,
                "Kwota": kwota,
                "Kategoria": kat,
                "Typ": typ
            }])
            existing = fetch_data("Wydatki")
            updated = pd.concat([existing, new_row], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, worksheet="Wydatki", data=updated)
            st.success("Zapisano! Budżet pod kontrolą! ✨")

elif choice == "Dodaj Przychód":
    st.title("💵 Nowe Wpływy")
    with st.form("inc_form", clear_on_submit=True):
        nazwa_p = st.text_input("Źródło")
        kwota_p = st.number_input("Kwota (PLN)", min_value=0.0, step=0.01)
        
        if st.form_submit_button("DODAJ"):
            new_row_p = pd.DataFrame([{
                "Data i Godzina": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Nazwa": nazwa_p,
                "Kwota": kwota_p
            }])
            existing_p = fetch_data("Przychody")
            updated_p = pd.concat([existing_p, new_row_p], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, worksheet="Przychody", data=updated_p)
            st.success("Pieniądze dodane! 🍒")

elif choice == "Zobowiązania":
    st.title("📅 Twoje Raty i Koszty")
    st.markdown("### 💎 Raty")
    st.dataframe(fetch_data("Raty"), use_container_width=True)
    st.markdown("### 🏠 Koszty Stałe")
    st.dataframe(fetch_data("Koszty_Stale"), use_container_width=True)

elif choice == "Lista Zakupów":
    st.title("📝 Lista zakupów")
    df_zak = fetch_data("Zakupy")
    
    new_prod = st.text_input("Co dopisać?")
    if st.button("DODAJ DO LISTY"):
        if new_prod:
            new_row_z = pd.DataFrame([{"Data i Godzina": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Produkt": new_prod}])
            updated_z = pd.concat([df_zak, new_row_z], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, worksheet="Zakupy", data=updated_z)
            st.rerun()
    
    st.markdown("---")
    if not df_zak.empty:
        for prod in df_zak["Produkt"]:
            st.write(f"🔘 {prod}")
