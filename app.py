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
        color: white; padding: 12px 20px; border-radius: 20px;
        text-decoration: none; font-weight: bold; display: block;
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

# --- 3. INTERFACE ---
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT - EXPERT PRO</h1>", unsafe_allow_html=True)

tab_diag, tab_chantier, tab_admin = st.tabs(["📟 DIAGNOSTIC IA", "📸 AVANT / APRÈS", "⚙️ GESTION"])

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
            dest_mail = st.text_input("📧 Envoyer à :", placeholder="ex: bureau@gh.fr")
            
        with col_r:
            st.markdown('<div class="holo-card">', unsafe_allow_html=True)
            img_diag = st.camera_input("SCAN")
            if img_diag and st.button("🚀 ANALYSER"):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(["Expert GH. Charge Bailleur, Locataire ou Entreprise ?", Image.open(img_diag)])
                    st.session_state.verdict = response.text
                    st.session_state.loc_info = f"{res} - {bat} - Appt {app}"
                    st.session_state.loc_name = nom_loc
                    st.success(response.text)
                except Exception as e: st.error(f"Erreur : {e}")

            if 'verdict' in st.session_state:
                st.divider()
                objet = urllib.parse.quote(f"Constat technique GH : {st.session_state.loc_info}")
                corps_texte = f"Bonjour,\n\nRapport concernant le logement de {st.session_state.loc_name} ({st.session_state.loc_info}).\n\nDiagnostic :\n{st.session_state.verdict}\n\nCordialement,"
                corps = urllib.parse.quote(corps_texte)
                mail_url = f"mailto:{dest_mail}?subject={objet}&body={corps}"
                st.markdown(f'<a href="{mail_url}" class="mail-btn">📧 GÉNÉRER LE MAIL RAPPORT</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# --- ONGLET 2 : CHANTIER ---
with tab_chantier:
    st.markdown("### 🛠️ Suivi de travaux")
    c1, c2 = st.columns(2)
    with c1: st.camera_input("📸 AVANT", key="c_av")
    with c2: st.camera_input("📸 APRÈS", key="c_ap")

# --- ONGLET 3 : GESTION (RETOUR DU FORMULAIRE) ---
with tab_admin:
    st.subheader("➕ Ajouter un nouveau résident")
    with st.form("add_loc"):
        ca, cb = st.columns(2)
        r_i = ca.text_input("Résidence")
        b_i = ca.text_input("Bâtiment")
        a_i = cb.text_input("Appartement")
        n_i = cb.text_input("Nom du Locataire")
        
        if st.form_submit_button("💾 ENREGISTRER DANS LE SHEETS"):
            if r_i and n_i:
                new_row = pd.DataFrame([{"Résidence": r_i, "Bâtiment": b_i, "Appartement": a_i, "Nom": n_i}])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"✅ {n_i} ajouté !")
                st.rerun()
            else:
                st.error("Remplis au moins la Résidence et le Nom.")

    st.divider()
    st.subheader("🗑️ Supprimer un résident")
    if not df.empty:
        target = st.selectbox("Choisir le profil à supprimer", df["Nom"].tolist())
        st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
        if st.button(f"❌ SUPPRIMER DÉFINITIVEMENT {target}"):
            conn.update(data=df[df["Nom"] != target])
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
