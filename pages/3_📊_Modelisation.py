import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import r2_score
import plotly.express as px
import plotly.graph_objects as go
from scripts.modele_mixtes import modele_mixtes
from scripts.nettoyage import nettoyer_donnees, identifier_variables_heritabilite, analyser_structure_genetique
from scripts.visualisation import (
    plot_trait_distribution,
    plot_heritability_results,
    plot_genetic_correlations,
    plot_trait_evolution,
    generate_summary_report
)

def app():
    st.title("📊 Modélisation et estimation de l'héritabilité")
    
    # Chargement et nettoyage des données
    df = st.session_state.get('df')
    if df is None:
        st.warning("Veuillez d'abord importer un fichier.")
        return

    # Identification automatique des variables
    variables = identifier_variables_heritabilite(df)
    
    if variables is None:
        st.error("""
        ⚠️ Structure des données incorrecte. Votre fichier doit contenir:
        
        1. Identification:
           - ID ou Sujet : identifiant unique de l'animal
        
        2. Variables de production (au moins une):
           - Rendement_lait/Production_lait
           - Taux_mg/Matière_grasse
           - Taux_prot/Protéine
        
        3. Variables généalogiques:
           - Père/pere
           - Mère/mere
           - Autres liens familiaux (optionnels)
        
        4. Variables environnementales (optionnelles):
           - Saison
           - Elevage
           - etc.
        """)
        return

    # Nettoyage approfondi des données
    df_clean, encoders = nettoyer_donnees(df)
    
    if df_clean.empty:
        st.error("Le nettoyage des données a échoué ou a résulté en un DataFrame vide.")
        return

    # Analyse de la structure génétique
    st.subheader("🧬 Analyse de la structure génétique")
    resultats_genetiques = analyser_structure_genetique(df_clean)
    
    # Affichage des résultats de l'analyse génétique
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("📊 Profondeur généalogique:")
        st.write(f"Nombre de générations: {resultats_genetiques.get('profondeur_genealogique', 'N/A')}")
        
        if 'stats_parents' in resultats_genetiques and resultats_genetiques['stats_parents'] is not None:
            st.write("📋 Statistiques parentales:")
            stats = resultats_genetiques['stats_parents']
            st.write(f"• Deux parents connus: {stats.get('deux_parents', 0)}")
            st.write(f"• Un parent connu: {stats.get('un_parent', 0)}")
            st.write(f"• Aucun parent connu: {stats.get('aucun_parent', 0)}")
        else:
             st.write("📋 Statistiques parentales: Non disponibles (colonnes Père/Mère manquantes).")

    with col2:
        if resultats_genetiques and 'clusters' in resultats_genetiques and resultats_genetiques['clusters'] is not None:
            st.write("🔍 Groupes génétiques identifiés:")
            clusters = resultats_genetiques['clusters']
            variance = clusters.get('variance_expliquee')
            if variance and len(variance) >= 2:
                st.write(f"Variance expliquée: {variance[0]:.2%}, {variance[1]:.2%}")
            else:
                st.write("Variance expliquée: Non disponible (moins de 2 composantes).")
            
            # Visualisation des clusters
            if resultats_genetiques and 'clusters' in resultats_genetiques and resultats_genetiques['clusters'] is not None and len(variables['traits']) >= 2 and len(clusters.get('centres', [])) > 1:
                try:
                    fig = go.Figure()
                    for i in range(len(clusters['centres'])):
                        if i < len(clusters.get('labels', [])):
                            mask = np.array(clusters['labels']) == i
                            if len(clusters['centres'][i]) >= 2:
                                fig.add_trace(go.Scatter(
                                    x=[clusters['centres'][i][0]],
                                    y=[clusters['centres'][i][1]],
                                    mode='markers',
                                    name=f'Groupe {i+1}',
                                    marker=dict(size=10)
                                ))
                    fig.update_layout(
                        title="Groupes génétiques",
                        xaxis_title="Composante 1",
                        yaxis_title="Composante 2"
                    )
                    st.plotly_chart(fig)
                except Exception as e:
                    st.warning(f"Impossible de visualiser les clusters: {e}")
            else:
                 st.info("Pas assez de données pour visualiser les groupes génétiques (moins de 2 caractères ou groupes identifiés).")
        else:
             st.info("Analyse de clustering non disponible (pas assez de caractères numériques). ")

    st.markdown("---")
    
    # --- Modèle linéaire mixte (héritabilité) ---
    st.subheader("📈 Estimation de l'héritabilité (h²)")
    
    heritabilites = {}
    
    if 'ID' not in df_clean.columns or df_clean['ID'].nunique() < 2:
        st.warning("""
        ⚠️ Impossible d'estimer l'héritabilité.
        La colonne 'ID' doit contenir au moins deux valeurs uniques pour l'analyse par modèle linéaire mixte.
        Veuillez vérifier votre fichier de données.
        """)
    else:
        for caractere in variables['traits']:
            try:
                # Calcul de l'héritabilité
                results = modele_mixtes(df_clean, caractere)
                heritabilites[caractere] = results
                
                # Affichage des résultats
                st.write(f"📊 {caractere}:")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("Héritabilité:")
                    st.write(f"• h² = {results.get('h2', np.nan):.3f} ± {results.get('se', np.nan):.3f}")
                    st.write(f"• IC-95%: [{results.get('ci_lower', np.nan):.3f}, {results.get('ci_upper', np.nan):.3f}]")
                
                with col2:
                    st.write("Composantes de la variance:")
                    st.write(f"• Génétique: {results.get('var_genetique', np.nan):.3f}")
                    st.write(f"• Résiduelle: {results.get('var_residuelle', np.nan):.3f}")
                
                # Visualisation de la distribution par génération
                st.plotly_chart(plot_trait_distribution(df_clean, caractere))
                
                # Visualisation de l'évolution
                st.plotly_chart(plot_trait_evolution(df_clean, caractere))
                
            except Exception as e:
                st.error(f"Erreur lors de l'estimation de l'héritabilité pour {caractere}: {str(e)}")
                heritabilites[caractere] = None
    
    # Visualisation des résultats d'héritabilité
    if heritabilites and any(results is not None for results in heritabilites.values()):
        st.subheader("📊 Comparaison des héritabilités")
        st.plotly_chart(plot_heritability_results(heritabilites))
        
        # Corrélations génétiques
        if len([r for r in heritabilites.values() if r is not None]) > 1 and variables and 'traits' in variables and len(variables['traits']) > 1:
            st.subheader("🔍 Corrélations entre caractères")
            successful_traits = [trait for trait, results in heritabilites.items() if results is not None]
            if len(successful_traits) > 1:
                 try:
                      st.plotly_chart(plot_genetic_correlations(df_clean, successful_traits))
                 except Exception as e:
                      st.warning(f"Impossible de calculer les corrélations génétiques: {e}")
            else:
                 st.info("Pas assez de caractères avec une héritabilité estimée pour calculer les corrélations génétiques.")

    # Génération du rapport
    st.subheader("📝 Résumé des résultats")
    st.markdown(generate_summary_report(heritabilites))
    
    # Sauvegarde des résultats pour le rapport
    st.session_state['heritabilites'] = heritabilites

    st.markdown("---")
    
    # --- Modélisation RandomForest ---
    st.subheader("🤖 Modélisation par Intelligence Artificielle")
    
    if variables and 'traits' in variables and variables['traits']:
        caractere = st.selectbox("Caractère à modéliser", variables['traits'])
        if caractere:
            # Préparation des features
            features = [col for col in df_clean.columns if col != caractere and (variables is None or col != variables.get('id'))]
            
            # Filter out non-numeric features for RandomForest
            numeric_features = df_clean[features].select_dtypes(include=np.number).columns.tolist()
            
            if not numeric_features:
                st.warning("Aucune variable numérique disponible pour la modélisation RandomForest.")
            else:
                 X = df_clean[numeric_features]
                 y = df_clean[caractere]
                
                # Drop rows with NaNs in features or target for RandomForest
                 combined_cols = numeric_features + [caractere]
                 df_model = df_clean[combined_cols].dropna()
                
                 if df_model.empty:
                      st.warning(f"Pas de données complètes pour la modélisation RandomForest de {caractere}.")
                 elif len(df_model) < 5:
                      st.warning(f"Pas assez de données ({len(df_model)} échantillons) pour la modélisation RandomForest de {caractere}. Au moins 5 échantillons sont requis.")
                 else:
                    X_model = df_model[numeric_features]
                    y_model = df_model[caractere]

                    try:
                        # Entraînement du modèle
                        model = RandomForestRegressor(n_estimators=100, random_state=42)
                        
                        # Cross-validation
                        cv_folds = min(5, len(df_model))
                        cv_scores = cross_val_score(model, X_model, y_model, cv=cv_folds)
                        
                        # Entraînement final
                        model.fit(X_model, y_model)
                        y_pred = model.predict(X_model)
                        r2 = r2_score(y_model, y_pred)
                        
                        # Affichage des résultats
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("📈 Performance du modèle:")
                            st.write(f"• R² score: {r2:.3f}")
                            st.write(f"• CV scores ({cv_folds}-fold): {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
                        
                        with col2:
                            # Importance des variables
                            importances = dict(zip(numeric_features, model.feature_importances_))
                            st.write("🎯 Importance des variables:")
                            
                            # Tri des importances
                            sorted_importances = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True)[:10])
                            
                            # Création du graphique avec Plotly
                            if sorted_importances:
                                fig = px.bar(
                                    x=list(sorted_importances.values()),
                                    y=list(sorted_importances.keys()),
                                    orientation='h',
                                    title=f"Top 10 des variables les plus importantes pour {caractere}"
                                )
                                fig.update_layout(
                                    xaxis_title="Importance",
                                    yaxis_title="Variables"
                                )
                                st.plotly_chart(fig)
                            else:
                                st.info("Aucune importance de variable à afficher (modèle non entraîné ou sans features).")
                            
                        # Sauvegarde pour le rapport
                        st.session_state['rapport'] = {
                            'analyse_genetique': resultats_genetiques,
                            'model_performance': {
                                'r2': r2,
                                'cv_scores': cv_scores.tolist()
                            },
                            'feature_importance': sorted_importances,
                            'target': caractere,
                            'features': numeric_features
                        }

                    except Exception as model_e:
                        st.error(f"Erreur lors de la modélisation RandomForest pour {caractere}: {model_e}")
        
    else:
        st.warning("Aucun caractère de production identifié pour la modélisation RandomForest.")
