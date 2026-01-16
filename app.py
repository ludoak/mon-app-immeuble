# --- 5. LOGIQUE D'ANALYSE AUTOMATIQUE ---
if st.button("🔍 GÉNÉRER LE RAPPORT ET LA LETTRE", type="primary", use_container_width=True):
    if not photo:
        st.warning("⚠️ Merci de prendre une photo pour lancer l'analyse automatique.")
    else:
        with st.spinner("L'IA examine la photo..."):
            try:
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                # On demande à l'IA d'être très précise sur la conclusion
                prompt_global = f"""
                Tu es l'expert technique de Gironde Habitat.
                Regarde cette photo et :
                1. Décris précisément le problème technique.
                2. Justifie selon les règles d'entretien.
                3. Conclus EXCLUSIVEMENT par l'un de ces trois codes en fin de réponse : 
                   CODE_RESULTAT:GH (si c'est pour Gironde Habitat)
                   CODE_RESULTAT:LOC (si c'est une charge locative)
                   CODE_RESULTAT:PREST (si c'est pour un prestataire)
                """
                
                img = Image.open(photo)
                res = model.generate_content([prompt_global, img])
                reponse_ia = res.text
                
                # --- LOGIQUE DE DÉTECTION DU BADGE ---
                type_charge = "🏢 CHARGE GH" # Par défaut
                label_lettre = "CHARGE GH"
                
                if "CODE_RESULTAT:LOC" in reponse_ia:
                    type_charge = "🛠️ CHARGE LOCATIVE"
                    label_lettre = "CHARGE LOCATIVE"
                elif "CODE_RESULTAT:PREST" in reponse_ia:
                    type_charge = "🏗️ CHARGE PRESTATAIRE"
                    label_lettre = "CHARGE PRESTATAIRE"
                elif "CODE_RESULTAT:GH" in reponse_ia:
                    type_charge = "🏢 CHARGE GH"
                    label_lettre = "CHARGE GH"
                
                # On nettoie le texte pour ne pas afficher le "CODE_RESULTAT" à l'utilisateur
                affichage_texte = reponse_ia.split("CODE_RESULTAT:")[0]

                # --- AFFICHAGE ---
                st.markdown("---")
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.metric("TYPE DE CHARGE", type_charge)
                with c2:
                    st.subheader("📋 Analyse Technique")
                    st.write(affichage_texte)
                
                # --- GÉNÉRATION DU COURRIER ---
                st.markdown("---")
                st.subheader("✉️ Courrier pour la plateforme")
                
                lettre = f"""OBJET : Signalement technique - {res_sel} / Appt {appt_sel}
DATE : {datetime.now().strftime("%d/%m/%Y")}

Madame, Monsieur,

J'ai constaté le désordre suivant dans le logement de M./Mme {nom_loc} (Appt {appt_sel}) :
{affichage_texte.split('.')[0]}.

Après diagnostic, ce désordre est classé en : {label_lettre}.

Merci de prendre les dispositions nécessaires.

Cordialement,
L'équipe technique GH."""

                st.text_area("Texte à copier :", lettre, height=200)
                
            except Exception as e:
                st.error(f"Erreur d'analyse : {e}")