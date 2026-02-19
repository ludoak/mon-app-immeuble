import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import urllib.parse

# --- 1. CONFIGURATION & STYLE ---
st.set_page_config(page_title="GH Expert Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #00f2ff; }
    .holo-card {
        background: rgba(255, 0, 255, 0.05);
        border: 1px solid #ff00ff;
        border-radius: 12px; padding: 20px; margin-bottom: 20px;
        box-shadow: 0 0 15px rgba(255, 0, 255, 0.2);
    }
    .neon-title { color: #ff00ff; text-align: center; text-shadow: 0 0 15px #ff00ff; font-family: monospace; font-size: 1.5rem; }
    .stButton>button { 
        background: linear-gradient(90deg, #ff00ff, #00f2ff); 
        color: white; font-weight: bold; border-radius: 20px; 
        width: 100%; min-height: 50px; font-size: 1.1rem;
    }
    .mail-btn {
        background: #0078d4; color: white; padding: 15px; border-radius: 20px;
        text-decoration: none; font-weight: bold; display: block; text-align: center; font-size: 1.1rem;
        margin-top: 10px;
    }
    .badge-loc { background-color: #e74c3c; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold;}
    .badge-gh { background-color: #3498db; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold;}
    .badge-ent { background-color: #f39c12; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNEXIONS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def load_data():
    try:
        df = conn.read()
        required_cols = ["Résidence", "Bâtiment", "Appartement", "Nom"]
        if df.empty or not all(col in df.columns for col in required_cols):
            return pd.DataFrame(columns=required_cols)
        return df
    except Exception as e:
        # On retourne un DataFrame vide si erreur pour ne pas planter l'app
        return pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

df = load_data()

# Configuration Gemini
if "CLE_TEST" in st.secrets:
    genai.configure(api_key=st.secrets["CLE_TEST"])
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        model = genai.GenerativeModel('gemini-pro-vision')
else:
    st.error("Clé API Gemini manquante dans les secrets.")
    st.stop()

# --- 3. INTERFACE ---
st.markdown("<h1 class='neon-title'>GH EXPERT PRO</h1>", unsafe_allow_html=True)

# Initialisation de l'historique
if 'history' not in st.session_state:
    st.session_state.history = []

tab_diag, tab_photos, tab_guide, tab_admin = st.tabs([
    "📟 DIAGNOSTIC", 
    "📸 PHOTOS", 
    "📋 GUIDE CHARGES", 
    "⚙️ GESTION"
])

# --- ONGLET 1 : DIAGNOSTIC ---
with tab_diag:
    if df.empty:
        st.warning("Base de données vide ou non connectée. Allez dans l'onglet Gestion ou vérifiez le partage du Sheet.")
    else:
        col_l, col_r = st.columns([1, 1.2])
        
        with col_l:
            st.subheader("1️⃣ LOCATAIRE")
            residences = df["Résidence"].unique().tolist()
            res = st.selectbox("Résidence", residences, key="sel_res")
            
            filtered_df = df[df["Résidence"] == res]
            apps = filtered_df["Appartement"].unique().tolist()
            app = st.selectbox("Appartement", apps, key="sel_app")
            
            loc_row = filtered_df[filtered_df["Appartement"] == app]
            nom_loc = loc_row.iloc[0]["Nom"] if not loc_row.empty else "Inconnu"
            st.success(f"👤 **{nom_loc}**")
            
            prob_type = st.selectbox("Type de problème", [
                "🔎 Détection automatique", 
                "💧 Plomberie", 
                "⚡ Électricité", 
                "🗝️ Serrurerie", 
                "🌡️ Chauffage", 
                "🧹 Nettoyage"
            ])
            
            dest_mail = st.text_input("Email destinataire", value="ludoak33@gmail.com")

        with col_r:
            st.subheader("2️⃣ CONSTAT")
            st.markdown('<div class="holo-card">', unsafe_allow_html=True)
            
            src = st.radio("Source", ["Caméra", "Fichier"], horizontal=True)
            img = st.camera_input("PRENDRE LA PHOTO") if src == "Caméra" else st.file_uploader("IMPORTER")
            
            if img and st.button("🚀 ANALYSER"):
                with st.spinner("Analyse en cours..."):
                    try:
                        context = f"Type signalé : {prob_type}." if "Détection" not in prob_type else ""
                        prompt = f"""
                        Tu es un expert technique bailleur social. {context}
                        Analyse cette photo.
                        
                        1. Identifie le problème en une phrase.
                        2. Détermine le responsable UNIQUEMENT selon ces règles :
                           - LOCATAIRE : Petit entretien, usure normale, joints, ampoules, propreté.
                           - BAILLEUR (GH) : Vétusté, gros œuvre, équipements vétustes.
                           - PRESTATAIRE : Maintenance sous contrat (chaudière, VMC).
                        
                        Réponds au format strict :
                        **Problème** : ...
                        **Responsable** : [LOCATAIRE / BAILLEUR / PRESTATAIRE]
                        **Action** : ...
                        """
                        
                        image = Image.open(img)
                        response = model.generate_content([prompt, image])
                        
                        verdict = response.text
                        info = f"Appt {app} ({nom_loc})"
                        
                        st.session_state.history.append({
                            "date": datetime.now().strftime("%H:%M"),
                            "info": info,
                            "result": verdict.split('\n')[0]
                        })
                        
                        st.session_state.verdict = verdict
                        st.session_state.info = info
                        
                    except Exception as e:
                        st.error(f"Erreur IA : {e}")

            if 'verdict' in st.session_state:
                st.markdown("#### 📝 Résultat")
                st.info(st.session_state.verdict)
                
                sujet = f"Constat {st.session_state.info} - {prob_type}"
                body_mail = f"BONJOUR,\n\nConstat pour : {st.session_state.info}.\nType : {prob_type}\n\nAnalyse :\n{st.session_state.verdict}\n\nCordialement."
                
                mail_link = f"mailto:{dest_mail}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(body_mail[:800])}"
                st.markdown(f'<a href="{mail_link}" class="mail-btn">📧 ENVOYER LE RAPPORT</a>', unsafe_allow_html=True)
                st.code(body_mail)

            st.markdown('</div>', unsafe_allow_html=True)

# --- ONGLET 2 : PHOTOS ---
with tab_photos:
    st.subheader("🛠️ Preuves de travaux")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**AVANT**")
        img_av = st.camera_input("Photo AVANT", key="cam_av")
        if img_av:
            st.download_button("⬇️ Télécharger", img_av, file_name=f"avant_{datetime.now().strftime('%H%M')}.jpg")
    with c2:
        st.markdown("**APRÈS**")
        img_ap = st.camera_input("Photo APRÈS", key="cam_ap")
        if img_ap:
            st.download_button("⬇️ Télécharger", img_ap, file_name=f"apres_{datetime.now().strftime('%H%M')}.jpg")

# --- ONGLET 3 : GUIDE ---
with tab_guide:
    st.subheader("🔍 Qui paie quoi ?")
    
    guide_data = [
        {"Eq": "Robinetterie / Joints", "Resp": "LOCATAIRE", "Badge": "badge-loc"},
        {"Eq": "Ampoules / Cache-prise", "Resp": "LOCATAIRE", "Badge": "badge-loc"},
        {"Eq": "Chaudière (Pannes)", "Resp": "PRESTATAIRE", "Badge": "badge-ent"},
        {"Eq": "VMC / Ascenseur", "Resp": "PRESTATAIRE", "Badge": "badge-ent"},
        {"Eq": "Fuite tuyau encastré", "Resp": "BAILLEUR (GH)", "Badge": "badge-gh"},
        {"Eq": "Fenêtres / Toiture", "Resp": "BAILLEUR (GH)", "Badge": "badge-gh"},
    ]
    
    for item in guide_data:
        st.markdown(f"**{item['Eq']}** : <span class='{item['Badge']}'>{item['Resp']}</span>", unsafe_allow_html=True)

# --- ONGLET 4 : GESTION ---
with tab_admin:
    st.subheader("➕ Ajouter un résident")
    with st.form("add"):
        r = st.text_input("Résidence", value=st.session_state.get("sel_res", ""))
        b = st.text_input("Bâtiment")
        a = st.text_input("Appartement")
        n = st.text_input("Nom")
            
        if st.form_submit_button("💾 ENREGISTRER"):
            if r and a and n:
                new = pd.DataFrame([{"Résidence": r, "Bâtiment": b, "Appartement": a, "Nom": n}])
                try:
                    current_df = conn.read()
                    updated_df = pd.concat([current_df, new], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success("Ajouté !")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Erreur : {e}")
    
    st.divider()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
