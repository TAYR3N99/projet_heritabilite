import streamlit as st
import os
from scripts.generer_rapport import generer_rapport_pdf
from scripts.nettoyage import analyser_qualite_donnees, identifier_variables_heritabilite

def app():
    st.title("📄 Génération du rapport")
    
    df = st.session_state.get('df')
    if df is None:
        st.warning("Veuillez d'abord importer un fichier.")
        return

    # Identification des variables
    variables = identifier_variables_heritabilite(df)
    if variables is None:
        st.error("Structure des données non reconnue.")
        return

    # Analyse de la qualité des données
    analyse_qualite = analyser_qualite_donnees(df)

    # Récupération des résultats de modélisation
    resultats = st.session_state.get('rapport', {})
    heritabilites = st.session_state.get('heritabilites', {})

    # Préparation des données pour le rapport
    mse = resultats.get('model_performance', {}).get('r2', 0)
    importances = resultats.get('feature_importance', {})
    cible = resultats.get('target', '')
    variables_exp = resultats.get('features', [])
    analyse_genetique = resultats.get('analyse_genetique', {
        'profondeur_genealogique': 0,
        'stats_parents': {'deux_parents': 0, 'un_parent': 0, 'aucun_parent': 0}
    })

    # Interface utilisateur pour le nom du fichier
    nom_fichier = st.text_input(
        "Nom du fichier rapport (sans extension)",
        value=f"rapport_analyse_{os.getenv('USERNAME', 'user')}",
        help="Le fichier sera sauvegardé au format PDF"
    )

    if st.button("Générer le rapport"):
        try:
            # Ajout de l'extension .pdf
            if not nom_fichier.endswith('.pdf'):
                nom_fichier += '.pdf'

            # Génération du rapport
            generer_rapport_pdf(
                nom_fichier=nom_fichier,
                mse=mse,
                importances=importances,
                cible=cible,
                variables_exp=variables_exp,
                analyse_qualite=analyse_qualite,
                heritabilites=heritabilites,
                analyse_genetique=analyse_genetique,
                user=os.getenv('USERNAME', 'user')
            )

            # Message de succès avec lien de téléchargement
            with open(nom_fichier, "rb") as pdf_file:
                PDFbyte = pdf_file.read()
                st.success("✅ Rapport généré avec succès!")
                st.download_button(
                    label="📥 Télécharger le rapport",
                    data=PDFbyte,
                    file_name=nom_fichier,
                    mime='application/octet-stream'
                )
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération du rapport : {str(e)}")
            st.error("Assurez-vous d'avoir d'abord effectué une analyse dans l'onglet Modélisation.")
