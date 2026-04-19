import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import calendar

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Pulp Fiction Budget", page_icon="🍒", layout="wide")

# --- STYLIZACJA: ABSOLUTNE SZALEŃSTWO LATA 50. ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bungee+Inline&family=Pacifico&family=Press+Start+2P&family=Space+Mono:wght@400;700&display=swap');

    /* Tło - Różowo-Czarna Szachownica z efektem winiety (przyciemnione rogi) */
    .stApp {
        background-color: #ff99c2;
        background-image:
          linear-gradient(45deg, #000 25%, transparent 25%, transparent 75%, #000 75%, #000),
          linear-gradient(45deg, #000 25%, transparent 25%, transparent 75%, #000 75%, #000);
        background-size: 80px 80px;
        background-position: 0 0, 40px 40px;
        background-attachment: fixed;
        font-family: 'Space Mono', monospace;
        box-shadow: inset 0 0 150px rgba(0,0,0,0.8);
    }

    /* Karta Menu - Środek ekranu */
    [data-testid="block-container"] {
        background-color: #fffdf5; 
        background-image: radial-gradient(#ffe5ec 1px, transparent 1px);
        background-size: 20px 20px;
        padding: 40px;
        border-radius: 20px;
        border: 10px groove #d90429;
        box-shadow: 20px 20px 0px rgba(0,0,0,0.9);
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    /* ANIMACJA MRUGAJĄCEGO NEONU */
    @keyframes neon-blink {
        0%, 18%, 22%, 25%, 53%, 57%, 100% { 
            text-shadow: 0 0 5px #ff0055, 0 0 15px #ff0055, 0 0 30px #ff0055, 0 0 50px #ff0055; 
            color: #ff0055; 
        }
        20%, 24%, 55% { 
            text-shadow: none; 
            color: #444; 
        }
    }
    
    .neon-text {
        font-family: 'Bungee Inline', cursive !important;
        font-size: 3rem;
        text-align: center;
        letter-spacing: 5px;
        animation: neon-blink 3s infinite alternate;
        margin-bottom: 20px;
    }

    h1, h2 { font-family: 'Bungee Inline', cursive !important; color: #ff0055; text-shadow: 2px 2px 0px #000; }
    h3 { font-family: 'Pacifico', cursive !important; color: #00b4d8 !important; font-size: 2.2rem !important; text-shadow: 1px 1px 0px #000;}

    /* Pasek boczny - WURLITZER JUKEBOX */
    [data-testid="stSidebar"] {
        background: repeating-linear-gradient( 0deg, #8a0c10, #8a0c10 15px, #d90429 15px, #d90429 30px );
        border-right: 15px ridge #ffb703; /* Chrom/Złoto */
        box-shadow: inset -10px 0 20px rgba(0,0,0,0.7);
    }
    [data-testid="stSidebarNav"], [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #fffdf5 !important; font-family: 'Space Mono', monospace; font-weight: 900; font-size: 1.1rem;
        text-shadow: 2px 2px 0px #000;
    }

    /* EKRAN KASY FISKALNEJ (Z efektem Scanlines!) */
    div[data-testid="metric-container"] {
        background-color: #000;
        /* Efekt starych monitorów kineskopowych CRT */
        background-image: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(57, 255, 20, 0.1) 2px, rgba(57, 255, 20, 0.1) 4px);
        border: 8px outset #8d99ae; /* Srebrny chrom */
        border-radius: 10px;
        padding: 20px;
        box-shadow: inset 0px 0px 20px rgba(0,0,0,1), 8px 8px 0px #d90429;
        text-align: center;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Press Start 2P', monospace !important; /* Cyfrowa czcionka */
        color: #39ff14 !important; /* Jaskrawa zieleń */
        text-shadow: 0 0 10px #39ff14;
        font-size: 1.8rem !important;
        padding-top: 10px;
    }
    [data-testid="stMetricLabel"] {
        color: #fffdf5 !important;
        font-family: 'Pacifico', cursive !important;
        font-size: 1.3rem !important;
    }

    /* KARTY HERO - Neonowy Szyld Drive-In */
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    .hero-card {
        background: #111;
        border: 6px dashed #00f5d4;
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 0 20px #00f5d4, inset 0 0 30px #00f5d4;
        text-align: center;
        animation: float 4s ease-in-out infinite;
    }
    .hero-card.danger { border-color: #ff0055; box-shadow: 0 0 20px #ff0055, inset 0 0 30px #ff0055; }
    .hero-card h2 {
        color: #00f5d4 !important; text-shadow: 0 0 15px #00f5d4; font-size: 3.5rem !important;
        font-family: 'Space Mono', monospace !important; margin: 15px 0;
    }
    .hero-card.danger h2 { color: #ff0055 !important; text-shadow: 0 0 15px #ff0055; }
    .hero-card p {
        color: #fffdf5 !important; font-family: 'Pacifico', cursive !important; font-size: 1.8rem; margin: 0;
    }

    /* PRZYCISKI - Wibrujące i Rockandrollowe */
    @keyframes wiggle {
        0%, 100% { transform: rotate(0deg); }
        25% { transform: rotate(-2deg); }
        75% { transform: rotate(2deg); }
    }
    .stButton>button {
        background-color: #ffb703; color: #1a1a1a !important;
        border: 4px solid #1a1a1a; border-radius: 50px; /* Owalne jak piguły */
        font-weight: 900; font-family: 'Space Mono', monospace; font-size: 1.2rem;
        text-transform: uppercase; box-shadow: 6px 6px 0px #1a1a1a;
        transition: all 0.1s;
    }
    .stButton>button:hover {
        transform: translate(3px, 3px); box-shadow: 3px 3px 0px #1a1a1a;
        background-color: #fb8500; animation: wiggle 0.3s ease-in-out infinite;
    }

    /* Formularze i Tabele */
    input, select { border: 3px solid #111 !important; border-radius: 8px !important; font-weight: bold; }
    .stDataFrame { border: 4px solid #111; border-radius: 10px; box-shadow: 5px 5px 0 #111;}
    
    /* MARQUEE KINO DRIVE-IN */
    .drive-in-sign {
        background-color: #111; color: #ffb703; font-family: 'Press Start 2P', monospace;
        padding: 10px; border: 4px inset #8d99ae; font-size: 1.2rem; margin-bottom: 30px;
        box-shadow: 0 0 10px #000;
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
        st.error(f"Silnik zgasł: {e}")
        return None

sh = init_connection()

def load_df(sheet_name):
    try:
        df = pd.DataFrame(sh.worksheet(sheet_name).get_all_records())
        if not df.empty and 'Data' in df.columns: df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        return df
    except: return pd.DataFrame()

def save_df(sheet_name, df):
    sheet = sh.worksheet(sheet_name)
    sheet.clear()
    df_save = df.copy()
    if 'Data' in df_save.columns: df_save['Data'] = df_save['Data'].dt.strftime('%Y-%m-%d %H:%M:%S')
    sheet.update([df_save.columns.values.tolist()] + df_save.fillna("").values.tolist())
    st.balloons()
    st.toast(f"🎸 YEAH! Taśma nagrana: {sheet_name}!", icon="🕺")

# --- MENU BOCZNE (SZAFA GRAJĄCA) ---
st.sidebar.markdown("<h1 style='color:#ffb703 !important; text-shadow: 2px 2px 0 #111; text-align:center;'>🎵 WURLITZER</h1>", unsafe_allow_html=True)
miesiące = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
wybrany_m = st.sidebar.selectbox("Strona A (Miesiąc):", miesiące, index=datetime.now().month - 1)
wybrany_rok = st.sidebar.selectbox("Strona B (Rok):", [2024, 2025, 2026], index=2)

m_idx = miesiące.index(wybrany_m) + 1
selected_date = date(wybrany_rok, m_idx, 1)

st.sidebar.markdown("---")
menu = st.sidebar.radio("Wciśnij Gumbik:", [
    "🍔 Drive-In (Kokpit)", 
    "🍟 Szybki Szam (Wydatki)", 
    "🧾 Haracz (Koszty Stałe)", 
    "💵 Wypłata (Przychody)", 
    "🎸 Szafa Grająca (Oszczędności)"
])

# --- WIDOKI ---
if menu == "🍔 Drive-In (Kokpit)":
    st.markdown("<div class='neon-text'>ROUTE 66 BUDGET</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='drive-in-sign'><marquee>⭐ DZIŚ W REPERTUARZE: BILANS NA {wybrany_m.upper()} {wybrany_rok} ⭐ ZAPINAJCIE PASY KOCIAKI! ⭐</marquee></div>", unsafe_allow_html=True)
    
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
    if dzis.month == m_idx and dzis.year == wybrany_rok: pozostalo_dni = ostatni_dzien - dzis.day + 1
    elif selected_date < dzis: pozostalo_dni = 0
    else: pozostalo_dni = ostatni_dzien
        
    dniowka = wolne / pozostalo_dni if pozostalo_dni > 0 and wolne > 0 else 0

    c_h1, c_h2 = st.columns(2)
    with c_h1:
        st.markdown(f"<div class='hero-card'><p>Szmalu na balety</p><h2>{wolne:,.2f} zł</h2></div>", unsafe_allow_html=True)
    with c_h2:
        klasa_karty = "hero-card danger" if dniowka < 50 else "hero-card"
        st.markdown(f"""
        <div class='{klasa_karty}'>
            <p>Dniówka na milkshaki (przez {pozostalo_dni} dni)</p>
            <h2>{dniowka:,.2f} zł</h2>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Wpadło Zielonych", f"{s_prz:,.2f} zł")
    col2.metric("Podatek od Życia", f"{s_zobowiazania:,.2f} zł")
    col3.metric("Dzisiejsze Frytki", f"{s_codzienne:,.2f} zł")
    col4.metric("Skarbonka w Cadillaku", f"{w_osz:,.2f} zł")

elif menu == "🍟 Szybki Szam (Wydatki)":
    st.markdown("<h1 style='text-align:center;'>🍟 Bierz na Wynos!</h1>", unsafe_allow_html=True)
    st.write("### Czas to pieniądz, kociaku! Kasa bije datę sama, wpisz tylko cyfry.")
    
    with st.form("quick_add", clear_on_submit=True):
        c1, c2, c3 = st.columns([2,1,1])
        nazwa = c1.text_input("Na co poszedł szmal?")
        kwota = c2.number_input("Ile baksów? (zł)", min_value=0.0, step=1.0)
        kat = c3.selectbox("Rodzaj baletu", ["Szama w Dinerze", "Paliwo do Cadillaca", "Dancing & Kino", "Chemia & Dom", "Lekarz", "Inne bajery"])
        if st.form_submit_button("🛎️ DING! NABIJ NA KASĘ"):
            if kwota > 0 and nazwa:
                teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sh.worksheet("Wydatki").append_row([teraz, nazwa, kat, kwota])
                st.toast("Zamówienie u kucharza!", icon="🍳")
                st.rerun()

    df_w = load_df("Wydatki")
    if not df_w.empty:
        st.write("### Ostatnie Rolki z Kasy Fiskalnej")
        ed_w = st.data_editor(df_w.sort_values("Data", ascending=False), hide_index=True, use_container_width=True)
        if st.button("💾 Potwierdź poprawki w księdze"): save_df("Wydatki", ed_w)

elif menu == "🧾 Haracz (Koszty Stałe)":
    st.markdown("<h1 style='text-align:center;'>🧾 Podatek od Luksusu</h1>", unsafe_allow_html=True)
    st.write("### Twardy biznes. Cennik rzeczy, które płacimy co miesiąc wujkowi Samowi.")
    
    with st.form("add_zob", clear_on_submit=True):
        st.write("### 📝 Wypisz weksel")
        c1, c2 = st.columns(2)
        n = c1.text_input("Dla kogo ta forsa? (np. Netflix, Czynsz, Mafia)")
        k = c2.number_input("Ile co miesiąc?", min_value=0.0)
        typ = st.selectbox("Typ rachunku", ["Subskrypcja (Kino/Muzyka)", "Koszt Stały (Rachunki)", "Rata za Cadillaca (Kredyt)"])
        if st.form_submit_button("🔥 Podpisz Krwią (Dodaj)"):
            if n and k > 0:
                sh.worksheet("Zobowiazania").append_row([n, typ, k])
                st.rerun()
                
    df_z = load_df("Zobowiazania")
    if not df_z.empty:
        st.write("### Zeszyt Dłużników")
        ed_z = st.data_editor(df_z, hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zamknij Sejf"): save_df("Zobowiazania", ed_z)

elif menu == "💵 Wypłata (Przychody)":
    st.markdown("<h1 style='text-align:center;'>💵 Gruby Portfel</h1>", unsafe_allow_html=True)
    with st.form("add_prz", clear_on_submit=True):
        c1, c2 = st.columns(2)
        zrodlo = c1.text_input("Kto sypnął groszem? (np. Szef, Pokaż z rock'n'rolla)")
        kwota = c2.number_input("Ile zielonych?", min_value=0.0)
        forma = st.selectbox("Forma zapłaty", ["Przelew na konto", "Złoto w gotówce", "Czek z banku"])
        if st.form_submit_button("🎰 Otwórz Szufladę i Zwiń Kasę"):
            if zrodlo and kwota > 0:
                sh.worksheet("Przychody").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), zrodlo, forma, kwota])
                st.rerun()

    df_p = load_df("Przychody")
    if not df_p.empty:
        st.write("### Rejestr Księgowego")
        ed_p = st.data_editor(df_p.sort_values("Data", ascending=False), hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zatwierdź Bilanse"): save_df("Przychody", ed_p)

elif menu == "🎸 Szafa Grająca (Oszczędności)":
    st.markdown("<h1 style='text-align:center;'>🎸 Złota Szafa Grająca</h1>", unsafe_allow_html=True)
    st.write("### Wrzuć monetę na lepsze czasy. Nie bądź zgredem, odkładaj szmal!")
    with st.form("add_osz", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        cel = c1.text_input("Na jaki odjazd zbieramy?")
        kwota = c2.number_input("Ile wrzucasz?", min_value=0.0)
        akcja = c3.selectbox("Co robimy, szefie?", ["Wpłata (Zasilamy Jukebox)", "Wypłata (Rozbijamy szybę)"])
        if st.form_submit_button("🎵 Wciśnij Guzik Jukeboxa"):
            if cel and kwota > 0:
                czysta_akcja = "Wpłata" if "Wpłata" in akcja else "Wypłata"
                sh.worksheet("Oszczednosci").append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cel, kwota, czysta_akcja])
                st.rerun()

    df_o = load_df("Oszczednosci")
    if not df_o.empty:
        st.write("### Historia Błyszczących Monet")
        ed_o = st.data_editor(df_o.sort_values("Data", ascending=False), hide_index=True, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Zarygluj Szafę na Kłódkę"): save_df("Oszczednosci", ed_o)
