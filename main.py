"""
Interface conversationnelle de l'Agent Échantillonnage.
"""

from agent_echantillonnage import agent_echantillonnage
from agent_echantillonnage.state import SamplingState


def extraire_dernier_message_agent(messages: list) -> str | None:
    """Récupère le dernier message de l'agent."""
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "assistant":
            return msg.get("content")
        if hasattr(msg, "type") and msg.type == "ai":
            return msg.content
    return None


def main():
    print("=" * 60)
    print("   TALE — Agent Échantillonnage")
    print("   Tapez 'quit' pour terminer")
    print("=" * 60)

    # Mémoire de la conversation
    messages = []
    pret_pour_calcul = False
    resultat_calcul = {}
    niveau_confiance = 95
    proportion = 0.5
    population_totale = None
    marge_erreur = 0.05
    mode_collecte = ""
    objectif_etude = ""
    population_cible = ""

    print("\n🤖 Agent : Bonjour ! Je suis votre assistant en études")
    print("           marketing. Comment puis-je vous aider aujourd'hui ?\n")

    while True:

        # ── Tu parles ──
        user_input = input("👤 Vous : ").strip()

        if user_input.lower() == "quit":
            print("\n👋 Au revoir !")
            break

        if not user_input:
            continue

        # ── Ajouter ton message ──
        messages.append({"role": "user", "content": user_input})

        # ── Envoyer à l'agent ──
        state = {
            "messages": messages,
            "pret_pour_calcul": pret_pour_calcul,
            "resultat_calcul": resultat_calcul,
            "niveau_confiance": niveau_confiance,
            "proportion": proportion,
            "population_totale": population_totale,
            "marge_erreur": marge_erreur,
            "mode_collecte": mode_collecte,
            "objectif_etude": objectif_etude,
            "population_cible": population_cible,
        }

        resultat = agent_echantillonnage.invoke(state)

        # ── Mettre à jour le state ──
        pret_pour_calcul = resultat.get("pret_pour_calcul", False)
        resultat_calcul = resultat.get("resultat_calcul", {})
        marge_erreur = resultat.get("marge_erreur", marge_erreur)
        mode_collecte = resultat.get("mode_collecte", mode_collecte)
        objectif_etude = resultat.get("objectif_etude", objectif_etude)
        population_cible = resultat.get("population_cible", population_cible)

        # ── Afficher la réponse ──
        reponse = extraire_dernier_message_agent(resultat["messages"])

        if reponse:
            print(f"\n🤖 Agent : {reponse}\n")
            messages.append({"role": "assistant", "content": reponse})

        # ── Si calcul terminé ──
        if resultat.get("etape_courante") == "termine" and resultat_calcul:
            print("\n" + "=" * 60)
            print("   ✅ PLAN D'ÉCHANTILLONNAGE CALCULÉ")
            print("=" * 60)
            print(f"📊 Taille échantillon  : {resultat_calcul.get('n_final')} répondants")
            print(f"📊 Marge d'erreur      : ±{resultat_calcul.get('marge_erreur')}%")
            print(f"📊 Niveau de confiance : {resultat_calcul.get('niveau_confiance')}%")
            print(f"📊 Mode de collecte    : {resultat_calcul.get('mode_collecte')}")
            print("\n⚠️  Alertes :")
            for alerte in resultat_calcul.get("alerte_biais", []):
                print(f"   {alerte}")
            print("=" * 60)
            break


if __name__ == "__main__":
    main()