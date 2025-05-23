import streamlit as st
import pandas as pd
import numpy as np
from scripts.nettoyage import analyser_qualite_donnees, nettoyer_donnees
from scripts.visualisation import plot_trait_distribution, plot_trait_evolution

def app():
    st.title("👁️ Agent IA - Analyse Avancée")
    
    # Chargement des données
    df_raw = st.session_state.get('df')
    if df_raw is None:
        st.warning("Veuillez d'abord importer un fichier.")
        return
    
    # Nettoyer les données
    df, nettoyage_status = nettoyer_donnees(df_raw)
    
    if df.empty:
        st.error("Le nettoyage des données a échoué ou a résulté en un DataFrame vide.")
        return

    # Aperçu des données nettoyées
    st.subheader("Aperçu des données nettoyées")
    st.write(df.head())
    
    # Analyse de la qualité des données
    st.subheader("📊 Analyse de la qualité des données")
    rapport = analyser_qualite_donnees(df)
    st.text(rapport)
    
    # Visualisations
    st.subheader("📈 Visualisations")
    
    # Sélection du caractère à visualiser (use standardized names)
    # Get standardized trait names from ESSENTIAL_COLS defined in nettoyage.py
    from scripts.nettoyage import ESSENTIAL_COLS
    trait_cols_standard = [col for col in ESSENTIAL_COLS.keys() if col in df.columns and ESSENTIAL_COLS[col] == float]

    if trait_cols_standard:
        trait = st.selectbox("Sélectionnez un caractère à visualiser", trait_cols_standard)
        
        # Distribution du caractère
        st.plotly_chart(plot_trait_distribution(df, trait))
        
        # Évolution du caractère (assuming plot_trait_evolution can handle standardized names)
        st.plotly_chart(plot_trait_evolution(df, trait))
    else:
        st.warning("Aucune colonne de caractère de production trouvée pour la visualisation.")

    
    # Suggestions d'amélioration
    st.subheader("💡 Suggestions d'amélioration")
    
    # Analyse des valeurs manquantes
    missing = df.isnull().sum()
    if missing.any():
        st.write("⚠️ Valeurs manquantes détectées:")
        for col in missing[missing > 0].index:
            st.write(f"- {col}: {missing[col]} valeurs manquantes")
    
    # Analyse des outliers
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        st.write("🔍 Valeurs aberrantes potentielles:")
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            # Check for valid bounds before filtering
            if pd.notna(lower_bound) and pd.notna(upper_bound):
                 outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col]
                 if len(outliers) > 0:
                     st.write(f"- {col}: {len(outliers)} valeurs aberrantes détectées")
            else:
                 st.write(f"- {col}: Impossible de détecter les valeurs aberrantes (données insuffisantes ou invalides).") 