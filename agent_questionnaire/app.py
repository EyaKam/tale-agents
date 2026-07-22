# app_streamlit.py
# Interface Streamlit pour tester l'Agent Questionnaire
# Lance avec : streamlit run app_streamlit.py

import streamlit as st
import json
import sys
import os

# ================================================
# CONFIG PAGE
# ================================================
st.set_page_config(
    page_title="Tale — Agent Questionnaire",
    page_icon="📋",
    layout="wide"
)

# ================================================
# CSS PERSONNALISÉ
# ================================================
st.markdown("""
<style>
    /* Palette Tale */
    :root {
        --tale-teal: #0F6E56;
        --tale-teal-light: #E1F5EE;
        --tale-coral: #C94F2C;
        --tale-coral-light: #FAECE7;
        --tale-amber: #BA7517;
        --tale-amber-light: #FAEEDA;
        --tale-gray: #F7F7F5;
        --tale-border: #E2E2DF;
    }

    /* Header */
    .tale-header {
        background: linear-gradient(135deg, #0F6E56, #1D9E75);
        color: white;
        padding: 24px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .tale-header h1 {
        margin: 0;
        font-size: 24px;
        font-weight: 600;
    }
    .tale-header p {
        margin: 4px 0 0 0;
        opacity: 0.85;
        font-size: 14px;
    }

    /* Bulles de chat */
    .chat-agent {
        background: var(--tale-teal-light);
        border-left: 3px solid var(--tale-teal);
        border-radius: 0 10px 10px 0;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 14px;
        color: #1a1a1a;
    }
    .chat-user {
        background: var(--tale-gray);
        border-left: 3px solid var(--tale-border);
        border-radius: 0 10px 10px 0;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 14px;
        color: #1a1a1a;
    }
    .chat-label-agent {
        font-size: 11px;
        font-weight: 600;
        color: var(--tale-teal);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .chat-label-user {
        font-size: 11px;
        font-weight: 600;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }

    /* Cartes résultat */
    .result-card {
        background: white;
        border: 1px solid var(--tale-border);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .result-card h4 {
        margin: 0 0 8px 0;
        font-size: 13px;
        color: #555;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Badge type question */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 500;
        margin-right: 4px;
    }
    .badge-screening { background: #FAECE7; color: #712B13; }
    .badge-principal { background: #E1F5EE; color: #085041; }
    .badge-verbatim  { background: #FAEEDA; color: #633806; }
    .badge-profilage { background: #EEEDFE; color: #3C3489; }
    .badge-likert    { background: #E6F1FB; color: #0C447C; }
    .badge-choice    { background: #F0F0EF; color: #444; }
    .badge-open      { background: #FEF9E7; color: #7D6608; }

    /* Alerte durée */
    .alerte-duree {
        background: #FCEBEB;
        border: 1px solid #F5A5A5;
        border-radius: 8px;
        padding: 12px 16px;
        color: #791F1F;
        font-size: 13px;
        margin-bottom: 12px;
    }
    .ok-duree {
        background: #E1F5EE;
        border: 1px solid #A8DCC9;
        border-radius: 8px;
        padding: 12px 16px;
        color: #085041;
        font-size: 13px;
        margin-bottom: 12px;
    }

    /* Barre de progression étapes */
    .step-bar {
        display: flex;
        gap: 8px;
        margin-bottom: 20px;
    }
    .step {
        flex: 1;
        height: 4px;
        border-radius: 2px;
        background: var(--tale-border);
    }
    .step.done { background: var(--tale-teal); }
    .step.active { background: var(--tale-amber); }

    /* Bouton principal */
    .stButton > button {
        background: #0F6E56 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    .stButton > button:hover {
        background: #0A5240 !important;
    }
</style>
""", unsafe_allow_html=True)

# ================================================
# INITIALISATION SESSION STATE
# ================================================
if "etape" not in st.session_state:
    st.session_state.etape = "dialogue"
if "historique" not in st.session_state:
    st.session_state.historique = []
if "parametres" not in st.session_state:
    st.session_state.parametres = None
if "introduction" not in st.session_state:
    st.session_state.introduction = ""
if "questionnaire" not in st.session_state:
    st.session_state.questionnaire = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "collecte_terminee" not in st.session_state:
    st.session_state.collecte_terminee = False

# ================================================
# IMPORTER L'AGENT
# ================================================
@st.cache_resource
def charger_agent():
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from agent import AgentQuestionnaire
        return AgentQuestionnaire()
    except Exception as e:
        st.error(f"Erreur chargement agent : {e}")
        return None

# ================================================
# HEADER
# ================================================
st.markdown("""
<div class="tale-header">
    <h1>📋 Agent Questionnaire — Tale</h1>
    <p>Créez votre enquête en quelques minutes grâce à l'IA</p>
</div>
""", unsafe_allow_html=True)

# ================================================
# BARRE D'ÉTAPES
# ================================================
etapes = ["dialogue", "introduction", "generation", "resultat"]
idx_actuel = etapes.index(st.session_state.etape) if st.session_state.etape in etapes else 0

cols_steps = st.columns(4)
labels = ["💬 Dialogue", "📝 Introduction", "⚙️ Génération", "✅ Résultat"]
for i, (col, label) in enumerate(zip(cols_steps, labels)):
    with col:
        if i < idx_actuel:
            st.success(label)
        elif i == idx_actuel:
            st.info(label)
        else:
            st.empty()

st.divider()

# ================================================
# ÉTAPE 1 — DIALOGUE
# ================================================
if st.session_state.etape == "dialogue":

    st.subheader("💬 Définissons votre enquête")

    agent = charger_agent()

    # Afficher l'historique de conversation
    for msg in st.session_state.historique:
        if msg["role"] == "agent":
            st.markdown(f"""
            <div class="chat-label-agent">🤖 Agent Tale</div>
            <div class="chat-agent">{msg["content"]}</div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-label-user">👤 Vous</div>
            <div class="chat-user">{msg["content"]}</div>
            """, unsafe_allow_html=True)

    # Premier message d'accueil
    if len(st.session_state.historique) == 0 and agent:
        with st.spinner("Connexion à l'agent..."):
            try:
                from prompts import PROMPT_ACCUEIL
                from google.genai import types

                response = agent._appel_llm(
                    prompt="Bonjour, je veux créer une enquête",
                    system=PROMPT_ACCUEIL
                )
                if response:
                    st.session_state.historique.append({
                        "role": "agent",
                        "content": response
                    })
                    st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")

    # Vérifier si collecte terminée
    if st.session_state.historique:
        dernier = st.session_state.historique[-1]
        if (dernier["role"] == "agent" and
                "toutes les informations" in dernier["content"].lower()):
            st.session_state.collecte_terminee = True

    # Input utilisateur
    if not st.session_state.collecte_terminee:
        with st.form("form_dialogue", clear_on_submit=True):
            user_input = st.text_input(
                "Votre réponse :",
                placeholder="Tapez votre réponse ici...",
                label_visibility="collapsed"
            )
            envoyer = st.form_submit_button("Envoyer →")

        if envoyer and user_input and agent:
            st.session_state.historique.append({
                "role": "user",
                "content": user_input
            })

            with st.spinner("Agent en train de répondre..."):
                try:
                    from prompts import PROMPT_ACCUEIL
                    contexte = "\n".join([
                        f"{'AGENT' if m['role']=='agent' else 'CLIENT'}: {m['content']}"
                        for m in st.session_state.historique
                    ])
                    prompt_ctx = f"{contexte}\nAGENT:"

                    response = agent._appel_llm(
                        prompt=prompt_ctx,
                        system=PROMPT_ACCUEIL
                    )
                    if response:
                        st.session_state.historique.append({
                            "role": "agent",
                            "content": response
                        })
                except Exception as e:
                    st.error(f"Erreur : {e}")

            st.rerun()

    # Bouton continuer quand collecte terminée
    if st.session_state.collecte_terminee:
        st.success("✅ Toutes les informations collectées !")
        if st.button("Continuer → Générer l'introduction", type="primary"):

            # Extraire les paramètres
            agent = charger_agent()
            historique_texte = "\n".join([
                f"{'AGENT' if m['role']=='agent' else 'CLIENT'}: {m['content']}"
                for m in st.session_state.historique
            ])

            with st.spinner("Extraction des paramètres..."):
                try:
                    parametres = agent._extraire(historique_texte)
                    st.session_state.parametres = parametres
                    st.session_state.agent = agent
                    st.session_state.etape = "introduction"
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur extraction : {e}")

# ================================================
# ÉTAPE 2 — INTRODUCTION
# ================================================
elif st.session_state.etape == "introduction":

    st.subheader("📝 Introduction du questionnaire")
    st.caption("L'agent propose une introduction — vous pouvez la valider ou la modifier.")

    agent = st.session_state.agent
    parametres = st.session_state.parametres

    # Générer introduction si pas encore fait
    if not st.session_state.introduction:
        with st.spinner("Génération de l'introduction..."):
            try:
                from prompts import PROMPT_INTRODUCTION
                prompt = PROMPT_INTRODUCTION.format(
                    objectif_etude=parametres.objectif_etude,
                    population_cible=parametres.population_cible,
                    type_enquete=parametres.type_enquete,
                    anonyme=parametres.anonyme,
                    langue=parametres.langue
                )
                intro = agent._appel_llm(prompt=prompt)
                st.session_state.introduction = intro
                st.rerun()
            except Exception as e:
                st.error(f"Erreur génération introduction : {e}")

    if st.session_state.introduction:

        # Afficher l'introduction générée
        st.markdown("**Proposition de l'agent :**")
        introduction_modifiee = st.text_area(
            "Introduction",
            value=st.session_state.introduction,
            height=200,
            label_visibility="collapsed"
        )
        st.session_state.introduction = introduction_modifiee

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Régénérer une nouvelle version"):
                st.session_state.introduction = ""
                st.rerun()
        with col2:
            if st.button("✅ Valider et générer le questionnaire", type="primary"):
                st.session_state.etape = "generation"
                st.rerun()

# ================================================
# ÉTAPE 3 — GÉNÉRATION
# ================================================
elif st.session_state.etape == "generation":

    st.subheader("⚙️ Génération du questionnaire en cours...")

    agent = st.session_state.agent
    parametres = st.session_state.parametres

    if st.session_state.questionnaire is None:
        with st.spinner("Le LLM génère vos questions..."):
            try:
                questionnaire = agent._generer(parametres)
                questionnaire.introduction = st.session_state.introduction
                questionnaire = agent._valider(questionnaire)
                st.session_state.questionnaire = questionnaire
                st.session_state.etape = "resultat"
                st.rerun()
            except Exception as e:
                st.error(f"Erreur génération : {e}")
                if st.button("← Retour"):
                    st.session_state.etape = "introduction"
                    st.rerun()

# ================================================
# ÉTAPE 4 — RÉSULTAT
# ================================================
elif st.session_state.etape == "resultat":

    q = st.session_state.questionnaire
    p = st.session_state.parametres

    st.subheader("✅ Votre enquête est prête !")

    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Questions", q.nb_questions_total)
    col2.metric("Durée estimée", f"{q.duree_estimee_minutes} min")
    col3.metric("Langue", p.langue.upper())
    col4.metric("Type", p.type_enquete.capitalize())

    # Alerte durée
    if q.duree_estimee_minutes > 10:
        st.markdown(f"""
        <div class="alerte-duree">
        ⏱️ <strong>Alerte durée</strong> — {q.duree_estimee_minutes} min estimées,
        au-dessus des 10 min recommandées.
        Risque d'abandon élevé. Envisagez de réduire à
        {q.nb_questions_total - 2} questions.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="ok-duree">
        ✅ <strong>Durée optimale</strong> — {q.duree_estimee_minutes} min,
        dans la fenêtre recommandée (≤ 10 min).
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 Questionnaire", "📊 Structure", "🔗 JSON pour Eya"])

    # TAB 1 — Questionnaire lisible
    with tab1:

        # Introduction
        if q.introduction:
            st.markdown("### 📄 Introduction")
            st.info(q.introduction)
            st.divider()

        # Questions
        st.markdown("### ❓ Questions")
        badges_role = {
            "screening": "badge-screening",
            "principal":  "badge-principal",
            "verbatim":   "badge-verbatim",
            "profilage":  "badge-profilage"
        }
        badges_type = {
            "likert_5":       ("badge-likert", "Likert 1-5"),
            "single_choice":  ("badge-choice", "Choix unique"),
            "multiple_choice":("badge-choice", "Choix multiple"),
            "open_text":      ("badge-open",   "Texte libre")
        }

        for question in q.questions:
            role_class = badges_role.get(question.role, "badge-choice")
            type_class, type_label = badges_type.get(
                question.type, ("badge-choice", question.type)
            )

            with st.expander(
                f"Q{question.index} — {question.texte[:60]}...",
                expanded=True
            ):
                st.markdown(f"""
                <span class="badge {role_class}">{question.role}</span>
                <span class="badge {type_class}">{type_label}</span>
                {"<span class='badge' style='background:#FFEBCC;color:#7A4400'>Obligatoire</span>" if question.obligatoire else ""}
                """, unsafe_allow_html=True)

                st.markdown(f"**{question.texte}**")

                if question.options:
                    for opt in question.options:
                        st.markdown(f"○ {opt}")

    # TAB 2 — Structure
    with tab2:
        st.markdown("### 📊 Répartition par rôle")

        roles = {}
        types = {}
        for question in q.questions:
            roles[question.role] = roles.get(question.role, 0) + 1
            types[question.type] = types.get(question.type, 0) + 1

        col_r, col_t = st.columns(2)
        with col_r:
            st.markdown("**Par rôle :**")
            for role, count in roles.items():
                st.markdown(f"- **{role}** : {count} question(s)")
        with col_t:
            st.markdown("**Par type :**")
            for typ, count in types.items():
                st.markdown(f"- **{typ}** : {count} question(s)")

        st.divider()
        st.markdown("### 📋 Paramètres extraits")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown(f"**Objectif :** {p.objectif_etude}")
            st.markdown(f"**Population :** {p.population_cible}")
            st.markdown(f"**Type :** {p.type_enquete}")
            st.markdown(f"**Anonyme :** {'Oui ✅' if p.anonyme else 'Non ❌'}")
        with col_p2:
            st.markdown(f"**Langue :** {p.langue}")
            st.markdown(f"**Thèmes :** {', '.join(p.themes)}")

    # TAB 3 — JSON pour Eya
    with tab3:
        st.markdown("### 🔗 JSON transmis à l'Agent 1 (Eya)")
        st.caption("Ce JSON sera transmis automatiquement à l'Agent Échantillonnage.")
        json_final = q.to_dict()
        st.json(json_final)

        # Bouton télécharger
        st.download_button(
            label="⬇️ Télécharger le JSON",
            data=json.dumps(json_final, ensure_ascii=False, indent=2),
            file_name="questionnaire_tale.json",
            mime="application/json"
        )

    st.divider()

    # Bouton recommencer
    if st.button("🔄 Créer une nouvelle enquête"):
        for key in ["etape", "historique", "parametres", "introduction",
                    "questionnaire", "agent", "collecte_terminee"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()