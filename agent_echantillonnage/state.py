"""

Imagine une feuille de papier que tous les nœuds de l'agent peuvent lire et écrire. Quand le nœud 1 termine, il écrit ses résultats sur la feuille. Le nœud 2 lit la feuille et continue.
C'est exactement ce que fait le State dans LangGraph


State de l'Agent Échantillonnage.
C'est la mémoire partagée entre tous les nœuds du graphe.
Chaque nœud lit et écrit dans ce State.
"""

from typing import Annotated, Any
from langgraph.graph.message import add_messages
from dataclasses import dataclass, field


@dataclass
class SamplingState:
    """
    Mémoire complète de la conversation d'échantillonnage.
    """

    # ── Historique de la conversation ──
    messages: Annotated[list, add_messages] = field(default_factory=list)

    # ── Ce que le client nous a dit ──
    objectif_etude: str = ""          # ex: "mesurer la notoriété de ma marque"
    population_cible: str = ""        # ex: "femmes 25-45 ans Tunis"
    budget_repondants: int | None = None   # nb max de répondants

    # ── Paramètres statistiques traduits ──
    marge_erreur: float = 0.05
    niveau_confiance: int = 95
    proportion: float = 0.5
    population_totale: int | None = None

    # ── Résultat du moteur statistique ──
    resultat_calcul: dict = field(default_factory=dict)

    # ── Mode de collecte choisi ──
    mode_collecte: str = ""   # "aleatoire" ou "panel"
    quotas: dict = field(default_factory=dict)

    # ── Statut du pipeline ──
    etape_courante: str = "debut"
    pret_pour_calcul: bool = False
    calcul_effectue: bool = False