import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Retro Budget Manager", page_icon="💃", layout="centered")

# --- STYLIZACJA RETRO PIN-UP (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pacifico&family=Roboto:wght@400;700&display=swap');

    /* Główny kontener */
    .stApp {
        background-color: #fce4ec; /* Jasny róż */
        background-image: radial-gradient(#f06292 2px, transparent 2px);
        background-size: 30px 30px; /* Polka dots */
    }

    /* Nagłówki */
    h1, h2, h3 {
        font-family: 'Pacifico', cursive !important;
        color: #c2185b !important;
        text-shadow: 2px 2px #ffffff;
    }

    /* Karty i sekcje */
    .stButton>button {
        background-color: #d81b60 !important;
        color: white !important;
        border-radius: 20px !important;
        border: 2px solid #880e4f !important;
        font-family: 'Roboto', sans-serif;
        font-weight: bold;
        text-transform: uppercase;
    }

    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #ffffff !important;
        border: 2px solid #d81b60 !important;
        border-radius: 10px !important;
    }

    /* Side bar */
    [data-testid="stSidebar"] {
        background-color: #f06292 !important;
        border-right: 5px solid #c2185b;
    }

    /* Styl tabeli */
    .styled-table {
        background-color: white;
        border-radius: 10px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(sheet_name):
    return conn.read(worksheet=sheet_name)

# --- LOGIKA APLIKACJI ---
st.title("💃 Retro Budżet SQM")
st.markdown("### Zarządzaj finansami w stylu lat 60.")

menu = ["Dodaj Wydatek", "Dodaj Przychód", "Koszty Stałe i Raty", "Podsumowanie"]
choice = st.sidebar.selectbox("Nawigacja", menu)

if choice == "Dodaj Wydatek":
    st.subheader("📍 Nowy Wydatek")
    
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Data", datetime.now())
            name = st.text_input("Nazwa (co kupiono?)")
            amount = st.number_input("Kwota (PLN)", min_value=0.0, step=0.01)
        with col2:
            category = st.selectbox("Kategoria", ["Jedzenie", "Transport", "Dom", "Rozrywka", "Inne"])
            expense_type = st.selectbox("Typ", ["Zmienny", "Stały"])
        
        submit = st.form_submit_button("ZAPISZ W ARKUSZU")

        if submit:
            new_data = pd.DataFrame([{
                "Data i Godzina": date.strftime("%Y-%m-%d %H:%M:%S"),
                "Nazwa": name,
                "Kwota": amount,
                "Kategoria": category,
                "Typ": expense_type
            }])
            # Tutaj logika zapisu:
            existing_data = get_data("Wydatki")
            updated_df = pd.concat([existing_data, new_data], ignore_index=True)
            conn.update(worksheet="Wydatki", data=updated_df)
            st.success("Dodano! Wyglądasz dziś zjawiskowo! ✨")

elif choice == "Dodaj Przychód":
    st.subheader("💰 Nowy Przychód")
    
    with st.form("income_form"):
        date = st.date_input("Data", datetime.now())
        name = st.text_input("Nazwa (np. Wypłata, Premia)")
        amount = st.number_input("Kwota (PLN)", min_value=0.0, step=0.01)
        
        submit = st.form_submit_button("DODAJ DO SALDA")

        if submit:
            new_data = pd.DataFrame([{
                "Data i Godzina": date.strftime("%Y-%m-%d %H:%M:%S"),
                "Nazwa": name,
                "Kwota": amount
            }])
            existing_data = get_data("Przychody")
            updated_df = pd.concat([existing_data, new_data], ignore_index=True)
            conn.update(worksheet="Przychody", data=updated_df)
            st.success("Kasa się zgadza, kochanie! 💸")

elif choice == "Koszty Stałe i Raty":
    st.subheader("📅 Zobowiązania")
    
    tab1, tab2 = st.tabs(["Koszty Stałe", "Raty"])
    
    with tab1:
        df_stale = get_data("Koszty_Stale")
        st.table(df_stale)
        
    with tab2:
        df_raty = get_data("Raty")
        st.table(df_raty)

elif choice == "Podsumowanie":
    st.subheader("📊 Raport Finansowy")
    
    df_wydatki = get_data("Wydatki")
    df_przychody = get_data("Przychody")
    
    total_inc = df_przychody["Kwota"].sum()
    total_exp = df_wydatki["Kwota"].sum()
    balance = total_inc - total_exp
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Przychody", f"{total_inc} zł")
    col2.metric("Wydatki", f"{total_exp} zł")
    col3.metric("Saldo", f"{balance} zł", delta_color="normal")

    st.markdown("---")
    st.markdown("#### Ostatnie operacje")
    st.dataframe(df_wydatki.tail(10), use_container_width=True)

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.write("✉️ SQM Logistics Admin")
st.sidebar.image("https://www.freeiconspng.com/uploads/retro-pin-up-girl-png-10.png", width=150)
