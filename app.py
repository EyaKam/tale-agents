"""
Interface conversationnelle — Agent Échantillonnage Tale
"""

import streamlit as st
from agent_echantillonnage import message_accueil, apres_choix_n, apres_choix_categories
from agent_echantillonnage.base_donnees import CATEGORIES
from agent_echantillonnage.moteur import _calculer_marge

st.set_page_config(
    page_title="Tale · Agent Échantillonnage",
    page_icon="✦",
    layout="wide"
)

st.markdown("""
<style>
    #MainMenu, footer, header { visibility: hidden; }
    .stApp { background: #f5f6f8; }
    .block-container { padding: 2rem 3rem; max-width: 960px; margin: auto; }

    /* Header */
    .tale-header {
        background: white;
        border-bottom: 1px solid #e5e7eb;
        padding: 16px 0;
        margin-bottom: 28px;
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .tale-logo {
        font-size: 1.2rem;
        font-weight: 800;
        color: #06b6d4;
        letter-spacing: -0.5px;
    }
    .tale-sep { color: #e5e7eb; }
    .tale-step { font-size: 0.78rem; color: #9ca3af; }

    /* Bulles de conversation */
    .msg-agent {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 2px 16px 16px 16px;
        padding: 18px 22px;
        margin: 10px 0;
        font-size: 0.875rem;
        color: #1f2937;
        line-height: 1.7;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .msg-user {
        background: #ecfeff;
        border: 1px solid #cffafe;
        border-radius: 16px 2px 16px 16px;
        padding: 12px 18px;
        margin: 10px 0;
        font-size: 0.875rem;
        color: #0e7490;
        text-align: right;
        max-width: 65%;
        margin-left: auto;
    }

    /* Paliers — style carte Tale */
    .palier-wrap {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin: 16px 0 8px;
    }

    /* Badges */
    .badge-ins {
        background: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.68rem;
        font-weight: 600;
        white-space: nowrap;
    }
    .badge-perso {
        background: #fffbeb;
        color: #92400e;
        border: 1px solid #fde68a;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.68rem;
        font-weight: 600;
        white-space: nowrap;
    }

    /* Catégorie row */
    .cat-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #f3f4f6;
        font-size: 0.85rem;
        color: #1f2937;
    }
    .cat-label { display: flex; align-items: center; gap: 8px; }
    .cat-sub { font-size: 0.72rem; color: #9ca3af; margin-top: 1px; }

    /* Panneau info */
    .info-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .info-lbl {
        font-size: 0.68rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 4px;
    }
    .info-val {
        font-size: 1.5rem;
        font-weight: 700;
        color: #111;
    }
    .info-ref {
        font-size: 0.68rem;
        color: #9ca3af;
        margin-top: 2px;
    }

    /* Boutons streamlit */
    .stButton > button {
        border-radius: 8px !important;
        font-size: 0.82rem !important;
    }

    /* Séparateur section */
    .section-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin: 16px 0 8px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# Header
# ─────────────────────────────────────────
st.markdown("""
<div class='tale-header'>
    <div class='tale-logo'>✦ tale</div>
    <div class='tale-sep'>|</div>
    <div class='tale-step'>Agent Échantillonnage &nbsp;·&nbsp; Targeting and Parameters</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# State
# ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.etape = "choix_n"
    st.session_state.n_choisi = None
    st.session_state.criteres_choisis = []
    st.session_state.resultat = None
    st.session_state.max_criteres = 1

    accueil = message_accueil()
    st.session_state.messages.append({
        "role": "agent",
        "content": accueil["message"],
        "options": accueil.get("options"),
        "etape": "choix_n",
    })

# ─────────────────────────────────────────
# Layout
# ─────────────────────────────────────────
col_chat, col_info = st.columns([2.6, 1])

with col_chat:
    for i, msg in enumerate(st.session_state.messages):

        # ── Message agent ──
        if msg["role"] == "agent":
            st.markdown(
                f"<div class='msg-agent'>{msg['content'].replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True
            )

            # ── Étape 1 : Paliers ──
            if msg.get("etape") == "choix_n" and st.session_state.etape == "choix_n":
                options = msg.get("options", [])
                cols = st.columns(len(options))

                for j, opt in enumerate(options):
                    with cols[j]:
                        n_val = opt["valeur"]
                        prix = n_val * 0.40
                        marge_val = _calculer_marge(n_val)
                        is_sel = st.session_state.n_choisi == n_val

                        border = "2px solid #06b6d4" if is_sel else "1.5px solid #e5e7eb"
                        bg = "#f0fdfe" if is_sel else "white"
                        num_color = "#06b6d4" if is_sel else "#111"
                        dot = (
                            "<div style='width:8px;height:8px;border-radius:50%;"
                            "background:#06b6d4;margin:5px auto 0;'></div>"
                            if is_sel else
                            "<div style='width:8px;height:8px;border-radius:50%;"
                            "border:1.5px solid #d1d5db;margin:5px auto 0;'></div>"
                        )

                        st.markdown(f"""
                        <div style='border:{border};border-radius:12px;
                        background:{bg};padding:12px 6px;text-align:center;
                        margin-bottom:2px;transition:all 0.15s;'>
                            <div style='font-size:1.15rem;font-weight:700;
                            color:{num_color};'>{n_val}</div>
                            <div style='font-size:0.68rem;color:#9ca3af;
                            margin-top:2px;'>{prix:.0f},00 DT</div>
                            {dot}
                        </div>
                        """, unsafe_allow_html=True)

                        if st.button(
                            f"{n_val}",
                            key=f"p_{n_val}_{i}",
                            use_container_width=True,
                            help=f"{n_val} répondants — ±{marge_val:.1f}% marge d'erreur"
                        ):
                            st.session_state.n_choisi = n_val
                            st.session_state.messages.append({
                                "role": "user",
                                "content": f"{n_val} répondants · {prix:.0f} DT",
                            })
                            rep = apres_choix_n(n_val)
                            st.session_state.messages.append({
                                "role": "agent",
                                "content": rep["message"],
                                "options": rep.get("options"),
                                "etape": "choix_categories",
                                "max_criteres": rep["max_criteres"],
                                "criteres_recommandes": rep["criteres_recommandes"],
                            })
                            st.session_state.max_criteres = rep["max_criteres"]
                            st.session_state.etape = "choix_categories"
                            st.rerun()

                # Custom amount
                st.markdown("<br>", unsafe_allow_html=True)
                col_c1, col_c2, col_c3 = st.columns([1.2, 1.2, 1.6])
                with col_c1:
                    custom = st.number_input(
                        "Montant personnalisé",
                        min_value=10,
                        max_value=10000,
                        value=st.session_state.n_choisi or 50,
                        step=10,
                        key=f"custom_{i}",
                        label_visibility="visible"
                    )
                with col_c2:
                    st.markdown(
                        f"<br><span style='font-size:0.82rem;color:#6b7280;'>"
                        f"Total · {custom * 0.40:.2f} DT</span>",
                        unsafe_allow_html=True
                    )
                with col_c3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Utiliser ce montant", key=f"custom_btn_{i}"):
                        n_val = custom
                        st.session_state.n_choisi = n_val
                        st.session_state.messages.append({
                            "role": "user",
                            "content": f"{n_val} répondants (personnalisé)",
                        })
                        rep = apres_choix_n(n_val)
                        st.session_state.messages.append({
                            "role": "agent",
                            "content": rep["message"],
                            "options": rep.get("options"),
                            "etape": "choix_categories",
                            "max_criteres": rep["max_criteres"],
                            "criteres_recommandes": rep["criteres_recommandes"],
                        })
                        st.session_state.max_criteres = rep["max_criteres"]
                        st.session_state.etape = "choix_categories"
                        st.rerun()

            # ── Étape 2 : Catégories ──
            if msg.get("etape") == "choix_categories" and st.session_state.etape == "choix_categories":
                max_c = msg.get("max_criteres", 1)
                rec = msg.get("criteres_recommandes", [])

                # Standard
                st.markdown(
                    f"<div class='section-label'>Standard · INS Tunisie · max {max_c} critère(s)</div>",
                    unsafe_allow_html=True
                )
                for key, cat in CATEGORIES.items():
                    if cat["type"] != "standard":
                        continue
                    est_sel = key in st.session_state.criteres_choisis
                    est_rec = key in rec
                    nb_std = len([
                        c for c in st.session_state.criteres_choisis
                        if CATEGORIES.get(c, {}).get("type") == "standard"
                    ])
                    col1, col2 = st.columns([0.5, 9.5])
                    with col1:
                        checked = st.checkbox("", value=est_sel, key=f"cat_{key}_{i}")
                        if checked and key not in st.session_state.criteres_choisis:
                            if nb_std < max_c:
                                st.session_state.criteres_choisis.append(key)
                                st.rerun()
                        elif not checked and key in st.session_state.criteres_choisis:
                            st.session_state.criteres_choisis.remove(key)
                            st.rerun()
                    with col2:
                        cout_txt = f"+{cat['cout_dt']} DT" if cat["cout_dt"] > 0 else "gratuit"
                        rec_txt = " · recommandé" if est_rec else ""
                        st.markdown(f"""
                        <div class='cat-row'>
                            <div class='cat-label'>
                                <span>{cat['icone']}</span>
                                <div>
                                    <div>{cat['label']}</div>
                                    <div class='cat-sub'>{cout_txt}{rec_txt}</div>
                                </div>
                            </div>
                            <span class='badge-ins'>INS ✓</span>
                        </div>
                        """, unsafe_allow_html=True)

                # Personnalisé
                st.markdown(
                    "<div class='section-label' style='margin-top:20px;'>Personnalisé · offre dédiée</div>",
                    unsafe_allow_html=True
                )
                for key, cat in CATEGORIES.items():
                    if cat["type"] != "personnalise":
                        continue
                    est_sel = key in st.session_state.criteres_choisis
                    col1, col2 = st.columns([0.5, 9.5])
                    with col1:
                        checked = st.checkbox("", value=est_sel, key=f"catp_{key}_{i}")
                        if checked and key not in st.session_state.criteres_choisis:
                            st.session_state.criteres_choisis.append(key)
                            st.rerun()
                        elif not checked and key in st.session_state.criteres_choisis:
                            st.session_state.criteres_choisis.remove(key)
                            st.rerun()
                    with col2:
                        cout_txt = f"+{cat['cout_dt']} DT" if cat["cout_dt"] > 0 else ""
                        st.markdown(f"""
                        <div class='cat-row'>
                            <div class='cat-label'>
                                <span>{cat['icone']}</span>
                                <div>
                                    <div>{cat['label']}</div>
                                    <div class='cat-sub'>{cout_txt}</div>
                                </div>
                            </div>
                            <span class='badge-perso'>Personnalisé</span>
                        </div>
                        """, unsafe_allow_html=True)

                # Résumé
                if st.session_state.criteres_choisis:
                    labels_sel = [CATEGORIES[c]["label"] for c in st.session_state.criteres_choisis]
                    st.markdown(
                        f"<div style='font-size:0.8rem;color:#374151;margin-top:12px;'>"
                        f"Sélection · {' · '.join(labels_sel)}</div>",
                        unsafe_allow_html=True
                    )

                # Bouton analyser
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(
                    "Analyser le plan d'échantillonnage",
                    type="primary",
                    use_container_width=True,
                    key=f"analyser_{i}"
                ):
                    criteres_envoyes = st.session_state.criteres_choisis or []
                    label_msg = (
                        ' · '.join([CATEGORIES[c]["label"] for c in criteres_envoyes])
                        if criteres_envoyes else "aucune catégorie"
                    )
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"Catégories sélectionnées · {label_msg}",
                    })
                    with st.spinner("Calcul en cours..."):
                        rep = apres_choix_categories(
                            n=st.session_state.n_choisi,
                            criteres=criteres_envoyes,
                        )
                    st.session_state.messages.append({
                        "role": "agent",
                        "content": rep["message"],
                        "etape": rep["etape"],
                        "resultat": rep.get("resultat"),
                    })
                    st.session_state.resultat = rep.get("resultat")
                    st.session_state.etape = rep["etape"]
                    st.rerun()

        # ── Message utilisateur ──
        elif msg["role"] == "user":
            st.markdown(
                f"<div class='msg-user'>{msg['content']}</div>",
                unsafe_allow_html=True
            )

    # ── Boutons fin ──
    if st.session_state.etape in ["resultat", "personnalisee"]:
        st.markdown("<br>", unsafe_allow_html=True)
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("Nouvelle analyse", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        with col_r2:
            if st.session_state.etape == "resultat":
                st.button(
                    "Confirmer et lancer l'étude",
                    type="primary",
                    use_container_width=True
                )

# ─────────────────────────────────────────
# Panneau récapitulatif
# ─────────────────────────────────────────
with col_info:
    n = st.session_state.n_choisi
    criteres = st.session_state.criteres_choisis

    if n:
        marge = _calculer_marge(n)
        marge_color = "#10b981" if marge <= 5 else "#374151"
        st.markdown(f"""
        <div class='info-card'>
            <div class='info-lbl'>Répondants</div>
            <div class='info-val'>{n}</div>
            <div style='border-top:1px solid #f3f4f6;margin:12px 0;'></div>
            <div class='info-lbl'>Marge d'erreur</div>
            <div class='info-val' style='color:{marge_color};'>±{marge:.1f}%</div>
            <div class='info-ref'>Référence standard · ±5%</div>
        </div>
        """, unsafe_allow_html=True)

    if criteres:
        items = ""
        for c in criteres:
            cat = CATEGORIES.get(c, {})
            is_std = cat.get("type") == "standard"
            badge_bg = "#ecfdf5" if is_std else "#fffbeb"
            badge_color = "#065f46" if is_std else "#92400e"
            badge_border = "#a7f3d0" if is_std else "#fde68a"
            badge_txt = "INS ✓" if is_std else "Personnalisé"
            items += (
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;padding:6px 0;"
                f"border-bottom:1px solid #f3f4f6;font-size:0.78rem;'>"
                f"{cat.get('icone','')} {cat.get('label', c)}"
                f"<span style='background:{badge_bg};color:{badge_color};"
                f"border:1px solid {badge_border};border-radius:10px;"
                f"padding:1px 7px;font-size:0.62rem;'>{badge_txt}</span></div>"
            )
        st.markdown(f"""
        <div class='info-card'>
            <div class='info-lbl'>Catégories</div>
            <div style='margin-top:8px;'>{items}</div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.resultat:
        r = st.session_state.resultat
        st.markdown(f"""
        <div class='info-card'>
            <div class='info-lbl'>Résultat</div>
            <div style='font-size:0.82rem;line-height:1.9;margin-top:6px;'>
                <div>Disponibilité &nbsp;<b>{r.get('disponibilite', '—')}</b></div>
                <div>Confiance &nbsp;<b>95%</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='margin-top:8px;font-size:0.68rem;color:#9ca3af;line-height:1.8;'>
        INS Tunisie · RGPH 2024<br>
    </div>
    """, unsafe_allow_html=True)