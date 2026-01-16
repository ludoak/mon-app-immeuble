import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# 1. CONFIGURATION
st.set_page_config(page_title="GH Diagnostic Pro", layout="wide")

# 2. TON IA GEMINI
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. TA BASE DE DONNÉES (Écrite directement ici !)
# Tu peux ajouter ou modifier des noms ici facilement
data = {
    "Résidence": ["Canterane", "Canterane", "La Dussaude", "La Dussaude"],
    "Appartement": ["101", "102", "201", "202"],
    "Nom": ["Lolo", "Zezette", "Kiki", "Aniotsbehere"]
}
df = pd.DataFrame(data)

# 4. INTERFACE
st.title("🏢 Assistant Technique Gironde Habitat")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Localisation")
    res_sel = st.selectbox("Choisir la Résidence", df["Résidence"].unique())
    
    # Filtre les appts selon la résidence
    df_res = df[df["Résidence"] == res_sel]
    appt_sel = st.selectbox("N° Appartement", df_res["Appartement"])
    
    # Trouve le nom
    nom_loc = df_res[df_res["Appartement"] == appt_sel]["Nom"].iloc[0]
    st.success(f"👤 Locataire : **{nom_loc}**")

with col2:
    st.subheader("📸 Signalement")
    photo = st.file_uploader("Prendre une photo", type=["jpg", "png", "jpeg"])
    note = st.text_input("Note rapide (ex: Fuite évier)")

# 5. ANALYSE IA
if st.button("🔍 LANCER L'ANALYSE", type="primary", use_container_width=True):
    with st.spinner("Analyse Gemini en cours..."):
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"Tu es expert pour Gironde Habitat. Analyse : {note}. Rappelle si c'est à la charge du locataire."
        
        if photo:
            img = Image.open(photo)
            response = model.generate_content([prompt, img])
        else:
            response = model.generate_content(prompt)
            
        st.markdown("---")
        st.subheader("📋 Résultat du Diagnostic")
        st.write(response.text)