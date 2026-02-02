import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import os

# --- 1. DESIGN HOLOGRAPHIQUE ---
st.set_page_config(page_title="GH - Project Neon", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #00f2ff; }
    .holo-card {
        background: rgba(255, 0, 255, 0.05);
        border: 1px solid #ff00ff;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .neon-title { color: #ff00ff; text-align: center; text-shadow: 0 0 10px #ff00ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VÉRIFICATION DES SECRETS ---
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT</h1>", unsafe_allow_html=True)

if "CLE_TEST" not in st.secrets:
    st.error("❌ ERREUR : Le tiroir 'Secrets' est vide ou mal rempli sur Streamlit Cloud.")
    st.info("💡 Rappel : Tu dois écrire CLE_TEST = 'TaClé' dans les paramètres de l'app.")
    st.stop() # On arrête l'app ici si la clé n'est pas là
else:
    st.success("✅ CONNEXION ÉTABLIE : La clé a été trouvée !")

# --- 3. CHARGEMENT DES DONNÉES ---
DB_FILE = "base_locataires_gh.csv"
def charger_donnees():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={"Appartement": str})
    return pd.DataFrame({"Résidence": ["Canterane"], "Appartement": ["10"], "Nom": ["Locataire Test"]})

if 'df_locataires' not in st.session_state:
    st.session_state.df_locataires = charger_donnees()

# --- 4. INTERFACE ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("👤 RÉSIDENTS")
    df = st.session_state.df_locataires
    st.dataframe(df, use_container_width=True)

with col2:
    st.markdown('<div class="holo-card">', unsafe_allow_html=True)
    res_sel = st.selectbox("Résidence", df["Résidence"].unique())
    appt_sel = st.selectbox("Appartement", df[df["Résidence"] == res_sel]["Appartement"])
    
    source = st.radio("Acquisition :", ["Photo Directe", "Galerie"], horizontal=True)
    photo = st.camera_input("SCAN") if source == "Photo Directe" else st.file_uploader("IMPORT", type=["jpg", "png", "jpeg"])
    
    if photo and st.button("🚀 LANCER L'ANALYSE"):
        try:
            genai.configure(api_key=st.secrets["CLE_TEST"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            img = Image.open(photo)
            
            with st.spinner("Analyse technique en cours..."):
                response = model.generate_content(["Expert GH. Charge : Bailleur, Locataire ou Prestataire ? Courte réponse.", img])
                st.subheader("RÉSULTAT")
                st.write(response.text)
                
                st.divider()
                nom_loc = df[df["Appartement"] == appt_sel]["Nom"].iloc[0]
                lettre = f"OBJET : Signalement {res_sel} / {appt_sel}\nDATE : {datetime.now().strftime('%d/%m/%Y')}\n\n{response.text}"
                st.text_area("Courrier prêt :", lettre, height=150)
        except Exception as e:
            st.error(f"Erreur d'analyse : {e}")
    st.markdown('</div>', unsafe_allow_html=True)
