# Tale Agents — Pipeline IA d'Études

Projet de stage IA — Talecrafter · Plateforme Tale · 2026

## Stagiaires
- **Eya** — Agent Échantillonnage + Agent Rapport (LangGraph / HuggingFace)
- **Amal** — Agent Questionnaire + Agent Accompagnement (LLM API / spaCy)

## Stack technique
- Python 3.14
- LangGraph / CrewAI — orchestration multi-agents
- pandas / NumPy / SciPy / statsmodels — moteur statistique
- FastAPI + Celery + Redis — API REST
- PostgreSQL — base de données
- Docker + GitHub Actions — déploiement CI/CD

## Règle d'or
Les moteurs déterministes calculent. Le LLM narre. L'humain valide.

## Structure
tale-agents/
├── agent_echantillonnage/
├── agent_questionnaire/
├── agent_rapport/
├── agent_accompagnement/
├── orchestrateur/
├── api/
├── moteur_stat/
├── tests/
└── docs/