import requests
import pandas as pd

API_KEY = "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"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

def detecter_type_donnees(df):
    extrait = df.head(5).to_csv(index=False)
    if len(extrait) > 2000:
        extrait = extrait[:2000]

    prompt = f"""
Voici un extrait d’un fichier de données :

{extrait}

Analyse ces colonnes et :
1. Classe-les en types : généalogiques, phénotypiques, environnementales, autres.
2. Dis-moi quels modèles statistiques ou IA sont les plus adaptés (modèle animal, RandomForest, etc.).
3. Propose une méthode d’analyse automatique ou prédictive.

Réponds en français.
"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"❌ Erreur lors de la communication avec l'agent IA : {e}"
