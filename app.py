import streamlit as st
from datetime import date
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuration
st.set_page_config(page_title="ImmoCheck Pro GS", page_icon="🏢", layout="wide")

# --- CONNEXION GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def charger_donnees():
    try:
        return conn.read(worksheet="Locataires", ttl=0)
    except:
        return pd.DataFrame(columns=["Logement", "Nom"])

def sauvegarder_locataire(logement, nom):
    df = charger_donnees()
    # Si le logement existe déjà, on met à jour, sinon on ajoute
    if logement in df['Logement'].values:
        df.loc[df['Logement'] == logement, 'Nom'] = nom
    else:
        new_row = pd.DataFrame({"Logement": [logement], "Nom": [nom]})
        df = pd.concat([df, new_row], ignore_index=True)
    
    conn.update(worksheet="Locataires", data=df)
    st.cache_data.clear()

def supprimer_locataire(logement):
    df = charger_donnees()
    df = df[df['Logement'] != logement]
    conn.update(worksheet="Locataires", data=df)
    st.cache_data.clear()

# --- INTERFACE ---
st.title("🏢 Gestion Immobilière (Cloud)")

# Menu latéral
with st.sidebar:
    st.header("👥 Base Locataires")
    tab_a, tab_s = st.tabs(["➕ Ajouter", "🗑️ Supprimer"])
    
    with tab_a:
        res_a = st.selectbox("Résidence", ["Canterane", "La Dussaude"], key="ra")
        if res_a == "Canterane":
            bat_a = st.radio("Bâtiment", ["A", "B"], horizontal=True)
            app_a = st.text_input("N° Appt", key="aa")
            cle = f"Canterane - Bat {bat_a} - Appt {app_a}"
        else:
            app_a = st.number_input("N° Appt", 1, 95)
            cle = f"La Dussaude - Appt {app_a}"
        
        nom_a = st.text_input("Nom")
        if st.button("Enregistrer"):
            sauvegarder_locataire(cle, nom_a)
            st.success("Enregistré dans Google Sheets !")
            st.rerun()

    with tab_s:
        df_current = charger_donnees()
        if not df_current.empty:
            log_s = st.selectbox("Supprimer", df_current['Logement'].tolist())
            if st.button("Confirmer suppression"):
                supprimer_locataire(log_s)
                st.error("Supprimé !")
                st.rerun()

# Formulaire Principal
df_base = charger_donnees()
with st.form("rapport"):
    res = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"])
    col1, col2 = st.columns(2)
    with col1:
        if res == "Canterane":
            bat = st.radio("Bâtiment", ["A", "B"], horizontal=True)
            n = st.text_input("Appt")
            id_l = f"Canterane - Bat {bat} - Appt {n}"
        else:
            n = st.number_input("Appt", 1, 95)
            id_l = f"La Dussaude - Appt {n}"
        
        # Recherche dans le DataFrame Google Sheets
        nom_trouve = ""
        if not df_base.empty and id_l in df_base['Logement'].values:
            nom_trouve = df_base.loc[df_base['Logement'] == id_l, 'Nom'].values[0]
        
        nom = st.text_input("👤 Locataire", value=nom_trouve)

    with col2:
        d = st.date_input("📅 Date", format="DD/MM/YYYY")
        p = st.selectbox("🚦 Urgence", ["Faible", "Moyenne", "Haute"])

    cat = st.selectbox("🛠️ Type", ["Plomberie", "Chauffage", "Électricité", "VMC", "Serrurerie", "Autre"])
    notes = st.text_area("Observations")

    if st.form_submit_button("GÉNÉRER"):
        msg = f"Bonjour,\nPassage le {d.strftime('%d/%m/%Y')} - {res}\n📍 {id_l}\n👤 Locataire : {nom}\n\nConstat : {cat}\nNote : {notes}"
        st.code(msg)


