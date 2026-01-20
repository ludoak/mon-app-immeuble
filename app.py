import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="GH Diagnostic Pro", layout="wide")

# --- 2. BASE DE DONNÉES ---
DB_FILE = "base_locataires_gh.csv"
def charger_donnees():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={"Appartement": str})
    return pd.DataFrame({"Résidence": ["Canterane"], "Appartement": ["10"], "Nom": ["lolo"]})

if 'df_locataires' not in st.session_state:
    st.session_state.df_locataires = charger_donnees()

# --- 3. CONNEXION IA (AUTO-DÉTECTION) ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    target_model = models[0] if models else "models/gemini-1.5-flash"
except:
    st.error("Erreur de configuration API")

# --- 4. INTERFACE ---
st.title("🏢 Expertise Terrain Gironde Habitat")

tab1, tab2 = st.tabs(["📸 Diagnostic & Courrier", "👥 Liste Locataires"])

with tab1:
    df = st.session_state.df_locataires
    col1, col2 = st.columns(2)
    with col1:
        res_sel = st.selectbox("📍 Résidence", sorted(df["Résidence"].unique().astype(str)))
    with col2:
        df_res = df[df["Résidence"] == res_sel]
        appt_sel = st.selectbox("🚪 Appartement", sorted(df_res["Appartement"].unique().astype(str)))
    
    # Récupération auto du nom
    loc_info = df_res[df_res["Appartement"] == appt_sel]
    nom_loc = loc_info["Nom"].iloc[0] if not loc_info.empty else "Inconnu"
    st.info(f"👤 Locataire actuel : **{nom_loc}**")

    st.divider()
    cam = st.camera_input("Prendre la photo")
    gal = st.file_uploader("Ou importer", type=["jpg", "png", "jpeg"])
    photo = cam if cam else gal

    if photo:
        if st.button("🔍 ANALYSER ET GÉNÉRER LE COURRIER", type="primary", use_container_width=True):
            with st.spinner("Expertise en cours..."):
                try:
                    model = genai.GenerativeModel(target_model)
                    img = Image.open(photo)
                    
                    prompt = """Tu es un expert en maintenance pour Gironde Habitat. Analyse cette photo.
                    1. Décris le problème technique.
                    2. Détermine la responsabilité selon ces critères :
                       - BAILLEUR : Gros oeuvre, canalisations encastrées, électricité lourde.
                       - LOCATAIRE : Entretien courant, joints, calcaire, dégradations.
                       - PRESTATAIRE : Contrat chaudière, ascenseur, VMC.
                    
                    Réponds exactement sous ce format :
                    DÉCISION : [BAILLEUR ou LOCATAIRE ou PRESTATAIRE]
                    CONSTAT : [Description courte]"""
                    
                    response = model.generate_content([prompt, img])
                    res_text = response.text
                    
                    # --- VISUEL RAPIDE ---
                    if "BAILLEUR" in res_text.upper():
                        st.error("### 🚨 CHARGE BAILLEUR (GH)")
                        decision_final = "Bailleur (Gironde Habitat)"
                    elif "PRESTATAIRE" in res_text.upper():
                        st.warning("### 🔧 CHARGE PRESTATAIRE (Sous contrat)")
                        decision_final = "Prestataire sous contrat"
                    else:
                        st.success("### ✅ CHARGE LOCATIVE")
                        decision_final = "Locataire (Entretien)"

                    st.write(res_text)

                    # --- COURRIER AUTOMATIQUE ---
                    st.divider()
                    st.subheader("✉️ Courrier pour la plateforme GH")
                    date_str = datetime.now().strftime("%d/%m/%Y")
                    lettre = f"""OBJET : Signalement technique - {res_sel} / Appt {appt_sel}
DATE : {date_str}

Logement : {res_sel}, appartement {appt_sel}
Locataire : {nom_loc}

Madame, Monsieur,
Suite à la visite de contrôle, un désordre a été identifié :
{res_text.split('CONSTAT :')[-1].strip() if 'CONSTAT :' in res_text else 'Voir constat technique.'}

Après expertise, cette intervention est classée comme : {decision_final}.

Merci de faire le nécessaire pour la prise en charge.
Cordialement,
Le service technique."""
                    
                    st.text_area("Copier le texte ci-dessous :", lettre, height=250)
                    
                except Exception as e:
                    st.error(f"Erreur : {e}")

with tab2:
    st.subheader("👥 Gestion de la base")
    st.dataframe(st.session_state.df_locataires, use_container_width=True)