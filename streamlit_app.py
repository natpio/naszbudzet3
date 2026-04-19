import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import calendar

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Route 66 Budget", page_icon="🍔", layout="wide")

# --- STYLIZACJA: PEŁNY AMERICAN DINER 50s ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bungee+Inline&family=Pacifico&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap');

    /* Tło - Różowo-Czarna Szachownica (Klasyk!) */
    .stApp {
        background-color: #ffc2d1;
        background-image:
          linear-gradient(45deg, #111 25%, transparent 25%, transparent 75%, #111 75%, #111),
          linear-gradient(45deg, #111 25%, transparent 25%, transparent 75%, #111 75%, #111);
        background-size: 60px 60px;
        background-position: 0 0, 30px 30px;
        background-attachment: fixed;
        font-family: 'Space Mono', monospace;
    }

    /* Karta Menu - Główny kontener aplikacji */
    [data-testid="block-container"] {
        background-color: #fffdf5; /* Kremowy papier */
        padding: 40px;
        border-radius: 20px;
        border: 8px dashed #d90429; /* Ramka jak w menu */
        box-shadow: 15px 15px 0px rgba(0,0,0,0.9);
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    /* Różowe Neony dla Nagłówków */
    h1, h2 {
        font-family: 'Bungee Inline', cursive !important;
        color: #ff0055 !important;
        text-shadow: 0 0 5px #ff0055, 0 0 10px #ff0055, 0 0 20px #ff0055;
        text-align: center;
        letter-spacing: 3px;
        margin-bottom: 1rem;
    }
    h3 {
        font-family: 'Pacifico', cursive !important;
        color: #03045e !important;
        font-size: 2rem !important;
    }

    /* Pasek boczny - Szafa Grająca (Jukebox) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #d90429 0%, #8a0c10 100%);
        border-right: 8px solid #ffb703; /* Musztardowa lamówka */
    }
    [data-testid="stSidebarNav"], [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #fffdf5 !important;
        font-family: 'Space Mono', monospace;
        font-size: 1.1rem;
    }

    /* Metryki - Klasyczna Kasa Fiskalna */
    div[data-testid="metric-container"] {
        background-color: #1a1a1a;
        border: 4px solid #8d99ae; /* Chromowana obudowa */
        border-radius: 10px;
        padding: 20px;
        box-shadow: inset 0px 0px 15px rgba(0,0,0,1), 5px 5px 0px #d90429;
        text-align: center;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Space Mono', monospace !important;
        color: #39ff14 !important; /* Świecąca zieleń */
        text-shadow: 0 0 8px #39ff14;
        font-size: 2.5rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #fffdf5 !important;
        font-family: 'Pacifico', cursive !important;
        font-size: 1.2rem !important;
    }

    /* Tarcze Główne (Hero Cards) - Neonowy Szyld */
    .hero-card {
        background: #111;
        border: 4px solid #00f5d4; /* Turkusowy neon */
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 15px #00f5d4, inset 0 0 20px #00f5d4;
        text-align: center;
    }
    .hero-card h2 {
        color: #00f5d4 !important;
        text-shadow: 0 0 10px #00f5d4;
        font-size: 3.5rem !important;
        margin: 10px 0;
        font-family: 'Space Mono', monospace !important;
    }
    .hero-card p {
        color: #fffdf5 !important;
        font-family: 'Pacifico', cursive !important;
        font-size: 1.5rem;
        margin: 0;
    }

    /* Przyciski - Grube, musztardowe klawisze kasy */
    .stButton>button {
        background-color: #ffb703;
        color: #1a1a1a !important;
        border: 4px solid #1a1a1a;
        border-radius: 12px;
        font-weight: 900;
        font-family: 'Space Mono', monospace;
        font-size: 1.2rem;
        text-transform: uppercase;
        box-shadow: 6px 6px 0px #1a1a1a;
        transition: all 0.1s;
    }
    .stButton>button:hover {
        transform: translate(3px, 3px);
        box-shadow: 3px 3px 0px #1a1a1a;
        background-color: #fb8500;
    }

    /* Tabele (żeby było widać na kremowym tle) */
    .stDataFrame {
        border: 3px solid #1a1a1a;
        border-radius: 5px;
        background-color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z BAZĄ ---
@st.cache_resource
def init_connection():
    try:
        creds = st.secrets["connections"]["gsheets"]
        fixed_key = creds["private_key"].replace("\\n", "\n").strip()
        credentials = Credentials.from_service_account_info(
            {"type": "service_account", "project_id": creds.get("project_id", "budzet"),
             "private_key": fixed_key, "client_email": creds["client_email"], "token_uri": creds["token_uri"]},
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(credentials).open_by_url(creds["spreadsheet"])
    except Exception as e:
        st.error(f"Błąd silnika: {e}")
        return None

sh = init_connection()

# --- FUNKCJE BAZY ---
def load_df(sheet_name):
    try:
        data = sh.worksheet(sheet_name).get_all_records()
        df = pd.DataFrame(data)
        if not df.empty and 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        return df
    except: return pd.DataFrame()

def save_df(sheet_name, df):
    sheet = sh.worksheet(sheet_name)
    sheet.clear()
    df_save = df.copy()
    if 'Data' in df_save.columns: df_save['Data'] = df_save['Data'].dt.strftime('%Y-%m-%d %H:%M:%S')
    sheet.update([df_save.columns.values.tolist()] + df_save.fillna("").values.tolist())
    st.toast(f"🍒 Bim Bam! Zapisano na taśmie: {sheet_name}!")

# --- MENU BOCZNE (SZAFA GRAJĄCA) ---
st.sidebar.markdown("<h1 style='color:#ffb703 !important; text-shadow: 2px 2px 0 #1a1a1a;'>📻 Jukebox Menu</h1>", unsafe_allow_html=True)
miesiące = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
wybrany_m = st.sidebar.selectbox("Wybierz Miesiąc (Strona A):", miesiące, index=datetime.now().month - 1)
wybrany_rok = st.sidebar.selectbox("Wybierz Rok (Strona B):", [2024, 2025, 2026], index=2)

m_idx = miesiące.index(wybrany_m) + 1
selected_date = date(wybrany_rok, m_idx, 1)

st.sidebar.markdown("---")
menu = st.sidebar.radio("Wybierz kawałek:", [
    "🍔 Drive-In (Kokpit)", 
    "🍟 Szybkie Zamówienia (Wydatki)", 
    "🧾 Opłaty za Lokal (Stałe)", 
    "💵 Kasa Fiskalna (Przychody)", 
    "🎸 Szafa Grająca (Oszczędności)"
])

# --- WIDOKI ---
if menu == "🍔 Drive-In (Kokpit)":
    st.markdown(f"<h1>Zestawienie: {wybrany_m} {wybrany_rok} 🥤</h1>", unsafe_allow_html=True)
    
    prz = load_df("Przychody")
    wyd_c = load_df("Wydatki")
    zob = load_df("Zobowiazania")
    osz = load_df("Oszczednosci")
    
    m_str = selected_date.strftime("%Y-%m")
    prz_m = prz[prz['Data'].dt.strftime("%Y-%m") == m_str] if not prz.empty else pd.DataFrame()
    wyd_m = wyd_c[wyd_c['Data'].dt.strftime("%Y-%m") == m_str] if not wyd_c.empty else pd.DataFrame()
    osz_m = osz[osz['Data'].dt.strftime("%Y-%m") == m_str] if not osz.empty else pd.DataFrame()
    
    s_prz = prz_m['Kwota'].sum() if not prz_m.empty else 0
    s_codzienne = wyd_m['Kwota'].sum() if not wyd_m.empty else 0
    s_zobowiazania = zob['Kwota'].sum() if not zob.empty else 0
    w_osz = osz_m[osz_m['Akcja'] == 'Wpłata']['Kwota'].sum() if not osz_m.empty and 'Akcja' in osz_m.columns else 0
    
    wolne = s_prz - s_codzienne - s_zobowiazania - w_osz
    
    ostatni_dzien = calendar.monthrange(wybrany_rok, m_idx)[1]
    dzis = date.today()
    if dzis.month == m_idx and dzis.year == wybrany_rok:
        pozostalo_dni = ostatni_dzien - dzis.day + 1
    elif selected_date < dzis: pozostalo_dni = 0
    else: pozostalo_dni = ostatni_dzien
        
    dniowka = wolne / pozostalo_dni if pozostalo_dni > 0 and wolne > 0 else 0

    c_h1, c_h2 = st.columns(2)
    with c_h1:
        st.markdown(f"<div class='hero-card'><p>Zostało na burgery i paliwo</p><h2>{wolne:,.2f} zł</h2></div>", unsafe_allow_html=True)
    with c_h2:
        kolor_neonu = "#ff0055" if dniowka < 50 else "#00f5d4" # Zmienia kolor na czerwony, gdy krucho z kasą
        st.markdown(f"""
        <div class='hero-card' style='border-color:{kolor_neonu}; box-shadow: 0 0 15px {kolor_neonu}, inset 0 0 20px {kolor_neonu};'>
            <p>Dniówka na frytki (przez {pozostalo_dni} dni)</p>
            <h2 style='color:{kolor_neonu} !important; text-shadow: 0 0 10px {kolor_neonu};'>{dniowka:,.2f} zł</h2>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Wpadło do Kasy", f"{s_prz:,.2f} zł")
    col2.metric("Opłaty za Lokal", f"{s_zobowiazania:,.2f} zł")
    col3.metric("Wydano na Mieście", f"{s_codzienne:,.2f} zł")
    col4.metric("Wrzucono do Szafy", f"{w_osz:,.2f} zł")

elif menu == "🍟 Szybkie Zamówienia (Wydatki)":
    st.markdown("<h1>🍟 Nabijamy Paragon!</h1>", unsafe_allow_html=True)
    st.write("### Data nabija się sama. Ty wpisujesz tylko co zjedliśmy!")
    
    with st.form("quick_add", clear_on_submit=True):
        c1, c2, c3 = st.columns([2,1,1])
        nazwa = c1.text_input("Co było grane?")
        kwota = c2.number_input("Ile to kosztowało? (zł)", min_value=0.0, step=1.0)
        kat = c3.selectbox("Menu Dział", ["Jedzenie", "Auto & Paliwo", "Rozrywka", "Dom", "Zdrowie", "Inne Bzdury"])
        if st.form_submit_button("🛎️ DING! ZAPISZ PARAGON"):
            if kwota > 0 and nazwa:
                teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sh.worksheet("Wydatki").append_row([teraz, nazwa, kat, kwota])
                st.success("Wysłane do kuchni!")
                st.rerun()

    df_w = load_df("Wydatki")
    if not df_w.empty:
        st.write("### Ostatnie Rolki z Kasy (Historia)")
        ed_w = st.data_editor(df_w.sort_values("Data", ascending=False), hide_index=True, use_container_width=True)
        if st.button("💾 Zatwierdź korektę paragonów"): save_df("Wydatki", ed_w)

elif menu == "🧾 Opłaty za Lokal (Stałe)":
    st.markdown("<h1>🧾 Rachunki i Czynsze</h1>", unsafe_allow_html=True)
    st.write("### Twardy biznes. Cennik rzeczy, które płacimy co miesiąc.")
    
    t1, t2 = st.tabs(["📋 Nasze Zobowiązania", "📝 Podpisz nowy weksel"])
    
    with t2:
        with st.form("add_zob", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n = c1.text_input("Komu płacimy? (np. Netflix, Czynsz)")
            k = c2.number_input("Ile co miesiąc?", min_value=0.0)
            typ = st.selectbox("Typ rachunku", ["Subskrypcja (Kino/Muzyka)", "Koszt Stały (Rachunki)", "Rata za Cadillaca (Kredyt)"])
            if st.form_submit_button("Pieczętuj umowę"):
                if n and k > 0:
                    sh.worksheet("Zobowiazania").append_row([n, typ, k])
                    st.rerun()
                
    with t1:
        df_z = load_df("Zobowiazania")
        if not df_z.empty:
            ed_z = st.data_editor(df_z, hide_index=True, num_rows="dynamic", use_container_width=True)
            if st.button("💾 Zaktualizuj Zeszyt Dłużników"): save_df("Zobowiazania", ed_z)

elif menu == "💵 Kasa Fiskalna (Przychody)":
    st.markdown("<h1>💵 Kasa Fiskalna</h1>", unsafe_allow_html=True)
    st.write("### Wypłaty, Napiwki, Kasa ze sprzedaży starych płyt.")
    with st.form("add_prz", clear_on_submit=True):
        c1, c2 = st.columns(2)
        zrodlo = c1.text_input("Kto płaci? (np. Szef, Klient)")
        kwota = c2.number_input("Ile hajsu?", min_value=0.0)
        forma = st.selectbox("Forma zapłaty", ["Przelew na konto", "Zielone w gotówce"])
        if st.form_submit_button("Otwórz Szufladę i Włóż Kasę"):
            if zrodlo and kwota > 0:
                sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), zrodlo, forma, kwota])
                st.rerun()

    df_p = load_df("Przychody")
    if not df_p.empty:
        st.write("### Księga Główna (Historia Wpływów)")
        ed_p = st.data_editor(df_p.sort_values("Data", ascending=False), hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zamknij Księgi"): save_df("Przychody", ed_p)

elif menu == "🎸 Szafa Grająca (Oszczędności)":
    st.markdown("<h1>🎸 Jukebox: Oszczędności</h1>", unsafe_allow_html=True)
    st.write("### Wrzuć monetę na lepsze czasy albo zbieraj na nowego Cadillaca!")
    with st.form("add_osz", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        cel = c1.text_input("Na co zbieramy?")
        kwota = c2.number_input("Ile wrzucamy?", min_value=0.0)
        akcja = c3.selectbox("Co robimy?", ["Wpłata (Wrzuć monetę)", "Wypłata (Rozbijamy świnkę)"])
        if st.form_submit_button("🎵 Wciśnij Play (Zapisz)"):
            if cel and kwota > 0:
                # Zamieniamy długie opcje na proste słowa do kalkulacji
                czysta_akcja = "Wpłata" if "Wpłata" in akcja else "Wypłata"
                sh.worksheet("Oszczednosci").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cel, kwota, czysta_akcja])
                st.rerun()

    df_o = load_df("Oszczednosci")
    if not df_o.empty:
        st.write("### Historia Wrzutek")
        ed_o = st.data_editor(df_o.sort_values("Data", ascending=False), hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zarygluj Szafę Grającą"): save_df("Oszczednosci", ed_o)
