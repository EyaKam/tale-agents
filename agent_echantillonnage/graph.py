"""
Graphe LangGraph de l'Agent Échantillonnage.
C'est ici qu'on connecte les nœuds dans l'ordre.
"""

from langgraph.graph import StateGraph, START, END
from .state import SamplingState
from .nodes import (
    noeud_accueil,
    noeud_extraction,
    noeud_calcul,
    noeud_restitution,
)


def creer_agent_echantillonnage():
    """
    Crée et retourne le graphe compilé de l'agent.
    """

    # ── Créer le graphe avec notre State ──
    graphe = StateGraph(SamplingState)

    # ── Ajouter les nœuds ──
    graphe.add_node("accueil", noeud_accueil)
    graphe.add_node("extraction", noeud_extraction)
    graphe.add_node("calcul", noeud_calcul)
    graphe.add_node("restitution", noeud_restitution)

    # ── Connecter les nœuds dans l'ordre ──
    graphe.add_edge(START, "accueil")
    graphe.add_edge("accueil", "extraction")
    graphe.add_edge("extraction", "calcul")
    graphe.add_edge("calcul", "restitution")
    graphe.add_edge("restitution", END)

    # ── Compiler le graphe ──
    return graphe.compile()


# Instance prête à l'emploi
agent_echantillonnage = creer_agent_echantillonnage()