import streamlit as st
from datetime import date
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuration simple
st.set_page_config(page_title="ImmoCheck Pro", page_icon="🏢", layout="wide")

# --- CONNEXION GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(worksheet="Locataires", ttl=0)
except Exception as e:
    st.error(f"Erreur de connexion au tableau : {e}")
    df_base = pd.DataFrame(columns=["Logement", "Nom"])

# --- INTERFACE ---
st.title("🏢 Rapport d'Intervention")

# Barre latérale pour gérer les locataires
with st.sidebar:
    st.header("👥 Base Locataires")
    if st.button("🔄 Actualiser la liste"):
        st.rerun()
    
    st.info("Utilisez votre Google Sheet pour modifier la liste des locataires pour le moment.")

# Formulaire Principal
with st.form("rapport"):
    res = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"])
    
    if res == "Canterane":
        bat = st.radio("Bâtiment", ["A", "B"], horizontal=True)
        n = st.text_input("N° Appt")
        id_l = f"Canterane - Bat {bat} - Appt {n}"
    else:
        n = st.number_input("N° Appt", 1, 95)
        id_l = f"La Dussaude - Appt {n}"
    
    # Recherche du nom
    nom_trouve = ""
    if not df_base.empty and id_l in df_base['Logement'].values:
        nom_trouve = df_base.loc[df_base['Logement'] == id_l, 'Nom'].values[0]
    
    nom = st.text_input("👤 Nom du Locataire", value=nom_trouve)
    cat = st.selectbox("🛠️ Type", ["Plomberie", "Chauffage", "Électricité", "VMC", "Serrurerie", "Autre"])
    notes = st.text_area("Observations")

    if st.form_submit_button("GÉNÉRER LE MESSAGE"):
        msg = f"Passage le {date.today().strftime('%d/%m/%Y')}\n📍 {id_l}\n👤 Locataire : {nom}\n🛠️ {cat}\n📝 {notes}"
        st.code(msg)
