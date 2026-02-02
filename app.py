import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime

# --- 1. CONFIG & DESIGN ---
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
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT - EXPERT 2.0</h1>", unsafe_allow_html=True)

tab_diag, tab_avant_apres, tab_guide, tab_admin = st.tabs([
    "📟 DIAGNOSTIC IA", 
    "📸 AVANT / APRÈS", 
    "📋 GUIDE DES CHARGES", 
    "⚙️ GESTION"
])

# --- ONGLET 1 : DIAGNOSTIC IA ---
with tab_diag:
    if not df.empty:
        col_l, col_r = st.columns([1, 1.5])
        with col_l:
            st.subheader("👥 LOCATAIRE")
            res = st.selectbox("📍 Résidence", df["Résidence"].unique())
            bat = st.selectbox("🏢 Bâtiment", df[df["Résidence"] == res]["Bâtiment"].unique())
            app = st.selectbox("🚪 Appartement", df[(df["Résidence"] == res) & (df["Bâtiment"] == bat)]["Appartement"].unique())
            nom_loc = df[(df["Résidence"] == res) & (df["Bâtiment"] == bat) & (df["Appartement"] == app)]["Nom"].iloc[0]
            st.info(f"📍 Occupant : {nom_loc}")
            
        with col_r:
            st.markdown('<div class="holo-card">', unsafe_allow_html=True)
            img_file = st.camera_input("SCANNER LE DÉSORDRE")
            
            if img_file and st.button("🚀 ANALYSER LE DÉSORDRE"):
                try:
                    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model = genai.GenerativeModel(next((m for m in models if "flash" in m), models[0]))
                    response = model.generate_content(["Expert GH. Charge Bailleur, Locataire ou Entreprise ? Réponse courte.", Image.open(img_file)])
                    st.session_state.last_report = response.text
                    st.session_state.info_loc = f"{res} - Bât {bat} - Appt {app} ({nom_loc})"
                    st.success(response.text)
                except Exception as e: st.error(f"Erreur : {e}")
            
            if 'last_report' in st.session_state:
                st.divider()
                full_text = f"*RAPPORT GH EXPERT*\n📍 {st.session_state.info_loc}\n📅 {datetime.now().strftime('%d/%m/%Y')}\n\n📢 *CONSTAT :*\n{st.session_state.last_report}"
                st.text_area("📋 Message à copier (WhatsApp/Mail) :", full_text, height=150)
            st.markdown('</div>', unsafe_allow_html=True)

# --- ONGLET 2 : AVANT / APRÈS ---
with tab_avant_apres:
    st.markdown("### 🛠️ Comparatif de Prestation")
    c1, c2 = st.columns(2)
    with c1: st.camera_input("📷 ÉTAT INITIAL (AVANT)", key="av")
    with c2: st.camera_input("📷 APRÈS INTERVENTION", key="ap")
    st.write("💡 *Prenez les photos pour valider la fin de chantier.*")

# --- ONGLET 3 : GUIDE DES CHARGES ---
with tab_guide:
    st.markdown("### 🔍 Matrice de Responsabilité")
    guide = {
        "Équipement": ["Joints/Robinets", "Chaudière", "Gros Oeuvre", "VMC", "Électricité"],
        "Responsable": ["🟢 LOCATAIRE", "🟠 PRESTATAIRE", "🔵 BAILLEUR (GH)", "🟠 PRESTATAIRE", "🟢 LOCATAIRE"],
        "Note": ["Entretien courant", "Contrat entretien", "Structure/Façade", "Entretien annuel", "Petites réparations"]
    }
    st.table(pd.DataFrame(guide))

# --- ONGLET 4 : GESTION ---
with tab_admin:
    st.subheader("⚙️ Administration Base de Données")
    # Formulaire d'ajout simple
    with st.expander("➕ Ajouter un nouveau locataire"):
        with st.form("add"):
            r = st.text_input("Résidence")
            b = st.text_input("Bâtiment")
            a = st.text_input("Appartement")
            n = st.text_input("Nom")
            if st.form_submit_button("Enregistrer"):
                new_row = pd.DataFrame([{"Résidence": r, "Bâtiment": b, "Appartement": a, "Nom": n}])
                conn.update(data=pd.concat([df, new_row], ignore_index=True))
                st.success("Enregistré !")
                st.rerun()
