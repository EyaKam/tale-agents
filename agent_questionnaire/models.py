# models.py
# Structures de données de l'Agent Questionnaire
# Définit le contrat d'interface avec l'Agent 1 (Eya)

from dataclasses import dataclass, field
from typing import List
import math

# ================================================
# STRUCTURE 1 — Paramètres collectés durant
#               le dialogue avec le client
# ================================================
@dataclass
class ParametresEtude:
    objectif_etude: str = ""
    population_cible: str = ""
    type_enquete: str = "externe"   # interne | externe
    anonyme: bool = True            # enquête anonyme ou non
    collecter_nom: bool = False     # False si anonyme
    collecter_genre: bool = False   # False si anonyme
    langue: str = "fr"
    themes: List[str] = field(default_factory=list)
    nb_questions: int = 12

    def est_complet(self) -> bool:
        """Vérifie que toutes les infos essentielles sont là"""
        return all([
            self.objectif_etude,
            self.population_cible,
            self.langue,
            len(self.themes) > 0
        ])

# ================================================
# STRUCTURE 2 — Une question du questionnaire
# ================================================
@dataclass
class Question:
    index: int = 0
    type: str = ""        # single_choice | likert_5 |
                          # open_text | multiple_choice
    texte: str = ""
    options: List[str] = field(default_factory=list)
    role: str = ""        # screening | principal |
                          # verbatim | profilage
    theme: str = ""
    obligatoire: bool = True

# ================================================
# STRUCTURE 3 — Le questionnaire complet
#               Sortie finale transmise à Eya
# ================================================
@dataclass
class Questionnaire:
    parametres: ParametresEtude = field(
        default_factory=ParametresEtude
    )
    questions: List[Question] = field(default_factory=list)
    introduction: str = ""
    nb_questions_total: int = 0
    duree_estimee_minutes: int = 0
    valide: bool = False

    def calculer_duree(self) -> int:
        """
        Calcule la durée estimée en minutes
        selon le type de chaque question.
        Python calcule — jamais le LLM.
        """
        temps_par_type = {
            "single_choice":   30,   # secondes
            "likert_5":        20,
            "multiple_choice": 40,
            "open_text":       90
        }

        total_secondes = 0
        for q in self.questions:
            temps = temps_par_type.get(q.type, 30)
            total_secondes += temps

        return math.ceil(total_secondes / 60)

    def to_dict(self) -> dict:
        """Convertit en JSON pour transmettre à Eya"""
        return {
            "objectif_etude": self.parametres.objectif_etude,
            "population_cible": self.parametres.population_cible,
            "type_enquete": self.parametres.type_enquete,
            "anonyme": self.parametres.anonyme,
            "langue": self.parametres.langue,
            "themes": self.parametres.themes,
            "introduction": self.introduction,
            "nb_questions_total": self.nb_questions_total,
            "duree_estimee_minutes": self.duree_estimee_minutes,
            "questions": [
                {
                    "index": q.index,
                    "type": q.type,
                    "texte": q.texte,
                    "options": q.options,
                    "role": q.role,
                    "theme": q.theme,
                    "obligatoire": q.obligatoire
                }
                for q in self.questions
            ]
        }