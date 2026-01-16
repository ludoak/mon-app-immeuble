import streamlit as st
import pandas as pd
from datetime import date
import google.generativeai as genai
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck GH Pro", page_icon="🏢", layout="wide")

# Récupération sécurisée de la clé API
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("❌ Erreur de clé API : Vérifiez vos Secrets Streamlit.")

# --- 2. CONNEXION GOOGLE SHEETS ---
try:
    # On récupère l'URL directement depuis la section gsheets des secrets
    url_sheet = st.secrets["connections"]["gsheets"]["spreadsheet"]
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    def charger_donnees():
        # Lecture de l'onglet Base_Locataires
        data = conn.read(spreadsheet=url_sheet, worksheet="Base_Locataires", ttl=0)
        data.columns = data.columns.str.strip()
        if 'Appartement' in data.columns:
            data['Appartement'] = data['Appartement'].astype(str).apply(lambda x: x.split('.')[0] if '.' in x else x)
        return data

    df_base = charger_donnees()
except Exception as e:
    st.error(f"❌ Erreur Google Sheets : {e}")
    df_base = pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

# --- 3. LOGIQUE PRESTATAIRES ---
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

# --- 4. INTERFACE ---
st.subheader("🛠️ Plateforme de signalement Gironde Habitat")

with st.container(border=True):
    col_in1, col_in2 = st.columns([1, 1.5])
    with col_in1:
        source_photo = st.file_uploader("📸 Photo", type=["jpg", "jpeg", "png"])
        if source_photo: st.image(source_photo, width=300)
    with col_in2:
        notes = st.text_input("🗒️ Notes terrain", placeholder="Ex: Joint noirci...")
        type_inter = st.selectbox("Type d'intervention", list(PRESTATAIRES.keys()))
        lancer_analyse = st.button("🔍 LANCER L'ANALYSE TECHNIQUE", type="primary", use_container_width=True)

with st.expander("📍 Lieu et Locataire", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        residences_selectionnees = []
        c1, c2 = st.columns(2)
        if c1.checkbox("Canterane"): residences_selectionnees.append("Canterane")
        if c2.checkbox("La Dussaude"): residences_selectionnees.append("La Dussaude")
        
        mode_lieu = st.radio("Cible", ["Logement", "Communs/Extérieur"], horizontal=True)
        
        n_appt, nom_locataire, lieu_ia = "N/A", "Gironde Habitat", ""
        
        if mode_lieu == "Logement" and len(residences_selectionnees) == 1:
            res = residences_selectionnees[0]
            bat = st.radio("Bâtiment", ["A", "B"], horizontal=True) if res == "Canterane" else ""
            
            filtre = (df_base['Résidence'] == res)
            if res == "Canterane": filtre = filtre & (df_base['Bâtiment'] == bat)
            
            appts_dispo = sorted(df_base[filtre]['Appartement'].unique())
            n_appt = st.selectbox("N° Appartement", options=appts_dispo if appts_dispo else ["Inconnu"])
            
            res_filtré = df_base[(df_base['Résidence'] == res) & (df_base['Appartement'] == n_appt)]
            nom_locataire = res_filtré.iloc[-1]['Nom'] if not res_filtré.empty else "Inconnu"
            lieu_ia = f"Appartement {n_appt} ({res})"
        else:
            lieu_ia = st.selectbox("Lieu précis", ["Hall d'entrée", "Parking", "Local Poubelle", "Espaces Extérieurs"])
            nom_locataire = "Gironde Habitat (Communs)"

    with col2:
        nom_final = st.text_input("Nom affiché", value=nom_locataire)

# --- 5. LOGIQUE IA (GEMINI 3) ---
resultat_ia = ""
phrase_locatif = "Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire (Décret n°87-712)."

if lancer_analyse:
    with st.spinner("Analyse Gemini 3..."):
        try:
            model = genai.GenerativeModel('gemini-3-flash-preview')
            prompt = f"Expert GH. Analyse : {notes}. Si c'est locatif, ajoute : '{phrase_locatif}'"
            if source_photo:
                img = Image.open(source_photo)
                response = model.generate_content([prompt, img])
            else:
                response = model.generate_content(prompt)
            resultat_ia = response.text
        except Exception as e:
            st.error(f"Erreur IA : {e}")

st.text_area("Résultat de l'analyse :", value=resultat_ia, height=250)

if st.button("📑 GÉNÉRER LE RAPPORT FINAL"):
    rapport = f"🏢 RAPPORT GH\n📍 {lieu_ia}\n👤 {nom_final}\n📅 {date.today()}\n🔧 Prestataire : {PRESTATAIRES[type_inter]}\n\n{resultat_ia}"
    st.code(rapport, language="text")