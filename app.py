import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="GH Diagnostic Pro", layout="wide")

# --- 2. CONFIGURATION DE L'IA (TON MODÈLE FAVORIS) ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Clé API manquante dans les Secrets !")

# --- 3. BASE DE DONNÉES LOCATAIRES INTÉGRÉE ---
# Plus de dépendance à GSheets pour une vitesse maximale
data = {
    "Résidence": ["Canterane", "Canterane", "La Dussaude", "La Dussaude", "Canterane"],
    "Appartement": ["10", "40", "95", "64", "103"],
    "Nom": ["lolo", "Aniotsbehere", "zezette", "kiki", "Dédé"]
}
df = pd.DataFrame(data)

# --- 4. INTERFACE ---
st.title("🚀 GH Diagnostic Rapide")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Localisation")
    res_sel = st.selectbox("Sélectionner la Résidence", sorted(df["Résidence"].unique()))
    df_res = df[df["Résidence"] == res_sel]
    appt_sel = st.selectbox("N° Appartement", sorted(df_res["Appartement"].unique()))
    
    # Récupération du nom du locataire
    nom_loc = df_res[df_res["Appartement"] == appt_sel]["Nom"].iloc[0]
    st.success(f"👤 Locataire actuel : **{nom_loc}**")

with col2:
    st.subheader("📸 Signalement")
    photo = st.file_uploader("Prendre une photo du désordre", type=["jpg", "png", "jpeg"])
    note = st.text_area("Note technique", placeholder="Décris le problème ici (ex: fuite, humidité...)")

# --- 5. LOGIQUE D'ANALYSE (AVEC GEMINI-3-FLASH-PREVIEW) ---
if st.button("🔍 LANCER L'ANALYSE EXPERTE", type="primary", use_container_width=True):
    if not photo and not note:
        st.warning("⚠️ Merci d'ajouter une photo ou une note.")
    else:
        with st.spinner("Analyse par gemini-3-flash-preview..."):
            try:
                # Utilisation forcée de ton modèle validé
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                prompt = f"""
                Tu es l'expert technique de Gironde Habitat. Analyse ce problème : '{note}'.
                1. Cause probable du désordre.
                2. Est-ce une charge locative selon le Décret n°87-712 ?
                3. Conseil pour le technicien.
                Réponds de façon structurée et professionnelle.
                """
                
                if photo:
                    img = Image.open(photo)
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(prompt)
                
                st.markdown("---")
                st.subheader("📋 Rapport de Diagnostic")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"❌ Erreur avec le modèle Gemini 3 : {e}")
                st.info("Note : Vérifiez que le modèle est bien disponible dans votre région Google AI Studio.")

st.markdown("---")
st.caption("Application GH - Modèle : gemini-3-flash-preview - Données locales")