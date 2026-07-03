"""
Tests unitaires du moteur statistique.
On vérifie que les calculs sont mathématiquement corrects.
"""

import pytest
import sys
import os

# Pour que Python trouve le module moteur_stat
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from moteur_stat.sample_size import calculer_taille_echantillon, SampleResult


# ─────────────────────────────────────────
# Test 1 — Le cas classique
# ─────────────────────────────────────────
def test_cas_classique():
    """
    95% confiance, ±5% marge, p=0.5
    Résultat attendu : 385 répondants
    C'est le chiffre standard en études marketing.
    """
    result = calculer_taille_echantillon(
        marge_erreur=0.05,
        niveau_confiance=95,
        proportion=0.5,
    )
    assert result.n_final == 385


# ─────────────────────────────────────────
# Test 2 — Marge d'erreur plus stricte
# ─────────────────────────────────────────
def test_marge_stricte():
    """
    Si on veut ±1% au lieu de ±5%,
    il faut beaucoup plus de répondants.
    """
    result = calculer_taille_echantillon(
        marge_erreur=0.01,
        niveau_confiance=95,
        proportion=0.5,
    )
    assert result.n_final > 9000


# ─────────────────────────────────────────
# Test 3 — Niveau de confiance 99%
# ─────────────────────────────────────────
def test_confiance_99():
    """
    99% confiance → plus de répondants que 95%
    """
    result_95 = calculer_taille_echantillon(niveau_confiance=95)
    result_99 = calculer_taille_echantillon(niveau_confiance=99)
    assert result_99.n_final > result_95.n_final


# ─────────────────────────────────────────
# Test 4 — Correction population finie
# ─────────────────────────────────────────
def test_correction_population_finie():
    """
    Si la population est petite (ex: 1000 personnes),
    on a besoin de moins de répondants que 385.
    """
    result = calculer_taille_echantillon(
        marge_erreur=0.05,
        niveau_confiance=95,
        proportion=0.5,
        population=1000,
    )
    assert result.n_final < 385
    assert result.correction_appliquee == True


# ─────────────────────────────────────────
# Test 5 — Les alertes sont toujours présentes
# ──────────────────────────────────────