import streamlit as st
from datetime import date
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="ImmoCheck Pro", page_icon="🏢", layout="wide")

# Connexion utilisant les Secrets (Service Account)
conn = st.connection("gsheets", type=GSheetsConnection)

def charger_donnees():
    try:
        # On lit la feuille 'Locataires'
        return conn.read(worksheet="Locataires", ttl="0")
    except Exception as e:
        return pd.DataFrame(columns=["Logement", "Nom"])

def sauvegarder_locataire(logement, nom):
    df = charger_donnees()
    if logement in df['Logement'].values:
        df.loc[df['Logement'] == logement, 'Nom'] = nom
    else:
        new_row = pd.DataFrame({"Logement": [logement], "Nom": [nom]})
        df = pd.concat([df, new_row], ignore_index=True)
    
    conn.update(worksheet="Locataires", data=df)
    st.cache_data.clear()

# --- INTERFACE ---
st.title("🏢 Gestion Immobilière")

# Chargement initial
df_base = charger_donnees()

with st.sidebar:
    st.header("👥 Base Locataires")
    res_a = st.selectbox("Résidence", ["Canterane", "La Dussaude"])
    if res_a == "Canterane":
        bat_a = st.radio("Bâtiment", ["A", "B"], horizontal=True)
        app_a = st.text_input("N° Appt")
        cle = f"Canterane - Bat {bat_a} - Appt {app_a}"
    else:
        app_a = st.number_input("N° Appt", 1, 95)
        cle = f"La Dussaude - Appt {app_a}"
    
    nom_a = st.text_input("Nom du locataire")
    if st.button("Enregistrer / Mettre à jour"):
        sauvegarder_locataire(cle, nom_a)
        st.success("Synchronisé avec Google Sheets !")
        st.rerun()

# Formulaire principal
st.subheader("Rapport d'intervention")
with st.form("rapport"):
    # ... (Le reste de ton formulaire de rapport habituel)
    res = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"])
    # Recherche du nom
    id_l = cle if 'cle' in locals() else "" # Simplifié pour l'exemple
    nom_trouve = ""
    if not df_base.empty and id_l in df_base['Logement'].values:
        nom_trouve = df_base.loc[df_base['Logement'] == id_l, 'Nom'].values[0]
    
    st.text_input("👤 Locataire identifié", value=nom_trouve, disabled=True)
    st.form_submit_button("Générer Rapport")
