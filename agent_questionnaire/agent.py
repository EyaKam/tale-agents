# agent.py
# Logique principale de l'Agent Questionnaire
# Orchestre les 5 phases : dialogue → extraction →
# génération → validation → restitution

import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

from models import ParametresEtude, Question, Questionnaire
from prompts import (
    PROMPT_ACCUEIL,
    PROMPT_EXTRACTION,
    PROMPT_GENERATION,
    PROMPT_RESTITUTION
)

# Charger la clé API
load_dotenv()

# ================================================
# Liste des modèles de fallback dans l'ordre
# Si le premier est surchargé → essai du suivant
# ================================================
MODELES_FALLBACK = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]


class AgentQuestionnaire:

    def __init__(self):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )
        self.historique_messages = []

    # ============================================
    # UTILITAIRE — Appel LLM avec fallback auto
    # ============================================
    def _appel_llm(self, prompt: str, system: str = None) -> str:
        """
        Appel au modèle Gemini avec fallback automatique.
        Si un modèle est surchargé (503) ou quota épuisé (429),
        essaie automatiquement le modèle suivant dans la liste.
        Retourne le texte de la réponse nettoyé.
        """
        config = None
        if system:
            config = types.GenerateContentConfig(
                system_instruction=system
            )

        # Essayer chaque modèle dans l'ordre
        for modele in MODELES_FALLBACK:
            try:
                response = self.client.models.generate_content(
                    model=modele,
                    config=config,
                    contents=prompt
                )

                # Nettoyer les balises markdown si présentes
                texte = response.text.strip()
                texte = texte.replace("```json", "")
                texte = texte.replace("```", "").strip()
                return texte

            except Exception as e:
                erreur = str(e)

                # Erreur 503 — modèle surchargé
                if "503" in erreur or "UNAVAILABLE" in erreur:
                    print(f"⚠️  {modele} surchargé — essai suivant...")
                    time.sleep(1)
                    continue

                # Erreur 429 — quota épuisé
                elif "429" in erreur or "RESOURCE_EXHAUSTED" in erreur:
                    print(f"⚠️  {modele} quota épuisé — essai suivant...")
                    time.sleep(1)
                    continue

                # Erreur 404 — modèle introuvable
                elif "404" in erreur or "NOT_FOUND" in erreur:
                    print(f"⚠️  {modele} introuvable — essai suivant...")
                    continue

                # Autre erreur — on arrête
                else:
                    print(f"❌ Erreur inattendue avec {modele} : {e}")
                    raise

        # Tous les modèles ont échoué
        print("❌ Tous les modèles sont indisponibles.")
        print("   Attends quelques minutes et relance.")
        return ""

    # ============================================
    # PHASE 1 — Dialogue avec le client
    # ============================================
    def _dialogue(self) -> str:
        """
        Dialogue avec le client pour collecter
        toutes les informations nécessaires.
        Retourne l'historique de conversation en texte.
        """
        print("\n" + "=" * 50)
        print("   AGENT QUESTIONNAIRE — TALE")
        print("=" * 50)

        self.historique_messages = []

        # Premier message d'accueil
        message_agent = self._appel_llm(
            prompt="Bonjour, je veux créer une enquête",
            system=PROMPT_ACCUEIL
        )

        if not message_agent:
            return ""

        self.historique_messages.append(f"AGENT: {message_agent}")
        print(f"\n🤖 Agent: {message_agent}")
        print("-" * 50)

        # Boucle de dialogue — max 8 tours
        for i in range(8):
            user_input = input("\n👤 Vous: ")
            self.historique_messages.append(f"CLIENT: {user_input}")

            # Construire le contexte complet pour garder la mémoire
            contexte = "\n".join(self.historique_messages)
            prompt_avec_contexte = f"{contexte}\nAGENT:"

            message_agent = self._appel_llm(
                prompt=prompt_avec_contexte,
                system=PROMPT_ACCUEIL
            )

            if not message_agent:
                break

            self.historique_messages.append(f"AGENT: {message_agent}")
            print(f"\n🤖 Agent: {message_agent}")
            print("-" * 50)

            # Arrêter quand toutes les infos sont collectées
            if "toutes les informations" in message_agent.lower():
                print("\n✅ Collecte terminée !")
                break

        return "\n".join(self.historique_messages)

    # ============================================
    # PHASE 2 — Extraction JSON
    # ============================================
    def _extraire(self, historique_texte: str) -> ParametresEtude:
        """
        Lit la conversation et extrait les paramètres
        en JSON structuré.
        """
        print("\n⚙️  Extraction des paramètres...")

        prompt = PROMPT_EXTRACTION.format(
            historique=historique_texte
        )

        texte = self._appel_llm(prompt=prompt)

        if not texte:
            return ParametresEtude()

        try:
            data = json.loads(texte)
            parametres = ParametresEtude(
                objectif_etude=data.get("objectif_etude", ""),
                population_cible=data.get("population_cible", ""),
                type_enquete=data.get("type_enquete", "externe"),
                anonyme=data.get("anonyme", True),
                collecter_nom=data.get("collecter_nom", False),
                collecter_genre=data.get("collecter_genre", False),
                langue=data.get("langue", "fr"),
                themes=data.get("themes", []),
                nb_questions=data.get("nb_questions", 12)
            )
            print(f"✅ Paramètres extraits :")
            print(f"   • Objectif   : {parametres.objectif_etude}")
            print(f"   • Population : {parametres.population_cible}")
            print(f"   • Type       : {parametres.type_enquete}")
            print(f"   • Anonyme    : {parametres.anonyme}")
            print(f"   • Langue     : {parametres.langue}")
            print(f"   • Thèmes     : {parametres.themes}")
            print(f"   • Questions  : {parametres.nb_questions}")
            return parametres

        except json.JSONDecodeError as e:
            print(f"❌ Erreur parsing JSON extraction : {e}")
            print(f"   Réponse brute : {texte[:200]}")
            return ParametresEtude()

    # ============================================
    # PHASE 3 — Génération du questionnaire
    # ============================================
    def _generer(self, parametres: ParametresEtude) -> Questionnaire:
        """
        Génère le questionnaire complet basé
        sur les paramètres extraits.
        La durée est calculée par Python — jamais par le LLM.
        """
        print("\n⚙️  Génération du questionnaire...")

        prompt = PROMPT_GENERATION.format(
            objectif_etude=parametres.objectif_etude,
            population_cible=parametres.population_cible,
            type_enquete=parametres.type_enquete,
            anonyme=parametres.anonyme,
            langue=parametres.langue,
            themes=", ".join(parametres.themes),
            nb_questions=parametres.nb_questions,
            collecter_nom=parametres.collecter_nom,
            collecter_genre=parametres.collecter_genre
        )

        texte = self._appel_llm(prompt=prompt)

        if not texte:
            return Questionnaire(parametres=parametres)

        try:
            data = json.loads(texte)

            # Construire la liste de questions
            questions = []
            for q_data in data.get("questions", []):
                question = Question(
                    index=q_data.get("index", 0),
                    type=q_data.get("type", ""),
                    texte=q_data.get("texte", ""),
                    options=q_data.get("options", []),
                    role=q_data.get("role", ""),
                    theme=q_data.get("theme", ""),
                    obligatoire=q_data.get("obligatoire", True)
                )
                questions.append(question)

            # Construire le questionnaire
            questionnaire = Questionnaire(
                parametres=parametres,
                questions=questions,
                introduction=data.get("introduction", ""),
                nb_questions_total=data.get("nb_questions_total", 0)
            )

            # ← CALCUL DURÉE PAR PYTHON — jamais par le LLM
            questionnaire.duree_estimee_minutes = (
                questionnaire.calculer_duree()
            )

            print(f"✅ Questionnaire généré :")
            print(f"   • {questionnaire.nb_questions_total} questions")
            print(f"   • Durée calculée : "
                  f"{questionnaire.duree_estimee_minutes} min")
            return questionnaire

        except json.JSONDecodeError as e:
            print(f"❌ Erreur parsing JSON génération : {e}")
            print(f"   Réponse brute : {texte[:200]}")
            return Questionnaire(parametres=parametres)

    # ============================================
    # PHASE 4 — Validation
    # (spaCy complet ajouté dans validator.py — semaine 4)
    # ============================================
    def _valider(self, questionnaire: Questionnaire) -> Questionnaire:
        """
        Valide les biais dans les questions et
        vérifie la durée estimée.
        """
        print("\n⚙️  Validation des questions...")

        problemes = []
        alertes = []

        # ← ALERTE DURÉE — calculée par Python
        duree = questionnaire.duree_estimee_minutes
        if duree > 10:
            alertes.append(
                f"⏱️  ALERTE DURÉE : {duree} min estimées — "
                f"dépasse les 10 min recommandées. "
                f"Risque d'abandon élevé. "
                f"Suggérer de réduire à "
                f"{questionnaire.nb_questions_total - 2} questions."
            )

        # Validation linguistique basique de chaque question
        for q in questionnaire.questions:

            # Règle 1 — question trop courte
            if len(q.texte) < 10:
                problemes.append(
                    f"Q{q.index} trop courte : '{q.texte}'"
                )

            # Règle 2 — double négation simple
            if "ne" in q.texte.lower() and "pas" in q.texte.lower():
                problemes.append(
                    f"Q{q.index} — possible double négation détectée"
                )

            # Règle 3 — double question
            if q.texte.count("?") > 1:
                problemes.append(
                    f"Q{q.index} — double question détectée"
                )

        # Afficher les alertes durée
        if alertes:
            print(f"\n⚠️  ALERTES :")
            for a in alertes:
                print(f"   {a}")

        # Afficher les problèmes de biais
        if problemes:
            print(f"\n⚠️  {len(problemes)} problème(s) détecté(s) :")
            for p in problemes:
                print(f"   • {p}")
        else:
            print("✅ Questions validées — aucun problème détecté")

        questionnaire.valide = len(problemes) == 0
        return questionnaire

    # ============================================
    # PHASE 5 — Restitution au client
    # ============================================
    def _restituer(self, questionnaire: Questionnaire):
        """
        Présente le questionnaire final au client
        et demande validation.
        """
        print("\n" + "=" * 50)
        print("   PRÉSENTATION DE L'ENQUÊTE")
        print("=" * 50)

        prompt = PROMPT_RESTITUTION.format(
            questionnaire=json.dumps(
                questionnaire.to_dict(),
                ensure_ascii=False,
                indent=2
            ),
            duree=questionnaire.duree_estimee_minutes
        )

        texte = self._appel_llm(prompt=prompt)
        if texte:
            print(f"\n🤖 Agent: {texte}")

    # ============================================
    # RUN — Orchestre les 5 phases
    # ============================================
    def run(self) -> dict:
        """
        Lance l'agent complet.
        Retourne le JSON final à transmettre à Eya (Agent 1).
        """
        # Phase 1 — Dialogue
        historique_texte = self._dialogue()

        if not historique_texte:
            print("\n❌ Dialogue échoué — tous les modèles indisponibles.")
            return {}

        # Phase 2 — Extraction
        parametres = self._extraire(historique_texte)

        # Vérifier que les paramètres sont complets
        if not parametres.est_complet():
            print("\n❌ Informations insuffisantes.")
            print("   Relance l'agent et réponds à toutes les questions.")
            return {}

        # Phase 3 — Génération
        questionnaire = self._generer(parametres)

        # Phase 4 — Validation
        questionnaire = self._valider(questionnaire)

        # Phase 5 — Restitution
        self._restituer(questionnaire)

        # JSON final pour Eya
        json_final = questionnaire.to_dict()

        print("\n" + "=" * 50)
        print("   JSON FINAL → AGENT 1 (EYA)")
        print("=" * 50)
        print(json.dumps(json_final, ensure_ascii=False, indent=2))

        return json_final