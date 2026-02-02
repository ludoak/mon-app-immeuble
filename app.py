import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime

# --- 1. DESIGN HOLOGRAPHIQUE ---
st.set_page_config(page_title="GH - Project Neon", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #00f2ff; }
    .holo-card {
        background: rgba(255, 0, 255, 0.05);
        border: 1px solid #ff00ff;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .neon-title { color: #ff00ff; text-align: center; text-shadow: 0 0 15px #ff00ff; }
    .stButton>button {
        background: linear-gradient(90deg, #ff00ff, #00f2ff);
        color: white; font-weight: bold; border-radius: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTION DES DONNÉES (MÉMOIRE LOCALE) ---
if 'df_locataires' not in st.session_state:
    # On charge une base par défaut
    st.session_state.df_locataires = pd.DataFrame([
        {"Résidence": "Canterane", "Bâtiment": "A", "Appartement": "10", "Nom": "Lolo"},
        {"Résidence": "La Dussaude", "Bâtiment": "B", "Appartement": "95", "Nom": "Zezette"}
    ])

# --- 3. CONFIGURATION IA ---
if "CLE_TEST" in st.secrets:
    genai.configure(api_key=st.secrets["CLE_TEST"])
else:
    st.error("🚨 Clé API manquante dans les Secrets.")

# --- 4. INTERFACE ---
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT - EXPERT</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📟 DIAGNOSTIC", "⚙️ GESTION LOCATAIRES"])

with tab1:
    df = st.session_state.df_locataires
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("👥 RÉSIDENTS")
        st.dataframe(df, use_container_width=True, hide_index=True)

    with col2:
        st.markdown('<div class="holo-card">', unsafe_allow_html=True)
        res_sel = st.selectbox("📍 Résidence", df["Résidence"].unique())
        bat_sel = st.selectbox("🏢 Bâtiment", df[df["Résidence"] == res_sel]["Bâtiment"].unique())
        appt_sel = st.selectbox("🚪 Appartement", df[(df["Résidence"] == res_sel) & (df["Bâtiment"] == bat_sel)]["Appartement"])
        
        source = st.radio("📸 Source :", ["Scanner", "Galerie"], horizontal=True)
        photo = st.camera_input("SCAN") if source == "Scanner" else st.file_uploader("IMPORT", type=["jpg", "png", "jpeg"])
        
        if photo and st.button("🚀 LANCER L'ANALYSE"):
            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                target_model = next((m for m in available_models if "flash" in m), available_models[0])
                model = genai.GenerativeModel(target_model)
                img = Image.open(photo)
                
                with st.spinner("Analyse technique..."):
                    response = model.generate_content(["Expert GH immo. Charge Bailleur, Locataire ou Prestataire ? Réponse courte.", img])
                    st.info(response.text)
                    
                    nom_loc = df[(df["Appartement"] == appt_sel) & (df["Bâtiment"] == bat_sel)]["Nom"].iloc[0]
                    lettre = f"OBJET : {res_sel} - {bat_sel} - Appt {appt_sel}\nLOCATAIRE : {nom_loc}\n\n{response.text}"
                    st.text_area("Courrier prêt :", lettre, height=150)
            except Exception as e:
                st.error(f"Erreur : {e}")
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.subheader("➕ Ajouter un résident")
    with st.form("ajout"):
        n_res = st.text_input("Résidence")
        n_bat = st.text_input("Bâtiment")
        n_appt = st.text_input("Appartement")
        n_nom = st.text_input("Nom")
        if st.form_submit_button("Ajouter"):
            new_row = pd.DataFrame([{"Résidence": n_res, "Bâtiment": n_bat, "Appartement": n_appt, "Nom": n_nom}])
            st.session_state.df_locataires = pd.concat([st.session_state.df_locataires, new_row], ignore_index=True)
            st.success("Ajouté temporairement !")
            st.rerun()

    st.divider()
    st.subheader("🗑️ Supprimer un résident")
    sel_del = st.selectbox("Choisir qui supprimer", st.session_state.df_locataires["Nom"].tolist())
    if st.button("Confirmer la suppression"):
        st.session_state.df_locataires = st.session_state.df_locataires[st.session_state.df_locataires["Nom"] != sel_del]
        st.warning(f"{sel_del} supprimé.")
        st.rerun()
