import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Retro Budżet Domowy", page_icon="💃", layout="centered")

# --- STYLIZACJA RETRO PIN-UP (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pacifico&family=Special+Elite&display=swap');

    /* Tło - klasyczne różowe kropki retro */
    .stApp {
        background-color: #fce4ec;
        background-image: radial-gradient(#f06292 2px, transparent 2px);
        background-size: 35px 35px;
    }

    /* Nagłówki w stylu Pacifico */
    h1, h2, h3 {
        font-family: 'Pacifico', cursive !important;
        color: #d81b60 !important;
        text-shadow: 2px 2px #ffffff;
    }

    /* Przyciski */
    div.stButton > button {
        background-color: #d81b60 !important;
        color: white !important;
        border-radius: 25px !important;
        border: 3px solid #880e4f !important;
        font-family: 'Special Elite', cursive;
        height: 3em;
        width: 100%;
    }

    /* Karty danych */
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        border: 2px solid #d81b60;
        box-shadow: 5px 5px 0px #f06292;
    }

    /* Pasek boczny */
    [data-testid="stSidebar"] {
        background-color: #f8bbd0 !important;
        border-right: 5px solid #d81b60;
    }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z TWOIM ARKUSZEM ---
# Adres URL Twojego arkusza
URL = "https://docs.google.com/spreadsheets/d/1a54M9VdkosyLqRWQc67oeR5vir4B6D4HccZ9V8LGuR0/edit?usp=drivesdk"

conn = st.connection("gsheets", type=GSheetsConnection)

def fetch_data(sheet_name):
    # Czytamy dane z konkretnej zakładki
    return conn.read(spreadsheet=URL, worksheet=sheet_name)

# --- PANEL BOCZNY (NAWIGACJA) ---
with st.sidebar:
    st.markdown("# 💄 Menu Retro")
    st.image("https://www.freeiconspng.com/uploads/retro-pin-up-girl-png-10.png", width=150)
    choice = st.radio("Dokąd idziemy?", 
                      ["Strona Główna", "Wprowadź Wydatek", "Wprowadź Przychód", "Raty i Koszty Stałe", "Lista Zakupów"])
    st.markdown("---")
    st.write("Aplikacja Prywatna")

# --- LOGIKA APLIKACJI ---

if choice == "Strona Główna":
    st.title("👗 Twój Budżetowy Salon")
    
    # Pobieranie danych do podsumowania
    df_wydatki = fetch_data("Wydatki")
    df_przychody = fetch_data("Przychody")
    df_oszczednosci = fetch_data("Oszczednosci")

    suma_wydatkow = df_wydatki["Kwota"].sum()
    suma_przychodow = df_przychody["Kwota"].sum()
    stan_oszczednosci = df_oszczednosci["Suma"].iloc[-1] if not df_oszczednosci.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Wpływy", f"{suma_przychodow} zł")
    col2.metric("Wydatki", f"{suma_wydatkow} zł")
    col3.metric("Oszczędności", f"{stan_oszczednosci} zł")

    st.markdown("### 📸 Ostatnie operacje")
    st.dataframe(df_wydatki.tail(10), use_container_width=True)

elif choice == "Wprowadź Wydatek":
    st.title("🛍️ Nowy Paragon")
    
    with st.form("expense_form"):
        nazwa = st.text_input("Nazwa zakupu")
        kwota = st.number_input("Kwota (PLN)", min_value=0.0, step=0.01)
        kat = st.selectbox("Kategoria", ["Jedzenie", "Dom", "Transport", "Rozrywka", "Inne"])
        typ = st.selectbox("Typ", ["Zmienny", "Stały"])
        
        submit = st.form_submit_button("ZAPISZ")
        
        if submit:
            new_row = pd.DataFrame([{
                "Data i Godzina": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Nazwa": nazwa,
                "Kwota": kwota,
                "Kategoria": kat,
                "Typ": typ
            }])
            existing = fetch_data("Wydatki")
            updated = pd.concat([existing, new_row], ignore_index=True)
            conn.update(spreadsheet=URL, worksheet="Wydatki", data=updated)
            st.success("Dodano! Wyglądasz dziś fantastycznie! ✨")

elif choice == "Wprowadź Przychód":
    st.title("💵 Nowe Wpływy")
    
    with st.form("income_form"):
        nazwa_p = st.text_input("Źródło (np. Wypłata)")
        kwota_p = st.number_input("Kwota (PLN)", min_value=0.0, step=0.01)
        
        submit_p = st.form_submit_button("DODAJ DO BUDŻETU")
        
        if submit_p:
            new_row_p = pd.DataFrame([{
                "Data i Godzina": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Nazwa": nazwa_p,
                "Kwota": kwota_p
            }])
            existing_p = fetch_data("Przychody")
            updated_p = pd.concat([existing_p, new_row_p], ignore_index=True)
            conn.update(spreadsheet=URL, worksheet="Przychody", data=updated_p)
            st.success("Pieniądze są już na koncie! 🍒")

elif choice == "Raty i Koszty Stałe":
    st.title("📅 Zobowiązania")
    
    tab1, tab2 = st.tabs(["💎 Raty", "🏠 Koszty Stałe"])
    
    with tab1:
        st.dataframe(fetch_data("Raty"), use_container_width=True)
        
    with tab2:
        st.dataframe(fetch_data("Koszty_Stale"), use_container_width=True)

elif choice == "Lista Zakupów":
    st.title("📝 Do kupienia")
    df_zakupy = fetch_data("Zakupy")
    
    new_item = st.text_input("Co dopisać?")
    if st.button("DODAJ PRODUKT"):
        new_row_z = pd.DataFrame([{
            "Data i Godzina": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Produkt": new_item
        }])
        updated_z = pd.concat([df_zakupy, new_row_z], ignore_index=True)
        conn.update(spreadsheet=URL, worksheet="Zakupy", data=updated_z)
        st.rerun()
    
    st.markdown("---")
    for item in df_zakupy["Produkt"]:
        st.write(f"🔘 {item}")
