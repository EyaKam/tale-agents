from agent import AgentQuestionnaire
import agent

print("Fichier agent utilisé :", agent.__file__)

print("Méthodes disponibles :")
print([m for m in dir(AgentQuestionnaire) if not m.startswith("__")])

if __name__ == "__main__":
    agent_obj = AgentQuestionnaire()
    resultat = agent_obj.run()