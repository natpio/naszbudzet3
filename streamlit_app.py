import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Retro Domowy Budżet", page_icon="💄", layout="centered")

# --- STYLIZACJA RETRO PIN-UP (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pacifico&family=Special+Elite&family=Roboto:wght@400;700&display=swap');

    /* Tło - klasyczne różowe kropki retro */
    .stApp {
        background-color: #fce4ec;
        background-image: radial-gradient(#f06292 2px, transparent 2px);
        background-size: 40px 40px;
    }

    /* Nagłówki */
    h1, h2, h3 {
        font-family: 'Pacifico', cursive !important;
        color: #d81b60 !important;
        text-shadow: 2px 2px #ffffff;
        text-align: center;
    }

    /* Pasek boczny */
    [data-testid="stSidebar"] {
        background-color: #f8bbd0 !important;
        border-right: 5px solid #d81b60;
    }

    /* Przyciski w stylu lat 60. */
    div.stButton > button {
        background-color: #d81b60 !important;
        color: white !important;
        font-family: 'Special Elite', cursive !important;
        font-size: 1.2rem !important;
        border-radius: 30px !important;
        border: 3px solid #880e4f !important;
        box-shadow: 4px 4px 0px #880e4f;
        width: 100%;
        height: 3em;
        transition: 0.3s;
    }

    div.stButton > button:hover {
        background-color: #ad1457 !important;
        transform: translateY(-2px);
    }

    /* Karty z danymi (Metric) */
    [data-testid="stMetricValue"] {
        font-family: 'Special Elite', cursive !important;
        color: #c2185b !important;
    }

    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 20px;
        border: 2px solid #d81b60;
        box-shadow: 6px 6px 0px #f06292;
    }

    /* Styl tabel */
    .stDataFrame {
        background-color: white;
        border-radius: 10px;
        border: 2px solid #d81b60;
    }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z ARKUSZEM ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Problem z połączeniem. Sprawdź formatowanie klucza w Secrets.")
    st.stop()

def fetch_data(sheet_name):
    try:
        # ttl=0 wyłącza cache, by widzieć zmiany natychmiast po zapisie
        return conn.read(worksheet=sheet_name, ttl=0)
    except Exception as e:
        st.warning(f"Nie znaleziono arkusza: {sheet_name}. Upewnij się, że nazwa zakładki w Google Sheets jest identyczna.")
        return pd.DataFrame()

# --- PANEL BOCZNY (NAWIGACJA) ---
with st.sidebar:
    st.markdown("# 💄 Menu")
    st.image("https://www.freeiconspng.com/uploads/retro-pin-up-girl-png-10.png", width=180)
    st.markdown("---")
    choice = st.radio("Dokąd idziemy, kochanie?", 
                      ["Salon (Podsumowanie)", "Wprowadź Wydatek", "Wprowadź Przychód", "Raty & Koszty Stałe", "Lista Zakupów"])
    st.markdown("---")
    st.write("✨ Prywatny Budżet Retro")

# --- LOGIKA PANELI ---

if choice == "Salon (Podsumowanie)":
    st.title("👗 Twój Budżetowy Salon")
    
    df_wyd = fetch_data("Wydatki")
    df_prz = fetch_data("Przychody")
    df_osz = fetch_data("Oszczednosci")

    # Obliczenia z konwersją na liczby
    total_in = pd.to_numeric(df_prz["Kwota"], errors='coerce').sum() if not df_prz.empty else 0
    total_out = pd.to_numeric(df_wyd["Kwota"], errors='coerce').sum() if not df_wyd.empty else 0
    total_savings = pd.to_numeric(df_osz["Suma"], errors='coerce').iloc[-1] if not df_osz.empty else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Wpływy", f"{total_in:,.2f} zł")
    c2.metric("Wydatki", f"{total_out:,.2f} zł")
    c3.metric("Oszczędności", f"{total_savings:,.2f} zł")

    st.markdown("### 📸 Ostatnie Wydatki")
    if not df_wyd.empty:
        st.dataframe(df_wyd.tail(8).sort_values(by="Data i Godzina", ascending=False), use_container_width=True)
    else:
        st.info("Brak wpisów w arkuszu 'Wydatki'.")

elif choice == "Wprowadź Wydatek":
    st.title("🛍️ Nowy Paragon")
    with st.form("exp_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nazwa = st.text_input("Co kupiono?")
            kwota = st.number_input("Kwota (PLN)", min_value=0.0, step=0.01)
        with col2:
            kat = st.selectbox("Kategoria", ["Jedzenie", "Dom", "Transport", "Rozrywka", "Inne"])
            typ = st.selectbox("Typ", ["Zmienny", "Stały"])
        
        if st.form_submit_button("ZAPISZ W DZIENNIKU"):
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
            st.success("Zapisano! Jesteś bardzo rozsądna! ✨")

elif choice == "Wprowadź Przychód":
    st.title("💵 Nowe Wpływy")
    with st.form("inc_form", clear_on_submit=True):
        nazwa_p = st.text_input("Źródło przychodu")
        kwota_p = st.number_input("Kwota (PLN)", min_value=0.0, step=0.01)
        
        if st.form_submit_button("DODAJ DO BUDŻETU"):
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
    st.title("📅 Twoje Zobowiązania")
    tab1, tab2 = st.tabs(["💎 Raty", "🏠 Koszty Stałe"])
    
    with tab1:
        df_raty = fetch_data("Raty")
        st.dataframe(df_raty, use_container_width=True)
        
    with tab2:
        df_stale = fetch_data("Koszty_Stale")
        st.dataframe(df_stale, use_container_width=True)

elif choice == "Lista Zakupów":
    st.title("📝 Lista zakupów")
    df_zak = fetch_data("Zakupy")
    
    new_prod = st.text_input("Co dopisać do listy?")
    if st.button("DODAJ"):
        if new_prod:
            new_row_z = pd.DataFrame([{
                "Data i Godzina": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                "Produkt": new_prod
            }])
            updated_z = pd.concat([df_zak, new_row_z], ignore_index=True)
            conn.update(worksheet="Zakupy", data=updated_z)
            st.rerun()
    
    st.markdown("---")
    if not df_zak.empty:
        for p in df_zak["Produkt"]:
            st.write(f"🔘 {p}")
