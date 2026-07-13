"""
Moteur statistique déterministe — Tale V3
Formule Ipsos/YouGov : ME = Z × √(p(1-p)/n)
Z = 1.96 (95%), p = 0.5 (cas le plus défavorable)

RÈGLE D'OR : Zéro LLM ici. Calculs purs et vérifiables.
"""

import math
from dataclasses import dataclass
from .base_donnees import (
    INS_2024,
    REGLES_PALIERS,
    CATEGORIES,
    get_disponibilite_panel,
    PANEL_TALE,
)

Z_95 = 1.96
P_DEFAVORABLE = 0.5
MARGE_REFERENCE = 5.0  # référence industrie en %


@dataclass
class ResultatCellule:
    critere: str
    valeur: str
    proportion_ins: float
    n_quota: int
    disponibilite_brute: int
    disponibilite_effective: int


@dataclass
class ResultatMoteur:
    n: int
    criteres: list[str]
    marge_erreur: float
    marge_reference: float
    niveau_confiance: int
    z_score: float
    p: float
    offre_type: str
    raisons_personnalisee: list[str]
    max_criteres_autorise: int
    criteres_recommandes: list[str]
    cellules: list[ResultatCellule]
    disponibilite_globale: str
    reponses_attendues: int
    suggestions: list[str]
    message_pertinence: dict


def analyser(n: int, criteres_choisis: list[str]) -> ResultatMoteur:
    """Analyse complète d'un plan d'échantillonnage."""

    # ── 1. Vérifier offre Personnalisée ──
    criteres_perso = [
        c for c in criteres_choisis
        if CATEGORIES.get(c, {}).get("type") == "personnalise"
    ]
    if criteres_perso:
        labels = [CATEGORIES[c]["label"] for c in criteres_perso]
        return ResultatMoteur(
            n=n,
            criteres=criteres_choisis,
            marge_erreur=_calculer_marge(n),
            marge_reference=MARGE_REFERENCE,
            niveau_confiance=95,
            z_score=Z_95,
            p=P_DEFAVORABLE,
            offre_type="personnalisee",
            raisons_personnalisee=labels,
            max_criteres_autorise=0,
            criteres_recommandes=[],
            cellules=[],
            disponibilite_globale="non_applicable",
            reponses_attendues=0,
            suggestions=[],
            message_pertinence={
                "type": "personnalisee",
                "texte": f"Les critères {', '.join(labels)} nécessitent un accompagnement Tale."
            }
        )

    # ── 2. Calcul marge d'erreur ──
    marge = _calculer_marge(n)

    # ── 3. Règles de palier ──
    palier = _palier_le_plus_proche(n)
    regles = REGLES_PALIERS[palier]
    max_criteres = regles["max_criteres"]
    criteres_recommandes = regles["criteres_recommandes"]

    # ── 4. Filtrer critères standard ──
    criteres_std = [
        c for c in criteres_choisis
        if CATEGORIES.get(c, {}).get("type") == "standard"
    ]
    nb_criteres = len(criteres_std)

    # ── 5. Calcul cellules ──
    cellules = []
    cellules_insuffisantes = 0

    for critere in criteres_std:
        cat = CATEGORIES[critere]
        ins_key = cat["ins_key"]
        distribution_ins = INS_2024.get(ins_key, {})

        for valeur, proportion in distribution_ins.items():
            n_quota = max(1, round(n * proportion))
            dispo = get_disponibilite_panel(critere, valeur)

            if dispo["effectif"] < n_quota:
                cellules_insuffisantes += 1

            cellule = ResultatCellule(
                critere=critere,
                valeur=valeur,
                proportion_ins=round(proportion * 100, 1),
                n_quota=n_quota,
                disponibilite_brute=dispo["brut"],
                disponibilite_effective=dispo["effectif"],
            )
            cellules.append(cellule)

    # ── 6. Disponibilité globale ──
    if cellules_insuffisantes > 0:
        dispo_globale = "insuffisante"
    else:
        dispo_globale = "suffisante"

    # ── 7. Réponses attendues ──
    reponses_attendues = int(
        PANEL_TALE["total_panelistes"] * PANEL_TALE["taux_reponse_global"]
    )

    # ── 8. Suggestions ──
    suggestions = []
    if nb_criteres > max_criteres:
        n_min = _n_minimum_pour_criteres(nb_criteres)
        suggestions.append(
            f"Pour {nb_criteres} critère(s), augmentez à {n_min} répondants minimum "
            f"ou réduisez à {max_criteres} critère(s) pour {n} répondants."
        )
    if cellules_insuffisantes > 0:
        suggestions.append(
            f"{cellules_insuffisantes} cellule(s) avec disponibilité insuffisante — "
            f"augmentez N ou retirez le critère concerné."
        )
    if not suggestions:
        suggestions.append("Configuration viable — vous pouvez lancer l'étude.")

    # ── 9. Message de pertinence ──
    message = {
        "marge_erreur": f"±{marge:.1f}%",
        "marge_reference": f"±{MARGE_REFERENCE}%",
        "disponibilite": dispo_globale,
        "nb_cellules_insuffisantes": cellules_insuffisantes,
        "suggestions": suggestions,
        "panel_note": (
            "Panel opt-in non-probabiliste (modèle YouGov/Ipsos). "
            "La marge d'erreur est théorique."
        ),
    }

    return ResultatMoteur(
        n=n,
        criteres=criteres_std,
        marge_erreur=round(marge, 1),
        marge_reference=MARGE_REFERENCE,
        niveau_confiance=95,
        z_score=Z_95,
        p=P_DEFAVORABLE,
        offre_type="standard",
        raisons_personnalisee=[],
        max_criteres_autorise=max_criteres,
        criteres_recommandes=criteres_recommandes,
        cellules=cellules,
        disponibilite_globale=dispo_globale,
        reponses_attendues=reponses_attendues,
        suggestions=suggestions,
        message_pertinence=message,
    )


def _calculer_marge(n: int) -> float:
    """ME = Z × √(p(1-p)/n) — Formule Ipsos/YouGov, p=0.5."""
    if n <= 0:
        return 100.0
    return Z_95 * math.sqrt((P_DEFAVORABLE * (1 - P_DEFAVORABLE)) / n) * 100


def _palier_le_plus_proche(n: int) -> int:
    paliers = sorted(REGLES_PALIERS.keys())
    palier = paliers[0]
    for p in paliers:
        if n >= p:
            palier = p
    return palier


def _n_minimum_pour_criteres(nb_criteres: int) -> int:
    for palier, regles in sorted(REGLES_PALIERS.items()):
        if regles["max_criteres"] >= nb_criteres:
            return palier
    return 5000