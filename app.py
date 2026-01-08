import streamlit as st
from datetime import date
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="ImmoCheck Pro", page_icon="🏢", layout="wide")

# --- CONNEXION GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def charger_donnees():
    try:
        return conn.read(worksheet="Locataires", ttl="0")
    except:
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

def supprimer_locataire(logement):
    df = charger_donnees()
    df = df[df['Logement'] != logement]
    conn.update(worksheet="Locataires", data=df)
    st.cache_data.clear()

# --- CHARGEMENT DES DONNÉES ---
df_base = charger_donnees()

st.title("🏢 Rapport d'Intervention ImmoCheck")

# --- BARRE LATÉRALE : GESTION DES LOCATAIRES ---
with st.sidebar:
    st.header("👥 Base Locataires")
    
    tab_ajout, tab_suppr = st.tabs(["➕ Ajouter", "🗑️ Supprimer"])
    
    with tab_ajout:
        res_a = st.selectbox("Résidence", ["Canterane", "La Dussaude"], key="res_add")
        if res_a == "Canterane":
            bat_a = st.radio("Bâtiment", ["A", "B"], horizontal=True, key="bat_add")
            app_a = st.text_input("N° Appt", key="app_add")
            cle_loc = f"Canterane - Bat {bat_a} - Appt {app_a}"
        else:
            app_a = st.number_input("N° Appt", 1, 95, key="app_add_duss")
            cle_loc = f"La Dussaude - Appt {app_a}"
        
        nom_a = st.text_input("Nom du locataire", key="nom_add")
        if st.button("💾 Enregistrer"):
            sauvegarder_locataire(cle_loc, nom_a)
            st.success("Enregistré !")
            st.rerun()

    with tab_suppr:
        if not df_base.empty:
            log_a_supprimer = st.selectbox("Choisir le logement à vider", df_base['Logement'].tolist())
            if st.button("❌ Confirmer suppression"):
                supprimer_locataire(log_a_supprimer)
                st.warning(f"Locataire de {log_a_supprimer} supprimé")
                st.rerun()
        else:
            st.write("La base est vide.")

# --- FORMULAIRE PRINCIPAL ---
st.subheader("📝 Nouveau Constat")

# Sélection du logement HORS du formulaire pour la recherche instantanée
col1, col2 = st.columns(2)
with col1:
    res_search = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"], key="res_s")
    if res_search == "Canterane":
        bat_s = st.radio("Bâtiment", ["A", "B"], horizontal=True, key="bat_s")
        app_s = st.text_input("N° Appt", key="app_s")
        id_logement = f"Canterane - Bat {bat_s} - Appt {app_s}"
    else:
        app_s = st.number_input("N° Appt", 1, 95, key="app_s_duss")
        id_logement = f"La Dussaude - Appt {app_s}"

# RECHERCHE DU NOM (Instantane)
nom_locataire = ""
if not df_base.empty and id_logement in df_base['Logement'].values:
    nom_locataire = df_base.loc[df_base['Logement'] == id_logement, 'Nom'].values[0]

with col2:
    date_visite = st.date_input("📅 Date", format="DD/MM/YYYY")
    st.text_input("👤 Locataire identifié", value=nom_locataire, disabled=True)

# Début du formulaire pour le reste des infos
with st.form("rapport_technique"):
    urgence = st.select_slider("🚦 Urgence", options=["Faible", "Moyenne", "Haute"])
    
    type_probleme = st.selectbox("🛠️ Type de problème", [
        "Plomberie (Fuite, robinet, chasse d'eau)",
        "Chauffage / Eau Chaude",
        "Électricité (Prise, tableau, éclairage)",
        "VMC / Ventilation",
        "Serrurerie / Porte",
        "Infiltration / Humidité",
        "Autre"
    ])
    
    observations = st.text_area("🗒️ Observations")

    soumettre = st.form_submit_button("🚀 GÉNÉRER LE RAPPORT")

# --- AFFICHAGE DU MESSAGE ---
if soumettre:
    msg = f"""*RAPPORT D'INTERVENTION* 🏢
----------------------------------
📍 *Lieu :* {id_logement}
👤 *Locataire :* {nom_locataire if nom_locataire else "Non renseigné"}
📅 *Date :* {date_visite.strftime('%d/%m/%Y')}
🚦 *Urgence :* {urgence}

🛠️ *Type :* {type_probleme}
📝 *Constat :* {observations}
----------------------------------"""
    st.code(msg, language="text")
