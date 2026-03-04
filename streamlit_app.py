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

# --- NAPRAWA POŁĄCZENIA ---
try:
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        # Tworzymy kopię sekretów, aby ich nie modyfikować bezpośrednio w st.secrets
        gsheets_secrets = dict(st.secrets.connections.gsheets)
        
        # 1. Naprawa znaku nowej linii w kluczu prywatnym
        if "private_key" in gsheets_secrets:
            gsheets_secrets["private_key"] = gsheets_secrets["private_key"].replace("\\n", "\n")
        
        # 2. KLUCZOWE: Usuwamy 'type' ze słownika, bo Streamlit sam go doda w st.connection
        if "type" in gsheets_secrets:
            del gsheets_secrets["type"]
            
        # Inicjalizacja połączenia z naprawionymi danymi
        conn = st.connection("gsheets", type=GSheetsConnection, **gsheets_secrets)
    else:
        st.error("Błąd: Nie znaleziono sekcji [connections.gsheets] w Secrets!")
        st.stop()
except Exception as e:
    st.error(f"Błąd inicjalizacji połączenia: {e}")
    st.stop()

def fetch_data(sheet_name):
    try:
        return conn.read(worksheet=sheet_name, ttl=0)
    except Exception as e:
        st.warning(f"Arkusz '{sheet_name}' nie jest dostępny. Sprawdź nazwy zakładek.")
        return pd.DataFrame()

# --- NAWIGACJA ---
with st.sidebar:
    st.markdown("# 💄 Menu Retro")
    st.image("https://www.freeiconspng.com/uploads/retro-pin-up-girl-png-10.png", width=150)
    choice = st.radio("Sekcja:", ["Salon (Podsumowanie)", "Wydatki", "Przychody", "Raty & Koszty Stałe", "Lista Zakupów"])

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
        st.dataframe(df_wyd.tail(10), use_container_width=True)

elif choice == "Wydatki":
    st.title("🛍️ Dodaj Wydatek")
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
            conn.update(worksheet="Wydatki", data=updated)
            st.success("Zapisano pomyślnie! ✨")

elif choice == "Przychody":
    st.title("💵 Dodaj Przychód")
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
            conn.update(worksheet="Przychody", data=updated_p)
            st.success("Wpływy zapisane! 🍒")

elif choice == "Raty & Koszty Stałe":
    st.title("📅 Zobowiązania")
    st.markdown("### 💎 Raty")
    st.dataframe(fetch_data("Raty"), use_container_width=True)
    st.markdown("### 🏠 Koszty Stałe")
    st.dataframe(fetch_data("Koszty_Stale"), use_container_width=True)

elif choice == "Lista Zakupów":
    st.title("📝 Lista zakupów")
    df_zak = fetch_data("Zakupy")
    
    new_prod = st.text_input("Dopisz do listy:")
    if st.button("DODAJ"):
        new_row_z = pd.DataFrame([{"Data i Godzina": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Produkt": new_prod}])
        updated_z = pd.concat([df_zak, new_row_z], ignore_index=True)
        conn.update(worksheet="Zakupy", data=updated_z)
        st.rerun()
    
    st.markdown("---")
    if not df_zak.empty:
        for prod in df_zak["Produkt"]:
            st.write(f"🔘 {prod}")
