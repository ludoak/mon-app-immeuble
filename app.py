import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="GH Diagnostic Pro", layout="wide")

# --- 2. CONFIGURATION DE L'IA (VERSION ULTRA-COMPATIBLE) ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Clé API manquante !")

# --- 3. BASE DE DONNÉES LOCATAIRES ---
data = {
    "Résidence": ["Canterane", "Canterane", "La Dussaude", "La Dussaude", "Canterane"],
    "Appartement": ["101", "102", "201", "202", "103"],
    "Nom": ["Lolo", "Zezette", "Kiki", "Aniotsbehere", "Dédé"]
}
df = pd.DataFrame(data)

# --- 4. INTERFACE ---
st.title("🏢 Assistant Technique GH")

col1, col2 = st.columns(2)
with col1:
    res_sel = st.selectbox("📍 Résidence", sorted(df["Résidence"].unique()))
    df_res = df[df["Résidence"] == res_sel]
    appt_sel = st.selectbox("🚪 N° Appartement", sorted(df_res["Appartement"].unique()))
    nom_loc = df_res[df_res["Appartement"] == appt_sel]["Nom"].iloc[0]
    st.info(f"👤 Locataire : **{nom_loc}**")

with col2:
    photo = st.file_uploader("📸 Photo", type=["jpg", "png", "jpeg"])
    note = st.text_area("📝 Description du problème")

# --- 5. LOGIQUE D'ANALYSE (CHANGEMENT DE MODÈLE ICI) ---
if st.button("🔍 ANALYSER", type="primary", use_container_width=True):
    with st.spinner("Analyse en cours..."):
        try:
            # On change 'gemini-1.5-flash' par 'gemini-pro' (ou 'gemini-1.5-pro')
            # C'est le modèle le plus robuste
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            prompt = f"Expert technique bâtiment. Analyse : {note}. Charge locative ?"
            
            if photo:
                img = Image.open(photo)
                response = model.generate_content([prompt, img])
            else:
                response = model.generate_content(prompt)
            
            st.success("✅ Diagnostic terminé")
            st.markdown(response.text)
            
        except Exception as e:
            # SI LE PRO NE MARCHE PAS, ON ESSAIE LE DERNIER RECOURS
            try:
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(f"Expert bâtiment. Problème: {note}")
                st.write(response.text)
            except:
                st.error(f"Erreur persistante : {e}")
                st.info("Conseil : Vérifie si ta clé API Gemini est bien active sur 'Google AI Studio'.")