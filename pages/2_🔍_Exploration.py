import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
import numpy as np
from statsmodels.regression.mixed_linear_model import MixedLM

def app():
    st.title("🔍 Exploration des données")
    df = st.session_state.get('df')
    
    if df is None:
        st.warning("Veuillez d'abord importer un fichier dans l'onglet Accueil.")
        return

    if df.empty:
        st.error("Le fichier importé est vide.")
        return

    # Aperçu de base
    st.subheader("📋 Aperçu des données")
    st.write(f"Nombre total de lignes : {len(df)}")
    st.write(f"Nombre de colonnes : {len(df.columns)}")
    st.dataframe(df.head(50))

    # Types de colonnes
    colonnes_num = df.select_dtypes(include=['number']).columns.tolist()
    colonnes_cat = df.select_dtypes(include=['object', 'category']).columns.tolist()
    colonnes_date = df.select_dtypes(include=['datetime']).columns.tolist()

    # Statistiques
    st.subheader("📊 Statistiques descriptives")
    if colonnes_num:
        st.write("Variables numériques :")
        st.write(df[colonnes_num].describe())
    
    if colonnes_cat:
        st.write("Variables catégorielles :")
        for col in colonnes_cat:
            st.write(f"\nDistribution de {col}:")
            st.write(df[col].value_counts().head())
    
    if colonnes_date:
        st.write("Variables temporelles :")
        for col in colonnes_date:
            st.write(f"\nPériode de {col}:")
            st.write(f"De {df[col].min()} à {df[col].max()}")

    # Visualisation
    st.subheader("📈 Visualisation")
    if not colonnes_num:
        st.warning("Aucune variable numérique détectée dans votre fichier.")
        return

    type_plot = st.selectbox("Type de graphique", ["Histogramme", "Boxplot", "Corrélation", "Scatter Plot (Plotly)"])

    if type_plot == "Histogramme":
        col = st.selectbox("Variable numérique", colonnes_num)
        if col:
            fig = plt.figure()
            sns.histplot(df[col].dropna(), kde=True)
            plt.title(f"Distribution de {col}")
            st.pyplot(fig)

    elif type_plot == "Boxplot":
        if not colonnes_cat:
            st.warning("Aucune variable catégorielle disponible.")
        else:
            col = st.selectbox("Variable numérique", colonnes_num)
            cat = st.selectbox("Variable catégorielle", colonnes_cat)
            if col and cat:
                if df[cat].nunique() <= 10:
                    fig = plt.figure()
                    sns.boxplot(x=df[cat], y=df[col])
                    plt.xticks(rotation=45)
                    st.pyplot(fig)
                else:
                    st.warning(f"Trop de catégories dans {cat} (>10).")

    elif type_plot == "Corrélation":
        if len(colonnes_num) > 1:
            fig = plt.figure(figsize=(10, 6))
            corr = df[colonnes_num].corr()
            sns.heatmap(corr, annot=True, cmap='coolwarm', center=0)
            plt.title("Matrice de corrélation")
            st.pyplot(fig)

            seuil = 0.7
            correlations_fortes = []
            for i in range(len(corr.columns)):
                for j in range(i+1, len(corr.columns)):
                    if abs(corr.iloc[i, j]) >= seuil:
                        correlations_fortes.append(f"{corr.columns[i]} - {corr.columns[j]}: {corr.iloc[i, j]:.2f}")
            if correlations_fortes:
                st.write("Corrélations importantes (>0.7):")
                for corr in correlations_fortes:
                    st.write(f"• {corr}")
        else:
            st.info("Deux variables numériques minimum sont requises.")

    elif type_plot == "Scatter Plot (Plotly)":
        if len(colonnes_num) > 1:
            x = st.selectbox("Axe X", colonnes_num)
            y = st.selectbox("Axe Y", [c for c in colonnes_num if c != x])
            color_var = st.selectbox("Variable de couleur (optionnel)", ["Aucune"] + colonnes_cat)
            if x and y:
                fig = px.scatter(
                    df,
                    x=x,
                    y=y,
                    color=None if color_var == "Aucune" else color_var,
                    title=f"{y} en fonction de {x}"
                )
                st.plotly_chart(fig)

    # Analyse spécifique des caractères de production
    st.subheader("📈 Analyse des caractères de production")
    caracteres = [c for c in df.columns if any(x in c.lower() for x in ["lait", "grasse", "prot"])]
    if caracteres:
        for col in caracteres:
            try:
                fig = plt.figure(figsize=(8, 4))
                sns.histplot(df[col].dropna(), kde=True, bins=30)
                plt.title(f"Distribution de {col}")
                st.pyplot(fig)
                stats = df[col].describe()
                st.write(f"• Moyenne: {stats['mean']:.2f} | Écart-type: {stats['std']:.2f} | Min: {stats['min']:.2f} | Max: {stats['max']:.2f}")
            except Exception as e:
                st.warning(f"Erreur avec {col}: {str(e)}")
    else:
        st.info("Aucun caractère de production détecté.")

    # Estimation de l'héritabilité
    st.subheader("📈 Estimation de l'héritabilité")
    required_cols = ["N° SNIT", "Kg Lait", "% MG", "% Prot"]
    if all(col in df.columns for col in required_cols):
        try:
            # Convert columns to numeric
            df["Kg Lait"] = pd.to_numeric(df["Kg Lait"], errors='coerce')
            df["% MG"] = pd.to_numeric(df["% MG"], errors='coerce')
            df["% Prot"] = pd.to_numeric(df["% Prot"], errors='coerce')
            df = df.dropna(subset=required_cols)

            results = {}
            for trait in ["Kg Lait", "% MG", "% Prot"]:
                try:
                    # Fit mixed model
                    model = MixedLM.from_formula(f"{trait} ~ 1", groups=df["N° SNIT"], data=df)
                    result = model.fit()
                    
                    # Calculate heritability
                    variance_components = result.cov_re.iloc[0, 0]
                    total_variance = variance_components + result.scale
                    h2 = variance_components / total_variance
                    results[trait] = round(h2, 3)
                except Exception as trait_error:
                    st.warning(f"Erreur pour {trait}: {str(trait_error)}")
                    continue

            if results:
                st.write("### Résultats de l'estimation de l'héritabilité")
                for k, v in results.items():
                    st.write(f"• {k} : h² = {v}")
            else:
                st.warning("Aucun résultat d'héritabilité n'a pu être calculé.")
                
        except Exception as e:
            st.error(f"Erreur de modélisation : {str(e)}")
    else:
        st.warning("Colonnes nécessaires non trouvées : " + ", ".join([col for col in required_cols if col not in df.columns]))
