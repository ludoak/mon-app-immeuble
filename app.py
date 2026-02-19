import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import urllib.parse

# --- 1. CONFIGURATION & STYLE ---
st.set_page_config(page_title="GH Expert Pro", layout="wide", initial_sidebar_state="collapsed")

# CSS pour un style "Mobile" rapide et lisible
st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #00f2ff; }
    /* Carte principale */
    .holo-card {
        background: rgba(255, 0, 255, 0.05);
        border: 1px solid #ff00ff;
        border-radius: 12px; padding: 20px; margin-bottom: 20px;
        box-shadow: 0 0 15px rgba(255, 0, 255, 0.2);
    }
    /* Titres */
    .neon-title { color: #ff00ff; text-align: center; text-shadow: 0 0 15px #ff00ff; font-family: monospace; font-size: 1.5rem; }
    /* Boutons plus gros pour le tactile */
    .stButton>button { 
        background: linear-gradient(90deg, #ff00ff, #00f2ff); 
        color: white; font-weight: bold; border-radius: 20px; 
        width: 100%; min-height: 50px; font-size: 1.2rem;
    }
    /* Bouton Mail */
    .mail-btn {
        background: #0078d4; color: white; padding: 15px; border-radius: 20px;
        text-decoration: none; font-weight: bold; display: block; text-align: center; font-size: 1.1rem;
        margin-top: 10px;
    }
    /* Badges responsabilités */
    .badge-loc { background-color: #e74c3c; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold;}
    .badge-gh { background-color: #3498db; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold;}
    .badge-ent { background-color: #f39c12; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold;}
    /* Masquer le footer Streamlit pour gagner de la place */
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
        return pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

df = load_data()

# Configuration Gemini
if "CLE_TEST" in st.secrets:
    genai.configure(api_key=st.secrets["CLE_TEST"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Clé API Gemini manquante dans les secrets.")
    st.stop()

# --- 3. INTERFACE PRINCIPALE ---
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT - EXPERT PRO</h1>", unsafe_allow_html=True)

# Barre latérale pour l'historique (gain de temps)
with st.sidebar:
    st.image("https://www.girondehabitat.fr/sites/all/themes/bootstrap_gH/logo.png", width=150)
    st.title("⏱️ Historique Session")
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    if st.session_state.history:
        for item in reversed(st.session_state.history[-5:]):
            st.markdown(f"**{item['date']}**")
            st.caption(f"{item['info']} - {item['result']}")
            st.divider()
    else:
        st.info("Aucune analyse en cours.")

# Onglets
tab_diag, tab_photos, tab_guide, tab_admin = st.tabs([
    "📟 DIAGNOSTIC", 
    "📸 PHOTOS", 
    "📋 GUIDE CHARGES", 
    "⚙️ GESTION"
])

# --- ONGLET 1 : DIAGNOSTIC (Optimisé) ---
with tab_diag:
    if df.empty:
        st.warning("Base de données vide. Allez dans l'onglet Gestion pour commencer.")
    else:
        # Utilisation de colonnes pour condenser l'affichage
        col_l, col_r = st.columns([1, 1.2])
        
        with col_l:
            st.subheader("1️⃣ LOCATAIRE")
            
            # Recherche rapide par résidence
            residences = df["Résidence"].unique().tolist()
            res = st.selectbox("Résidence", residences, key="sel_res", label_visibility="collapsed")
            
            filtered_df = df[df["Résidence"] == res]
            apps = filtered_df["Appartement"].unique().tolist()
            app = st.selectbox("Appartement", apps, key="sel_app", label_visibility="collapsed")
            
            loc_row = filtered_df[filtered_df["Appartement"] == app]
            nom_loc = loc_row.iloc[0]["Nom"] if not loc_row.empty else "Inconnu"
            
            # Affichage compact
            st.success(f"👤 **{nom_loc}**")
            
            # Choix du type de problème pour guider l'IA
            prob_type = st.selectbox("Type de problème", [
                "🔎 Détection automatique", 
                "💧 Plomberie / Fuite", 
                "⚡ Électricité", 
                "🗝️ Serrurerie", 
                "🌡️ Chauffage / VMC", 
                "🧹 Nettoyage / Dégradations"
            ])
            
            dest_mail = st.text_input("Email destinataire", value="ludoak33@gmail.com", label_visibility="collapsed")

        with col_r:
            st.subheader("2️⃣ CONSTAT")
            st.markdown('<div class="holo-card">', unsafe_allow_html=True)
            
            src = st.radio("Source", ["Caméra", "Fichier"], horizontal=True, label_visibility="collapsed")
            img = st.camera_input("PRENDRE LA PHOTO") if src == "Caméra" else st.file_uploader("IMPORTER", label_visibility="collapsed")
            
            if img and st.button("🚀 ANALYSER MAINTENANT"):
                with st.spinner("Analyse en cours..."):
                    try:
                        # Prompt amélioré pour plus de rapidité et précision
                        context = f"Type signalé : {prob_type}." if "Détection" not in prob_type else ""
                        prompt = f"""
                        Tu es un expert technique bailleur social. {context}
                        Analyse cette photo.
                        
                        1. Identifie le problème en une phrase.
                        2. Détermine le responsable UNIQUEMENT selon ces règles :
                           - LOCATAIRE : Petit entretien, usure normale, joints, ampoules, propreté, clé perdue.
                           - BAILLEUR (GH) : Vétusté, gros œuvre, équipements vétustes (fenêtres, tuyaux corrodés), toiture.
                           - PRESTATAIRE : Maintenance sous contrat (chaudière, VMC, ascenseur, chauffage urbain).
                        
                        Réponds au format strict :
                        **Problème** : ...
                        **Responsable** : [LOCATAIRE / BAILLEUR / PRESTATAIRE]
                        **Action** : (ex: Envoi facture / Intervention GH / Appel prestataire)
                        """
                        
                        image = Image.open(img)
                        response = model.generate_content([prompt, image])
                        
                        verdict = response.text
                        info = f"Appt {app} ({nom_loc})"
                        
                        # Sauvegarde dans l'historique
                        st.session_state.history.append({
                            "date": datetime.now().strftime("%H:%M"),
                            "info": info,
                            "result": verdict.split('\n')[0] # Première ligne seulement
                        })
                        
                        st.session_state.verdict = verdict
                        st.session_state.info = info
                        
                    except Exception as e:
                        st.error(f"Erreur IA : {e}")

            if 'verdict' in st.session_state:
                st.markdown("#### 📝 Résultat")
                st.info(st.session_state.verdict)
                
                # Boutons d'action rapide
                sujet = f"Constat {st.session_state.info} - {prob_type.split()[-1]}"
                body_mail = f"BONJOUR,\n\nConstat effectué pour : {st.session_state.info}.\nType : {prob_type}\n\nAnalyse :\n{st.session_state.verdict}\n\nCordialement."
                
                # Lien Mail
                mail_link = f"mailto:{dest_mail}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(body_mail[:800])}"
                st.markdown(f'<a href="{mail_link}" class="mail-btn">📧 ENVOYER LE RAPPORT</a>', unsafe_allow_html=True)
                
                # Bouton Copier (Utile sur mobile)
                st.caption("Ou copiez le texte ci-dessous :")
                st.code(body_mail, language='text')

            st.markdown('</div>', unsafe_allow_html=True)

# --- ONGLET 2 : PHOTOS AVANT/APRÈS ---
with tab_photos:
    st.subheader("🛠️ Preuves de travaux")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**AVANT**")
        img_av = st.camera_input("Photo AVANT", key="cam_av_new")
        if img_av:
            st.download_button("⬇️ Télécharger AVANT", img_av, file_name=f"avant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
    with c2:
        st.markdown("**APRÈS**")
        img_ap = st.camera_input("Photo APRÈS", key="cam_ap_new")
        if img_ap:
            st.download_button("⬇️ Télécharger APRÈS", img_ap, file_name=f"apres_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")

# --- ONGLET 3 : GUIDE DES CHARGES (Le tableau demandé) ---
with tab_guide:
    st.subheader("🔍 Qui paie quoi ? (Référence rapide)")
    st.markdown("Utilisez ce tableau pour vérifier la décision de l'IA.")
    
    # Tableau plus complet
    guide_data = [
        {"Équipement": "Robinetterie / Joints / Flexibles", "Responsable": "LOCATAIRE", "Détail": "Entretien courant"},
        {"Équipement": "Ampoules / Cache-prise / Clapet VM", "Responsable": "LOCATAIRE", "Détail": "Petite fourniture"},
        {"Équipement": "Serrure (perte de clé)", "Responsable": "LOCATAIRE", "Détail": "Négligence"},
        {"Équipement": "Traces de moisissure", "Responsable": "LOCATAIRE", "Détail": "Manque d'aération"},
        
        {"Équipement": "Chaudière (Pannes)", "Responsable": "PRESTATAIRE", "Détail": "Contrat maintenance"},
        {"Équipement": "VMC / Ascenseur", "Responsable": "PRESTATAIRE", "Détail": "Contrat maintenance"},
        {"Équipement": "Porte digicode (bloc)", "Responsable": "PRESTATAIRE", "Détail": "Contrat maintenance"},
        
        {"Équipement": "Fuite canalisation encastrée", "Responsable": "BAILLEUR (GH)", "Détail": "Vétusté / Gros œuvre"},
        {"Équipement": "Fenêtres (mécanisme cassé)", "Responsable": "BAILLEUR (GH)", "Détail": "Usure normale"},
        {"Équipement": "Toiture / Gouttières", "Responsable": "BAILLEUR (GH)", "Détail": "Gros œuvre"},
        {"Équipement": "Peinture (si état vétuste)", "Responsable": "BAILLEUR (GH)", "Détail": "Réfection"},
    ]
    
    for item in guide_data:
        if item['Responsable'] == "LOCATAIRE":
            badge_class = "badge-loc"
        elif item['Responsable'] == "BAILLEUR (GH)":
            badge_class = "badge-gh"
        else:
            badge_class = "badge-ent"
            
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; border-bottom: 1px solid #333;">
            <div style="flex: 2;"><b>{item['Équipement']}</b><br><small style="color:gray;">{item['Détail']}</small></div>
            <div style="flex: 1; text-align: right;"><span class='{badge_class}'>{item['Responsable']}</span></div>
        </div>
        """, unsafe_allow_html=True)

# --- ONGLET 4 : GESTION ---
with tab_admin:
    st.subheader("➕ Ajouter un résident")
    with st.form("add"):
        c1, c2 = st.columns(2)
        with c1:
            r = st.text_input("Résidence", value=st.session_state.get("sel_res", ""))
            b = st.text_input("Bâtiment")
        with c2:
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
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")
    
    st.divider()
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
