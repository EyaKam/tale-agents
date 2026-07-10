"""
Agent Échantillonnage — Conversationnel V3
Flow :
  1. Accueil + contexte questionnaire
  2. Question 1 : choix du nombre de répondants
  3. Question 2 : choix des catégories
  4. Moteur statistique → message de pertinence
  5. LLM explique le résultat en langage clair
"""

import json
import os
from turtle import st
from google import genai
from dotenv import load_dotenv

from .moteur import analyser, _calculer_marge
from .base_donnees import (
    get_contexte_questionnaire,
    CATEGORIES,
    REGLES_PALIERS,
)

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PALIERS_DISPONIBLES = [50, 100, 150, 250, 500, 1000, 2000, 5000]


def _gemini(prompt: str) -> str:
    """Appel Gemini — LLM narratif uniquement, jamais de calcul."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text.strip()


# ─────────────────────────────────────────
# ÉTAPE 1 — Message d'accueil
# ─────────────────────────────────────────
def message_accueil() -> dict:
    """
    Lit le contexte du questionnaire depuis la DB
    et génère le message d'accueil.
    """
    contexte = get_contexte_questionnaire()
    texte = (
        f"👋 Bonjour ! Je suis l'agent d'échantillonnage Tale.\n\n"
        f"J'ai récupéré votre questionnaire  :\n"
        f"📋 {contexte['titre']}\n"
        f"🎯 Objectif : {contexte['objectif']}\n"
        f"❓ {contexte['nb_questions']} questions · "
        f"⏱ ~{contexte['duree_estimee_min']} minutes\n\n"
        f"Je vais vous aider à définir votre plan d'échantillonnage "
        f"en 2 étapes simples.\n\n"
        f"---\n"
        f"Étape 1 sur 2 — Combien de répondants souhaitez-vous ?\n\n"
        f"Choisissez un palier :"
    )
    return {
        "etape": "choix_n",
        "message": texte,
        "contexte": contexte,
        "options": _options_paliers(),
    }


# ─────────────────────────────────────────
# ÉTAPE 2 — Après choix de N
# ─────────────────────────────────────────
def apres_choix_n(n: int) -> dict:
    """
    Reçoit le N choisi.
    Calcule la marge immédiatement.
    Présente les catégories disponibles avec les règles.
    """
    marge = _calculer_marge(n)
    palier = _palier_le_plus_proche(n)
    regles = REGLES_PALIERS[palier]
    max_criteres = regles["max_criteres"]
    criteres_rec = regles["criteres_recommandes"]

    # Couleur marge
    if marge > 10:
        marge_txt = f"⚠️ ±{marge:.1f}% (élevée)"
    elif marge > 7:
        marge_txt = f"🟡 ±{marge:.1f}% (modérée)"
    else:
        marge_txt = f"✅ ±{marge:.1f}% (bonne)"

    texte = (
        f"✅ {n} répondants sélectionnés.\n\n"
        f"📊 Marge d'erreur théorique : {marge_txt}\n"
        f"Étape 2 sur 2 — Quelles catégories de ciblage souhaitez-vous ?\n\n"
        f"⚠️ Règle statistique : Pour {n} répondants, "
        f"vous pouvez sélectionner maximum {max_criteres} critère(s).\n"
        f"Au-delà, les cellules seront trop petites pour être fiables.\n\n"
        f"💡 Recommandé pour ce palier : "
        f"{', '.join([CATEGORIES[c]['label'] for c in criteres_rec])}\n\n"
        f"Catégories disponibles :"
    )

    return {
        "etape": "choix_categories",
        "message": texte,
        "n": n,
        "marge_erreur": round(marge, 1),
        "max_criteres": max_criteres,
        "criteres_recommandes": criteres_rec,
        "options": _options_categories(max_criteres),
    }


# ─────────────────────────────────────────
# ÉTAPE 3 — Après choix des catégories
# ─────────────────────────────────────────
def apres_choix_categories(n: int, criteres: list[str]) -> dict:
    """
    Reçoit N + critères choisis.
    Lance le moteur statistique déterministe.
    LLM explique le résultat.
    """

    # ── Moteur déterministe ──
    resultat = analyser(n=n, criteres_choisis=criteres)

    # ── Si Personnalisée ──
    if resultat.offre_type == "personnalisee":
        texte = (
            "⚠️ Offre Personnalisée requise\n\n"
            "Les critères suivants n'ont pas de référence INS nationale :\n"
        )
        for r in resultat.raisons_personnalisee:
            texte += f"• {r}\n"
        texte += (
            "\nCes critères ne peuvent pas être utilisés en mode Standard.\n"
            "Un conseiller Tale va vous contacter pour finaliser votre étude."
        )
        return {
            "etape": "personnalisee",
            "message": texte,
            "resultat": None,
        }

    # ── Construire le message de pertinence ──
    mp = resultat.message_pertinence
    alertes_critiques = [a for a in resultat.alertes if a["niveau"] == "critique"]
    alertes_warnings = [a for a in resultat.alertes if a["niveau"] == "warning"]

    # ── LLM explique en langage clair ──
    prompt_llm = f"""Tu es l'assistant d'échantillonnage de la plateforme Tale (Tunisie).
Le moteur statistique a produit ces résultats (tu ne recalcules rien) :

RÉSULTATS CALCULÉS :
- Répondants demandés : {n}
- Marge d'erreur théorique : ±{resultat.marge_erreur}%
- Formule : ME = 1.96 × √(0.5 × 0.5 / {n})
- Niveau de confiance : 95%
- Critères sélectionnés : {', '.join([CATEGORIES.get(c, {}).get('label', c) for c in criteres])}
- Disponibilité panel : {mp['disponibilite']}
- Risque global : {mp['risque']}
- Cellules critiques : {mp['nb_cellules_critiques']}
- Cellules fragiles : {mp['nb_cellules_fragiles']}

ALERTES CRITIQUES : {json.dumps(alertes_critiques, ensure_ascii=False)}
ALERTES WARNINGS : {json.dumps(alertes_warnings, ensure_ascii=False)}

SUGGESTIONS : {json.dumps(mp['suggestions'], ensure_ascii=False)}

Rédige un message de pertinence clair et honnête (5-6 phrases max) qui :
1. Confirme la marge d'erreur et ce qu'elle signifie concrètement
2. Évalue si le panel peut fournir les répondants nécessaires
3. Mentionne le risque principal s'il y en a un
4. Donne UNE recommandation concrète

Ton : professionnel, direct, honnête. Pas de jargon inutile.
Tu n'inventes AUCUN chiffre."""

    explication_llm = _gemini(prompt_llm)

    # ── Construire le message final ──
    texte = "📊Résultat de l'analyse\n\n"

    # Métriques principales
    texte += (
        f"```\n"
        f"Marge d'erreur théorique : ±{resultat.marge_erreur}%\n"
        f"Disponibilité estimée    : {mp['disponibilite']}\n"
        f"Risque                   : {mp['risque']}\n"
        f"```\n\n"
    )

    # Explication LLM
    texte += f"💬Analyse :\n{explication_llm}\n\n"

    # Suggestions
    if mp["suggestions"]:
        texte += "💡 Suggestions :\n"
        for s in mp["suggestions"]:
            texte += f"• {s}\n"
        texte += "\n"

    # Quotas par cellule
    if resultat.cellules:
        texte += "📋 Quotas par cellule (selon INS 2024) :\n"
        critere_courant = None
        for c in resultat.cellules:
            if c.critere != critere_courant:
                critere_courant = c.critere
                label = CATEGORIES.get(c.critere, {}).get("label", c.critere)
                texte += f"\n {label} \n"
            statut_emoji = {"ok": "✅", "fragile": "🟡", "critique": "🔴"}.get(c.statut, "")
            texte += (
                f"  {statut_emoji} {c.valeur} : "
                f"{c.proportion_ins}% INS → {c.n_quota} requis "
                f"/ {c.disponibilite_effective} disponibles\n"
            )

    texte += "\n---\n"
    if resultat.disponibilite_globale == "suffisante" and not alertes_critiques:
        texte += "✅ Votre étude peut être lancée."
    else:
        texte += "⚠️ Corrigez les alertes avant de lancer l'étude."

    return {
        "etape": "resultat",
        "message": texte,
        "resultat": {
            "n": resultat.n,
            "marge_erreur": resultat.marge_erreur,
            "niveau_confiance": resultat.niveau_confiance,
            "offre_type": resultat.offre_type,
            "disponibilite": resultat.disponibilite_globale,
            "risque": mp["risque"],
            "cellules": [
                {
                    "critere": c.critere,
                    "valeur": c.valeur,
                    "proportion_ins": c.proportion_ins,
                    "n_quota": c.n_quota,
                    "disponibilite_effective": c.disponibilite_effective,
                    "statut": c.statut,
                }
                for c in resultat.cellules
            ],
            "alertes": resultat.alertes,
            "suggestions": mp["suggestions"],
        }
    }


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────
def _options_paliers() -> list[dict]:
    """Génère les options de paliers avec marge d'erreur."""
    options = []
    for n in PALIERS_DISPONIBLES:
        marge = _calculer_marge(n)
        if marge > 10:
            qualite = "⚠️"
        elif marge > 7:
            qualite = "🟡"
        else:
            qualite = "✅"
        options.append({
            "valeur": n,
            "label": f"{n} répondants",
            "marge": f"±{marge:.1f}%",
            "qualite": qualite,
            "prix_dt": f"{n * 0.40:.0f} DT",
        })
    return options


def _options_categories(max_criteres: int) -> list[dict]:
    """Génère les options de catégories."""
    options = []
    for key, cat in CATEGORIES.items():
        options.append({
            "key": key,
            "label": cat["label"],
            "icone": cat["icone"],
            "type": cat["type"],
            "cout_dt": cat["cout_dt"],
            "max_criteres": max_criteres,
        })
    return options


def _palier_le_plus_proche(n: int) -> int:
    """Trouve le palier de règles le plus proche."""
    paliers = sorted(REGLES_PALIERS.keys())
    palier = paliers[0]
    for p in paliers:
        if n >= p:
            palier = p
    return palier