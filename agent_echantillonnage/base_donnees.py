"""
Base de données simulée — Tale
Simule ce qui viendrait vraiment de la DB en production :
- Contexte du questionnaire (depuis Agent Questionnaire)
- Liste des panélistes avec leurs profils
- Taux de réponse historiques par cellule
- Données INS 2024 (recensement officiel)
"""

# ─────────────────────────────────────────
# DONNÉES INS 2024
# Source : Recensement Général Population Tunisie 2024
# Population : 11 972 169 habitants
# ─────────────────────────────────────────
INS_2024 = {
    "genre": {
        "Homme": 0.493,
        "Femme": 0.507,
    },
    "age": {
        "15-24": 0.172,
        "25-34": 0.195,
        "35-44": 0.181,
        "45-54": 0.156,
        "55-64": 0.120,
        "65+":   0.176,
    },
    "region": {
        "Grand Tunis":   0.237,
        "Nord-Est":      0.132,
        "Nord-Ouest":    0.101,
        "Centre-Est":    0.198,
        "Centre-Ouest":  0.099,
        "Sud-Est":       0.121,
        "Sud-Ouest":     0.112,
    },
    "milieu": {
        "Urbain": 0.72,
        "Rural":  0.28,
    },
    "secteur_nat": {
        "Agriculture & Pêche":            0.142,
        "Industries manufacturières":     0.198,
        "Industries non-manufacturières": 0.087,
        "Services":                       0.573,
    },
}

# ─────────────────────────────────────────
# RÈGLES DE PALIERS
# Basées sur Brief Tale v1.0 Section 4.1
# Plus N est petit, moins de critères possibles
# ─────────────────────────────────────────
REGLES_PALIERS = {
    50:   {"max_criteres": 1, "criteres_recommandes": ["genre"]},
    100:  {"max_criteres": 2, "criteres_recommandes": ["genre", "age"]},
    150:  {"max_criteres": 2, "criteres_recommandes": ["genre", "age"]},
    250:  {"max_criteres": 3, "criteres_recommandes": ["genre", "age", "region"]},
    500:  {"max_criteres": 4, "criteres_recommandes": ["genre", "age", "region", "secteur_nat"]},
    1000: {"max_criteres": 5, "criteres_recommandes": ["genre", "age", "region", "secteur_nat", "milieu"]},
    2000: {"max_criteres": 5, "criteres_recommandes": ["genre", "age", "region", "secteur_nat", "milieu"]},
    5000: {"max_criteres": 5, "criteres_recommandes": ["genre", "age", "region", "secteur_nat", "milieu"]},
}

# ─────────────────────────────────────────
# CATÉGORIES DISPONIBLES
# Standard = référencées INS → offre Standard
# Hors-standard = pas de référence INS → offre Personnalisée
# ─────────────────────────────────────────
CATEGORIES = {
    # ── Standard INS ──
    "genre": {
        "label": "Gender",
        "icone": "👤",
        "type": "standard",
        "ins_key": "genre",
        "cout_dt": 0,
        "valeurs": ["Homme", "Femme"],
    },
    "age": {
        "label": "Age range",
        "icone": "🎂",
        "type": "standard",
        "ins_key": "age",
        "cout_dt": 100,
        "valeurs": ["15-24", "25-34", "35-44", "45-54", "55-64", "65+"],
    },
    "region": {
        "label": "Region",
        "icone": "🗺️",
        "type": "standard",
        "ins_key": "region",
        "cout_dt": 0,
        "valeurs": ["Grand Tunis", "Nord-Est", "Nord-Ouest", "Centre-Est",
                    "Centre-Ouest", "Sud-Est", "Sud-Ouest"],
    },
    "milieu": {
        "label": "Milieu (Urbain/Rural)",
        "icone": "🏙️",
        "type": "standard",
        "ins_key": "milieu",
        "cout_dt": 0,
        "valeurs": ["Urbain", "Rural"],
    },
    "secteur_nat": {
        "label": "Sector of Activity (NAT)",
        "icone": "🏭",
        "type": "standard",
        "ins_key": "secteur_nat",
        "cout_dt": 0,
        "valeurs": ["Agriculture & Pêche", "Industries manufacturières",
                    "Industries non-manufacturières", "Services"],
    },

    # ── Hors-standard → Personnalisée ──
    "revenu": {
        "label": "Household Income",
        "icone": "💰",
        "type": "personnalise",
        "ins_key": None,
        "cout_dt": 10,
        "valeurs": ["< 500 DT", "500-1000 DT", "1000-2000 DT", "> 2000 DT"],
    },
    "situation_matrimoniale": {
        "label": "Marital Status",
        "icone": "💍",
        "type": "personnalise",
        "ins_key": None,
        "cout_dt": 40,
        "valeurs": ["Célibataire", "Marié(e)", "Divorcé(e)", "Veuf/Veuve"],
    },
    "education": {
        "label": "Education",
        "icone": "🎓",
        "type": "personnalise",
        "ins_key": None,
        "cout_dt": 120,
        "valeurs": ["Primaire", "Secondaire", "Universitaire", "Post-grad"],
    },
    "cartes_credit": {
        "label": "Credit Cards Owned",
        "icone": "💳",
        "type": "personnalise",
        "ins_key": None,
        "cout_dt": 150,
        "valeurs": ["Aucune", "1 carte", "2+ cartes"],
    },
    "assurance_auto": {
        "label": "Current Auto Insurance",
        "icone": "🚗",
        "type": "personnalise",
        "ins_key": None,
        "cout_dt": 90,
        "valeurs": ["Oui", "Non"],
    },
}

# ─────────────────────────────────────────
# PANEL TALE SIMULÉ
# En production : requête SQL sur la vraie DB
# Simule 2800 panélistes avec profils et taux réponse
# ─────────────────────────────────────────
PANEL_TALE = {
    "total_panelistes": 2800,
    "taux_reponse_global": 0.55,

    # Disponibilité brute par cellule (comptage réel)
    # + taux de réponse historique par cellule
    "cellules": {
        # Genre
        ("genre", "Homme"): {"brut": 1350, "taux_reponse": 0.58},
        ("genre", "Femme"): {"brut": 1450, "taux_reponse": 0.52},

        # Âge
        ("age", "15-24"):   {"brut": 420,  "taux_reponse": 0.65},
        ("age", "25-34"):   {"brut": 580,  "taux_reponse": 0.60},
        ("age", "35-44"):   {"brut": 490,  "taux_reponse": 0.55},
        ("age", "45-54"):   {"brut": 380,  "taux_reponse": 0.48},
        ("age", "55-64"):   {"brut": 290,  "taux_reponse": 0.40},
        ("age", "65+"):     {"brut": 170,  "taux_reponse": 0.32},

        # Région
        ("region", "Grand Tunis"):   {"brut": 980,  "taux_reponse": 0.62},
        ("region", "Nord-Est"):      {"brut": 340,  "taux_reponse": 0.55},
        ("region", "Nord-Ouest"):    {"brut": 180,  "taux_reponse": 0.48},
        ("region", "Centre-Est"):    {"brut": 520,  "taux_reponse": 0.57},
        ("region", "Centre-Ouest"):  {"brut": 150,  "taux_reponse": 0.42},
        ("region", "Sud-Est"):       {"brut": 280,  "taux_reponse": 0.50},
        ("region", "Sud-Ouest"):     {"brut": 200,  "taux_reponse": 0.44},

        # Milieu
        ("milieu", "Urbain"): {"brut": 2100, "taux_reponse": 0.60},
        ("milieu", "Rural"):  {"brut": 700,  "taux_reponse": 0.42},

        # Secteur NAT
        ("secteur_nat", "Agriculture & Pêche"):            {"brut": 180, "taux_reponse": 0.38},
        ("secteur_nat", "Industries manufacturières"):     {"brut": 420, "taux_reponse": 0.50},
        ("secteur_nat", "Industries non-manufacturières"): {"brut": 210, "taux_reponse": 0.52},
        ("secteur_nat", "Services"):                       {"brut": 980, "taux_reponse": 0.62},
    }
}

# ─────────────────────────────────────────
# CONTEXTE QUESTIONNAIRE
# En production : lu depuis la DB après Agent Questionnaire
# ─────────────────────────────────────────
def get_contexte_questionnaire() -> dict:
    """
    Simule la lecture du contexte depuis la base de données.
    En production : SELECT * FROM questionnaires WHERE id = current_session
    """
    return {
        "id": "Q-2026-001",
        "titre": "Étude sur les habitudes de consommation de yaourt",
        "theme": "Test de concept produit",
        "nb_questions": 12,
        "duree_estimee_min": 8,
        "objectif": "Mesurer l'appréciation d'un nouveau goût et l'intention d'achat",
        "population_cible_declaree": "Adultes tunisiens consommateurs de produits laitiers",
        "type_etude": "Quantitative",
        "statut": "En attente d'échantillonnage",
    }


def get_disponibilite_panel(critere: str, valeur: str) -> dict:
    """
    Retourne la disponibilité brute et effective pour une cellule.
    En production : SELECT COUNT(*) FROM panelistes WHERE critere = valeur
    """
    cellule = PANEL_TALE["cellules"].get((critere, valeur))
    if not cellule:
        return {"brut": 0, "effectif": 0, "taux_reponse": 0}

    effectif = int(cellule["brut"] * cellule["taux_reponse"])
    return {
        "brut": cellule["brut"],
        "effectif": effectif,
        "taux_reponse": cellule["taux_reponse"],
    }