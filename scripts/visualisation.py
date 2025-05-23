import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def distribution_variable(df, variable):
    plt.figure(figsize=(8, 4))
    sns.histplot(df[variable].dropna(), kde=True)
    plt.title(f'Distribution de {variable}')
    st.pyplot(plt.gcf())

def plot_trait_distribution(df, trait):
    """Visualise la distribution d'un caractère par lactation"""
    if 'Lactation' not in df.columns:
         st.warning("La colonne 'Lactation' n'est pas disponible pour cette visualisation.")
         return go.Figure()

    fig = px.box(df, 
                 x='Lactation', 
                 y=trait,
                 title=f'Distribution de {trait} par lactation',
                 labels={'Lactation': 'Lactation', trait: trait})
    fig.update_layout(
        xaxis_title="Lactation",
        yaxis_title=trait,
        showlegend=True
    )
    return fig

def plot_heritability_results(results_dict):
    """Visualise les résultats d'héritabilité pour tous les caractères"""
    # Filter out traits with None results
    valid_results = {trait: results for trait, results in results_dict.items() if results is not None}
    
    if not valid_results:
        st.warning("Aucun résultat d'héritabilité valide à afficher.")
        return go.Figure() # Return an empty figure if no valid results

    traits = list(valid_results.keys())
    h2_values = [valid_results[trait]['h2'] for trait in traits]
    se_values = [valid_results[trait]['se'] for trait in traits]
    
    fig = go.Figure()
    
    # Barres pour les valeurs d'héritabilité
    fig.add_trace(go.Bar(
        x=traits,
        y=h2_values,
        name='h²',
        error_y=dict(
            type='data',
            array=se_values,
            visible=True
        )
    ))
    
    fig.update_layout(
        title='Estimation de l\'héritabilité par caractère',
        xaxis_title='Caractère',
        yaxis_title='h²',
        yaxis=dict(range=[0, 1]),
        showlegend=True
    )
    
    return fig

def plot_genetic_correlations(df, traits):
    """Visualise les corrélations génétiques entre caractères"""
    # Calcul des corrélations
    corr_matrix = df[traits].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix,
        x=traits,
        y=traits,
        colorscale='RdBu',
        zmin=-1,
        zmax=1
    ))
    
    fig.update_layout(
        title='Corrélations entre caractères',
        xaxis_title='Caractère 1',
        yaxis_title='Caractère 2'
    )
    
    return fig

def plot_trait_evolution(df, trait):
    """Visualise l'évolution d'un caractère au fil des lactations (using Lactation as proxy for evolution)"""
    if 'Lactation' not in df.columns:
         st.warning("La colonne 'Lactation' n'est pas disponible pour cette visualisation.")
         return go.Figure()

    df_sorted = df.sort_values(by='Lactation')

    means = df_sorted.groupby('Lactation', as_index=False)[trait].mean()
    
    fig = go.Figure()
    
    # Line for means
    fig.add_trace(go.Scatter(
        x=means['Lactation'],
        y=means[trait],
        mode='lines+markers',
        name='Moyenne'
    ))
    
    # Cloud of points for raw data
    fig.add_trace(go.Scatter(
        x=df['Lactation'],
        y=df[trait],
        mode='markers',
        marker=dict(
            size=8,
            opacity=0.5
        ),
        name='Données brutes'
    ))
    
    fig.update_layout(
        title=f'Évolution de {trait} par lactation',
        xaxis_title='Lactation',
        yaxis_title=trait,
        showlegend=True
    )
    
    return fig

def generate_summary_report(results_dict):
    """Génère un résumé des résultats en français"""
    report = []
    report.append("# Résumé des estimations d'héritabilité\n")
    
    # Filter out traits with None results for the report
    valid_results = {trait: results for trait, results in results_dict.items() if results is not None}

    if not valid_results:
        report.append("Aucun résultat d'héritabilité valide à inclure dans le rapport.")
        return "\n".join(report)

    for trait, results in valid_results.items():
        report.append(f"## {trait}")
        report.append(f"- Héritabilité (h²): {results['h2']:.3f} ± {results['se']:.3f}")
        report.append(f"- Intervalle de confiance 95%: [{results['ci_lower']:.3f}, {results['ci_upper']:.3f}]")
        report.append(f"- Variance génétique: {results['var_genetique']:.3f}")
        report.append(f"- Variance résiduelle: {results['var_residuelle']:.3f}\n")
    
    return "\n".join(report)
