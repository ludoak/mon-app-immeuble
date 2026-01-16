import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="GH Diagnostic Terrain", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CONFIGURATION DE L'IA (CLE DANS LES SECRETS) ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Erreur : La clé GEMINI_API_KEY est introuvable dans les Secrets Streamlit.")

# --- 3. BASE DE DONNÉES LOCATAIRES (INTERNE) ---
# Tu peux modifier cette liste ici même si les locataires changent
data = {
    "Résidence": ["Canterane", "Canterane", "La Dussaude", "La Dussaude", "Canterane"],
    "Appartement": ["101", "102", "201", "202", "103"],
    "Nom": ["Lolo", "Zezette", "Kiki", "Aniotsbehere", "Dédé"]
}
df = pd.DataFrame(data)

# --- 4. INTERFACE UTILISATEUR ---
st.title("🏢 Assistant Technique GH")
st.markdown("---")

# Zone de sélection du locataire
with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        res_sel = st.selectbox("📍 Résidence", sorted(df["Résidence"].unique()))
        # Filtrage automatique des appartements selon la résidence choisie
        df_res = df[df["Résidence"] == res_sel]
        appt_sel = st.selectbox("🚪 N° Appartement", sorted(df_res["Appartement"].unique()))
    
    with col2:
        # Récupération automatique du nom
        nom_loc = df_res[df_res["Appartement"] == appt_sel]["Nom"].iloc[0]
        st.info(f"👤 Locataire actuel :\n\n**{nom_loc}**")

st.markdown("---")

# Zone de diagnostic
st.subheader("📸 Constat sur place")
photo = st.file_uploader("Prendre une photo du désordre", type=["jpg", "png", "jpeg"])
note = st.text_area("Note technique / Description du problème", placeholder="Ex: Traces d'humidité plafond salle de bain...")

# --- 5. LOGIQUE D'ANALYSE ---
if st.button("🔍 LANCER L'ANALYSE EXPERTE", type="primary", use_container_width=True):
    if not photo and not note:
        st.warning("⚠️ Veuillez ajouter au moins une photo ou une description.")
    else:
        with st.spinner("Analyse technique en cours (Gemini 1.5 Flash)..."):
            try:
                # Utilisation du modèle le plus stable
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Prompt d'expertise adapté à Gironde Habitat
                prompt = f"""
                Tu agis en tant qu'expert technique pour le bailleur social Gironde Habitat.
                Analyse le problème suivant : '{note}'.
                
                1. Identifie la cause probable du désordre.
                2. Détermine si la réparation est à la CHARGE DU LOCATAIRE (Entretien courant, Décret n°87-712) 
                   ou à la CHARGE DU BAILLEUR (Grosse réparation, vétusté).
                3. Donne un conseil technique rapide pour le technicien sur place.
                
                Réponds de manière concise et professionnelle.
                """
                
                if photo:
                    img = Image.open(photo)
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(prompt)
                
                # Affichage du résultat
                st.success("✅ Diagnostic terminé")
                st.markdown("### 📋 Rapport d'analyse IA")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"❌ Une erreur est survenue avec l'IA : {e}")

# --- PIED DE PAGE ---
st.markdown("---")
st.caption("Application interne GH - Vitesse et Efficacité Terrain")