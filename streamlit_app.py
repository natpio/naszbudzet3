import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Retro Budżet Domowy", page_icon="💃", layout="centered")

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

# --- POŁĄCZENIE ---
conn = st.connection("gsheets", type=GSheetsConnection)

def fetch_data(sheet_name):
    # ttl=0 zapewnia, że dane są zawsze pobierane na nowo po zapisie
    return conn.read(worksheet=sheet_name, ttl=0)

# --- NAWIGACJA ---
with st.sidebar:
    st.markdown("# 💄 Retro Menu")
    st.image("https://www.freeiconspng.com/uploads/retro-pin-up-girl-png-10.png", width=150)
    choice = st.radio("Sekcja:", ["Salon (Podsumowanie)", "Wydatki", "Przychody", "Raty & Koszty Stałe", "Lista Zakupów"])

# --- WIDOKI ---

if choice == "Salon (Podsumowanie)":
    st.title("👗 Twój Budżetowy Salon")
    
    df_wyd = fetch_data("Wydatki")
    df_prz = fetch_data("Przychody")
    
    total_in = pd.to_numeric(df_prz["Kwota"], errors='coerce').sum()
    total_out = pd.to_numeric(df_wyd["Kwota"], errors='coerce').sum()
    bilans = total_in - total_out

    c1, c2, c3 = st.columns(3)
    c1.metric("Wpływy", f"{total_in:,.2f} zł")
    c2.metric("Wydatki", f"{total_out:,.2f} zł")
    c3.metric("Do dyspozycji", f"{bilans:,.2f} zł")

    st.markdown("### 📸 Ostatnie wpisy")
    st.dataframe(df_wyd.tail(10).sort_values(by="Data i Godzina", ascending=False), use_container_width=True)

elif choice == "Wydatki":
    st.title("🛍️ Dodaj Wydatek")
    with st.form("exp_form", clear_on_submit=True):
        nazwa = st.text_input("Nazwa zakupu")
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
            st.success("Dodano do dziennika! ✨")

elif choice == "Przychody":
    st.title("💵 Dodaj Przychód")
    with st.form("inc_form", clear_on_submit=True):
        nazwa_p = st.text_input("Źródło przychodu")
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
            st.success("Budżet zasiliły nowe środki! 🍒")

elif choice == "Raty & Koszty Stałe":
    st.title("📅 Zobowiązania")
    colA, colB = st.columns(2)
    with colA:
        st.markdown("### 💎 Raty")
        st.dataframe(fetch_data("Raty"))
    with colB:
        st.markdown("### 🏠 Stałe")
        st.dataframe(fetch_data("Koszty_Stale"))

elif choice == "Lista Zakupów":
    st.title("📝 Lista zakupów")
    df_zak = fetch_data("Zakupy")
    
    new_prod = st.text_input("Dopisz produkt:")
    if st.button("DODAJ DO LISTY"):
        new_row_z = pd.DataFrame([{"Data i Godzina": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Produkt": new_prod}])
        updated_z = pd.concat([df_zak, new_row_z], ignore_index=True)
        conn.update(worksheet="Zakupy", data=updated_z)
        st.rerun()
    
    st.markdown("---")
    for prod in df_zak["Produkt"]:
        st.write(f"🔘 {prod}")
