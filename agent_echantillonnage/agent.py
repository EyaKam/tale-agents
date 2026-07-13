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
MARGE_REFERENCE = 5.0


def _gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text.strip()


# ─────────────────────────────────────────
# ÉTAPE 1 — Message d'accueil
# ─────────────────────────────────────────
def message_accueil() -> dict:
    contexte = get_contexte_questionnaire()
    texte = (
        f"👋 Bonjour ! Je suis l'agent d'échantillonnage Tale.\n\n"
        f"J'ai récupéré votre questionnaire :\n"
        f"📋 {contexte['titre']}\n"
        f"🎯 Objectif : {contexte['objectif']}\n"
        f"❓ {contexte['nb_questions']} questions · "
        f"⏱ ~{contexte['duree_estimee_min']} minutes\n\n"
        f"Je vais vous aider à définir votre plan d'échantillonnage "
        f"en 2 étapes simples.\n\n"
        f"---\n"
        f"**Étape 1 sur 2 — Combien de répondants souhaitez-vous ?**\n\n"
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
    marge = _calculer_marge(n)
    palier = _palier_le_plus_proche(n)
    regles = REGLES_PALIERS[palier]
    max_criteres = regles["max_criteres"]
    criteres_rec = regles["criteres_recommandes"]

    texte = (
        f"✅ **{n} répondants** sélectionnés.\n\n"
        f"📊 **Marge d'erreur : ±{marge:.1f}%**\n"
        f"*(Référence industrie : ±{MARGE_REFERENCE}% · "
        f"Formule : ME = 1.96 × √(0.5×0.5/{n}))*\n\n"
        f"---\n"
        f"**Étape 2 sur 2 — Quelles catégories de ciblage souhaitez-vous ?**\n\n"
        f"Pour **{n} répondants**, vous pouvez sélectionner "
        f"**maximum {max_criteres} critère(s)**.\n"
        f"Au-delà, les sous-groupes seront trop petits pour être statistiquement fiables.\n\n"
        f"💡 Recommandé : "
        f"{', '.join([CATEGORIES[c]['label'] for c in criteres_rec])}\n\n"
        f"**Catégories disponibles :**"
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

    # ── Moteur déterministe ──
    resultat = analyser(n=n, criteres_choisis=criteres)

    # ── Si Personnalisée ──
    if resultat.offre_type == "personnalisee":
        texte = (
            "⚠️ **Offre Personnalisée requise**\n\n"
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

    mp = resultat.message_pertinence

    # ── LLM explique en langage clair ──
    criteres_labels = ', '.join([CATEGORIES.get(c, {}).get('label', c) for c in criteres]) or "Aucun"
    prompt_llm = f"""Tu es l'assistant d'échantillonnage de la plateforme Tale (Tunisie).
Le moteur statistique a produit ces résultats. Tu ne recalcules rien, tu expliques uniquement.

RÉSULTATS :
- Répondants : {n}
- Marge d'erreur : ±{resultat.marge_erreur}% (référence industrie : ±{MARGE_REFERENCE}%)
- Formule : ME = 1.96 × √(0.5 × 0.5 / {n})
- Niveau de confiance : 95%
- Critères : {criteres_labels}
- Disponibilité panel : {mp['disponibilite']}
- Cellules insuffisantes : {mp['nb_cellules_insuffisantes']}
- Suggestions : {json.dumps(mp['suggestions'], ensure_ascii=False)}

Rédige 3-4 phrases qui :
1. Indique la marge d'erreur et la compare à la référence ±{MARGE_REFERENCE}%
2. Indique si le panel peut fournir les répondants nécessaires
3. Donne la suggestion principale si nécessaire

Ton : professionnel, direct. Pas de labels subjectifs. Que des faits et chiffres."""

    explication_llm = _gemini(prompt_llm)

    # ── Message final ──
    texte = "**📊 Résultat de l'analyse**\n\n"

    # Bloc métriques
    texte += (
        f"```\n"
        f"Marge d'erreur      : ±{resultat.marge_erreur}%\n"
        f"Référence industrie : ±{MARGE_REFERENCE}%\n"
        f"Disponibilité panel : {mp['disponibilite']}\n"
        f"```\n\n"
    )

    # Explication LLM
    texte += f"💬 **Analyse :**\n{explication_llm}\n\n"

    # Suggestions
    if mp["suggestions"]:
        texte += "**💡 Suggestions :**\n"
        for s in mp["suggestions"]:
            texte += f"• {s}\n"
        texte += "\n"

    # Quotas par cellule
    if resultat.cellules:
        texte += "**📋 Quotas par cellule (INS 2024) :**\n"
        critere_courant = None
        for c in resultat.cellules:
            if c.critere != critere_courant:
                critere_courant = c.critere
                label = CATEGORIES.get(c.critere, {}).get("label", c.critere)
                texte += f"\n*{label}*\n"
            dispo_txt = (
                f"{c.disponibilite_effective} disponibles / {c.n_quota} requis"
            )
            texte += f"  • {c.valeur} : {c.proportion_ins}% INS → {dispo_txt}\n"

    texte += "\n---\n"
    if resultat.disponibilite_globale == "suffisante" and not mp["nb_cellules_insuffisantes"]:
        texte += "✅ **Votre étude peut être lancée.**"
    else:
        texte += "⚠️ **Ajustez les paramètres avant de lancer l'étude.**"

    return {
        "etape": "resultat",
        "message": texte,
        "resultat": {
            "n": resultat.n,
            "marge_erreur": resultat.marge_erreur,
            "marge_reference": resultat.marge_reference,
            "niveau_confiance": resultat.niveau_confiance,
            "offre_type": resultat.offre_type,
            "disponibilite": resultat.disponibilite_globale,
            "cellules": [
                {
                    "critere": c.critere,
                    "valeur": c.valeur,
                    "proportion_ins": c.proportion_ins,
                    "n_quota": c.n_quota,
                    "disponibilite_effective": c.disponibilite_effective,
                }
                for c in resultat.cellules
            ],
            "suggestions": mp["suggestions"],
            "nb_cellules_insuffisantes": mp["nb_cellules_insuffisantes"],
        }
    }


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────
def _options_paliers() -> list[dict]:
    options = []
    for n in PALIERS_DISPONIBLES:
        marge = _calculer_marge(n)
        options.append({
            "valeur": n,
            "label": f"{n} répondants",
            "marge": f"±{marge:.1f}%",
            "prix_dt": f"{n * 0.40:.0f} DT",
        })
    return options


def _options_categories(max_criteres: int) -> list[dict]:
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
    paliers = sorted(REGLES_PALIERS.keys())
    palier = paliers[0]
    for p in paliers:
        if n >= p:
            palier = p
    return palier