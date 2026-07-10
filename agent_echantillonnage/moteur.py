"""
Moteur statistique déterministe — Tale V3
Formule Ipsos/YouGov : ME = Z × √(p(1-p)/n)
Z = 1.96 (95%), p = 0.5 (cas le plus défavorable)

RÈGLE D'OR : Zéro LLM ici. Calculs purs et vérifiables.
"""

import math
from dataclasses import dataclass, field
from .base_donnees import (
    INS_2024,
    REGLES_PALIERS,
    CATEGORIES,
    get_disponibilite_panel,
)


# ─────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────
Z_95 = 1.96
P_DEFAVORABLE = 0.5  # cas le plus défavorable → marge max


# ─────────────────────────────────────────
# Structures de résultat
# ─────────────────────────────────────────
@dataclass
class ResultatCellule:
    """Résultat pour une cellule de quota."""
    critere: str
    valeur: str
    proportion_ins: float       # % selon INS
    n_quota: int                # répondants nécessaires
    disponibilite_brute: int    # panélistes dans la DB
    disponibilite_effective: int # panélistes × taux réponse
    ratio_couverture: float     # effectif / n_quota
    statut: str                 # "ok" / "fragile" / "critique"


@dataclass
class ResultatMoteur:
    """Résultat complet du moteur statistique."""
    # Paramètres
    n: int
    criteres: list[str]

    # Calculs statistiques
    marge_erreur: float         # en %
    niveau_confiance: int       # 95
    z_score: float              # 1.96
    p: float                    # 0.5

    # Offre
    offre_type: str             # "standard" / "personnalisee"
    raisons_personnalisee: list[str]

    # Quotas
    max_criteres_autorise: int
    criteres_recommandes: list[str]
    cellules: list[ResultatCellule]

    # Disponibilité globale
    disponibilite_globale: str  # "suffisante" / "insuffisante" / "risquee"
    reponses_attendues: int

    # Alertes
    alertes: list[dict]

    # Message de pertinence (structure)
    message_pertinence: dict


# ─────────────────────────────────────────
# Fonction principale
# ─────────────────────────────────────────
def analyser(n: int, criteres_choisis: list[str]) -> ResultatMoteur:
    """
    Analyse complète d'un plan d'échantillonnage.

    Args:
        n: nombre de répondants souhaité
        criteres_choisis: liste des clés de critères
                         ex: ["genre", "age"]

    Returns:
        ResultatMoteur complet
    """

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
            alertes=[{
                "niveau": "redirect",
                "message": f"Critère(s) hors-standard détecté(s) : {', '.join(labels)}",
                "recommandation": "Redirection vers l'offre Personnalisée Tale."
            }],
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

    # ── 4. Filtrer critères standard uniquement ──
    criteres_std = [
        c for c in criteres_choisis
        if CATEGORIES.get(c, {}).get("type") == "standard"
    ]

    # ── 5. Calcul cellules ──
    cellules = []
    alertes = []

    for critere in criteres_std:
        cat = CATEGORIES[critere]
        ins_key = cat["ins_key"]
        distribution_ins = INS_2024.get(ins_key, {})

        for valeur, proportion in distribution_ins.items():
            n_quota = max(1, round(n * proportion))
            dispo = get_disponibilite_panel(critere, valeur)

            # Ratio couverture = effectif / n_quota
            ratio = dispo["effectif"] / n_quota if n_quota > 0 else 0

            # Statut de la cellule
            if ratio >= 1.5:
                statut = "ok"
            elif ratio >= 1.0:
                statut = "fragile"
            else:
                statut = "critique"

            cellule = ResultatCellule(
                critere=critere,
                valeur=valeur,
                proportion_ins=round(proportion * 100, 1),
                n_quota=n_quota,
                disponibilite_brute=dispo["brut"],
                disponibilite_effective=dispo["effectif"],
                ratio_couverture=round(ratio, 2),
                statut=statut,
            )
            cellules.append(cellule)

            # Alerte cellule critique
            if statut == "critique":
                alertes.append({
                    "niveau": "critique",
                    "message": (
                        f"Cellule critique : {cat['label']} → {valeur} "
                        f"({dispo['effectif']} disponibles / {n_quota} requis)"
                    ),
                    "recommandation": "Augmentez N ou retirez ce critère."
                })
            elif statut == "fragile":
                alertes.append({
                    "niveau": "warning",
                    "message": (
                        f"Cellule fragile : {cat['label']} → {valeur} "
                        f"({dispo['effectif']} disponibles / {n_quota} requis)"
                    ),
                    "recommandation": "Résultat peu fiable pour ce sous-groupe."
                })

    # ── 6. Trop de critères pour ce N ──
    nb_criteres = len(criteres_std)
    if nb_criteres > max_criteres:
        alertes.append({
            "niveau": "critique",
            "message": (
                f"{nb_criteres} critères sélectionnés mais "
                f"maximum {max_criteres} pour {n} répondants."
            ),
            "recommandation": (
                f"Retirez {nb_criteres - max_criteres} critère(s) "
                f"ou augmentez N à {_n_minimum_pour_criteres(nb_criteres)} minimum."
            )
        })

    # ── 7. Marge d'erreur élevée ──
    if marge > 10:
        alertes.append({
            "niveau": "critique",
            "message": f"Marge d'erreur très élevée : ±{marge:.1f}%",
            "recommandation": "Augmentez à 385 répondants minimum pour ±5%."
        })
    elif marge > 7:
        alertes.append({
            "niveau": "warning",
            "message": f"Marge d'erreur élevée : ±{marge:.1f}%",
            "recommandation": "Idéalement 200+ répondants pour ±7% ou moins."
        })

    # ── 8. Disponibilité globale ──
    cellules_critiques = [c for c in cellules if c.statut == "critique"]
    if len(cellules_critiques) > len(cellules) * 0.3:
        dispo_globale = "insuffisante"
    elif len(cellules_critiques) > 0:
        dispo_globale = "risquee"
    else:
        dispo_globale = "suffisante"

    # Réponses attendues (estimation)
    from .base_donnees import PANEL_TALE
    reponses_attendues = int(
        PANEL_TALE["total_panelistes"] * PANEL_TALE["taux_reponse_global"]
    )

    # Alerte panel
    alertes.append({
        "niveau": "info",
        "message": (
            "Panel opt-in non-probabiliste (modèle YouGov/Ipsos). "
            "La marge d'erreur est théorique — la probabilité de "
            "participation individuelle n'est pas connue."
        ),
        "recommandation": "Résultat indicatif, conforme aux pratiques du marché."
    })

    # ── 9. Message de pertinence ──
    message = _construire_message_pertinence(
        n=n,
        marge=marge,
        criteres_std=criteres_std,
        cellules=cellules,
        dispo_globale=dispo_globale,
        nb_criteres=nb_criteres,
        max_criteres=max_criteres,
    )

    return ResultatMoteur(
        n=n,
        criteres=criteres_std,
        marge_erreur=round(marge, 1),
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
        alertes=alertes,
        message_pertinence=message,
    )


# ─────────────────────────────────────────
# Formule ME = Z × √(p(1-p)/n)
# ─────────────────────────────────────────
def _calculer_marge(n: int) -> float:
    """
    Formule Ipsos/YouGov.
    p = 0.5 → cas le plus défavorable → marge maximale.
    Retourne la marge en %.
    """
    if n <= 0:
        return 100.0
    return Z_95 * math.sqrt((P_DEFAVORABLE * (1 - P_DEFAVORABLE)) / n) * 100


def _palier_le_plus_proche(n: int) -> int:
    """Trouve le palier de règles le plus proche pour N."""
    paliers = sorted(REGLES_PALIERS.keys())
    palier = paliers[0]
    for p in paliers:
        if n >= p:
            palier = p
    return palier


def _n_minimum_pour_criteres(nb_criteres: int) -> int:
    """Retourne le N minimum pour supporter nb_criteres critères."""
    mapping = {
        1: 50,
        2: 100,
        3: 250,
        4: 500,
        5: 1000,
    }
    return mapping.get(nb_criteres, 1000)


def _construire_message_pertinence(
    n: int,
    marge: float,
    criteres_std: list,
    cellules: list,
    dispo_globale: str,
    nb_criteres: int,
    max_criteres: int,
) -> dict:
    """
    Construit le message de pertinence structuré.
    Combine précision statistique + faisabilité recrutement.
    Inspiré du brief Tale Section 4.2.
    """
    cellules_critiques = [c for c in cellules if c.statut == "critique"]
    cellules_fragiles = [c for c in cellules if c.statut == "fragile"]

    if dispo_globale == "insuffisante" or nb_criteres > max_criteres:
        risque = "élevé"
    elif dispo_globale == "risquee" or marge > 10:
        risque = "modéré"
    else:
        risque = "faible"

    suggestions = []
    if nb_criteres > max_criteres:
        suggestions.append(
            f"Réduire à {max_criteres} critère(s) maximum pour {n} répondants"
        )
    if marge > 10:
        suggestions.append("Augmenter à 385+ répondants pour ±5% de marge")
    if cellules_critiques:
        suggestions.append(
            f"Retirer les critères avec cellules critiques "
            f"({len(cellules_critiques)} cellule(s) insuffisante(s))"
        )
    if not suggestions:
        suggestions.append("Configuration viable — vous pouvez lancer l'étude")

    return {
        "marge_erreur_theorique": f"±{marge:.1f}%",
        "disponibilite": dispo_globale,
        "nb_cellules_critiques": len(cellules_critiques),
        "nb_cellules_fragiles": len(cellules_fragiles),
        "risque": risque,
        "suggestions": suggestions,
    }