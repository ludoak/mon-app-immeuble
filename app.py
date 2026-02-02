import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import urllib.parse

# --- 1. CONFIG & STYLE ---
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
    .stButton>button { background: linear-gradient(90deg, #ff00ff, #00f2ff); color: white; font-weight: bold; border-radius: 20px; border: none; width: 100%; }
    .mail-btn {
        background: linear-gradient(90deg, #0078d4, #00bcf2);
        color: white; padding: 10px 20px; border-radius: 20px;
        text-decoration: none; font-weight: bold; display: inline-block;
        text-align: center; width: 100%; margin-top: 10px;
    }
    .delete-btn>button { background: linear-gradient(90deg, #ff4b4b, #ff0000) !important; }
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

# Initialisation de l'historique
if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. INTERFACE ---
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT - EXPERT 2.0</h1>", unsafe_allow_html=True)

tab_diag, tab_avant_apres, tab_admin = st.tabs([
    "📟 DIAGNOSTIC IA", 
    "📸 AVANT / APRÈS", 
    "⚙️ GESTION & SUPPRESSION"
])

# --- ONGLET 1 : DIAGNOSTIC ---
with tab_diag:
    if not df.empty:
        col_l, col_r = st.columns([1, 1.5])
        with col_l:
            st.subheader("👥 CHOIX LOCATAIRE")
            res = st.selectbox("📍 Résidence", df["Résidence"].unique())
            bat = st.selectbox("🏢 Bâtiment", df[df["Résidence"] == res]["Bâtiment"].unique())
            app = st.selectbox("🚪 Appartement", df[(df["Résidence"] == res) & (df["Bâtiment"] == bat)]["Appartement"].unique())
            nom_loc = df[(df["Résidence"] == res) & (df["Bâtiment"] == bat) & (df["Appartement"] == app)]["Nom"].iloc[0]
            st.warning(f"Occupant : {nom_loc}")
            
        with col_r:
            st.markdown('<div class="holo-card">', unsafe_allow_html=True)
            mode = st.radio("Image :", ["Appareil Photo", "Fichier PC"], horizontal=True)
            img_diag = st.camera_input("SCAN") if mode == "Appareil Photo" else st.file_uploader("FICHIER", type=["jpg", "png"])
            
            if img_diag and st.button("🚀 ANALYSER"):
                try:
                    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model = genai.GenerativeModel(next((m for m in models if "flash" in m), models[0]))
                    response = model.generate_content(["Expert GH. Charge Bailleur, Locataire ou Entreprise ?", Image.open(img_diag)])
                    
                    # Sauvegarde pour le mail et l'historique
                    verdict = response.text
                    loc_info = f"{res} - {bat} - Appt {app}"
                    st.session_state.verdict = verdict
                    st.session_state.loc_info = loc_info
                    st.session_state.loc_name = nom_loc
                    
                    # Ajout à l'historique
                    st.session_state.history.insert(0, {"date": datetime.now().strftime("%H:%M"), "loc": loc_info, "txt": verdict[:50]+"..."})
                    
                    st.success(verdict)
                except Exception as e: st.error(f"Erreur : {e}")

            if 'verdict' in st.session_state:
                st.divider()
                objet = f"Constat technique : {st.session_state.loc_info}"
                corps = f"Bonjour,\n\nVoici le rapport concernant le logement de {st.session_state.loc_name} ({st.session_state.loc_info}).\n\nConstat du {datetime.now().strftime('%d/%m/%Y')} :\n{st.session_state.verdict}\n\nCordialement,"
                mail_url = f"mailto:?subject={urllib.parse.quote(objet)}&body={urllib.parse.quote(corps)}"
                st.markdown(f'<a href="{mail_url}" class="mail-btn">📧 GÉNÉRER LE MAIL RAPPORT</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # Affichage de l'historique rapide
    if st.session_state.history:
        with st.expander("🕒 Derniers diagnostics de la session"):
            for h in st.session_state.history[:5]:
                st.write(f"**{h['date']}** - {h['loc']} : {h['txt']}")

# --- ONGLET 2 : AVANT / APRÈS ---
with tab_avant_apres:
    st.markdown("### 🛠️ Suivi de chantier")
    c1, c2 = st.columns(2)
    with c1: st.camera_input("📷 AVANT", key="c_av")
    with c2: st.camera_input("📷 APRÈS", key="c_ap")

# --- ONGLET 3 : GESTION ---
with tab_admin:
    st.subheader("➕ Ajouter un résident")
    with st.form("add"):
        c1, c2 = st.columns(2)
        r_in = c1.text_input("Résidence")
        b_in = c1.text_input("Bâtiment")
        a_in = c2.text_input("Appartement")
        n_in = c2.text_input("Nom")
        if st.form_submit_button("💾 ENREGISTRER"):
            new_row = pd.DataFrame([{"Résidence": r_in, "Bâtiment": b_in, "Appartement": a_in, "Nom": n_in}])
            conn.update(data=pd.concat([df, new_row], ignore_index=True))
            st.rerun()

    st.divider()
    st.subheader("🗑️ Supprimer un résident")
    if not df.empty:
        target = st.selectbox("Qui supprimer ?", df["Nom"].tolist())
        st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
        if st.button(f"❌ SUPPRIMER {target}"):
            conn.update(data=df[df["Nom"] != target])
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
