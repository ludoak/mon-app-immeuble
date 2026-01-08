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

# --- CHARGEMENT DES DONNÉES ---
df_base = charger_donnees()

st.title("🏢 Rapport d'Intervention ImmoCheck")

# --- BARRE LATÉRALE : GESTION DES LOCATAIRES ---
with st.sidebar:
    st.header("👥 Base Locataires")
    st.info("Utilisez cette section pour enregistrer un nouveau locataire dans la base Google.")
    res_a = st.selectbox("Résidence", ["Canterane", "La Dussaude"], key="res_sidebar")
    
    if res_a == "Canterane":
        bat_a = st.radio("Bâtiment", ["A", "B"], horizontal=True)
        app_a = st.text_input("N° Appartement")
        cle_loc = f"Canterane - Bat {bat_a} - Appt {app_a}"
    else:
        app_a = st.number_input("N° Appartement", 1, 95)
        cle_loc = f"La Dussaude - Appt {app_a}"
    
    nom_a = st.text_input("Nom du locataire")
    if st.button("💾 Enregistrer le locataire"):
        sauvegarder_locataire(cle_loc, nom_a)
        st.success("Enregistré dans Google Sheets !")
        st.rerun()

# --- FORMULAIRE PRINCIPAL ---
st.subheader("📝 Nouveau Constat")

with st.form("rapport_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        residence = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"])
        if residence == "Canterane":
            batiment = st.radio("Bâtiment", ["A", "B"], horizontal=True)
            appartement = st.text_input("N° Appt")
            id_logement = f"Canterane - Bat {batiment} - Appt {appartement}"
        else:
            appartement = st.number_input("N° Appt", 1, 95)
            id_logement = f"La Dussaude - Appt {appartement}"

    with col2:
        date_visite = st.date_input("📅 Date d'intervention", format="DD/MM/YYYY")
        urgence = st.select_slider("🚦 Degré d'urgence", options=["Faible", "Moyenne", "Haute"])

    st.divider()

    # --- RECHERCHE AUTOMATIQUE DU NOM ---
    nom_locataire = ""
    if not df_base.empty and id_logement in df_base['Logement'].values:
        nom_locataire = df_base.loc[df_base['Logement'] == id_logement, 'Nom'].values[0]
    
    st.text_input("👤 Locataire (auto)", value=nom_locataire, disabled=True)
    
    # --- PROBLÈMES TECHNIQUES ---
    type_probleme = st.selectbox("🛠️ Type de problème", [
        "Plomberie (Fuite, robinet, chasse d'eau)",
        "Chauffage / Eau Chaude",
        "Électricité (Prise, tableau, éclairage)",
        "VMC / Ventilation",
        "Serrurerie / Porte",
        "Infiltration / Humidité",
        "Autre (Préciser dans les notes)"
    ])
    
    observations = st.text_area("🗒️ Observations détaillées", placeholder="Décrivez le problème constaté...")

    soumettre = st.form_submit_button("🚀 GÉNÉRER LE RAPPORT")

# --- AFFICHAGE DU RÉSULTAT ---
if soumettre:
    st.success("Rapport généré ! Copiez le texte ci-dessous :")
    
    msg = f"""*RAPPORT D'INTERVENTION* 🏢
----------------------------------
📍 *Lieu :* {id_logement} ({residence})
👤 *Locataire :* {nom_locataire if nom_locataire else "Non renseigné"}
📅 *Date :* {date_visite.strftime('%d/%m/%Y')}
🚦 *Urgence :* {urgence}

🛠️ *Type de problème :* {type_probleme}
📝 *Constat :* {observations}

----------------------------------
_Généré par ImmoCheck Pro_"""
    
    st.code(msg, language="text")
    st.info("💡 Vous pouvez maintenant copier ce texte et l'envoyer par SMS ou Email.")
