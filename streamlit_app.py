import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- KONFIGURACJA ---
st.set_page_config(page_title="Nasz Budżet PRO", page_icon="🏦", layout="wide")

# --- STYLIZACJA GLASSMORPHISM ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .stButton>button {
        border-radius: 10px;
        background: #4A90E2;
        color: white;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); background: #357ABD; }
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
        st.error(f"Połączenie przerwane: {e}")
        return None

sh = init_connection()

# --- LOGIKA DANYCH ---
def load_df(sheet_name):
    try:
        data = sh.worksheet(sheet_name).get_all_records()
        df = pd.DataFrame(data)
        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        if 'Data końca' in df.columns:
            df['Data końca'] = pd.to_datetime(df['Data końca'], errors='coerce')
        return df
    except:
        return pd.DataFrame()

def save_df(sheet_name, df):
    sheet = sh.worksheet(sheet_name)
    sheet.clear()
    df_to_save = df.copy()
    for col in df_to_save.select_dtypes(include=['datetime64']).columns:
        df_to_save[col] = df_to_save[col].dt.strftime('%Y-%m-%d')
    sheet.update([df_to_save.columns.values.tolist()] + df_to_save.fillna("").values.tolist())
    st.toast("Dane zapisane!")

# --- AUTOMATYZACJA KOSZTÓW ---
def run_monthly_billing(month_date):
    wydatki_df = load_df("Wydatki")
    month_str = month_date.strftime("%Y-%m")
    
    # Sprawdź czy już naliczono koszty dla tego miesiąca
    already_billed = wydatki_df[
        (wydatki_df['Data'].dt.strftime("%Y-%m") == month_str) & 
        (wydatki_df['Nazwa'].str.contains("AUTOMAT:"))
    ]
    
    if already_billed.empty:
        # Szukaj kosztów stałych i subskrypcji, które są aktywne
        aktywne = wydatki_df[
            ((wydatki_df['Typ'].str.contains("Stały")) | (wydatki_df['Kategoria'] == "Subskrypcje")) &
            (wydatki_df['Data'] < month_date) &
            ((wydatki_df['Data końca'].isna()) | (wydatki_df['Data końca'] >= month_date)) &
            (~wydatki_df['Nazwa'].str.contains("AUTOMAT:"))
        ].copy()
        
        if not aktywne.empty:
            if st.sidebar.button(f"🚀 Naliczyć koszty na {month_str}?"):
                for _, row in aktywne.iterrows():
                    new_row = [
                        month_date.strftime("%Y-%m-01"),
                        f"AUTOMAT: {row['Nazwa']}",
                        row['Kategoria'],
                        row['Typ'],
                        row['Kwota'],
                        row['Data końca'].strftime('%Y-%m-%d') if pd.notnull(row['Data końca']) else ""
                    ]
                    sh.worksheet("Wydatki").append_row(new_row)
                st.rerun()

# --- SIDEBAR ---
st.sidebar.title("💎 Nawigacja")
selected_month = st.sidebar.date_input("Wybierz miesiąc do analizy", datetime.now().replace(day=1))
run_monthly_billing(selected_month)
menu = st.sidebar.radio("Sekcja", ["🏠 Kokpit", "📥 Wpływy", "💸 Wydatki", "📅 Raty", "🐷 Oszczędności"])

# Filtracja danych dla wybranego miesiąca
def filter_month(df):
    if df.empty: return df
    return df[df['Data'].dt.strftime("%Y-%m") == selected_month.strftime("%Y-%m")]

# --- WIDOKI ---
if menu == "🏠 Kokpit":
    st.title(f"📊 Bilans: {selected_month.strftime('%B %Y')}")
    
    prz = filter_month(load_df("Przychody"))
    wyd = filter_month(load_df("Wydatki"))
    raty = load_df("Raty") # Raty zazwyczaj stałe miesięcznie
    osz = load_df("Oszczednosci")
    
    total_in = prz['Kwota'].sum() if not prz.empty else 0
    total_out = wyd['Kwota'].sum() if not wyd.empty else 0
    total_raty = raty['Kwota raty'].sum() if not raty.empty else 0
    
    # Bilans Oszczędnościowy (Suma wszystkich wpłat - wypłat)
    total_savings = osz[osz['Typ'] == 'Wpłata']['Kwota'].sum() - osz[osz['Typ'] == 'Wypłata']['Kwota'].sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wpływy", f"{total_in:,.2f} zł")
    c2.metric("Wydatki", f"{total_out:,.2f} zł")
    c3.metric("Raty", f"{total_raty:,.2f} zł")
    c4.metric("Wolne środki", f"{(total_in - total_out - total_raty):,.2f} zł")
    
    st.markdown("---")
    st.subheader(f"🐷 Całkowite oszczędności: {total_savings:,.2f} zł")
    
    if not wyd.empty:
        st.write("### Rozkład wydatków")
        st.bar_chart(wyd.groupby("Kategoria")["Kwota"].sum())

elif menu == "💸 Wydatki":
    st.title("💸 Rejestr Wydatków")
    
    with st.expander("➕ Dodaj nowy koszt (stały lub zmienny)"):
        with st.form("wyd_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nazwa = c1.text_input("Nazwa")
            kwota = c2.number_input("Kwota", min_value=0.0)
            kat = c1.selectbox("Kategoria", ["Dom", "Jedzenie", "Subskrypcje", "Transport", "Dzieci", "Rozrywka", "Inne"])
            typ = c2.selectbox("Rodzaj", ["Zmienny", "Stały"])
            data_konca = st.date_input("Data zakończenia (opcjonalnie, tylko dla stałych)", value=None)
            
            if st.form_submit_button("Zapisz"):
                sh.worksheet("Wydatki").append_row([
                    datetime.now().strftime("%Y-%m-%d"), nazwa, kat, typ, kwota, 
                    data_konca.strftime("%Y-%m-%d") if data_konca else ""
                ])
                st.rerun()

    df_w = load_df("Wydatki")
    if not df_w.empty:
        st.write("### Pełna lista (Możesz edytować datę końca)")
        ed_w = st.data_editor(df_w, num_rows="dynamic", use_container_width=True)
        if st.button("Zapisz zmiany w tabeli"):
            save_df("Wydatki", ed_w)

elif menu == "🐷 Oszczędności":
    st.title("🐷 Kasa Oszczędnościowa")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.form("osz_form"):
            cel = st.text_input("Cel (np. Fundusz Wakacyjny)")
            kw = st.number_input("Kwota", min_value=0.0)
            t = st.selectbox("Typ", ["Wpłata", "Wypłata"])
            if st.form_submit_button("Dodaj operację"):
                sh.worksheet("Oszczednosci").append_row([datetime.now().strftime("%Y-%m-%d"), cel, kw, t])
                st.rerun()
                
    df_o = load_df("Oszczednosci")
    if not df_o.empty:
        st.write("### Historia oszczędności")
        st.dataframe(df_o, use_container_width=True)

# Reszta sekcji (Wpływy, Raty) analogicznie jak wcześniej...
