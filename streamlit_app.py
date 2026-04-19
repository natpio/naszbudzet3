import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import calendar
import extra_streamlit_components as stx

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Midwest Budget", page_icon="🏈", layout="centered", initial_sidebar_state="collapsed")

# --- STYLIZACJA: CZYTELNOŚĆ + MIDWEST VIBE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Roboto:wght@400;700;900&family=Oswald:wght@500;700&display=swap');

    /* UKRYWANIE ZBĘDNYCH RELIKTÓW STREAMLITA */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stHeader"], header, .stAppHeader { background: transparent !important; box-shadow: none !important; }
    [data-testid="stToolbar"], #MainMenu, footer, .stDeployButton { display: none !important; }
    
    /* TŁO GŁÓWNE Z GITHUBA */
    .stApp {
        background-image: url('https://raw.githubusercontent.com/natpio/naszbudzet3/refs/heads/main/1776619317829.jpg');
        background-size: cover; background-position: center; background-attachment: fixed;
        font-family: 'Roboto', sans-serif;
    }

    /* GŁÓWNY KONTENER (TARCZA OCHRONNA DLA TEKSTU) */
    [data-testid="block-container"] {
        background-color: rgba(0, 34, 68, 0.92) !important; 
        padding: 30px !important; border-radius: 20px; border: 4px solid #c83803; 
        margin-top: 1rem; margin-bottom: 2rem; box-shadow: 0 15px 40px rgba(0,0,0,0.8);
        max-width: 800px;
    }

    /* GLOBALNE KOLORY TEKSTU */
    p, label, span, .stMarkdown p, li { color: #f8fafc !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); }
    h1, h2 { font-family: 'Bebas Neue', cursive !important; color: #ffb612 !important; text-transform: uppercase; letter-spacing: 2px; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }
    h3 { font-family: 'Oswald', sans-serif !important; color: #ffffff !important; text-transform: uppercase; border-bottom: 2px solid #c83803; padding-bottom: 5px; margin-top: 15px; }
    input, select { color: #000000 !important; font-weight: bold; }
    [data-testid="stDataFrame"] { background-color: rgba(255, 255, 255, 0.95); border-radius: 8px; padding: 5px; }

    /* NOWOCZESNA NAWIGACJA (TABS) */
    [data-testid="stTabs"] [data-baseweb="tab-list"] { background-color: rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 5px; gap: 5px; justify-content: center; margin-bottom: 20px; }
    [data-testid="stTabs"] [data-baseweb="tab"] { color: #e2e8f0; font-family: 'Oswald', sans-serif !important; font-size: 1rem; border-radius: 8px; padding: 8px 15px; border: none; background: transparent; }
    [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] { background-color: #c83803 !important; color: white !important; font-weight: bold; box-shadow: 0 4px 10px rgba(200, 56, 3, 0.5); }
    [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] div[data-testid="stMarkdownContainer"] p { color: white !important; text-shadow: none; }

    /* WIELKI PRZYCISK DODAWANIA */
    .stButton>button[kind="primary"] {
        background: linear-gradient(90deg, #c83803 0%, #ff5722 100%); color: white !important; border: none; border-radius: 30px;
        font-family: 'Bebas Neue', cursive; font-size: 2rem !important; letter-spacing: 2px; padding: 15px !important; box-shadow: 0 10px 20px rgba(200, 56, 3, 0.4); width: 100%; transition: transform 0.2s;
    }
    .stButton>button[kind="primary"]:active { transform: scale(0.95); }
    .stButton>button[kind="secondary"] { background-color: #002244; color: white !important; border: 2px solid #ffb612; border-radius: 8px; font-family: 'Oswald', sans-serif; text-transform: uppercase; width: 100%; font-weight: bold; }
    [data-testid="stForm"] { background-color: rgba(255, 255, 255, 0.05); border: 2px solid #c83803; border-radius: 15px; padding: 20px; }

    /* KARTY Z WYNIKAMI (SCOREBOARDS) */
    .hero-card { background-color: #006b3d; border: 3px solid #ffffff; border-radius: 15px; padding: 20px; box-shadow: 0 8px 15px rgba(0,0,0,0.5); text-align: center; color: white; margin-bottom: 15px; }
    .hero-card.interstate { background-color: #003882; border: 3px solid #ffffff; border-top: 15px solid #c8102e; border-radius: 15px; padding: 20px; box-shadow: 0 8px 15px rgba(0,0,0,0.6); text-align: center; color: white; margin-bottom: 15px; }
    .hero-card.danger { background-color: #c8102e; border: 3px solid #ffffff; border-radius: 15px; padding: 20px; text-align: center; color: white; margin-bottom: 15px; }
    .hero-card h2, .hero-card.interstate h2, .hero-card.danger h2 { color: #ffffff !important; font-size: 3rem !important; margin: 0; font-family: 'Bebas Neue', cursive !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
    .hero-card p, .hero-card.interstate p, .hero-card.danger p { font-weight: 900; font-size: 1rem; text-transform: uppercase; margin: 0 0 5px 0; font-family: 'Roboto', sans-serif !important; opacity: 0.9; }

    /* Metryki */
    [data-testid="stMetric"] { background-color: #111 !important; border: 2px solid #ffb612 !important; border-radius: 10px !important; padding: 15px !important; text-align: center !important; }
    [data-testid="stMetricValue"] div { font-family: 'Bebas Neue', cursive !important; color: #ffb612 !important; font-size: 2rem !important; }
    [data-testid="stMetricLabel"] p { color: #ffffff !important; font-weight: 700 !important; text-transform: uppercase !important; font-family: 'Roboto', sans-serif !important; font-size: 0.8rem !important; opacity: 1 !important;}

    /* Modale */
    div[role="dialog"] { background-color: #002244 !important; border: 4px solid #c83803; border-radius: 15px; }
    div[role="dialog"] h2 { color: #ffb612 !important; text-align: center; font-family: 'Bebas Neue', cursive !important; }
    div[role="dialog"] p, div[role="dialog"] label { color: white !important; }

    /* MOBILE RWD */
    @media (max-width: 768px) {
        [data-testid="block-container"] { padding: 15px !important; border-width: 2px !important; }
        [data-testid="stTabs"] [data-baseweb="tab"] { font-size: 0.8rem; padding: 8px 5px; }
        .hero-card h2, .hero-card.interstate h2 { font-size: 2.5rem !important; }
        .stButton>button[kind="primary"] { font-size: 1.5rem !important; padding: 10px !important;}
    }
    </style>
    """, unsafe_allow_html=True)

# --- SYSTEM LOGOWANIA Z CIASTECZKAMI (COOKIES) ---
cookie_manager = stx.CookieManager()

def check_password():
    auth_cookie = cookie_manager.get(cookie="midwest_auth")
    
    if auth_cookie == "granted" or st.session_state.get("password_correct"):
        return True

    st.markdown("<h1 style='text-align: center; color: #ffb612;'>🔒 IDENTYFIKACJA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Wpisz hasło drużyny. Zostaniesz zapamiętany na 30 dni.</p>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        haslo = st.text_input("Hasło:", type="password")
        if st.form_submit_button("WEJDŹ NA BOISKO (Zaloguj)", use_container_width=True):
            if haslo == st.secrets.get("app_password", ""):
                st.session_state["password_correct"] = True
                cookie_manager.set("midwest_auth", "granted", max_age=30 * 24 * 60 * 60)
                st.rerun()
            else:
                st.error("❌ Błędne hasło. Sędzia odgwizdał faul.")
    return False

if not check_password():
    st.stop()

# ==============================================================================
# OD TEGO MIEJSCA KOD URUCHOMI SIĘ TYLKO DLA ZALOGOWANYCH
# ==============================================================================

# --- BAZA DANYCH ---
@st.cache_resource
def init_connection():
    try:
        creds = st.secrets["connections"]["gsheets"]
        fixed_key = creds["private_key"].replace("\\n", "\n").strip()
        credentials = Credentials.from_service_account_info(
            {"type": "service_account", "project_id": creds["project_id"], "private_key": fixed_key, "client_email": creds["client_email"], "token_uri": creds["token_uri"]},
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(credentials).open_by_url(creds["spreadsheet"])
    except Exception as e:
        st.error(f"Błąd silnika: {e}")
        return None

sh = init_connection()

def load_df(sheet_name):
    try:
        df = pd.DataFrame(sh.worksheet(sheet_name).get_all_records())
        # Bezpieczne konwertowanie dat na typ datetime, omijając puste stringi
        if not df.empty:
            for col in ['Data', 'Data rozpoczęcia', 'Data zakończenia']:
                if col in df.columns:
                    # Zamienia wszystko co puste/błędne na NaT (Not a Time)
                    df[col] = pd.to_datetime(df[col], errors='coerce') 
        return df
    except: return pd.DataFrame()

def save_df(sheet_name, df):
    sheet = sh.worksheet(sheet_name)
    sheet.clear()
    df_save = df.copy()
    
    # Zamiana obiektów Datetime z powrotem na ładne stringi przed zapisem do Sheets
    for col in ['Data', 'Data rozpoczęcia', 'Data zakończenia']:
        if col in df_save.columns:
            # Jeśli NaT (puste) - wpisz pusty string "", inaczej wstaw datę
            df_save[col] = df_save[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else "")
            
    sheet.update([df_save.columns.values.tolist()] + df_save.fillna("").values.tolist())
    st.toast(f"Zapisano na serwerze w Chicago: {sheet_name}!", icon="☁️")

prz_all = load_df("Przychody")
wyd_all = load_df("Wydatki")
zob_all = load_df("Zobowiazania")
osz_all = load_df("Oszczednosci")

# --- WYSKAKUJĄCE OKNO (SMART MODAL) ---
@st.dialog("CO ROBIMY, COACHU? 🏈")
def add_operation_modal():
    akcja = st.radio("Wybierz typ operacji:", ["📉 Wydatek (Zakupy)", "📈 Przelew (Wpływ)", "🏦 Skarbiec (Sejf)"])
    st.write("---")
    
    if "Wydatek" in akcja:
        n = st.text_input("Na co wydałeś?")
        k = st.number_input("Koszt (zł)", min_value=0.0, step=1.0)
        if st.button("Zanotuj Wydatek", use_container_width=True):
            if k > 0 and n:
                sh.worksheet("Wydatki").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), n, "Codzienne", k])
                st.rerun()

    elif "Przelew" in akcja:
        z = st.text_input("Od kogo ta kasa?")
        kw = st.number_input("Wpływ (zł)", min_value=0.0)
        if st.button("Zaksięguj Przelew", use_container_width=True):
            if z and kw > 0:
                sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), z, "Konto", kw])
                st.rerun()

    elif "Skarbiec" in akcja:
        cl = st.text_input("Jaki cel w Des Moines?")
        kwo = st.number_input("Podaj kwotę (zł)", min_value=0.0)
        typ_osz = st.selectbox("Typ", ["Wpłata", "Wypłata"])
        if st.button("Zarygluj Skarbiec", use_container_width=True):
            if cl and kwo > 0:
                sh.worksheet("Oszczednosci").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cl, kwo, typ_osz])
                st.rerun()

# --- GŁÓWNY INTERFEJS ---
c_m, c_y = st.columns(2)
miesiące = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
wybrany_m_nazwa = c_m.selectbox("MIESIĄC ROZLICZENIOWY:", miesiące, index=datetime.now().month - 1)
wybrany_rok = c_y.selectbox("SEZON:", [2024, 2025, 2026, 2027], index=2)

m_idx = miesiące.index(wybrany_m_nazwa) + 1
# Kontekst czasowy dla aplikacji (np. 1 Kwiecień 2026)
selected_date = pd.to_datetime(f"{wybrany_rok}-{m_idx:02d}-01")

st.write("") 

if st.button("➕ DODAJ OPERACJĘ", type="primary"):
    add_operation_modal()

st.write("") 

t1, t2, t3, t4 = st.tabs(["🏠 KOKPIT", "📜 HISTORIA", "🏢 STAŁE KOSZTY", "🌽 SEJF (DES MOINES)"])

with t1:
    m_str = selected_date.strftime("%Y-%m")
    
    prz_m = prz_all[prz_all['Data'].dt.strftime("%Y-%m") == m_str] if not prz_all.empty else pd.DataFrame()
    wyd_m = wyd_all[wyd_all['Data'].dt.strftime("%Y-%m") == m_str] if not wyd_all.empty else pd.DataFrame()
    osz_m = osz_all[osz_all['Data'].dt.strftime("%Y-%m") == m_str] if not osz_all.empty else pd.DataFrame()
    
    # INTELIGENTNE ODLICZANIE STAŁYCH KOSZTÓW
    # Bierzemy pod uwagę daty rozpoczęcia i zakończenia kontraktów!
    if not zob_all.empty:
        # Zabezpieczenie przed brakiem kolumn w starym arkuszu
        if 'Data rozpoczęcia' not in zob_all.columns: zob_all['Data rozpoczęcia'] = pd.NaT
        if 'Data zakończenia' not in zob_all.columns: zob_all['Data zakończenia'] = pd.NaT
            
        zob_aktywne = zob_all[
            # Kontrakt zaczął się w tym miesiącu ALBO wcześniej (lub data startu nie jest podana)
            ((zob_all['Data rozpoczęcia'] <= selected_date) | (zob_all['Data rozpoczęcia'].isnull())) &
            # Kontrakt kończy się w tym miesiącu ALBO później (lub trwa w nieskończoność)
            ((zob_all['Data zakończenia'] >= selected_date) | (zob_all['Data zakończenia'].isnull()))
        ]
        s_zobowiazania = zob_aktywne['Kwota'].sum()
    else:
        s_zobowiazania = 0

    s_prz = prz_m['Kwota'].sum() if not prz_m.empty else 0
    s_codzienne = wyd_m['Kwota'].sum() if not wyd_m.empty else 0
    w_osz = osz_m[osz_m['Akcja'] == 'Wpłata']['Kwota'].sum() if (not osz_m.empty and 'Akcja' in osz_m.columns) else 0
    
    wolne = s_prz - s_codzienne - s_zobowiazania - w_osz
    
    ostatni_dzien = calendar.monthrange(wybrany_rok, m_idx)[1]
    dzis = date.today()
    if dzis.month == m_idx and dzis.year == wybrany_rok: pozostalo_dni = ostatni_dzien - dzis.day + 1
    elif selected_date.date() < dzis: pozostalo_dni = 0
    else: pozostalo_dni = ostatni_dzien
        
    dniowka = wolne / pozostalo_dni if pozostalo_dni > 0 and wolne > 0 else 0

    st.markdown(f"<div class='hero-card'><p>I-80 FUNDS (W PORTFELU)</p><h2>{wolne:,.2f} zł</h2></div>", unsafe_allow_html=True)
    
    klasa = "hero-card danger" if dniowka < 50 else "hero-card interstate"
    st.markdown(f"<div class='{klasa}'><p>LIMIT NA DZIEŃ ({pozostalo_dni} DNI)</p><h2>{dniowka:,.2f} zł</h2></div>", unsafe_allow_html=True)

    cm1, cm2, cm3 = st.columns(3)
    cm1.metric("Wpływy w miesiącu", f"{s_prz:,.2f} zł")
    cm2.metric("Opłaty za mury", f"{s_zobowiazania:,.2f} zł")
    cm3.metric("Odkłożono", f"{w_osz:,.2f} zł")

with t2:
    st.markdown("<h3>📜 Ostatnie Akcje na Koncie</h3>", unsafe_allow_html=True)
    st.write("Twoje codzienne wydatki na mieście (z wybranego u góry miesiąca).")
    
    m_str = selected_date.strftime("%Y-%m")
    wyd_m = wyd_all[wyd_all['Data'].dt.strftime("%Y-%m") == m_str] if not wyd_all.empty else pd.DataFrame()
    
    if not wyd_m.empty:
        ed_w = st.data_editor(wyd_m.sort_values("Data", ascending=False), hide_index=True, use_container_width=True)
        if st.button("💾 Zapisz korektę historii wydatków"): save_df("Wydatki", ed_w)
    else:
        st.info("Brak wydatków w tym miesiącu. Użyj przycisku DODAJ OPERACJĘ na górze ekranu.")

with t3:
    st.markdown("<h3>🏢 Kontrakty i Rachunki</h3>", unsafe_allow_html=True)
    st.write("Wprowadzasz to tylko raz. Jeśli wpiszesz 'Datę zakończenia', po jej upływie system przestanie pobierać opłatę z Twojego budżetu.")
    
    with st.form("f_zob", clear_on_submit=True):
        st.write("📝 Dodaj nowy stały rachunek (Kontrakt)")
        nz = st.text_input("Nazwa (np. Czynsz, Rata auta)")
        
        c_k, c_t = st.columns(2)
        kz = c_k.number_input("Kwota stała", min_value=0.0)
        tz = c_t.selectbox("Typ", ["Subskrypcja", "Koszt Stały", "Rata Kredytu"])
        
        c_start, c_end = st.columns(2)
        # Data rozpoczęcia domyślnie "dzisiaj", Data zakończenia - pusta (opcjonalna)
        d_start = c_start.date_input("Data rozpoczęcia")
        d_end = c_end.date_input("Data zakończenia (Opcjonalnie)", value=None)
        
        if st.form_submit_button("Podpisz umowę"):
            if nz and kz > 0:
                # Zamiana na tekst dla Sheets
                start_str = d_start.strftime("%Y-%m-%d %H:%M:%S")
                end_str = d_end.strftime("%Y-%m-%d %H:%M:%S") if d_end else ""
                
                # Zabezpieczenie przed starym arkuszem (Google Sheets uzupełni kolumny, jeśli uderzymy w odpowiednie komórki)
                sh.worksheet("Zobowiazania").append_row([nz, tz, kz, start_str, end_str])
                st.rerun()
                
    if not zob_all.empty:
        # Odpowiednio konfigurujemy kolumny dat do edycji
        ed_z = st.data_editor(
            zob_all, 
            hide_index=True, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "Data rozpoczęcia": st.column_config.DateColumn(format="YYYY-MM-DD"),
                "Data zakończenia": st.column_config.DateColumn(format="YYYY-MM-DD")
            }
        )
        if st.button("💾 Zapisz zmiany w rachunkach"): save_df("Zobowiazania", ed_z)

with t4:
    st.markdown("<h3>🌽 Skarbiec Des Moines</h3>", unsafe_allow_html=True)
    st.write("Żeby dodać lub wypłacić środki, użyj głównego przycisku DODAJ OPERACJĘ na górze.")
    
    if not osz_all.empty:
        ed_o = st.data_editor(osz_all.sort_values("Data", ascending=False), hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zapisz korekty w sejfie"): save_df("Oszczednosci", ed_o)
    else:
        st.info("Sejf jest pusty.")
