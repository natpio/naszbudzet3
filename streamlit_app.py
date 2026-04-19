import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Rodzinny Budżet PRO", page_icon="🏦", layout="wide")

# --- STYLIZACJA ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #1e3a8a; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    .css-1kyx001 { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    h1 { color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z GOOGLE SHEETS ---
@st.cache_resource
def init_connection():
    try:
        creds = st.secrets["connections"]["gsheets"]
        # Czyszczenie klucza prywatnego
        fixed_key = creds["private_key"].replace("\\n", "\n").strip()
        
        credentials = Credentials.from_service_account_info(
            {
                "type": "service_account",
                "project_id": creds.get("project_id", "budzet"),
                "private_key": fixed_key,
                "client_email": creds["client_email"],
                "token_uri": creds["token_uri"],
            },
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        gc = gspread.authorize(credentials)
        return gc.open_by_url(creds["spreadsheet"])
    except Exception as e:
        st.error(f"Błąd połączenia: {e}")
        return None

sh = init_connection()

# --- FUNKCJE POMOCNICZE ---
def load_df(sheet_name):
    try:
        data = sh.worksheet(sheet_name).get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def save_df(sheet_name, df):
    try:
        sheet = sh.worksheet(sheet_name)
        sheet.clear()
        # Zapisanie nagłówków i danych (obsługa pustych wartości)
        sheet.update([df.columns.values.tolist()] + df.fillna("").values.tolist())
        st.success(f"Zaktualizowano bazę: {sheet_name}!")
        st.balloons()
    except Exception as e:
        st.error(f"Błąd zapisu: {e}")

# --- AUTOMATYZACJA 800+ ---
def sync_recurring_benefits():
    df = load_df("Przychody")
    current_month = datetime.now().strftime("%Y-%m")
    
    # Jeśli arkusz jest pusty lub brakuje kolumn - przycisk inicjalizacji
    if df.empty or 'Źródło' not in df.columns or 'Data' not in df.columns:
        if st.sidebar.button("🚨 Zainicjuj 800+ w tym miesiącu"):
            sh.worksheet("Przychody").append_row([
                datetime.now().strftime("%Y-%m-%d"), "Rodzina", "800+", "Konto", 1600.0
            ])
            st.rerun()
        return

    # Sprawdzenie czy w tym miesiącu już dodano 800+
    mask = (df['Źródło'] == "800+") & (df['Data'].astype(str).str.startswith(current_month))
    
    if not mask.any():
        if st.sidebar.button("🚨 Dodaj 800+ za ten miesiąc"):
            sh.worksheet("Przychody").append_row([
                datetime.now().strftime("%Y-%m-%d"), "Rodzina", "800+", "Konto", 1600.0
            ])
            st.success("Dodano świadczenie 800+!")
            st.rerun()

# --- INTERFEJS ---
st.sidebar.title("💎 Panel Sterowania")
sync_recurring_benefits()
menu = st.sidebar.radio("Wybierz sekcję:", ["🏠 Dashboard", "💰 Przychody", "💸 Wydatki & Koszty", "📅 Raty & Kredyty"])

if menu == "🏠 Dashboard":
    st.title("📊 Przegląd Finansów")
    
    prz = load_df("Przychody")
    wyd = load_df("Wydatki")
    raty = load_df("Raty")
    
    # Konwersja na liczby dla pewności
    total_in = pd.to_numeric(prz["Kwota"], errors='coerce').sum() if not prz.empty else 0
    total_out = pd.to_numeric(wyd["Kwota"], errors='coerce').sum() if not wyd.empty else 0
    total_raty = pd.to_numeric(raty["Kwota raty"], errors='coerce').sum() if not raty.empty else 0
    
    zostaje = total_in - total_out - total_raty
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wszystkie Przychody", f"{total_in:,.2f} zł")
    c2.metric("Wszystkie Wydatki", f"{total_out:,.2f} zł")
    c3.metric("Suma Rat", f"{total_raty:,.2f} zł")
    c4.metric("Wolne Środki", f"{zostaje:,.2f} zł", delta=f"{zostaje:,.2f} zł")

    if not prz.empty:
        st.subheader("Podział przychodów na osoby")
        st.bar_chart(prz.groupby("Osoba")["Kwota"].sum())

elif menu == "💰 Przychody":
    st.title("💰 Zarobki Natalii i Piotrka")
    
    with st.expander("➕ Dodaj nowy przychód"):
        with st.form("form_p"):
            col1, col2 = st.columns(2)
            kto = col1.selectbox("Osoba", ["Natalia", "Piotrek", "Rodzina"])
            zrodlo = col2.text_input("Źródło (np. Pensja, Premia, Sprzedaż)")
            forma = col1.selectbox("Gdzie?", ["Konto", "Gotówka"])
            ile = col2.number_input("Kwota", min_value=0.0, step=100.0)
            if st.form_submit_button("Zapisz"):
                sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d"), kto, zrodlo, forma, ile])
                st.rerun()

    st.subheader("Baza Przychodów")
    df_p = load_df("Przychody")
    if not df_p.empty:
        st.write("Dwu-kliknij w komórkę, aby edytować. Zaznacz wiersz i naciśnij `Delete`, aby usunąć.")
        ed_p = st.data_editor(df_p, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zapisz zmiany w Przychodach"):
            save_df("Przychody", ed_p)

elif menu == "💸 Wydatki & Koszty":
    st.title("💸 Zarządzanie Wydatkami")
    
    with st.expander("➕ Szybkie dodawanie wydatku"):
        with st.form("form_w"):
            nazwa = st.text_input("Nazwa (np. Czynsz, Biedronka, Paliwo)")
            kwota = st.number_input("Kwota", min_value=0.0, step=10.0)
            rodzaj = st.selectbox("Rodzaj", ["Stały", "Zmienny"])
            kat = st.selectbox("Kategoria", ["Dom", "Jedzenie", "Transport", "Dzieci", "Przyjemności", "Inne"])
            if st.form_submit_button("Dodaj Wydatek"):
                sh.worksheet("Wydatki").append_row([datetime.now().strftime("%Y-%m-%d"), nazwa, kat, rodzaj, kwota])
                st.rerun()

    st.subheader("Baza Wydatków i Kosztów Stałych")
    df_w = load_df("Wydatki")
    if not df_w.empty:
        ed_w = st.data_editor(df_w, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zapisz zmiany w Wydatkach"):
            save_df("Wydatki", ed_w)

elif menu == "📅 Raty & Kredyty":
    st.title("📅 Harmonogram Rat i Zobowiązań")
    
    df_r = load_df("Raty")
    if df_r.empty:
        df_r = pd.DataFrame(columns=["Nazwa banku/kredytu", "Dzień płatności", "Kwota raty", "Pozostało do spłaty", "Data końcowa"])
    
    st.info("Wpisz wszystkie raty. Możesz edytować kwoty co miesiąc, jeśli się zmieniają.")
    ed_r = st.data_editor(df_r, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Zaktualizuj bazę rat"):
        save_df("Raty", ed_r)
