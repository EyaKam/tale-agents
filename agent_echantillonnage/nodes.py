"""
Nœuds de l'Agent Échantillonnage.
Chaque nœud fait UNE seule chose et retourne le State modifié.
Utilise Google Gemini (gratuit) comme LLM.
"""

import json
import os
from google import genai
from dotenv import load_dotenv

from .state import SamplingState
from .prompts import PROMPT_ACCUEIL, PROMPT_EXTRACTION, PROMPT_RESTITUTION
from moteur_stat.sample_size import calculer_taille_echantillon

load_dotenv()

# Configuration Gemini
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def _appeler_gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text


# ─────────────────────────────────────────
# Fonction utilitaire
# ─────────────────────────────────────────
def _messages_to_text(messages: list, system_prompt: str) -> str:
    """
    Convertit l'historique des messages en texte
    pour l'envoyer à Gemini.
    """
    texte = f"INSTRUCTIONS:\n{system_prompt}\n\nCONVERSATION:\n"
    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get("role", "user")
            content = msg.get("content", "")
        else:
            role = getattr(msg, "type", "user")
            content = getattr(msg, "content", "")
        texte += f"{role.upper()}: {content}\n"
    return texte


# ─────────────────────────────────────────
# Nœud 1 — Accueil et dialogue
# ─────────────────────────────────────────
def noeud_accueil(state: SamplingState) -> dict:
    print("🟢 Nœud 1 : Accueil")

    prompt = _messages_to_text(state.messages, PROMPT_ACCUEIL)
    response = _appeler_gemini(prompt)

    return {
        "messages": [{"role": "assistant", "content": response}],
        "etape_courante": "dialogue",
    }


# ─────────────────────────────────────────
# Nœud 2 — Extraction des paramètres
# ─────────────────────────────────────────
def noeud_extraction(state: SamplingState) -> dict:
    print("🟡 Nœud 2 : Extraction des paramètres")

    prompt = _messages_to_text(state.messages, PROMPT_EXTRACTION)
    response = _appeler_gemini(prompt)

    texte = response.strip()

    # Nettoyer les backticks si Gemini en ajoute
    texte = texte.replace("```json", "").replace("```", "").strip()

    try:
        params = json.loads(texte)
    except json.JSONDecodeError:
        print("⚠️ Erreur parsing JSON — valeurs par défaut utilisées")
        params = {}

    return {
        "objectif_etude": params.get("objectif_etude", state.objectif_etude),
        "population_cible": params.get("population_cible", state.population_cible),
        "marge_erreur": params.get("marge_erreur", state.marge_erreur),
        "niveau_confiance": params.get("niveau_confiance", state.niveau_confiance),
        "proportion": params.get("proportion", state.proportion),
        "population_totale": params.get("population_totale", state.population_totale),
        "budget_repondants": params.get("budget_repondants", state.budget_repondants),
        "mode_collecte": params.get("mode_collecte", state.mode_collecte),
        "quotas": params.get("quotas", state.quotas),
        "pret_pour_calcul": True,
        "etape_courante": "extraction_faite",
    }


# ─────────────────────────────────────────
# Nœud 3 — Calcul statistique (moteur pur)
# ─────────────────────────────────────────
def noeud_calcul(state: SamplingState) -> dict:
    print("🔵 Nœud 3 : Calcul statistique (moteur déterministe)")

    # AUCUN LLM ICI — calcul mathématique pur
    resultat = calculer_taille_echantillon(
        marge_erreur=state.marge_erreur,
        niveau_confiance=state.niveau_confiance,
        proportion=state.proportion,
        population=state.population_totale,
    )

    resultat_dict = {
        "n_theorique": resultat.n_theorique,
        "n_final": resultat.n_final,
        "marge_erreur": resultat.marge_erreur,
        "niveau_confiance": resultat.niveau_confiance,
        "z_score": resultat.z_score,
        "proportion": resultat.proportion,
        "population": resultat.population,
        "correction_appliquee": resultat.correction_appliquee,
        "alerte_biais": resultat.alerte_biais,
        "mode_collecte": state.mode_collecte,
        "quotas": state.quotas,
        "objectif_etude": state.objectif_etude,
        "population_cible": state.population_cible,
    }

    return {
        "resultat_calcul": resultat_dict,
        "calcul_effectue": True,
        "etape_courante": "calcul_fait",
    }


# ─────────────────────────────────────────
# Nœud 4 — Restitution au client
# ─────────────────────────────────────────
def noeud_restitution(state: SamplingState) -> dict:
    print("🟣 Nœud 4 : Restitution au client")

    prompt = PROMPT_RESTITUTION.format(
        resultats=json.dumps(state.resultat_calcul, ensure_ascii=False, indent=2)
    ) + "\n\nExplique-moi le plan d'échantillonnage recommandé."

    response = _appeler_gemini(prompt)

    return {
        "messages": [{"role": "assistant", "content": response}],
        "etape_courante": "termine",
    }