import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import calendar

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Budżet Domowy", page_icon="💳", layout="wide")

# --- NOWOCZESNY DESIGN (APLIKACJA WEBOWA) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp { 
        background-color: #f4f7f6;
        font-family: 'Inter', sans-serif;
    }
    
    /* Główne nagłówki */
    h1, h2, h3 { color: #111827; font-weight: 800; letter-spacing: -0.5px; }
    
    /* Karty metryk (Statystyki) */
    div[data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    
    /* Wartości w kartach */
    [data-testid="stMetricValue"] { 
        font-size: 2rem; 
        font-weight: 800;
        color: #111827;
    }
    
    /* Przyciski Akcji */
    .stButton>button { 
        background-color: #0f172a;
        color: #ffffff; 
        border: none;
        border-radius: 10px; 
        font-weight: 600; 
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #334155;
        transform: translateY(-1px);
    }
    
    /* Karta Dziennego Limitu */
    .hero-card {
        background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
        color: white; 
        padding: 30px; 
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.2);
    }
    .hero-card h2 { color: white; font-size: 3.5rem; margin-top: 5px; margin-bottom: 5px;}
    .hero-card p { font-size: 1.1rem; opacity: 0.9; margin: 0; }
    
    /* Zakładki (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z GOOGLE SHEETS ---
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

# --- FUNKCJE BAZY DANYCH ---
def load_df(sheet_name):
    try:
        data = sh.worksheet(sheet_name).get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            if 'Data' in df.columns: df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
            if 'Data końca' in df.columns: df['Data końca'] = pd.to_datetime(df['Data końca'], errors='coerce')
        return df
    except: return pd.DataFrame()

def save_df(sheet_name, df):
    try:
        sheet = sh.worksheet(sheet_name)
        sheet.clear()
        df_to_save = df.copy()
        for col in df_to_save.select_dtypes(include=['datetime64']).columns:
            df_to_save[col] = df_to_save[col].dt.strftime('%Y-%m-%d')
        sheet.update([df_to_save.columns.values.tolist()] + df_to_save.fillna("").values.tolist())
        st.toast(f"✅ Zapisano: {sheet_name}")
    except Exception as e: st.error(f"Błąd zapisu: {e}")

# --- AUTOMATYZACJA ---
def run_monthly_billing(month_date):
    wyd = load_df("Wydatki")
    if wyd.empty or 'Data' not in wyd.columns: return
    m_str = month_date.strftime("%Y-%m")
    
    already_billed = wyd[(wyd['Data'].dt.strftime("%Y-%m") == m_str) & (wyd['Nazwa'].astype(str).str.contains("🔄"))]
    if already_billed.empty:
        aktywne = wyd[
            ((wyd['Typ'].astype(str).str.contains("Stały")) | (wyd['Kategoria'] == "Subskrypcje")) &
            (wyd['Data'] < month_date) &
            ((wyd['Data końca'].isna()) | (wyd['Data końca'] >= month_date)) &
            (~wyd['Nazwa'].astype(str).str.contains("🔄"))
        ].copy()
        
        if not aktywne.empty:
            if st.sidebar.button(f"⚡ Pobierz stałe koszty ({m_str})", use_container_width=True):
                for _, r in aktywne.iterrows():
                    sh.worksheet("Wydatki").append_row([
                        month_date.strftime("%Y-%m-01"), f"🔄 {r['Nazwa']}", r['Kategoria'], r['Typ'], r['Kwota'],
                        r['Data końca'].strftime('%Y-%m-%d') if pd.notna(r['Data końca']) else ""
                    ])
                st.rerun()

# --- SIDEBAR (SELEKTOR MIESIĄCA) ---
st.sidebar.markdown("### 📅 Okres rozliczeniowy")
miesiące = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
lata = list(range(2024, 2030))

dzis = date.today()
c1, c2 = st.sidebar.columns(2)
wybrany_m_nazwa = c1.selectbox("Miesiąc", miesiące, index=dzis.month - 1)
wybrany_rok = c2.selectbox("Rok", lata, index=lata.index(dzis.year))

# Tworzenie obiektu daty na 1. dzień wybranego miesiąca
m_idx = miesiące.index(wybrany_m_nazwa) + 1
selected_date = date(wybrany_rok, m_idx, 1)

run_monthly_billing(selected_date)
st.sidebar.markdown("---")
menu = st.sidebar.radio("Nawigacja:", ["🏠 Kokpit", "📥 Przychody", "💸 Wydatki", "🐷 Oszczędności", "📅 Raty"])

def filter_month(df):
    if df.empty or 'Data' not in df.columns: return df
    return df[df['Data'].dt.strftime("%Y-%m") == selected_date.strftime("%Y-%m")]

# --- WIDOKI ---
if menu == "🏠 Kokpit":
    st.markdown(f"<h1>Podsumowanie: {wybrany_m_nazwa} {wybrany_rok}</h1>", unsafe_allow_html=True)
    
    prz_m = filter_month(load_df("Przychody"))
    wyd_m = filter_month(load_df("Wydatki"))
    osz_m = filter_month(load_df("Oszczednosci"))
    raty = load_df("Raty")
    
    # Matma
    s_wplywy = prz_m['Kwota'].sum() if not prz_m.empty else 0
    s_wydatki = wyd_m['Kwota'].sum() if not wyd_m.empty else 0
    s_raty = pd.to_numeric(raty['Kwota raty'], errors='coerce').sum() if not raty.empty else 0
    w_osz = osz_m[osz_m['Typ'] == 'Wpłata']['Kwota'].sum() if not osz_m.empty and 'Typ' in osz_m.columns else 0
    
    # Wolne środki 
    wolne = s_wplywy - s_wydatki - s_raty - w_osz
    
    # Zamknięcie miesiąca (jeśli zostały wolne środki)
    ostatni_dzien_m = calendar.monthrange(wybrany_rok, m_idx)[1]
    if wolne > 0:
        st.info(f"💡 Zostało Wam jeszcze {wolne:,.2f} zł w tym miesiącu.")
        if st.button("🔒 Zamknij ten miesiąc (Przelej nadwyżkę na Oszczędności)"):
            data_zamkniecia = f"{wybrany_rok}-{m_idx:02d}-{ostatni_dzien_m}"
            sh.worksheet("Oszczednosci").append_row([data_zamkniecia, f"Nadwyżka z {wybrany_m_nazwa} {wybrany_rok}", wolne, "Wpłata"])
            st.success("Miesiąc zamknięty! Środki zabezpieczone.")
            st.rerun()

    # Dniówka
    if dzis.month == m_idx and dzis.year == wybrany_rok:
        pozostalo_dni = ostatni_dzien_m - dzis.day + 1
    elif selected_date < dzis:
        pozostalo_dni = 0 # Miesiąc minął
    else:
        pozostalo_dni = ostatni_dzien_m

    dniowka = wolne / pozostalo_dni if pozostalo_dni > 0 and wolne > 0 else 0

    st.write("") # Odstęp
    c_hero1, c_hero2 = st.columns(2)
    with c_hero1:
        st.markdown(f"""
            <div class='hero-card'>
                <p>Wolne środki (Na koncie)</p>
                <h2>{wolne:,.2f} zł</h2>
            </div>
        """, unsafe_allow_html=True)
    with c_hero2:
        if pozostalo_dni > 0:
            st.markdown(f"""
                <div class='hero-card' style='background: linear-gradient(135deg, #10b981 0%, #059669 100%);'>
                    <p>Budżet dzienny (zostało {pozostalo_dni} dni)</p>
                    <h2>{dniowka:,.2f} zł</h2>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class='hero-card' style='background: linear-gradient(135deg, #64748b 0%, #475569 100%);'>
                    <p>Miesiąc zakończony</p>
                    <h2>-</h2>
                </div>
            """, unsafe_allow_html=True)

    st.write("### Szczegóły rozliczenia")
    c1, c2, c3 = st.columns(3)
    c1.metric("Wpływy", f"{s_wplywy:,.2f} zł")
    c2.metric("Wydatki i Raty", f"{(s_wydatki + s_raty):,.2f} zł")
    c3.metric("Odkłożono", f"{w_osz:,.2f} zł")

elif menu == "📥 Przychody":
    st.markdown("<h1>Rejestr Przychodów</h1>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["📋 Baza danych", "➕ Dodaj nowy wpływ"])
    
    with t2:
        with st.form("f_prz", clear_on_submit=True):
            st.write("Zarejestruj nowy przychód")
            c1, c2 = st.columns(2)
            zrodlo = c1.text_input("Źródło (np. Wypłata, Sprzedaż)")
            forma = c2.selectbox("Gdzie?", ["Konto", "Gotówka"])
            kwota = st.number_input("Kwota (zł)", min_value=0.0, step=100.0)
            if st.form_submit_button("Zapisz wpływ"):
                sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d"), zrodlo, forma, kwota])
                st.rerun()
                
    with t1:
        df_p = load_df("Przychody")
        if not df_p.empty:
            ed_p = st.data_editor(df_p, hide_index=True, use_container_width=True, 
                                  column_config={"Kwota": st.column_config.NumberColumn(format="%.2f zł")})
            if st.button("💾 Nadpisz zmiany"): save_df("Przychody", ed_p)

elif menu == "💸 Wydatki":
    st.markdown("<h1>Koszty i Wydatki</h1>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["📋 Lista wydatków", "🛒 Dodaj wydatek"])
    
    with t2:
        with st.form("f_wyd", clear_on_submit=True):
            n = st.text_input("Nazwa (np. Zakupy Biedronka, Czynsz)")
            c1, c2 = st.columns(2)
            k = c1.number_input("Kwota (zł)", min_value=0.0)
            typ = c2.selectbox("Rodzaj", ["Zmienny (jednorazowy)", "Stały (rachunki)", "Subskrypcje"])
            kat = st.selectbox("Kategoria", ["Dom i Rachunki", "Jedzenie", "Transport", "Dzieci", "Rozrywka", "Inne"])
            dk = st.date_input("Koniec subskrypcji/umowy (opcjonalne)", value=None)
            if st.form_submit_button("Dodaj"):
                sh.worksheet("Wydatki").append_row([datetime.now().strftime("%Y-%m-%d"), n, kat, typ, k, dk.strftime("%Y-%m-%d") if dk else ""])
                st.rerun()

    with t1:
        df_w = load_df("Wydatki")
        if not df_w.empty:
            ed_w = st.data_editor(df_w, hide_index=True, use_container_width=True,
                                  column_config={"Kwota": st.column_config.NumberColumn(format="%.2f zł")})
            if st.button("💾 Nadpisz zmiany"): save_df("Wydatki", ed_w)

elif menu == "🐷 Oszczędności":
    st.markdown("<h1>Fundusze Celowe</h1>", unsafe_allow_html=True)
    
    osz_all = load_df("Oszczednosci")
    if not osz_all.empty and 'Typ' in osz_all.columns:
        tot = osz_all[osz_all['Typ']=='Wpłata']['Kwota'].sum() - osz_all[osz_all['Typ']=='Wypłata']['Kwota'].sum()
    else: tot = 0
    
    st.info(f"💰 Całkowity stan oszczędności (z wszystkich miesięcy): **{tot:,.2f} zł**")
    
    t1, t2 = st.tabs(["📋 Rejestr operacji", "⚙️ Wpłać / Wypłać"])
    
    with t2:
        with st.form("f_osz", clear_on_submit=True):
            cel = st.text_input("Cel (np. Wakacje, Awaria, Poduszka)")
            c1, c2 = st.columns(2)
            akcja = c1.selectbox("Akcja", ["Wpłata", "Wypłata"])
            kw = c2.number_input("Kwota (zł)", min_value=0.0)
            if st.form_submit_button("Potwierdź operację"):
                sh.worksheet("Oszczednosci").append_row([datetime.now().strftime("%Y-%m-%d"), cel, kw, akcja])
                st.rerun()
                
    with t1:
        if not osz_all.empty:
            ed_o = st.data_editor(osz_all, hide_index=True, use_container_width=True,
                                  column_config={"Kwota": st.column_config.NumberColumn(format="%.2f zł")})
            if st.button("💾 Nadpisz zmiany"): save_df("Oszczednosci", ed_o)

elif menu == "📅 Raty":
    st.markdown("<h1>Raty i Kredyty</h1>", unsafe_allow_html=True)
    st.write("Ta sekcja ignoruje filtr miesiąca – pokazuje Wasze stałe obciążenia w ujęciu ogólnym.")
    
    df_r = load_df("Raty")
    if df_r.empty:
        df_r = pd.DataFrame(columns=["Nazwa banku/kredytu", "Dzień płatności", "Kwota raty", "Pozostało do spłaty", "Data końcowa"])
    
    ed_r = st.data_editor(df_r, hide_index=True, num_rows="dynamic", use_container_width=True,
                          column_config={"Kwota raty": st.column_config.NumberColumn(format="%.2f zł"), 
                                         "Pozostało do spłaty": st.column_config.NumberColumn(format="%.2f zł")})
    if st.button("💾 Zaktualizuj harmonogram"):
        save_df("Raty", ed_r)
