"""
Test de l'Agent Échantillonnage en mode conversationnel.
Lance une étude complète de bout en bout.
"""

from agent_echantillonnage import agent_echantillonnage


def main():
    print("=" * 50)
    print("   TALE — Agent Échantillonnage")
    print("=" * 50)

    # État initial — le client commence la conversation
    state = {
        "messages": [{
            "role": "user",
            "content": (
                "Bonjour, je veux faire une étude pour savoir "
                "si les Tunisiens connaissent ma marque de yaourt. "
                "Je vise les femmes de 25 à 45 ans à Tunis. "
                "Je veux être précis et j'ai un budget de 500 répondants max."
            )
        }]
    }

    # Lancer le graphe
    print("\n🚀 Lancement du pipeline...\n")
    resultat = agent_echantillonnage.invoke(state)

    # Afficher le résultat final
    print("\n" + "=" * 50)
    print("   RÉSULTAT FINAL")
    print("=" * 50)

    # Afficher le dernier message de l'agent
    for message in resultat["messages"]:
        if hasattr(message, "content"):
            print(f"\n{message.content}")

    # Afficher les chiffres calculés
    print("\n" + "=" * 50)
    print("   CHIFFRES CALCULÉS (moteur déterministe)")
    print("=" * 50)
    calcul = resultat.get("resultat_calcul", {})
    if calcul:
        print(f"✅ Taille échantillon : {calcul.get('n_final')} répondants")
        print(f"✅ Marge d'erreur     : ±{calcul.get('marge_erreur')}%")
        print(f"✅ Niveau de confiance: {calcul.get('niveau_confiance')}%")
        print(f"✅ Mode de collecte   : {calcul.get('mode_collecte')}")
        print("\n⚠️  Alertes :")
        for alerte in calcul.get("alerte_biais", []):
            print(f"   {alerte}")


if __name__ == "__main__":
    main()