import streamlit as st
import pandas as pd
from datetime import date
import google.generativeai as genai
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck GH Pro", page_icon="🏢", layout="wide")

# Récupération de la clé API
api_key = st.secrets.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("❌ Clé API manquante dans les Secrets.")

# Connexion à Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def charger_donnees():
    try:
        data = conn.read(worksheet="Base_Locataires", ttl=0)
        data.columns = data.columns.str.strip()
        if 'Appartement' in data.columns:
            data['Appartement'] = data['Appartement'].astype(str).apply(lambda x: x.split('.')[0] if '.' in x else x)
        return data
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

df_base = charger_donnees()

# --- 2. LOGIQUE PRESTATAIRES ---
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

# --- 3. INTERFACE UTILISATEUR ---
st.subheader("🛠️ Plateforme de signalement Gironde Habitat")

with st.container(border=True):
    col_in1, col_in2 = st.columns([1, 1.5])
    with col_in1:
        source_photo = st.file_uploader("📸 Photo (Caméra ou Galerie)", type=["jpg", "jpeg", "png"])
        if source_photo:
            st.image(source_photo, caption="Image sélectionnée", width=300)
            
    with col_in2:
        notes = st.text_input("🗒️ Notes / Observations terrain", placeholder="Ex: Moisissures sur les joints...")
        type_inter = st.selectbox("Type d'intervention", list(PRESTATAIRES.keys()))
        lancer_analyse = st.button("🔍 LANCER L'ANALYSE TECHNIQUE", type="primary", use_container_width=True)

with st.expander("📍 Lieu et Locataire", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        residences = []
        c1, c2 = st.columns(2)
        if c1.checkbox("Canterane"): residences.append("Canterane")
        if c2.checkbox("La Dussaude"): residences.append("La Dussaude")
        mode_lieu = st.radio("Cible", ["Logement", "Communs/Extérieur"], horizontal=True)
        
        n_appt, nom_locataire, lieu_ia = "N/A", "Gironde Habitat", ""
        if mode_lieu == "Logement" and len(residences) == 1:
            res = residences[0]
            bat = st.radio("Bâtiment", ["A", "B"], horizontal=True) if res == "Canterane" else ""
            filtre = (df_base['Résidence'] == res)
            if res == "Canterane": filtre = filtre & (df_base['Bâtiment'] == bat)
            appts_dispo = sorted(df_base[filtre]['Appartement'].unique())
            n_appt = st.selectbox("N° Appartement", options=appts_dispo if appts_dispo else ["Inconnu"])
            res_filtré = df_base[(df_base['Résidence'] == res) & (df_base['Appartement'] == n_appt)]
            nom_locataire = res_filtré.iloc[-1]['Nom'] if not res_filtré.empty else "Inconnu"
            lieu_ia = f"Appartement {n_appt} ({res})"
        elif mode_lieu == "Communs/Extérieur":
            lieu_ia = st.selectbox("Lieu précis", ["Hall d'entrée", "Garage / Parking", "Local Poubelle", "Espaces Extérieurs", "Escaliers", "Sous-sol"])
            nom_locataire = "Gironde Habitat (Communs)"

    with col2:
        nom_final = st.text_input("Nom affiché sur le rapport", value=nom_locataire)

# --- 4. LOGIQUE D'ANALYSE IA ---
phrase_locatif = "Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire (Décret n°87-712)."
resultat_ia = ""

if lancer_analyse:
    if source_photo or notes:
        with st.spinner("Analyse technique par Gemini 3..."):
            try:
                # Utilisation de la version confirmée par ta vidéo
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                prompt = f"""Tu es l'inspecteur expert technique de Gironde Habitat. 
                Analyse les notes : '{notes}' et la photo fournie.
                
                CONSIGNES :
                1. Identifie précisément le problème technique.
                2. Si c'est un défaut d'entretien (moisissures, calcaire, saleté), ajoute : '{phrase_locatif}'.
                3. Propose une solution d'entretien.
                4. Sois poli et professionnel.
                """
                
                if source_photo:
                    img = Image.open(source_photo)
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(prompt)
                resultat_ia = response.text
            except Exception as e:
                st.error(f"Erreur d'analyse : {e}")
    else:
        st.warning("⚠️ Merci d'ajouter une photo ou une observation.")

st.divider()
st.subheader("🔍 Rapport de l'Inspecteur IA")
constat_final = st.text_area("Résultat de l'analyse :", value=resultat_ia, height=300)

# --- 5. ACTIONS ---
if st.button("📑 GÉNÉRER LE RAPPORT FINAL"):
    rapport = f"""🏢 SIGNALEMENT GIRONDE HABITAT
👤 CONCERNÉ : {nom_final}
📍 LIEU : {lieu_ia}
📅 DATE : {date.today()}
🔧 PRESTATAIRE : {PRESTATAIRES.get(type_inter, 'N/A')}

---
{constat_final}
"""
    st.code(rapport, language="text")