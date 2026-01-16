# --- 4. LOGIQUE IA EXPERTE (ANALYSE VISUELLE) ---
objet_ia = ""
phrase_locatif = "Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire."

if notes or photo:
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Le prompt est maintenant beaucoup plus précis sur l'analyse d'image
        prompt = f"""Tu es l'inspecteur technique expert de Gironde Habitat. 
        Analyse la photo et les notes suivantes : '{notes}'.
        
        TON OBJECTIF : Faire un diagnostic précis basé sur la photo.
        
        GRILLE D'ANALYSE VISUELLE :
        1. ÉTANCHÉITÉ (Joints silicone, douche, évier) : 
           - Si noirci ou décollé = Défaut d'entretien. -> CHARGE LOCATAIRE.
        2. ÉLECTRICITÉ : 
           - Si prise sortie du mur ou cassée physiquement = Dégradation. -> CHARGE LOCATAIRE.
           - Si aspect brûlé ou usure interne = Panne technique. -> GIRONDE HABITAT.
        3. MENUISERIE : 
           - Vitre fêlée/cassée = Dégradation. -> CHARGE LOCATAIRE.
           - Poignée lâche ou serrure grippée = Entretien courant. -> CHARGE LOCATAIRE.
        4. HYGIÈNE :
           - Calcaire excessif, moisissures de surface = Défaut de nettoyage. -> CHARGE LOCATAIRE.

        CONSIGNE DE RÉDACTION :
        - Sois très précis sur ce que tu vois (ex: 'On observe un décollement du joint silicone').
        - Si c'est locatif (Orange), insère obligatoirement : '{phrase_locatif}'.
        - Si c'est pour une entreprise (Logista, etc.), explique pourquoi.

        FORMAT : 
        Bonjour,
        [Diagnostic visuel précis] + [Décision de charge]
        Cordialement"""
        
        # On envoie la photo et le texte à l'IA
        if photo:
            img = Image.open(photo)
            response = model.generate_content([prompt, img])
        else:
            response = model.generate_content(prompt)
            
        objet_ia = response.text
    except Exception as e:
        objet_ia = f"Erreur d'analyse : {e}"

st.divider()
st.subheader("🔍 Analyse de l'Inspecteur IA")
constat_final = st.text_area("Rapport détaillé :", value=objet_ia, height=300)