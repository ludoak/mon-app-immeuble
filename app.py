import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime

# --- 1. DESIGN & CONFIG ---
st.set_page_config(page_title="GH Expert Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #00f2ff; }
    .holo-card {
        background: rgba(255, 0, 255, 0.05);
        border: 1px solid #ff00ff;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 0 15px rgba(255, 0, 255, 0.2);
    }
    .neon-title { color: #ff00ff; text-align: center; text-shadow: 0 0 15px #ff00ff; font-family: monospace; }
    .stButton>button { background: linear-gradient(90deg, #ff00ff, #00f2ff); color: white; font-weight: bold; border-radius: 20px; border: none; }
    
    /* Couleurs pour le Guide */
    .badge-loc { background-color: #2ecc71; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold; }
    .badge-gh { background-color: #3498db; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold; }
    .badge-ent { background-color: #e67e22; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNEXIONS ---
conn = st.connection("gsheets", type=GSheetsConnection)
def load_data():
    try: return conn.read(ttl="1s")
    except: return pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

df = load_data()

if "CLE_TEST" in st.secrets:
    genai.configure(api_key=st.secrets["CLE_TEST"])

# --- 3. INTERFACE ---
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT - EXPERT PRO</h1>", unsafe_allow_html=True)

tab_diag, tab_guide, tab_admin = st.tabs(["📟 DIAGNOSTIC", "📋 GUIDE DES CHARGES", "⚙️ GESTION"])

# --- ONGLET 1 : DIAGNOSTIC ---
with tab_diag:
    if not df.empty:
        col_list, col_scan = st.columns([1, 1.5])
        with col_list:
            st.subheader("👥 RÉSIDENTS")
            st.dataframe(df, use_container_width=True, hide_index=True)
        with col_scan:
            st.markdown('<div class="holo-card">', unsafe_allow_html=True)
            res_sel = st.selectbox("📍 Résidence", df["Résidence"].unique())
            bat_sel = st.selectbox("🏢 Bâtiment", df[df["Résidence"] == res_sel]["Bâtiment"].unique())
            appt_sel = st.selectbox("🚪 Appartement", df[(df["Résidence"] == res_sel) & (df["Bâtiment"] == bat_sel)]["Appartement"].unique())
            
            source = st.radio("Source :", ["Scanner Photo", "Galerie"], horizontal=True)
            photo = st.camera_input("SCAN") if source == "Scanner Photo" else st.file_uploader("IMPORT", type=["jpg", "png", "jpeg"])
            
            if photo and st.button("🚀 LANCER L'ANALYSE"):
                try:
                    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    target_model = next((m for m in models if "flash" in m), models[0])
                    model = genai.GenerativeModel(target_model)
                    img = Image.open(photo)
                    prompt = "Expert bâtiment. Dis si c'est la charge du Bailleur (GH), du Locataire ou d'une Entreprise. Réponse courte."
                    response = model.generate_content([prompt, img])
                    st.info(response.text)
                except Exception as e: st.error(f"Erreur : {e}")
            st.markdown('</div>', unsafe_allow_html=True)

# --- ONGLET 2 : GUIDE DES CHARGES (LA MATRICE) ---
with tab_guide:
    st.markdown("### 🔍 Matrice des Responsabilités & Entreprises")
    
    # Données du guide
    guide_data = [
        {"Équipement": "Robinetterie / Joints", "Responsable": "LOCATAIRE", "Action": "Remplacement / Entretien"},
        {"Équipement": "Chaudière (Panne)", "Responsable": "ENTREPRISE", "Action": "Contrat de maintenance P3"},
        {"Équipement": "Électricité (Prises)", "Responsable": "LOCATAIRE", "Action": "Réparation usure normale"},
        {"Équipement": "Gros œuvre / Toiture", "Responsable": "BAILLEUR (GH)", "Action": "Réparation structurelle"},
        {"Équipement": "VMC / Bouches", "Responsable": "ENTREPRISE", "Action": "Contrat entretien annuel"},
        {"Équipement": "Menuiserie (Poignées)", "Responsable": "LOCATAIRE", "Action": "Remplacement / Graissage"}
    ]
    
    # Affichage sous forme de cartes colorées
    for item in guide_data:
        color_class = "badge-loc" if item["Responsable"] == "LOCATAIRE" else "badge-gh" if item["Responsable"] == "BAILLEUR (GH)" else "badge-ent"
        st.markdown(f"""
            <div class="holo-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:1.2em;">{item['Équipement']}</b>
                    <span class="{color_class}">{item['Responsable']}</span>
                </div>
                <p style="margin-top:10px; color:#aaa;">{item['Action']}</p>
            </div>
        """, unsafe_allow_html=True)

# --- ONGLET 3 : GESTION ---
with tab_admin:
    st.subheader("⚙️ Configuration de la base")
    # Formulaire d'ajout
    with st.form("add_loc"):
        c1, c2 = st.columns(2)
        with c1:
            r = st.text_input("Résidence")
            b = st.text_input("Bâtiment")
        with c2:
            a = st.text_input("Appartement")
            n = st.text_input("Nom")
        if st.form_submit_button("💾 Enregistrer dans le Sheets"):
            new_df = pd.concat([df, pd.DataFrame([{"Résidence": r, "Bâtiment": b, "Appartement": a, "Nom": n}])], ignore_index=True)
            conn.update(data=new_df)
            st.success("Ajouté !")
            st.rerun()
