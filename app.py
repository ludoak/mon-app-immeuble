import streamlit as st
from datetime import date
import json
import os

# Configuration pour mobile et ordinateur
st.set_page_config(page_title="ImmoCheck Pro", page_icon="🏢", layout="wide")

# --- 1. GESTION DE LA MÉMOIRE (FICHIER JSON) ---
FILE_LOCATAIRES = "liste_locataires.json"

def charger_locataires():
    if os.path.exists(FILE_LOCATAIRES):
        try:
            with open(FILE_LOCATAIRES, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def sauvegarder_tous_locataires(dictionnaire):
    with open(FILE_LOCATAIRES, "w", encoding="utf-8") as f:
        json.dump(dictionnaire, f, indent=4, ensure_ascii=False)

# Charger les données dans la session
if 'locataires' not in st.session_state:
    st.session_state['locataires'] = charger_locataires()

# --- 2. BARRE LATÉRALE (MENU MOBILE) ---
# Sur téléphone, clique sur la petite flèche ">" en haut à gauche
with st.sidebar:
    st.header("👥 Gestion Locataires")
    tab_ajout, tab_suppr = st.tabs(["➕ Ajouter", "🗑️ Supprimer"])
    
    with tab_ajout:
        res_add = st.selectbox("Résidence", ["Canterane", "La Dussaude"], key="res_sidebar")
        
        if res_add == "Canterane":
            bat_add = st.radio("Bâtiment", ["Bâtiment A", "Bâtiment B"], horizontal=True)
            appt_add = st.text_input("N° Appartement", key="app_c_side")
            cle_loc = f"Canterane - {bat_add} - Appt {appt_add}"
        else:
            appt_add = st.number_input("N° Appartement (1-95)", 1, 95, key="app_d_side")
            cle_loc = f"La Dussaude - Appt {appt_add}"
        
        nom_add = st.text_input("Nom du locataire")
        
        if st.button("Enregistrer le locataire"):
            st.session_state['locataires'][cle_loc] = nom_add
            sauvegarder_tous_locataires(st.session_state['locataires'])
            st.success(f"Enregistré : {nom_add}")
            st.rerun()

    with tab_suppr:
        if st.session_state['locataires']:
            choix_suppr = st.selectbox("Logement à vider", list(st.session_state['locataires'].keys()))
            if st.button("Supprimer ce locataire"):
                del st.session_state['locataires'][choix_suppr]
                sauvegarder_tous_locataires(st.session_state['locataires'])
                st.error("Locataire supprimé.")
                st.rerun()
        else:
            st.write("Aucun locataire en base.")

# --- 3. FORMULAIRE PRINCIPAL ---
st.title("🏢 Rapport d'Intervention")

with st.form("rapport_form"):
    residence = st.selectbox("📍 Sélectionner la Résidence", ["Canterane", "La Dussaude"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Logique différente selon la résidence
        if residence == "Canterane":
            batiment = st.radio("Bâtiment", ["Bâtiment A", "Bâtiment B"], horizontal=True)
            n_appt = st.text_input("N° Appartement")
            id_logement = f"Canterane - {batiment} - Appt {n_appt}"
        else:
            # LA DUSSAUDE : Pas de bâtiment, direct numéro
            n_appt = st.number_input("N° Appartement (1 à 95)", 1, 95)
            id_logement = f"La Dussaude - Appt {n_appt}"
        
        # Recherche automatique du locataire
        nom_detecte = st.session_state['locataires'].get(id_logement, "")
        nom_locataire = st.text_input("👤 Nom du Locataire", value=nom_detecte)
        if not nom_detecte and n_appt:
            st.caption("ℹ️ Inconnu. Ajoutez-le dans le menu de gauche si besoin.")

    with col2:
        # Date au format FR
        date_visite = st.date_input("📅 Date d'intervention", value=date.today(), format="DD/MM/YYYY")
        priorite = st.selectbox("🚦 Urgence", ["Faible", "Moyenne", "Haute"])

    categorie = st.selectbox("🛠️ Catégorie", ["Plomberie", "Chauffage", "Électricité", "VMC", "Serrurerie", "Propreté", "Autre"])
    
    details_dict = {
        "Plomberie": ["Fuite sous évier", "Chasse d'eau HS", "Robinet qui goutte", "Canalisation bouchée"],
        "Chauffage": ["Radiateur froid", "Bruit anormal", "Fuite chaudière", "Pas d'eau chaude"],
        "VMC": ["Ne tourne plus", "Bruit excessif", "Grille encrassée"],
        "Électricité": ["Panne totale", "Prise défectueuse", "Interphone HS", "Lumière commune"],
        "Serrurerie": ["Serrure bloquée", "Porte frotte", "Clé cassée"],
        "Propreté": ["Encombrants", "Nettoyage requis", "Poubelles"],
        "Autre": ["Voir les notes ci-dessous"]
    }
    
    problemes = st.multiselect("Détails du constat", details_dict[categorie])
    notes = st.text_area("Observations complémentaires (Actions menées, etc.)")

    submit = st.form_submit_button("GÉNÉRER LE MESSAGE")

# --- 4. RÉSULTAT ---
if submit:
    date_fr = date_visite.strftime('%d/%m/%Y')
    liste_constats = ", ".join(problemes)
    
    message = f"""Bonjour,

Suite à mon passage le {date_fr} à la résidence {residence}, je vous informe d'un problème :
📍 {id_logement}
👤 Locataire : {nom_locataire if nom_locataire else "Non renseigné"}

DÉTAILS :
- Type : {categorie}
- Constat : {liste_constats}
- Urgence : {priorite.upper()}
- Note : {notes if notes else "RAS"}

Merci de faire le nécessaire.
Cordialement,
Votre chargé d'immeuble."""

    st.success("Message prêt ! Copiez-le ci-dessous :")
    st.code(message, language="markdown")
