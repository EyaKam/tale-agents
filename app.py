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
    .stApp { background: #f8f9fa; }
    .block-container { padding: 2rem 3rem; max-width: 900px; margin: auto; }

    /* Messages chat */
    .msg-agent {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0 14px 14px 14px;
        padding: 16px 20px;
        margin: 8px 0 8px 0;
        font-size: 0.88rem;
        color: #111;
        line-height: 1.6;
    }
    .msg-user {
        background: #ecfeff;
        border: 1px solid #a5f3fc;
        border-radius: 14px 0 14px 14px;
        padding: 12px 18px;
        margin: 8px 0 8px auto;
        font-size: 0.88rem;
        color: #0e7490;
        text-align: right;
        max-width: 70%;
        margin-left: auto;
    }

    /* Paliers */
    .palier-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 12px 0;
    }
    .palier-card {
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 12px;
        padding: 12px 16px;
        text-align: center;
        min-width: 110px;
        cursor: pointer;
        transition: all 0.15s;
    }
    .palier-card:hover { border-color: #06b6d4; }
    .palier-card .p-n { font-size: 1.1rem; font-weight: 700; color: #111; }
    .palier-card .p-marge { font-size: 0.72rem; color: #6b7280; margin-top: 2px; }
    .palier-card .p-prix { font-size: 0.72rem; color: #9ca3af; }

    /* Catégories */
    .cat-standard {
        background: white;
        border: 1.5px solid #e5e7eb;
        border-radius: 10px;
        padding: 12px 16px;
        margin: 4px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.85rem;
    }
    .cat-perso {
        background: #fffbeb;
        border: 1.5px solid #fcd34d;
        border-radius: 10px;
        padding: 12px 16px;
        margin: 4px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.85rem;
    }
    .badge-ins {
        background: #d1fae5;
        color: #065f46;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .badge-perso {
        background: #fef3c7;
        color: #92400e;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.7rem;
        font-weight: 600;
    }

    /* Résultat */
    .result-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 20px;
        margin: 8px 0;
    }
    .metric-inline {
        display: inline-block;
        background: #f9fafb;
        border-radius: 8px;
        padding: 8px 16px;
        margin: 4px;
        font-size: 0.85rem;
        text-align: center;
    }
    .metric-inline .val { font-size: 1.2rem; font-weight: 700; color: #111; }
    .metric-inline .lbl { font-size: 0.68rem; color: #9ca3af; text-transform: uppercase; }

    /* Alertes */
    .al-crit { background:#fef2f2; border-left:3px solid #ef4444; border-radius:0 8px 8px 0; padding:10px 14px; margin:4px 0; font-size:0.8rem; color:#991b1b; }
    .al-warn { background:#fffbeb; border-left:3px solid #f59e0b; border-radius:0 8px 8px 0; padding:10px 14px; margin:4px 0; font-size:0.8rem; color:#92400e; }
    .al-info { background:#f0f9ff; border-left:3px solid #06b6d4; border-radius:0 8px 8px 0; padding:10px 14px; margin:4px 0; font-size:0.8rem; color:#0c4a6e; }

    /* Header */
    .tale-header {
        background: white;
        border-bottom: 1px solid #e5e7eb;
        padding: 14px 0;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .tale-logo { font-size: 1.3rem; font-weight: 800; color: #06b6d4; }
    .tale-step { font-size: 0.78rem; color: #9ca3af; }

    /* Bouton reset */
    .stButton button { border-radius: 8px !important; }
    
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# Header
# ─────────────────────────────────────────
st.markdown("""
<div class='tale-header'>
    <div class='tale-logo'>✦ tale</div>
    <div class='tale-step'>Agent Échantillonnage · Targeting and Parameters</div>
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

    # Message d'accueil automatique
    accueil = message_accueil()
    st.session_state.messages.append({
        "role": "agent",
        "content": accueil["message"],
        "options": accueil.get("options"),
        "etape": "choix_n",
    })

# ─────────────────────────────────────────
# Affichage messages
# ─────────────────────────────────────────
col_chat, col_info = st.columns([2.5, 1])

with col_chat:
    for i, msg in enumerate(st.session_state.messages):

        # ── Message agent ──
        if msg["role"] == "agent":
            st.markdown(
                f"<div class='msg-agent'>{msg['content'].replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True
            )

            # Options paliers
            if msg.get("etape") == "choix_n" and st.session_state.etape == "choix_n":
                options = msg.get("options", [])
                # Paliers style Tale
                paliers_display = []
                for opt in options:
                    paliers_display.append(opt)

                cols = st.columns(len(paliers_display))
                for j, opt in enumerate(paliers_display):
                    with cols[j]:
                        n_val = opt["valeur"]
                        prix = n_val * 0.40
                        marge_val = _calculer_marge(n_val)
                        
                        # Badge marge en haut à droite du premier palier sélectionné
                        is_selected = st.session_state.n_choisi == n_val
                        
                        border_color = "#06b6d4" if is_selected else "#e5e7eb"
                        bg_color = "#f0fdfe" if is_selected else "white"
                        radio_inner = "<div style='width:10px;height:10px;border-radius:50%;background:#06b6d4;margin:auto;'></div>" if is_selected else ""
                        
                        if st.button(
                            f"{n_val}\n\n{prix:.0f},00 DT",
                            key=f"card_{n_val}_{i}",
                            use_container_width=True,
                        ):
                            st.session_state.n_choisi = n_val

                            st.session_state.messages.append({
                                "role": "user",
                                "content": f"Je choisis {n_val} répondants ({opt['marge']})",
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
                        
                        
                # Badge marge d'erreur globale
                if st.session_state.n_choisi:
                    n_sel = st.session_state.n_choisi
                    marge_sel = _calculer_marge(n_sel)
                    if marge_sel > 10:
                        st.markdown(
                            f"<div style='background:#fef2f2;border:1px solid #fca5a5;border-radius:20px;"
                            f"padding:6px 14px;font-size:0.78rem;color:#ef4444;display:inline-block;margin-top:8px;'>"
                            f"⚠️ {n_sel} : Margin of error > {marge_sel:.0f}%</div>",
                            unsafe_allow_html=True
                        )

                # Custom amount
                st.markdown("<br>", unsafe_allow_html=True)
                col_c1, col_c2 = st.columns([1, 2])
                with col_c1:
                    st.markdown("<span style='font-size:0.85rem;color:#374151;'>Custom amount:</span>", unsafe_allow_html=True)
                    custom = st.number_input(
                        "",
                        min_value=10,
                        max_value=10000,
                        value=st.session_state.n_choisi or 50,
                        step=10,
                        key=f"custom_{i}",
                        label_visibility="collapsed"
                    )
                with col_c2:
                    st.markdown(
                        f"<br><span style='font-size:0.85rem;color:#6b7280;'>"
                        f"Total: {(custom or 50) * 0.40:.2f} DT</span>",
                        unsafe_allow_html=True
                    )
                    if st.button("→ Utiliser ce montant", key=f"custom_btn_{i}"):
                        n_val = custom
                        st.session_state.n_choisi = n_val
                        st.session_state.messages.append({
                            "role": "user",
                            "content": f"Je choisis {n_val} répondants (montant personnalisé)",
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

            # Options catégories
            if msg.get("etape") == "choix_categories" and st.session_state.etape == "choix_categories":
                max_c = msg.get("max_criteres", 1)
                rec = msg.get("criteres_recommandes", [])

                st.markdown(f"Catégories Standard (référencées INS — max {max_c} critère(s))")
                for key, cat in CATEGORIES.items():
                    if cat["type"] == "standard":
                        est_rec = key in rec
                        est_sel = key in st.session_state.criteres_choisis
                        col1, col2, col3 = st.columns([0.4, 3.5, 1])
                        with col1:
                            checked = st.checkbox(
                                "",
                                value=est_sel,
                                key=f"cat_{key}_{i}",
                            )
                            if checked and key not in st.session_state.criteres_choisis:
                                if len([c for c in st.session_state.criteres_choisis
                                        if CATEGORIES.get(c, {}).get("type") == "standard"]) < max_c:
                                    st.session_state.criteres_choisis.append(key)
                                    st.rerun()
                            elif not checked and key in st.session_state.criteres_choisis:
                                st.session_state.criteres_choisis.remove(key)
                                st.rerun()
                        with col2:
                            rec_txt = " ⭐ recommandé" if est_rec else ""
                            cout_txt = f" · +{cat['cout_dt']} DT" if cat["cout_dt"] > 0 else " · gratuit"
                            st.markdown(
                                f"{cat['icone']} {cat['label']}"
                                f"<span style='color:#6b7280;font-size:0.78rem;'>{cout_txt}{rec_txt}</span>",
                                unsafe_allow_html=True
                            )
                        with col3:
                            st.markdown("<span class='badge-ins'>INS ✓</span>", unsafe_allow_html=True)

                st.markdown("Catégories Personnalisées (→ offre Personnalisée)")
                for key, cat in CATEGORIES.items():
                    if cat["type"] == "personnalise":
                        est_sel = key in st.session_state.criteres_choisis
                        col1, col2, col3 = st.columns([0.4, 3.5, 1])
                        with col1:
                            checked = st.checkbox("", value=est_sel, key=f"catp_{key}_{i}")
                            if checked and key not in st.session_state.criteres_choisis:
                                st.session_state.criteres_choisis.append(key)
                                st.rerun()
                            elif not checked and key in st.session_state.criteres_choisis:
                                st.session_state.criteres_choisis.remove(key)
                                st.rerun()
                        with col2:
                            cout_txt = f" · +{cat['cout_dt']} DT" if cat["cout_dt"] > 0 else ""
                            st.markdown(
                                f"{cat['icone']} {cat['label']}"
                                f"<span style='color:#92400e;font-size:0.78rem;'>{cout_txt}</span>",
                                unsafe_allow_html=True
                            )
                        with col3:
                            st.markdown("<span class='badge-perso'>Personnalisé</span>", unsafe_allow_html=True)

                # Résumé sélection
                std_sel = [c for c in st.session_state.criteres_choisis
                           if CATEGORIES.get(c, {}).get("type") == "standard"]
                perso_sel = [c for c in st.session_state.criteres_choisis
                             if CATEGORIES.get(c, {}).get("type") == "personnalise"]

                if st.session_state.criteres_choisis:
                    st.markdown(
                        f"Sélection actuelle : "
                        f"{', '.join([CATEGORIES[c]['label'] for c in st.session_state.criteres_choisis])}"
                    )
                    if len(std_sel) > max_c:
                        st.error(f"⚠️ Trop de critères standard ({len(std_sel)}/{max_c} max pour {st.session_state.n_choisi} répondants)")

                # Bouton analyser
                if st.button("🤖 Analyser avec le moteur statistique", type="primary", use_container_width=True):
                    if not st.session_state.criteres_choisis:
                        # Sans critères → analyse basique
                        criteres_envoyes = []
                    else:
                        criteres_envoyes = st.session_state.criteres_choisis

                    # Message utilisateur
                    if criteres_envoyes:
                        labels = [CATEGORIES[c]["label"] for c in criteres_envoyes]
                        st.session_state.messages.append({
                            "role": "user",
                            "content": f"Je sélectionne : {', '.join(labels)}",
                        })
                    else:
                        st.session_state.messages.append({
                            "role": "user",
                            "content": "Aucune catégorie — analyse sans critères de ciblage.",
                        })

                    # Moteur + LLM
                    with st.spinner("Moteur statistique en cours..."):
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

    # ── Bouton reset ──
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.etape in ["resultat", "personnalisee"]:
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("🔄 Nouvelle analyse", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        with col_r2:
            if st.session_state.etape == "resultat":
                r = st.session_state.resultat
                if r and r.get("risque") == "faible":
                    st.button("✅ Confirmer et lancer l'étude", type="primary", use_container_width=True)

# ─────────────────────────────────────────
# Panneau info (droite)
# ─────────────────────────────────────────
with col_info:
    st.markdown("📊 Récapitulatif")

    n = st.session_state.n_choisi
    criteres = st.session_state.criteres_choisis

    if n:
        marge = _calculer_marge(n)
        marge_color = "#ef4444" if marge > 10 else ("#f59e0b" if marge > 7 else "#10b981")
        st.markdown(f"""
        <div style='background:white;border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:12px;'>
            <div style='font-size:0.75rem;color:#9ca3af;text-transform:uppercase;'>Répondants</div>
            <div style='font-size:1.5rem;font-weight:700;color:#111;'>{n}</div>
            <div style='font-size:0.75rem;color:#9ca3af;margin-top:8px;text-transform:uppercase;'>Marge d'erreur</div>
            <div style='font-size:1.3rem;font-weight:700;color:{marge_color};'>±{marge:.1f}%</div>
            <div style='font-size:0.7rem;color:#9ca3af;margin-top:4px;'>Formule Ipsos/YouGov<br>ME = 1.96 × √(0.5×0.5/{n})</div>
        </div>
        """, unsafe_allow_html=True)

    if criteres:
        st.markdown("""
        <div style='background:white;border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:12px;'>
            <div style='font-size:0.75rem;color:#9ca3af;text-transform:uppercase;margin-bottom:8px;'>Critères sélectionnés</div>
        """, unsafe_allow_html=True)
        for c in criteres:
            cat = CATEGORIES.get(c, {})
            badge = "🟢 INS" if cat.get("type") == "standard" else "🟡 Personnalisé"
            st.markdown(
                f"<div style='font-size:0.82rem;padding:4px 0;border-bottom:1px solid #f3f4f6;'>"
                f"{cat.get('icone','')} {cat.get('label', c)} <span style='color:#9ca3af;font-size:0.7rem;'>{badge}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.resultat:
        r = st.session_state.resultat
        risque_color = {
            "faible": "#10b981",
            "modéré": "#f59e0b",
            "élevé": "#ef4444",
        }.get(r.get("risque", ""), "#9ca3af")

        st.markdown(f"""
        <div style='background:white;border:1px solid #e5e7eb;border-radius:12px;padding:16px;'>
            <div style='font-size:0.75rem;color:#9ca3af;text-transform:uppercase;margin-bottom:8px;'>Résultat</div>
            <div style='font-size:0.85rem;'>
                <div>Disponibilité : <b>{r.get('disponibilite', '—')}</b></div>
                <div>Risque : <b style='color:{risque_color};'>{r.get('risque', '—')}</b></div>
                <div>Confiance : <b>95%</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Légende
    st.markdown("""
    <div style='margin-top:16px;font-size:0.72rem;color:#9ca3af;line-height:1.6;'>
        <b>Légende cellules :</b><br>
        ✅ OK (ratio ≥ 1.5)<br>
        🟡 Fragile (ratio 1.0-1.5)<br>
        🔴 Critique (ratio < 1.0)<br><br>
        <b>Source :</b> INS Tunisie RGPH 2024<br>
        <b>Formule :</b> Ipsos/YouGov<br>
        ME = Z × √(p(1-p)/n)
    </div>
    """, unsafe_allow_html=True)