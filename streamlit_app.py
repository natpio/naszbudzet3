import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Retro Domowy Budżet", page_icon="💄", layout="centered")

# --- STYLIZACJA RETRO PIN-UP ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pacifico&family=Special+Elite&family=Roboto:wght@400;700&display=swap');

    /* Tło całej strony - różowe kropki */
    .stApp {
        background-color: #fce4ec;
        background-image: radial-gradient(#f06292 2px, transparent 2px);
        background-size: 40px 40px;
    }

    /* Nagłówki retro */
    h1, h2, h3 {
        font-family: 'Pacifico', cursive !important;
        color: #d81b60 !important;
        text-shadow: 2px 2px #ffffff;
        text-align: center;
    }

    /* Karty i Formularze */
    div.stButton > button {
        background-color: #d81b60 !important;
        color: white !important;
        font-family: 'Special Elite', cursive !important;
        font-size: 20px !important;
        border-radius: 50px !important;
        border: 3px solid #880e4f !important;
        width: 100%;
        transition: 0.3s;
    }
    
    div.stButton > button:hover {
        background-color: #ad1457 !important;
        transform: scale(1.02);
    }

    /* Pola input */
    input, select, textarea {
        background-color: #fff !important;
        border: 2px solid #d81b60 !important;
    }

    /* Pasek boczny */
    [data-testid="stSidebar"] {
        background-color: #f8bbd0 !important;
        border-right: 4px solid #d81b60;
    }

    /* Styl tabel */
    .stDataFrame {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 15px;
        border: 2px solid #d81b60;
    }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z GOOGLE SHEETS ---
# Musisz mieć skonfigurowane secrets w Streamlit dla GSheetsConnection
conn = st.connection("gsheets", type=GSheetsConnection)

def load_sheet(name):
    return conn.read(worksheet=name)

# --- MENU BOCZNE ---
with st.sidebar:
    st.markdown("## ✨ Retro Menu")
    # Link do obrazka pin-up dla klimatu
    st.image("https://www.pinup-fashion.de/wp-content/uploads/2012/10/pinup-girl-vintage.png", width=150)
    menu = ["Panel Główny", "Wydatki", "Przychody", "Raty & Koszty Stałe", "Lista Zakupów"]
    choice = st.selectbox("Wybierz sekcję:", menu)
    st.markdown("---")
    st.info("Aplikacja Budżetowa - Styl Retro 60s")

# --- LOGIKA PANELI ---

if choice == "Panel Główny":
    st.title("👗 Twój Budżetowy Salon")
    
    # Załadowanie danych do podsumowania
    df_wydatki = load_sheet("Wydatki")
    df_przychody = load_sheet("Przychody")
    df_oszczednosci = load_sheet("Oszczednosci")

    total_in = df_przychody["Kwota"].sum()
    total_out = df_wydatki["Kwota"].sum()
    savings = df_oszczednosci["Suma"].iloc[0] if not df_oszczednosci.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Wpływy", f"{total_in:,.2f} zł".replace(",", " "))
    c2.metric("Wydatki", f"{total_out:,.2f} zł".replace(",", " "))
    c3.metric("Oszczędności", f"{savings:,.2f} zł".replace(",", " "))

    st.markdown("### 📸 Ostatnie Wydatki")
    st.dataframe(df_wydatki.tail(10).sort_values(by="Data i Godzina", ascending=False), use_container_width=True)

elif choice == "Wydatki":
    st.title("🛍️ Rejestr Wydatków")
    
    with st.form("expense_form", clear_on_submit=True):
        st.markdown("#### Dodaj nowy paragon")
        col1, col2 = st.columns(2)
        with col1:
            nazwa = st.text_input("Co kupiono?")
            kwota = st.number_input("Ile wydano? (PLN)", min_value=0.0, step=0.01)
        with col2:
            kat = st.selectbox("Kategoria", ["Jedzenie", "Dom", "Transport", "Rozrywka", "Inne"])
            typ = st.selectbox("Typ", ["Zmienny", "Stały"])
        
        submitted = st.form_submit_button("ZAPISZ W DZIENNIKU")
        
        if submitted:
            new_row = pd.DataFrame([{
                "Data i Godzina": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Nazwa": nazwa,
                "Kwota": kwota,
                "Kategoria": kat,
                "Typ": typ
            }])
            existing = load_sheet("Wydatki")
            updated = pd.concat([existing, new_row], ignore_index=True)
            conn.update(worksheet="Wydatki", data=updated)
            st.balloons()
            st.success("Zapisano! Jesteś bardzo oszczędna! ✨")

elif choice == "Przychody":
    st.title("💵 Twoje Przychody")
    
    with st.form("income_form", clear_on_submit=True):
        nazwa_p = st.text_input("Źródło przychodu")
        kwota_p = st.number_input("Kwota (PLN)", min_value=0.0, step=0.01)
        
        submitted_p = st.form_submit_button("DODAJ DO SKARBONKI")
        
        if submitted_p:
            new_row_p = pd.DataFrame([{
                "Data i Godzina": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Nazwa": nazwa_p,
                "Kwota": kwota_p
            }])
            existing_p = load_sheet("Przychody")
            updated_p = pd.concat([existing_p, new_row_p], ignore_index=True)
            conn.update(worksheet="Przychody", data=updated_p)
            st.success("Pieniądze wpłynęły! Czas na zakupy? 💄")

elif choice == "Raty & Koszty Stałe":
    st.title("📅 Zobowiązania")
    
    tab1, tab2 = st.tabs(["💎 Aktualne Raty", "🏠 Koszty Stałe"])
    
    with tab1:
        df_raty = load_sheet("Raty")
        # Formatowanie daty dla czytelności
        st.dataframe(df_raty, use_container_width=True)
        
    with tab2:
        df_stale = load_sheet("Koszty_Stale")
        st.dataframe(df_stale, use_container_width=True)

elif choice == "Lista Zakupów":
    st.title("📝 Lista do kupienia")
    df_zakupy = load_sheet("Zakupy")
    
    new_item = st.text_input("Dodaj produkt do listy:")
    if st.button("DODAJ"):
        new_row_z = pd.DataFrame([{
            "Data i Godzina": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Produkt": new_item
        }])
        updated_z = pd.concat([df_zakupy, new_row_z], ignore_index=True)
        conn.update(worksheet="Zakupy", data=updated_z)
        st.rerun()

    st.markdown("---")
    for index, row in df_zakupy.iterrows():
        st.write(f"◽ {row['Produkt']}")
