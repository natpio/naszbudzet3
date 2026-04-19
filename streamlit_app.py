import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import calendar

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Nasz Budżet PRO", page_icon="🏦", layout="wide")

# --- STYLIZACJA UI ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    div[data-testid="metric-container"] {
        background: white; border: 1px solid #e2e8f0; padding: 20px; border-radius: 16px;
    }
    .hero-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: white; padding: 32px; border-radius: 24px; text-align: center;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }
    .hero-card h2 { color: #f8fafc !important; font-size: 3.5rem !important; margin: 10px 0; }
    
    .stButton>button { border-radius: 12px; font-weight: 600; transition: all 0.2s; }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE ---
@st.cache_resource
def init_connection():
    try:
        creds = st.secrets["connections"]["gsheets"]
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
        return gspread.authorize(credentials).open_by_url(creds["spreadsheet"])
    except Exception as e:
        st.error(f"Błąd połączenia: {e}")
        return None

sh = init_connection()

# --- FUNKCJE BAZY ---
def load_df(sheet_name):
    try:
        data = sh.worksheet(sheet_name).get_all_records()
        df = pd.DataFrame(data)
        # Upewniamy się, że Data to zawsze poprawny format czasu, aby uniknąć błędów
        if not df.empty and 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        return df
    except: 
        return pd.DataFrame()

def save_df(sheet_name, df):
    sheet = sh.worksheet(sheet_name)
    sheet.clear()
    df_save = df.copy()
    if 'Data' in df_save.columns:
        df_save['Data'] = df_save['Data'].dt.strftime('%Y-%m-%d %H:%M:%S')
    sheet.update([df_save.columns.values.tolist()] + df_save.fillna("").values.tolist())
    st.toast(f"✅ Zaktualizowano: {sheet_name}")

# --- NAWIGACJA BOCZNA ---
st.sidebar.title("🏦 Menu Główne")
miesiące = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
wybrany_m = st.sidebar.selectbox("Miesiąc", miesiące, index=datetime.now().month - 1)
wybrany_rok = st.sidebar.selectbox("Rok", [2024, 2025, 2026], index=2)

m_idx = miesiące.index(wybrany_m) + 1
selected_date = date(wybrany_rok, m_idx, 1)

st.sidebar.markdown("---")
menu = st.sidebar.radio("Nawigacja", ["🏠 Kokpit", "🛒 Wydatki Codzienne", "🗓️ Stałe Zobowiązania", "📥 Przychody", "🐷 Oszczędności"])

# --- WIDOKI ---
if menu == "🏠 Kokpit":
    st.title(f"Analiza: {wybrany_m} {wybrany_rok}")
    
    prz = load_df("Przychody")
    wyd_c = load_df("Wydatki") # Tylko wydatki codzienne
    zob = load_df("Zobowiazania") # Subskrypcje, Raty, Stałe opłaty
    osz = load_df("Oszczednosci")
    
    # Filtracja danych dla wybranego miesiąca (bezpieczna za pomocą tekstowego strftime)
    m_str = selected_date.strftime("%Y-%m")
    prz_m = prz[prz['Data'].dt.strftime("%Y-%m") == m_str] if not prz.empty else pd.DataFrame()
    wyd_m = wyd_c[wyd_c['Data'].dt.strftime("%Y-%m") == m_str] if not wyd_c.empty else pd.DataFrame()
    osz_m = osz[osz['Data'].dt.strftime("%Y-%m") == m_str] if not osz.empty else pd.DataFrame()
    
    # Podsumowanie liczbowe
    s_prz = prz_m['Kwota'].sum() if not prz_m.empty else 0
    s_codzienne = wyd_m['Kwota'].sum() if not wyd_m.empty else 0
    s_zobowiazania = zob['Kwota'].sum() if not zob.empty else 0
    w_osz = osz_m[osz_m['Akcja'] == 'Wpłata']['Kwota'].sum() if not osz_m.empty and 'Akcja' in osz_m.columns else 0
    
    # Kasa na życie (Wpływy z danego miesiąca MINUS wszystkie obciążenia i wpłaty na oszczędności)
    wolne = s_prz - s_codzienne - s_zobowiazania - w_osz
    
    # Dniówka (Licznik przetrwania)
    ostatni_dzien = calendar.monthrange(wybrany_rok, m_idx)[1]
    dzis = date.today()
    if dzis.month == m_idx and dzis.year == wybrany_rok:
        pozostalo_dni = ostatni_dzien - dzis.day + 1
    elif selected_date < dzis:
        pozostalo_dni = 0 # Ten miesiąc już minął
    else:
        pozostalo_dni = ostatni_dzien
        
    dniowka = wolne / pozostalo_dni if pozostalo_dni > 0 and wolne > 0 else 0

    c_h1, c_h2 = st.columns(2)
    with c_h1:
        st.markdown(f"<div class='hero-card'><p>Zostało na życie w tym miesiącu</p><h2>{wolne:,.2f} zł</h2></div>", unsafe_allow_html=True)
    with c_h2:
        bg_color = "linear-gradient(135deg, #059669 0%, #10b981 100%)" if pozostalo_dni > 0 else "linear-gradient(135deg, #64748b 0%, #475569 100%)"
        st.markdown(f"<div class='hero-card' style='background:{bg_color}'><p>Budżet dzienny (przez {pozostalo_dni} dni)</p><h2>{dniowka:,.2f} zł</h2></div>", unsafe_allow_html=True)

    st.write("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Wpływy", f"{s_prz:,.2f} zł")
    col2.metric("Stałe opłaty", f"{s_zobowiazania:,.2f} zł")
    col3.metric("Dzisiejsze zakupy", f"{s_codzienne:,.2f} zł")
    col4.metric("Odkłożono", f"{w_osz:,.2f} zł")

elif menu == "🛒 Wydatki Codzienne":
    st.title("🛒 Wydatki Codzienne")
    st.info("Nie musisz wybierać daty! Kliknij 'Zapisz', a aplikacja sama doda dzisiejszą datę i dokładną godzinę zakupu.")
    
    with st.form("quick_add", clear_on_submit=True):
        c1, c2, c3 = st.columns([2,1,1])
        nazwa = c1.text_input("Co zostało kupione?")
        kwota = c2.number_input("Kwota", min_value=0.0, step=5.0)
        kat = c3.selectbox("Kategoria", ["Jedzenie", "Dom", "Transport", "Zdrowie", "Rozrywka", "Inne"])
        if st.form_submit_button("⚡ ZAPISZ ZAKUP"):
            if kwota > 0 and nazwa:
                teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sh.worksheet("Wydatki").append_row([teraz, nazwa, kat, kwota])
                st.success("Zapisano zakup!")
                st.rerun()

    df_w = load_df("Wydatki")
    if not df_w.empty:
        st.write("### Ostatnie paragony (Edycja)")
        ed_w = st.data_editor(df_w.sort_values("Data", ascending=False), hide_index=True, use_container_width=True)
        if st.button("💾 Zapisz poprawki w historii"): 
            save_df("Wydatki", ed_w)

elif menu == "🗓️ Stałe Zobowiązania":
    st.title("🗓️ Stałe Zobowiązania")
    st.markdown("Tutaj zarządzacie opłatami, które nie zmieniają się z dnia na dzień. Aplikacja co miesiąc odliczy je z automatu z Waszego budżetu.")
    
    t1, t2 = st.tabs(["📋 Lista opłat", "➕ Dodaj Nowe Zobowiązanie"])
    
    with t2:
        with st.form("add_zob", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nazwa (np. Netflix, Czynsz, Rata za auto)")
            k = c2.number_input("Kwota miesięczna", min_value=0.0)
            typ = st.selectbox("Typ", ["Subskrypcja", "Koszt Stały", "Rata Kredytu"])
            if st.form_submit_button("Dodaj do planu"):
                if n and k > 0:
                    sh.worksheet("Zobowiazania").append_row([n, typ, k])
                    st.rerun()
                
    with t1:
        df_z = load_df("Zobowiazania")
        if not df_z.empty:
            ed_z = st.data_editor(df_z, hide_index=True, num_rows="dynamic", use_container_width=True)
            if st.button("💾 Zaktualizuj bazę stałych opłat"): 
                save_df("Zobowiazania", ed_z)

elif menu == "📥 Przychody":
    st.title("📥 Rejestr Przychodów")
    with st.form("add_prz", clear_on_submit=True):
        c1, c2 = st.columns(2)
        zrodlo = c1.text_input("Źródło (np. Pensja, Sprzedaż)")
        kwota = c2.number_input("Kwota", min_value=0.0)
        forma = st.selectbox("Forma", ["Konto", "Gotówka"])
        if st.form_submit_button("Zapisz wpływ"):
            if zrodlo and kwota > 0:
                sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), zrodlo, forma, kwota])
                st.rerun()

    df_p = load_df("Przychody")
    if not df_p.empty:
        st.write("### Baza wpływów")
        ed_p = st.data_editor(df_p.sort_values("Data", ascending=False), hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Nadpisz wpływy"): 
            save_df("Przychody", ed_p)

elif menu == "🐷 Oszczędności":
    st.title("🐷 Oszczędności")
    with st.form("add_osz", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        cel = c1.text_input("Cel (np. Wakacje)")
        kwota = c2.number_input("Kwota", min_value=0.0)
        akcja = c3.selectbox("Rodzaj operacji", ["Wpłata", "Wypłata"])
        if st.form_submit_button("Zapisz operację"):
            if cel and kwota > 0:
                sh.worksheet("Oszczednosci").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cel, kwota, akcja])
                st.rerun()

    df_o = load_df("Oszczednosci")
    if not df_o.empty:
        st.write("### Historia Oszczędności")
        ed_o = st.data_editor(df_o.sort_values("Data", ascending=False), hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zapisz zmiany w skarbonce"): 
            save_df("Oszczednosci", ed_o)
