import streamlit as st
import pandas as pd
from datetime import date
import google.generativeai as genai
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="ImmoCheck GH Pro", page_icon="🏢", layout="wide")

# --- 2. CONFIGURATION DE L'IA (GEMINI 3) ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("❌ Clé GEMINI_API_KEY manquante dans les Secrets.")

# --- 3. CONNEXION GOOGLE SHEETS ---
def charger_donnees():
    try:
        # On récupère l'URL et on la nettoie pour éviter les erreurs 400/404
        url_sheet = st.secrets["connections"]["gsheets"]["spreadsheet"]
        if "/edit" in url_sheet:
            url_sheet = url_sheet.split("/edit")[0]
            
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Lecture du fichier (on prend le premier onglet par défaut pour plus de sécurité)
        data = conn.read(spreadsheet=url_sheet, ttl=0)
        
        # Nettoyage des colonnes
        data.columns = data.columns.str.strip()
        if 'Appartement' in data.columns:
            data['Appartement'] = data['Appartement'].astype(str).apply(lambda x: x.split('.')[0] if '.' in x else x)
        return data
    except Exception as e:
        st.error(f"❌ Erreur de connexion Google Sheets : {e}")
        return pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

df_base = charger_donnees()

# --- 4. DICTIONNAIRE DES PRESTATAIRES ---
PRESTATAIRES = {
    "VMC (Moteur/Entretien)": "LOGISTA HOMETECH",
    "Robinetterie / Fuites": "LOGISTA HOMETECH",
    "Chaudière / Thermostat / Chauffe-eau": "LOGISTA HOMETECH",
    "DAAF (Détecteur fumée)": "LOGISTA HOMETECH",
    "Chauffage Collectif": "COMAINTEF",
    "Menuiserie / Serrurerie / Portes": "GIRONDE HABITAT (Régie)",
    "Électricité (Prises/Tableau)": "GIRONDE HABITAT (Régie)",
    "Autre": "À PRÉCISER"
}

# --- 5. INTERFACE UTILISATEUR ---
st.title("🛠️ Diagnostic Technique Gironde Habitat")

with st.container(border=True):
    col_in1, col_in2 = st.columns([1, 1.5])
    with col_in1:
        source_photo = st.file_uploader("📸 Photo du désordre", type=["jpg", "jpeg", "png"])
        if source_photo:
            st.image(source_photo, width=300)
            
    with col_in2:
        notes = st.text_input("🗒️ Notes terrain", placeholder="Décrivez le problème ici...")
        type_inter = st.selectbox("Type d'intervention", list(PRESTATAIRES.keys()))
        lancer_analyse = st.button("🔍 ANALYSER LE DÉFAUT", type="primary", use_container_width=True)

# Bloc de localisation
with st.expander("📍 Localisation et Locataire", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        res_selectionnees = []
        c1, c2 = st.columns(2)
        if c1.checkbox("Canterane"): res_selectionnees.append("Canterane")
        if c2.checkbox("La Dussaude"): res_selectionnees.append("La Dussaude")
        
        mode_lieu = st.radio("Cible", ["Logement", "Parties Communes"], horizontal=True)
        
        n_appt, nom_loc, lieu_final = "N/A", "Gironde Habitat", ""
        
        if mode_lieu == "Logement" and len(res_selectionnees) == 1:
            res_nom = res_selectionnees[0]
            # Filtrage bâtiment pour Canterane
            bat = ""
            if res_nom == "Canterane":
                bat = st.radio("Bâtiment", ["A", "B"], horizontal=True)
            
            # Filtrage des appartements
            mask = (df_base['Résidence'] == res_nom)
            if bat: mask = mask & (df_base['Bâtiment'] == bat)
            
            appts_dispo = sorted(df_base[mask]['Appartement'].unique()) if not df_base.empty else []
            n_appt = st.selectbox("N° Appartement", options=appts_dispo if appts_dispo else ["Aucun"])
            
            # Récupération du nom
            info_loc = df_base[(df_base['Résidence'] == res_nom) & (df_base['Appartement'] == n_appt)]
            nom_loc = info_loc.iloc[-1]['Nom'] if not info_loc.empty else "Inconnu"
            lieu_final = f"Appartement {n_appt} ({res_nom})"
        else:
            lieu_final = st.selectbox("Zone", ["Hall", "Parking", "Espaces Verts", "Locaux techniques"])

    with col2:
        nom_affiche = st.text_input("Nom sur le rapport", value=nom_loc)

# --- 6. ANALYSE IA (GEMINI 3) ---
phrase_legale = "Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire (Décret n°87-712)."
resultat_ia = ""

if lancer_analyse:
    if source_photo or notes:
        with st.spinner("Analyse par Gemini 3 en cours..."):
            try:
                # Utilisation du modèle confirmé par ta vidéo
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                prompt = f"""Tu es l'expert technique de Gironde Habitat. 
                Analyse : '{notes}'. 
                1. Identifie la cause.
                2. Si c'est un défaut d'entretien, cite : '{phrase_legale}'.
                3. Donne une recommandation courte.
                """
                
                if source_photo:
                    img = Image.open(source_photo)
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(prompt)
                resultat_ia = response.text
            except Exception as e:
                st.error(f"Erreur IA : {e}")
    else:
        st.warning("⚠️ Veuillez fournir une photo ou une note.")

st.divider()
st.subheader("📋 Rapport d'Analyse")
constat_final = st.text_area("Résultat de l'IA :", value=resultat_ia, height=250)

if st.button("📑 GÉNÉRER LE RAPPORT FINAL"):
    rapport_texte = f"""🏢 GIRONDE HABITAT - RAPPORT TECHNIQUE
📍 LIEU : {lieu_final}
👤 NOM : {nom_affiche}
📅 DATE : {date.today()}
🔧 PRESTATAIRE : {PRESTATAIRES[type_inter]}

--- CONSTAT ---
{constat_final}
"""
    st.code(rapport_texte, language="text")