"""
Moteur statistique déterministe — Calcul de taille d'échantillon.
RÈGLE D'OR : ce module ne contient AUCUN appel LLM.
Toutes les valeurs produites ici sont vérifiables mathématiquement.
"""

import math
from dataclasses import dataclass


# ─────────────────────────────────────────
# Constantes : niveaux de confiance → z
# ─────────────────────────────────────────
Z_SCORES = {
    90: 1.645,# loi normale
    95: 1.960,
    99: 2.576,
}


# ─────────────────────────────────────────
# Structure de résultat
# ─────────────────────────────────────────
@dataclass
class SampleResult:
    """
    Résultat complet du calcul d'échantillon.
    Tout ce qui sort de ce module est typé et traçable.
    """
    n_theorique: int          # taille avant correction population finie
    n_final: int              # taille finale (après correction si besoin)
    marge_erreur: float       # marge d'erreur en %
    niveau_confiance: int     # niveau de confiance en %
    z_score: float            # z utilisé
    proportion: float         # p utilisé
    population: int | None    # N si fourni
    correction_appliquee: bool  # True si population finie appliquée
    alerte_biais: list[str]   # alertes représentativité


# ─────────────────────────────────────────
# Fonction principale
# ─────────────────────────────────────────
def calculer_taille_echantillon(
    marge_erreur: float = 0.05,
    niveau_confiance: int = 95,
    proportion: float = 0.5,
    population: int | None = None,
) -> SampleResult:
    """
    Calcule la taille d'échantillon nécessaire.

    Args:
        marge_erreur: ex. 0.05 pour ±5%
        niveau_confiance: 90, 95 ou 99
        proportion: proportion estimée (0.5 si inconnue = cas conservateur)
        population: taille de la population totale (None = infinie)

    Returns:
        SampleResult avec tous les détails du calcul

    Raises:
        ValueError: si les paramètres sont invalides
    """

    # ── Validation des paramètres ──
    if niveau_confiance not in Z_SCORES:
        raise ValueError(
            f"Niveau de confiance invalide : {niveau_confiance}. "
            f"Valeurs acceptées : {list(Z_SCORES.keys())}"
        )
    if not (0 < marge_erreur < 1):
        raise ValueError(
            f"Marge d'erreur invalide : {marge_erreur}. "
            "Doit être entre 0 et 1 (ex: 0.05 pour 5%)"
        )
    if not (0 < proportion < 1):
        raise ValueError(
            f"Proportion invalide : {proportion}. "
            "Doit être entre 0 et 1 (ex: 0.5)"
        )
    if population is not None and population <= 0:
        raise ValueError("La population doit être un entier positif.")

    # ── Calcul de base ──
    z = Z_SCORES[niveau_confiance]
    n_theorique = math.ceil(
        (z ** 2 * proportion * (1 - proportion)) / (marge_erreur ** 2)
    )

    # ── Correction population finie ──
    # Si la population N est connue et petite,
    # on peut réduire la taille d'échantillon
    correction_appliquee = False
    n_final = n_theorique

    if population is not None and n_theorique > population * 0.05:
        n_final = math.ceil(
            n_theorique / (1 + (n_theorique - 1) / population)
        )
        correction_appliquee = True

    # ── Alertes de représentativité ──
    alertes = _generer_alertes(n_final, population)

    return SampleResult(
        n_theorique=n_theorique,
        n_final=n_final,
        marge_erreur=marge_erreur * 100,   # converti en %
        niveau_confiance=niveau_confiance,
        z_score=z,
        proportion=proportion,
        population=population,
        correction_appliquee=correction_appliquee,
        alerte_biais=alertes,
    )


# ─────────────────────────────────────────
# Alertes de représentativité
# ─────────────────────────────────────────
def _generer_alertes(n: int, population: int | None) -> list[str]:
    """
    Génère des alertes honnêtes sur les limites de l'échantillon.
    Ces alertes sont affichées au client — elles ne sont jamais cachées.
    """
    alertes = []

    if n < 30:
        alertes.append(
            "⚠️ Échantillon très petit (n<30) : "
            "les résultats ne sont pas généralisables."
        )
    if n < 100:
        alertes.append(
            "⚠️ Échantillon petit (n<100) : "
            "les analyses par sous-groupes seront peu fiables."
        )

    alertes.append(
        "ℹ️ Panel en ligne : biais probable de sur-représentation "
        "urbaine, jeune et connectée. Les conclusions ne sont pas "
        "généralisables à l'ensemble de la population tunisienne."
    )

    if population is None:
        alertes.append(
            "ℹ️ Population totale non renseignée : "
            "calcul effectué pour une population infinie."
        )

    return alertes