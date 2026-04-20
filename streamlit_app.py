import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import calendar
import time
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

    /* GŁÓWNY KONTENER */
    .block-container, [data-testid="block-container"] {
        background-color: rgba(0, 21, 43, 0.95) !important; 
        padding: 30px !important; border-radius: 20px; border: 4px solid #c83803; 
        margin-top: 1rem; margin-bottom: 2rem; box-shadow: 0 20px 50px rgba(0,0,0,0.9);
        max-width: 800px;
    }

    /* GLOBAL KOLORY TEKSTU */
    p, label, .stMarkdown p { color: #f8fafc !important; }
    h1, h2 { font-family: 'Bebas Neue', cursive !important; color: #ffb612 !important; text-transform: uppercase; letter-spacing: 2px; }
    h3 { font-family: 'Oswald', sans-serif !important; color: #ffffff !important; text-transform: uppercase; border-bottom: 2px solid #c83803; padding-bottom: 5px; margin-top: 15px; }
    
    /* INPUTY I DROPDOWNY */
    input { color: #000000 !important; font-weight: bold; }
    div[data-baseweb="select"] { background-color: #ffffff !important; border-radius: 6px; }
    div[data-baseweb="select"] span { color: #000000 !important; font-weight: bold; } 
    ul[role="listbox"] { background-color: #ffffff !important; }
    ul[role="listbox"] li { color: #000000 !important; font-weight: bold; } 

    /* TABELA DANYCH */
    [data-testid="stDataFrame"] { background-color: rgba(255, 255, 255, 0.98); border-radius: 12px; padding: 5px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
    [data-testid="stDataFrame"] span { color: #000000 !important; font-family: 'Roboto', sans-serif; font-weight: 500; }
    div[data-testid="stDataFrameResizable"] { border: 2px solid #003366; border-radius: 10px; }

    /* NAWIGACJA (TABS) */
    [data-testid="stTabs"] [data-baseweb="tab-list"] { background-color: #003366 !important; border-radius: 12px; padding: 5px; gap: 5px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap; }
    [data-testid="stTabs"] [data-baseweb="tab"] { color: #e2e8f0 !important; font-family: 'Oswald', sans-serif !important; font-size: 0.85rem; border-radius: 8px; padding: 8px 10px; border: none; background: transparent; }
    [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] { background-color: #c83803 !important; color: white !important; font-weight: bold; box-shadow: 0 4px 10px rgba(200, 56, 3, 0.5); }
    [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] div[data-testid="stMarkdownContainer"] p { color: white !important; text-shadow: none; }

    /* PRZYCISKI */
    .stButton>button[kind="primary"] {
        background: linear-gradient(90deg, #c83803 0%, #ff5722 100%); color: white !important; border: none; border-radius: 30px;
        font-family: 'Bebas Neue', cursive; font-size: 2rem !important; letter-spacing: 2px; padding: 15px !important; box-shadow: 0 10px 20px rgba(200, 56, 3, 0.4); width: 100%; transition: transform 0.2s;
    }
    .stButton>button[kind="primary"]:active { transform: scale(0.95); }
    .stButton>button[kind="secondary"], [data-testid="stFormSubmitButton"]>button { background-color: #003366 !important; color: white !important; border: 2px solid #ffb612 !important; border-radius: 8px; font-family: 'Oswald', sans-serif !important; text-transform: uppercase; width: 100%; font-weight: bold; }
    [data-testid="stFormSubmitButton"]>button p { color: white !important; }
    [data-testid="stForm"] { background-color: rgba(255, 255, 255, 0.05); border: 2px solid #c83803; border-radius: 15px; padding: 20px; }

    /* KARTY WYNIKÓW */
    .hero-card { background-color: #006b3d; border: 3px solid #ffffff; border-radius: 15px; padding: 20px; box-shadow: 0 8px 15px rgba(0,0,0,0.5); text-align: center; color: white; margin-bottom: 15px; }
    .hero-card.interstate { background-color: #003882; border: 3px solid #ffffff; border-top: 15px solid #c8102e; border-radius: 15px; padding: 20px; box-shadow: 0 8px 15px rgba(0,0,0,0.6); text-align: center; color: white; margin-bottom: 15px; }
    .hero-card.danger { background-color: #c8102e; border: 3px solid #ffffff; border-radius: 15px; padding: 20px; text-align: center; color: white; margin-bottom: 15px; }
    .hero-card h2, .hero-card.interstate h2, .hero-card.danger h2 { color: #ffffff !important; font-size: 3rem !important; margin: 0; font-family: 'Bebas Neue', cursive !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
    .hero-card p, .hero-card.interstate p, .hero-card.danger p { font-weight: 900; font-size: 1rem; text-transform: uppercase; margin: 0 0 5px 0; font-family: 'Roboto', sans-serif !important; opacity: 0.9; }

    /* METRYKI */
    [data-testid="stMetric"] { background-color: #111 !important; border: 2px solid #ffb612 !important; border-radius: 10px !important; padding: 15px !important; text-align: center !important; }
    [data-testid="stMetricValue"] div { font-family: 'Bebas Neue', cursive !important; color: #ffb612 !important; font-size: 2rem !important; }
    [data-testid="stMetricLabel"] p { color: #ffffff !important; font-weight: 700 !important; text-transform: uppercase !important; font-family: 'Roboto', sans-serif !important; font-size: 0.8rem !important; opacity: 1 !important;}

    /* MODALE */
    div[role="dialog"] { background-color: #00152b !important; border: 4px solid #c83803; border-radius: 15px; }
    div[role="dialog"] h2 { color: #ffb612 !important; text-align: center; font-family: 'Bebas Neue', cursive !important; }
    div[role="dialog"] p, div[role="dialog"] label { color: white !important; }

    /* MOBILE RWD */
    @media (max-width: 768px) {
        .block-container, [data-testid="block-container"] { padding: 15px !important; border-width: 2px !important; margin-top: 0 !important; }
        [data-testid="stTabs"] [data-baseweb="tab"] { font-size: 0.60rem !important; padding: 6px 4px !important; }
        .hero-card h2, .hero-card.interstate h2 { font-size: 2.2rem !important; }
        .stButton>button[kind="primary"] { font-size: 1.5rem !important; padding: 10px !important;}
    }
    </style>
    """, unsafe_allow_html=True)

# --- SYSTEM LOGOWANIA ---
cookie_manager = stx.CookieManager()

def check_password():
    auth_cookie = cookie_manager.get(cookie="midwest_auth")
    if auth_cookie == "granted" or st.session_state.get("password_correct"):
        return True

    st.markdown("<div style='background-color: rgba(0, 34, 68, 0.95); padding: 30px; border-radius: 15px; border: 2px solid #ffb612; text-align: center;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='color: #ffb612;'>🔒 IDENTYFIKACJA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: white;'>Wpisz hasło, aby odblokować aplikację. Sesja trwa 30 dni.</p>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        haslo = st.text_input("Hasło:", type="password")
        if st.form_submit_button("ZALOGUJ", use_container_width=True):
            if haslo == st.secrets.get("app_password", ""):
                st.session_state["password_correct"] = True
                cookie_manager.set("midwest_auth", "granted", max_age=30 * 24 * 60 * 60)
                st.rerun()
            else:
                st.error("❌ Błędne hasło.")
    st.markdown("</div>", unsafe_allow_html=True)
    return False

if not check_password():
    st.stop()

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
        st.error(f"Błąd połączenia: {e}")
        return None

sh = init_connection()

def load_df(sheet_name):
    try:
        df = pd.DataFrame(sh.worksheet(sheet_name).get_all_records())
        if not df.empty:
            df.columns = df.columns.str.strip()
            for col in df.columns:
                if 'kwota' in col.lower() or 'koszt' in col.lower():
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)
            for col in ['Data', 'Data rozpoczęcia', 'Data zakończenia']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce') 
        return df
    except Exception: 
        return pd.DataFrame()

def bezpieczny_zapis(sheet_name, dane_dict):
    try:
        df = load_df(sheet_name)
        nowy_wiersz = pd.DataFrame([dane_dict])
        
        if df.empty:
            df_final = nowy_wiersz
        else:
            df_final = pd.concat([df, nowy_wiersz], ignore_index=True)
            
        sheet = sh.worksheet(sheet_name)
        sheet.clear()
        
        for col in ['Data', 'Data rozpoczęcia', 'Data zakończenia']:
            if col in df_final.columns:
                df_final[col] = pd.to_datetime(df_final[col], errors='coerce')
                df_final[col] = df_final[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else "")
                
        sheet.update([df_final.columns.values.tolist()] + df_final.fillna("").values.tolist(), value_input_option='USER_ENTERED')
        return True
    except Exception as e:
        st.error(f"Krytyczny błąd zapisu: {e}")
        return False

def save_df(sheet_name, df):
    try:
        sheet = sh.worksheet(sheet_name)
        sheet.clear()
        df_save = df.copy()
        for col in ['Data', 'Data rozpoczęcia', 'Data zakończenia']:
            if col in df_save.columns:
                df_save[col] = pd.to_datetime(df_save[col], errors='coerce')
                df_save[col] = df_save[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else "")
                
        sheet.update([df_save.columns.values.tolist()] + df_save.fillna("").values.tolist(), value_input_option='USER_ENTERED')
        st.toast(f"Zaktualizowano chmurę: {sheet_name}!", icon="☁️")
    except Exception as e:
        st.error(f"Błąd przy masowym zapisie: {e}")

prz_all = load_df("Przychody")
wyd_all = load_df("Wydatki")
zob_all = load_df("Zobowiazania")
osz_all = load_df("Oszczednosci")

# KATEGORIE
KATEGORIE = ["Jedzenie", "Dom", "Transport", "Rozrywka", "Inne"]

# --- MODALE ---
@st.dialog("CO ROBIMY? 🏈")
def add_operation_modal():
    akcja = st.radio("Wybierz typ operacji:", ["📉 Wydatek (Zakupy)", "📈 Przelew (Wpływ)", "🏦 Konto oszczędnościowe"])
    st.write("---")
    
    if "Wydatek" in akcja:
        n = st.text_input("Na co wydane?")
        kat = st.selectbox("Kategoria", KATEGORIE)
        k = st.number_input("Koszt (zł)", min_value=0.0, step=1.0)
        
        if st.button("Zanotuj Wydatek", use_container_width=True):
            if k <= 0: st.warning("⚠️ Ej! Kwota musi być większa niż zero.")
            elif not n: st.warning("⚠️ Wpisz nazwę wydatku (np. 'Kawa').")
            else:
                if bezpieczny_zapis("Wydatki", {"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Nazwa": n, "Kategoria": kat, "Kwota": float(k)}):
                    st.success("✅ Wysłano do bazy! Zaraz odświeżę...")
                    time.sleep(1)
                    st.rerun()

    elif "Przelew" in akcja:
        z = st.text_input("Od kogo wpłynęło?")
        kw = st.number_input("Wpływ (zł)", min_value=0.0, step=1.0)
        if st.button("Zaksięguj Przelew", use_container_width=True):
            if kw <= 0: st.warning("⚠️ Wpisz kwotę większą niż zero.")
            elif not z: st.warning("⚠️ Wpisz źródło przelewu.")
            else:
                if bezpieczny_zapis("Przychody", {"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Źródło": z, "Typ": "Konto", "Kwota": float(kw)}):
                    st.success("✅ Zaksięgowano! Zaraz odświeżę...")
                    time.sleep(1)
                    st.rerun()

    elif "Konto oszczędnościowe" in akcja:
        cl = st.text_input("Cel oszczędzania:")
        kwo = st.number_input("Podaj kwotę (zł)", min_value=0.0, step=1.0)
        typ_osz = st.selectbox("Typ", ["Wpłata", "Wypłata"])
        if st.button("Zatwierdź w oszczędnościach", use_container_width=True):
            if kwo <= 0: st.warning("⚠️ Wpisz kwotę większą niż zero.")
            elif not cl: st.warning("⚠️ Podaj cel.")
            else:
                if bezpieczny_zapis("Oszczednosci", {"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Cel": cl, "Kwota": float(kwo), "Akcja": typ_osz, "Typ": typ_osz }):
                    st.success("✅ Sejf zaktualizowany! Zaraz odświeżę...")
                    time.sleep(1)
                    st.rerun()

@st.dialog("ZAMKNIĘCIE MIESIĄCA 📆")
def close_month_modal(wolne, m_nazwa, rok, m_idx):
    st.markdown(f"<h3 style='text-align: center; color: #ffb612;'>KAPITAŁ: {wolne:.2f} zł</h3>", unsafe_allow_html=True)
    st.write("Podziel zaoszczędzone środki. Ile wrzucamy do Sejfu, a ile przenosimy jako bonus na start kolejnego miesiąca?")
    
    do_sejfu = st.slider("Kwota do SEJFU (zł)", 0.0, float(wolne), float(wolne)/2, step=10.0)
    na_kolejny = float(wolne) - do_sejfu
    
    st.info(f"**Do Sejfu (Oszczędności):** {do_sejfu:.2f} zł\n\n**Na kolejny miesiąc:** {na_kolejny:.2f} zł")
    
    if st.button("ZATWIERDŹ ZAMKNIĘCIE MIESIĄCA", type="primary", use_container_width=True):
        next_m = 1 if m_idx == 12 else m_idx + 1
        next_y = rok + 1 if m_idx == 12 else rok
        next_date_str = f"{next_y}-{next_m:02d}-01 00:00:00"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        sukces = True
        if do_sejfu > 0:
            s1 = bezpieczny_zapis("Oszczednosci", {"Data": now_str, "Cel": f"Reszta z {m_nazwa} {rok}", "Kwota": float(do_sejfu), "Akcja": "Wpłata", "Typ": "Wpłata"})
            sukces = sukces and s1
        if na_kolejny > 0:
            s2 = bezpieczny_zapis("Przychody", {"Data": next_date_str, "Źródło": f"Zaskórniaki z {m_nazwa} {rok}", "Typ": "Konto", "Kwota": float(na_kolejny)})
            sukces = sukces and s2
            
        if sukces:
            st.success("Miesiąc zamknięty mistrzowsko! 🏆 Zaraz odświeżę...")
            time.sleep(1.5)
            st.rerun()

# --- GŁÓWNY INTERFEJS ---
c_m, c_y = st.columns(2)
miesiące = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
wybrany_m_nazwa = c_m.selectbox("MIESIĄC ROZLICZENIOWY:", miesiące, index=datetime.now().month - 1)
wybrany_rok = c_y.selectbox("ROK:", [2024, 2025, 2026, 2027], index=2)

m_idx = miesiące.index(wybrany_m_nazwa) + 1
selected_date = pd.to_datetime(f"{wybrany_rok}-{m_idx:02d}-01")

# OBLICZENIE OSTATNIEGO DNIA WYBRANEGO MIESIĄCA (FIX DLA KOSZTÓW STAŁYCH)
ostatni_dzien_miesiaca = calendar.monthrange(wybrany_rok, m_idx)[1]
end_of_month = pd.to_datetime(f"{wybrany_rok}-{m_idx:02d}-{ostatni_dzien_miesiaca} 23:59:59")

st.write("") 

if st.button("➕ DODAJ OPERACJĘ", type="primary"):
    add_operation_modal()

st.write("") 

t1, t2, t3, t4, t5, t6 = st.tabs(["🏠 KOKPIT", "📜 WYDATKI", "📥 WPŁYWY", "🏢 STAŁE", "🏦 SEJF", "📊 STATYSTYKI"])

with t1:
    m_str = selected_date.strftime("%Y-%m")
    
    prz_m = prz_all[prz_all['Data'].dt.strftime("%Y-%m") == m_str] if not prz_all.empty else pd.DataFrame()
    wyd_m = wyd_all[wyd_all['Data'].dt.strftime("%Y-%m") == m_str] if not wyd_all.empty else pd.DataFrame()
    osz_m = osz_all[osz_all['Data'].dt.strftime("%Y-%m") == m_str] if not osz_all.empty else pd.DataFrame()
    
    # POPRAWIONE OBLICZANIE KOSZTÓW STAŁYCH
    if not zob_all.empty:
        if 'Data rozpoczęcia' not in zob_all.columns: zob_all['Data rozpoczęcia'] = pd.NaT
        if 'Data zakończenia' not in zob_all.columns: zob_all['Data zakończenia'] = pd.NaT
            
        zob_aktywne = zob_all[
            ((zob_all['Data rozpoczęcia'] <= end_of_month) | (zob_all['Data rozpoczęcia'].isnull())) &
            ((zob_all['Data zakończenia'] >= selected_date) | (zob_all['Data zakończenia'].isnull()))
        ]
        s_zobowiazania = zob_aktywne['Kwota'].sum()
    else:
        s_zobowiazania = 0

    s_prz = prz_m['Kwota'].sum() if not prz_m.empty else 0
    s_codzienne = wyd_m['Kwota'].sum() if not wyd_m.empty else 0
    w_osz = osz_m[osz_m['Akcja'] == 'Wpłata']['Kwota'].sum() if (not osz_m.empty and 'Akcja' in osz_m.columns) else 0
    
    wolne = s_prz - s_codzienne - s_zobowiazania - w_osz
    
    dzis = date.today()
    if dzis.month == m_idx and dzis.year == wybrany_rok: pozostalo_dni = ostatni_dzien_miesiaca - dzis.day + 1
    elif selected_date.date() < dzis: pozostalo_dni = 0
    else: pozostalo_dni = ostatni_dzien_miesiaca
        
    dniowka = wolne / pozostalo_dni if pozostalo_dni > 0 and wolne > 0 else 0

    st.markdown(f"<div class='hero-card'><p>ŚRODKI DO WYDANIA W TYM MIESIĄCU</p><h2>{wolne:,.2f} zł</h2></div>", unsafe_allow_html=True)
    
    klasa = "hero-card danger" if dniowka < 50 else "hero-card interstate"
    st.markdown(f"<div class='{klasa}'><p>LIMIT NA DZIEŃ ({pozostalo_dni} DNI)</p><h2>{dniowka:,.2f} zł</h2></div>", unsafe_allow_html=True)

    cm1, cm2, cm3 = st.columns(3)
    cm1.metric("Wpływy w miesiącu", f"{s_prz:,.2f} zł")
    cm2.metric("Koszty Stałe", f"{s_zobowiazania:,.2f} zł")
    cm3.metric("Wpłata na oszczędności", f"{w_osz:,.2f} zł")

    st.write("---")
    if wolne > 0:
        if st.button("🔒 ZAMKNIJ MIESIĄC (Podziel resztę)", type="secondary"):
            close_month_modal(wolne, wybrany_m_nazwa, wybrany_rok, m_idx)
    else:
        st.info("💡 Brak wolnych środków do przeniesienia na koniec tego miesiąca.")

with t2:
    st.markdown("<h3>📜 Historia Wydatków</h3>", unsafe_allow_html=True)
    st.info("💡 **Aby usunąć wydatek:** Zaznacz szary kwadracik po lewej stronie wiersza i kliknij ikonę kosza w prawym górnym rogu tabeli.")
    
    if not wyd_m.empty:
        ed_w = st.data_editor(
            wyd_m.sort_values("Data", ascending=False), 
            hide_index=True, num_rows="dynamic", use_container_width=True,
            column_config={
                "Data": st.column_config.DatetimeColumn("Kiedy? 🕒", format="YYYY-MM-DD HH:mm"),
                "Nazwa": st.column_config.TextColumn("Co kupiono? 🛒"),
                "Kategoria": st.column_config.SelectboxColumn("Kategoria 📂", options=KATEGORIE),
                "Kwota": st.column_config.NumberColumn("Kwota", format="%.2f zł")
            }
        )
        if st.button("💾 Zapisz korektę wydatków"): save_df("Wydatki", ed_w)
    else:
        st.info("Brak wydatków w tym miesiącu.")

with t3:
    st.markdown("<h3>📥 Historia Wpływów</h3>", unsafe_allow_html=True)
    
    if not prz_m.empty:
        ed_p = st.data_editor(
            prz_m.sort_values("Data", ascending=False), 
            hide_index=True, num_rows="dynamic", use_container_width=True,
            column_config={
                "Data": st.column_config.DatetimeColumn("Kiedy? 🕒", format="YYYY-MM-DD HH:mm"),
                "Źródło": st.column_config.TextColumn("Od kogo? 💼"),
                "Typ": st.column_config.SelectboxColumn("Gdzie?", options=["Konto", "Gotówka"]),
                "Kwota": st.column_config.NumberColumn("Kwota", format="%.2f zł")
            }
        )
        if st.button("💾 Zapisz korektę wpływów"): save_df("Przychody", ed_p)
    else:
        st.info("Brak wpływów w tym miesiącu.")

with t4:
    st.markdown("<h3>🏢 Koszty Stałe (Zobowiązania)</h3>", unsafe_allow_html=True)
    
    with st.form("f_zob", clear_on_submit=True):
        st.write("📝 **Nowy Koszt Stały**")
        nz = st.text_input("Nazwa (np. Czynsz, Rata za auto)")
        
        c_k, c_t = st.columns(2)
        kz = c_k.number_input("Kwota stała", min_value=0.0)
        tz = c_t.selectbox("Typ", ["Subskrypcja", "Koszt Stały", "Rata Kredytu"])
        
        c_start, c_end = st.columns(2)
        d_start = c_start.date_input("Data rozpoczęcia")
        d_end = c_end.date_input("Data zakończenia (Opcjonalnie)", value=None)
        
        if st.form_submit_button("Dodaj koszt stały"):
            if nz and kz > 0:
                start_str = d_start.strftime("%Y-%m-%d %H:%M:%S")
                end_str = d_end.strftime("%Y-%m-%d %H:%M:%S") if d_end else ""
                sh.worksheet("Zobowiazania").append_row([nz, tz, kz, start_str, end_str])
                st.rerun()
                
    if not zob_all.empty:
        ed_z = st.data_editor(
            zob_all, hide_index=True, num_rows="dynamic", use_container_width=True,
            column_config={ 
                "Nazwa": st.column_config.TextColumn("Nazwa Rachunku 🧾"),
                "Typ": st.column_config.SelectboxColumn("Typ", options=["Subskrypcja", "Koszt Stały", "Rata Kredytu"]),
                "Kwota": st.column_config.NumberColumn("Kwota", format="%.2f zł"),
                "Data rozpoczęcia": st.column_config.DateColumn("Start 🟢", format="YYYY-MM-DD"), 
                "Data zakończenia": st.column_config.DateColumn("Koniec 🔴", format="YYYY-MM-DD") 
            }
        )
        if st.button("💾 Zapisz zmiany w kosztach stałych"): save_df("Zobowiazania", ed_z)

with t5:
    st.markdown("<h3>🏦 Konto Oszczędnościowe</h3>", unsafe_allow_html=True)
    
    if not osz_all.empty:
        ed_o = st.data_editor(
            osz_all.sort_values("Data", ascending=False), hide_index=True, num_rows="dynamic", use_container_width=True,
            column_config={
                "Data": st.column_config.DatetimeColumn("Kiedy?", format="YYYY-MM-DD HH:mm"),
                "Cel": st.column_config.TextColumn("Cel 🎯"),
                "Kwota": st.column_config.NumberColumn("Kwota", format="%.2f zł"),
                "Akcja": st.column_config.SelectboxColumn("Operacja", options=["Wpłata", "Wypłata"]),
                "Typ": None 
            }
        )
        if st.button("💾 Zapisz korekty w oszczędnościach"): save_df("Oszczednosci", ed_o)
    else:
        st.info("Brak środków na koncie oszczędnościowym.")

with t6:
    st.markdown("<h3>📊 Podsumowanie Kategorii</h3>", unsafe_allow_html=True)
    
    if not wyd_m.empty and "Kategoria" in wyd_m.columns:
        st.write(f"Struktura Twoich wydatków za **{wybrany_m_nazwa} {wybrany_rok}**:")
        
        suma_kat = wyd_m.groupby("Kategoria")["Kwota"].sum().reset_index()
        suma_kat = suma_kat.sort_values(by="Kwota", ascending=False)
        
        st.bar_chart(suma_kat.set_index("Kategoria"), color="#ffb612")
        
        st.dataframe(
            suma_kat, 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "Kategoria": st.column_config.TextColumn("Kategoria 📂"),
                "Kwota": st.column_config.NumberColumn("Suma wydatków", format="%.2f zł")
            }
        )
    else:
        st.info("Brak wydatków w tym miesiącu do wygenerowania statystyk.")
