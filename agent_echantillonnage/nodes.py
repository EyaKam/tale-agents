"""
Nœuds de l'Agent Échantillonnage.
L'agent dialogue jusqu'à avoir toutes les infos,
puis calcule et restitue le plan.
"""

import json
import os
from google import genai
from dotenv import load_dotenv

from .state import SamplingState
from moteur_stat.sample_size import calculer_taille_echantillon

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _appeler_gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text


def _historique_en_texte(messages: list) -> str:
    """Convertit l'historique en texte lisible."""
    texte = ""
    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get("role", "user")
            content = msg.get("content", "")
        else:
            role = getattr(msg, "type", "user")
            content = getattr(msg, "content", "")
        role_label = "Client" if role == "user" else "Agent"
        texte += f"{role_label}: {content}\n"
    return texte


# ─────────────────────────────────────────
# Nœud 1 — L'agent décide quoi faire
# ─────────────────────────────────────────
def noeud_dialogue(state: SamplingState) -> dict:
    """
    L'agent analyse la conversation et décide :
    - Soit poser une question pour collecter plus d'infos
    - Soit dire qu'il a assez d'infos pour calculer
    """
    print("🟢 Nœud dialogue : analyse de la conversation")

    historique = _historique_en_texte(state.messages)

    prompt = f"""Tu es un expert en études marketing pour la plateforme Tale (Tunisie).
Tu aides le client à définir son plan d'échantillonnage.

Voici la conversation jusqu'ici :
{historique}

Tu dois collecter ces 4 informations OBLIGATOIRES :
1. L'objectif de l'étude (que veut-il mesurer ?)
2. La population cible (qui veut-il interroger ?)
3. La précision souhaitée (marge d'erreur acceptable ? Si pas mentionné, demande si "standard ±5%" lui convient)
4. Le mode de collecte (panel avec critères ou aléatoire sur réseaux sociaux ?)

RÈGLES :
- Pose UNE seule question à la fois
- Sois naturel et conversationnel
- Si tu as déjà toutes les 4 informations, réponds UNIQUEMENT avec ce JSON exact :
  {{"statut": "complet", "objectif": "...", "population": "...", "precision": "standard ou precise", "mode": "panel ou aleatoire"}}
- Sinon, pose la prochaine question manquante en langage naturel

Réponds maintenant :"""

    reponse = _appeler_gemini(prompt)

    # L'agent a-t-il toutes les infos ?
    try:
        reponse_nettoyee = reponse.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(reponse_nettoyee)
        if data.get("statut") == "complet":
            print("✅ Toutes les infos collectées — passage au calcul")
            return {
                "messages": [],
                "pret_pour_calcul": True,
                "objectif_etude": data.get("objectif", ""),
                "population_cible": data.get("population", ""),
                "marge_erreur": 0.03 if data.get("precision") == "precise" else 0.05,
                "mode_collecte": data.get("mode", "aleatoire"),
                "etape_courante": "pret",
            }
    except (json.JSONDecodeError, AttributeError):
        pass

    # L'agent pose encore une question
    print("💬 Agent pose une question")
    return {
        "messages": [{"role": "assistant", "content": reponse}],
        "pret_pour_calcul": False,
        "etape_courante": "dialogue",
    }


# ─────────────────────────────────────────
# Nœud 2 — Calcul statistique (ZERO LLM)
# ─────────────────────────────────────────
def noeud_calcul(state: SamplingState) -> dict:
    print("🔵 Nœud calcul : moteur statistique déterministe")

    resultat = calculer_taille_echantillon(
        marge_erreur=state.marge_erreur,
        niveau_confiance=state.niveau_confiance,
        proportion=state.proportion,
        population=state.population_totale,
    )

    resultat_dict = {
        "n_final": resultat.n_final,
        "marge_erreur": resultat.marge_erreur,
        "niveau_confiance": resultat.niveau_confiance,
        "alerte_biais": resultat.alerte_biais,
        "mode_collecte": state.mode_collecte,
        "objectif_etude": state.objectif_etude,
        "population_cible": state.population_cible,
    }

    return {
        "resultat_calcul": resultat_dict,
        "calcul_effectue": True,
        "etape_courante": "calcul_fait",
    }


# ─────────────────────────────────────────
# Nœud 3 — Restitution en langage clair
# ─────────────────────────────────────────
def noeud_restitution(state: SamplingState) -> dict:
    print("🟣 Nœud restitution : explication au client")

    calcul = state.resultat_calcul

    prompt = f"""Tu es un expert en études marketing. Explique ce plan d'échantillonnage 
au client en langage simple et chaleureux. Pas de jargon technique inutile.

Résultats calculés (tu ne recalcules rien, tu expliques uniquement ces chiffres) :
- Objectif : {calcul.get('objectif_etude')}
- Population cible : {calcul.get('population_cible')}
- Nombre de répondants nécessaires : {calcul.get('n_final')}
- Marge d'erreur : ±{calcul.get('marge_erreur')}%
- Niveau de confiance : {calcul.get('niveau_confiance')}%
- Mode de collecte : {calcul.get('mode_collecte')}

Alertes à mentionner honnêtement :
{chr(10).join(calcul.get('alerte_biais', []))}

Explique en 3 parties courtes :
1. Ce qu'on va faire et combien de personnes interroger
2. Ce que ça permet de conclure
3. Les limites importantes à connaître"""

    explication = _appeler_gemini(prompt)

    return {
        "messages": [{"role": "assistant", "content": explication}],
        "etape_courante": "termine",
    }