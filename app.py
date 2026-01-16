import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="GH Diagnostic Pro", layout="wide")

# --- 2. CONFIGURATION DE L'IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Clé API manquante dans les Secrets !")

# --- 3. BASE DE DONNÉES LOCATAIRES (Tout est ici !) ---
# Ajoute ou modifie tes locataires directement dans cette liste
data = {
    "Résidence": ["Canterane", "Canterane", "La Dussaude", "La Dussaude", "Canterane"],
    "Appartement": ["101", "102", "201", "202", "103"],
    "Nom": ["Lolo", "Zezette", "Kiki", "Aniotsbehere", "Dédé"]
}
df = pd.DataFrame(data)

# --- 4. INTERFACE ---
st.title("🏢 Assistant Technique GH")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Localisation")
    res_sel = st.selectbox("Sélectionner la Résidence", sorted(df["Résidence"].unique()))
    df_res = df[df["Résidence"] == res_sel]
    appt_sel = st.selectbox("N° Appartement", sorted(df_res["Appartement"].unique()))
    nom_loc = df_res[df_res["Appartement"] == appt_sel]["Nom"].iloc[0]
    st.success(f"👤 Locataire actuel : **{nom_loc}**")

with col2:
    st.subheader("📸 Signalement")
    photo = st.file_uploader("Prendre une photo", type=["jpg", "png", "jpeg"])
    note = st.text_area("Note technique rapide", placeholder="Décris le problème ici...")

# --- 5. LOGIQUE D'ANALYSE (SÉCURISÉE) ---
if st.button("🔍 LANCER L'ANALYSE", type="primary", use_container_width=True):
    if not photo and not note:
        st.warning("⚠️ Merci d'ajouter une photo ou une note.")
    else:
        with st.spinner("Analyse en cours..."):
            # On définit la liste des modèles à tester par ordre de préférence
            # Si le 3-flash-preview échoue, on prend le 1.5-flash
            modeles_a_tester = ['gemini-3-flash-preview', 'gemini-1.5-flash']
            
            reponse_obtenue = False
            
            for nom_modele in modeles_a_tester:
                if not reponse_obtenue:
                    try:
                        model = genai.GenerativeModel(nom_modele)
                        prompt = f"Expert technique bâtiment GH. Analyse ce problème : {note}. Précise si c'est une charge locative (Décret 87-712)."
                        
                        if photo:
                            img = Image.open(photo)
                            response = model.generate_content([prompt, img])
                        else:
                            response = model.generate_content(prompt)
                        
                        st.markdown("---")
                        st.subheader(f"📋 Rapport (Modèle: {nom_modele})")
                        st.write(response.text)
                        reponse_obtenue = True
                    except Exception as e:
                        # Si ce modèle échoue, on passe au suivant
                        continue
            
            if not reponse_obtenue:
                st.error("❌ Impossible de contacter l'IA. Vérifie ta clé API ou réessaie dans quelques instants.")

st.markdown("---")
st.caption("Application interne GH - Données locataires intégrées")