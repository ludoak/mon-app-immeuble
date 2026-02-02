import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION & DESIGN ---
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

# --- 2. CONNEXIONS (IA & GOOGLE SHEETS) ---
if "CLE_TEST" in st.secrets:
    genai.configure(api_key=st.secrets["CLE_TEST"])
else:
    st.error("🚨 Clé API manquante.")

# Connexion au Google Sheets (configuré dans les secrets Streamlit)
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    return conn.read(ttl="1m") # Rafraîchissement toutes les minutes

# --- 3. INTERFACE ---
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT - EXPERT</h1>", unsafe_allow_html=True)

tab_diag, tab_admin = st.tabs(["📟 DIAGNOSTIC", "⚙️ GESTION LOCATAIRES"])

# --- ONGLET 1 : DIAGNOSTIC (TON USAGE TERRAIN) ---
with tab_diag:
    df = get_data()
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("👥 RÉSIDENTS")
        st.dataframe(df, use_container_width=True, hide_index=True)

    with col2:
        st.markdown('<div class="holo-card">', unsafe_allow_html=True)
        res_sel = st.selectbox("📍 Résidence", df["Résidence"].unique() if not df.empty else ["Vide"])
        bat_sel = st.selectbox("🏢 Bâtiment", df[df["Résidence"] == res_sel]["Bâtiment"].unique() if not df.empty else ["-"])
        appt_sel = st.selectbox("🚪 Appartement", df[(df["Résidence"] == res_sel) & (df["Bâtiment"] == bat_sel)]["Appartement"] if not df.empty else ["-"])
        
        source = st.radio("📸 Source :", ["Scanner", "Galerie"], horizontal=True)
        photo = st.camera_input("SCAN") if source == "Scanner" else st.file_uploader("IMPORT", type=["jpg", "png", "jpeg"])
        
        if photo and st.button("🚀 LANCER L'ANALYSE"):
            try:
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(next((m for m in models if "flash" in m), models[0]))
                img = Image.open(photo)
                
                with st.spinner("Analyse technique..."):
                    response = model.generate_content(["Expert GH immo. Charge Bailleur, Locataire ou Prestataire ?", img])
                    st.info(response.text)
                    
                    # Courrier auto
                    nom_loc = df[(df["Appartement"] == appt_sel) & (df["Bâtiment"] == bat_sel)]["Nom"].iloc[0]
                    lettre = f"OBJET : {res_sel} - {bat_sel} - Appt {appt_sel}\nLOCATAIRE : {nom_loc}\n\n{response.text}"
                    st.text_area("Courrier prêt :", lettre, height=150)
            except Exception as e:
                st.error(f"Erreur : {e}")
        st.markdown('</div>', unsafe_allow_html=True)

# --- ONGLET 2 : ADMIN (AJOUTER / RETIRER) ---
with tab_admin:
    st.subheader("➕ Ajouter un nouveau résident")
    with st.form("ajout_locataire"):
        n_res = st.text_input("Résidence")
        n_bat = st.text_input("Bâtiment")
        n_appt = st.text_input("Appartement")
        n_nom = st.text_input("Nom du locataire")
        
        if st.form_submit_button("Valider l'ajout"):
            new_row = pd.DataFrame([{"Résidence": n_res, "Bâtiment": n_bat, "Appartement": n_appt, "Nom": n_nom}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=updated_df)
            st.success("✅ Locataire ajouté au Google Sheets !")
            st.rerun()

    st.divider()
    st.subheader("🗑️ Supprimer un résident")
    sel_del = st.selectbox("Choisir qui supprimer", df["Nom"].tolist() if not df.empty else [])
    if st.button("Confirmer la suppression"):
        updated_df = df[df["Nom"] != sel_del]
        conn.update(data=updated_df)
        st.warning(f"Locataire {sel_del} supprimé.")
        st.rerun()
