import streamlit as st
import pandas as pd
from datetime import date
import google.generativeai as genai
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck GH Pro", page_icon="🏢", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

conn = st.connection("gsheets", type=GSheetsConnection)

def charger_donnees():
    try:
        # On lit l'onglet exact de ton fichier
        data = conn.read(worksheet="Base_Locataires", ttl=0)
        data.columns = data.columns.str.strip()
        # On utilise 'Appartement' car c'est le nom dans ton Excel
        if 'Appartement' in data.columns:
            data['Appartement'] = data['Appartement'].astype(str).apply(lambda x: x.split('.')[0] if '.' in x else x)
        return data
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
        return pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

df_base = charger_donnees()

# --- 2. LOGIQUE PRESTATAIRES ---
PRESTATAIRES = {
    "VMC (Moteur/Entretien)": "LOGISTA HOMETECH",
    "Robinetterie / Fuites": "LOGISTA HOMETECH",
    "Chaudière / Thermostat / Chauffe-eau": "LOGISTA HOMETECH",
    "DAAF (Détecteur fumée)": "LOGISTA HOMETECH",
    "Chauffage Collectif": "COMAINTEF",
    "Assainissement (Conduites)": "ACS",
    "Encombrants": "Atelier-Remuménage",
    "Platines / Interphonie": "COUTAREL",
    "Menuiserie / Serrurerie / Portes": "GIRONDE HABITAT (Régie)",
    "Électricité (Prises/Tableau)": "GIRONDE HABITAT (Régie)",
    "Autre": "À PRÉCISER"
}

# --- 3. INTERFACE ---
st.subheader("🛠️ Plateforme de signalement Gironde Habitat")

with st.container(border=True):
    col_in1, col_in2 = st.columns([1, 1.5])
    with col_in1:
        photo = st.camera_input("📸 Photo")
    with col_in2:
        notes = st.text_input("🗒️ Notes (ex: vitre cassée, poignée HS...)", key="notes_brutes")
        type_inter = st.selectbox("Type d'intervention", list(PRESTATAIRES.keys()))
        entreprise = PRESTATAIRES.get(type_inter)

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
            
            # Correction ici : on n'utilise PLUS DU TOUT le mot 'Logement'
            filtre = (df_base['Résidence'] == res)
            if res == "Canterane": 
                filtre = filtre & (df_base['Bâtiment'] == bat)
            
            # On vérifie que la colonne Appartement existe bien
            if 'Appartement' in df_base.columns:
                appts_dispo = sorted(df_base[filtre]['Appartement'].unique())
                n_appt = st.selectbox("N° Appartement", options=appts_dispo if appts_dispo else ["Inconnu"])
                
                # On récupère le nom du locataire via la colonne Appartement
                res_filtré = df_base[(df_base['Résidence'] == res) & (df_base['Appartement'] == n_appt)]
                nom_locataire = res_filtré.iloc[-1]['Nom'] if not res_filtré.empty else "Inconnu"
                lieu_ia = f"Appartement {n_appt}"
            
        elif mode_lieu == "Communs/Extérieur":
            lieu_ia = st.selectbox("Lieu précis", ["Hall d'entrée", "Garage / Parking", "Local Poubelle", "Espaces Extérieurs", "Escaliers", "Sous-sol"])
            nom_locataire = "Gironde Habitat (Communs)"

    with col2:
        nom = st.text_input("Nom affiché", value=nom_locataire)

# --- 4. LOGIQUE IA (AVEC TES RÈGLES ORANGE/BLEU/VERT) ---
objet_ia = ""
phrase_locatif = "Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire."

if notes or photo:
    # Sécurité : Mots qui déclenchent la phrase longue d'office
    mots_orange = ["vitre", "poignée", "serrure", "verrou", "mastic", "joint", "ampoule", "fusible", "cassé", "cassée", "arraché", "bouché"]
    est_orange = any(mot in notes.lower() for mot in mots_orange)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""Expert GH. Analyse : '{notes}'. 
        RÈGLES :
        - Orange (Locataire) : Vitres, mastics, poignées, serrures, fusibles, joints, débouchage.
        - Bleu (GH) : Prises (usure), cadres fenêtres, interphone.
        - Vert (Contrat) : Chaudière, Thermostat, VMC.
        SI ORANGE : Utilise obligatoirement la phrase : '{phrase_locatif}'.
        FORMAT : Bonjour, [Message corrigé sans fautes], merci, bonne journée, cordialement. (Avec sauts de ligne)"""
        
        response = model.generate_content([prompt, Image.open(photo)] if photo else prompt)
        objet_ia = response.text
    except:
        if est_orange:
            objet_ia = f"Bonjour,\n\nUne anomalie a été constatée concernant : {notes}. {phrase_locatif}\n\nmerci\nbonne journée\ncordialement"
        else:
            objet_ia = f"Bonjour,\n\nAnomalie constatée : {notes}.\n\nmerci\nbonne journée\ncordialement"

st.divider()
constat_final = st.text_area("📝 Message rédigé", value=objet_ia, height=250)

# --- 5. ACTIONS ---
col_b1, col_b2 = st.columns(2)
if col_b1.button("📑 GÉNÉRER LE RAPPORT"):
    st.code(f"🏢 SIGNALEMENT GH\n👤 NOM : {nom}\n📍 LIEU : {lieu_ia}\n\n{objet_ia}")

if col_b2.button("🧹 NETTOYER"):
    st.rerun()
