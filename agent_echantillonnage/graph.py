"""
Graphe LangGraph de l'Agent Échantillonnage.
Le graphe décide dynamiquement de continuer le dialogue
ou de passer au calcul.
"""

from langgraph.graph import StateGraph, START, END
from .state import SamplingState
from .nodes import noeud_dialogue, noeud_calcul, noeud_restitution


def _continuer_ou_calculer(state: SamplingState) -> str:
    """
    Décision : continuer le dialogue ou passer au calcul ?
    """
    if state.pret_pour_calcul:
        return "calculer"
    return "dialoguer"


def creer_agent_echantillonnage():

    graphe = StateGraph(SamplingState)

    # Ajouter les nœuds
    graphe.add_node("dialogue", noeud_dialogue)
    graphe.add_node("calcul", noeud_calcul)
    graphe.add_node("restitution", noeud_restitution)

    # Point d'entrée
    graphe.add_edge(START, "dialogue")

    # Décision après dialogue
    graphe.add_conditional_edges(
        "dialogue",
        _continuer_ou_calculer,
        {
            "dialoguer": END,      # on attend la prochaine réponse du client
            "calculer": "calcul",  # on calcule
        }
    )

    # Après calcul → restitution → fin
    graphe.add_edge("calcul", "restitution")
    graphe.add_edge("restitution", END)

    return graphe.compile()


agent_echantillonnage = creer_agent_echantillonnage()