import streamlit as st
from datetime import date
import json
import os

st.set_page_config(page_title="ImmoCheck Pro", page_icon="🏢", layout="wide")

# --- 1. GESTION DE LA MÉMOIRE ---
FILE_LOCATAIRES = "liste_locataires.json"

def charger_locataires():
    if os.path.exists(FILE_LOCATAIRES):
        with open(FILE_LOCATAIRES, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def sauvegarder_tous_locataires(dictionnaire):
    with open(FILE_LOCATAIRES, "w", encoding="utf-8") as f:
        json.dump(dictionnaire, f, indent=4, ensure_ascii=False)

if 'locataires' not in st.session_state:
    st.session_state['locataires'] = charger_locataires()

# --- 2. BARRE LATÉRALE (AJOUT & SUPPRESSION) ---
with st.sidebar:
    st.header("👥 Gestion des Locataires")
    
    # Onglets pour séparer l'ajout de la suppression
    tab_ajout, tab_suppr = st.tabs(["➕ Ajouter", "🗑️ Supprimer"])
    
    with tab_ajout:
        res_add = st.selectbox("Résidence", ["Canterane", "La Dussaude"], key="res_a")
        if res_add == "Canterane":
            bat_add = st.radio("Bâtiment", ["Bâtiment A", "Bâtiment B"], horizontal=True, key="bat_a")
            appt_add = st.text_input("N° Appartement", key="appt_a")
            cle_loc = f"Canterane - {bat_add} - Appt {appt_add}"
        else:
            appt_add = st.number_input("N° Appartement (1-95)", 1, 95, key="appt_d_a")
            cle_loc = f"La Dussaude - Appt {appt_add}"
        
        nom_add = st.text_input("Nom du locataire entrant", key="nom_a")
        
        if st.button("Enregistrer"):
            if nom_add and (appt_add or res_add == "La Dussaude"):
                st.session_state['locataires'][cle_loc] = nom_add
                sauvegarder_tous_locataires(st.session_state['locataires'])
                st.success(f"Enregistré : {nom_add}")
                st.rerun()

    with tab_suppr:
        st.write("Choisissez le logement à vider :")
        # On ne propose que les logements qui ont un locataire enregistré
        if st.session_state['locataires']:
            logement_a_suppr = st.selectbox("Logement occupé", list(st.session_state['locataires'].keys()))
            nom_actuel = st.session_state['locataires'][logement_a_suppr]
            
            st.warning(f"Locataire actuel : **{nom_actuel}**")
            
            if st.button("Confirmer le départ"):
                del st.session_state['locataires'][logement_a_suppr]
                sauvegarder_tous_locataires(st.session_state['locataires'])
                st.error(f"Le logement {logement_a_suppr} est désormais vide.")
                st.rerun()
        else:
            st.info("Aucun locataire en base.")

# --- 3. FORMULAIRE PRINCIPAL (Identique) ---
st.title("🏢 Rapport d'Intervention")

with st.form("rapport_form"):
    residence = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"])
    col1, col2 = st.columns(2)
    
    with col1:
        if residence == "Canterane":
            batiment = st.radio("Bâtiment", ["Bâtiment A", "Bâtiment B"], horizontal=True)
            n_appt = st.text_input("N° Appartement")
            id_logement = f"Canterane - {batiment} - Appt {n_appt}"
        else:
            n_appt = st.number_input("N° Appartement (1 à 95)", 1, 95)
            id_logement = f"La Dussaude - Appt {n_appt}"
        
        nom_auto = st.session_state['locataires'].get(id_logement, "")
        nom_locataire = st.text_input("👤 Locataire", value=nom_auto)

    with col2:
        date_visite = st.date_input("📅 Date d'intervention", value=date.today(), format="DD/MM/YYYY")
        priorite = st.selectbox("🚦 Urgence", ["Faible", "Moyenne", "Haute"])

    categorie = st.selectbox("🛠️ Catégorie", ["Plomberie", "Chauffage", "Électricité", "VMC", "Serrurerie", "Propreté", "Autre"])
    details_dict = {
        "Plomberie": ["Fuite sous évier", "Chasse d'eau HS", "Robinet qui goutte"],
        "Chauffage": ["Radiateur froid", "Bruit anormal", "Fuite chaudière"],
        "VMC": ["Ne tourne plus", "Bruit excessif", "Grille bouchée"],
        "Électricité": ["Panne totale", "Prise défectueuse", "Interphone"],
        "Serrurerie": ["Serrure bloquée", "Porte frotte"],
        "Propreté": ["Encombrants", "Nettoyage requis"],
        "Autre": ["Voir notes ci-dessous"]
    }
    
    problemes = st.multiselect("Détails du constat", details_dict[categorie])
    notes = st.text_area("Observations complémentaires")

    if st.form_submit_button("GÉNÉRER LE MESSAGE"):
        date_fr = date_visite.strftime('%d/%m/%Y')
        message = f"Bonjour,\n\nPassage le {date_fr} - {residence}\n📍 {id_logement}\n👤 Locataire : {nom_locataire}\n\nDÉTAILS :\n- Type : {categorie}\n- Constat : {', '.join(problemes)}\n- Urgence : {priorite.upper()}\n- Note : {notes if notes else 'RAS'}\n\nCordialement."
        st.code(message, language="markdown")