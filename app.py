# --- 2. CONNEXION IA ---
if "CLE_TEST" not in st.secrets:
    st.error("Clé API Gemini non trouvée.")
    st.stop()
else:
    genai.configure(api_key=st.secrets["CLE_TEST"])
    
    # --- ASTUCE : On cherche le bon nom automatiquement ---
    try:
        # On liste les modèles disponibles sur votre compte
        models_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # On cherche celui qui contient "flash" (le plus rapide), sinon on prend le premier dispo
        model_id = next((m for m in models_list if "flash" in m), models_list[0])
        
        # On affiche le nom trouvé dans un petit message gris pour info
        st.caption(f"Modèle IA détecté : {model_id}")
        
        model = genai.GenerativeModel(model_id)
    except Exception as e:
        st.error(f"Impossible de trouver un modèle Gemini valide : {e}")
        st.stop()
