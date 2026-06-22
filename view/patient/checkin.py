"""
Melshape — Check-in Diário Unificado.

O ritual central do MelShape. Uma ação alimenta:
humor → energia → hábito do dia → pequena vitória →
→ Orchestrator → metas → jornada → XP → badge → notificação

Substitui a aba de check-in do register_hub.
"""
import streamlit as st
from datetime import date

from services.orchestrator import Orchestrator, OrchestratorResult
from views.components.cards import (
    section_header, metric_card, alert,
    show_new_achievements, xp_toast,
)
from views.patient.checkin_result import render_resultado
from views.patient.checkin_done import _tela_ja_feito


def render(services: dict, user: dict) -> None:
    db    = services["db"]
    orch  = services.get("orchestrator") or Orchestrator(db)

    section_header("✅ Check-in Diário", "Seu ritual de 30 segundos")

    # Verifica se já fez hoje
    ci_hoje = db.get_checkin_today()
    if ci_hoje:
        _tela_ja_feito(ci_hoje, db, user)
        return

    _form_checkin(db, orch, user)


# ── FORMULÁRIO ────────────────────────────────────────────────────────────────
def _form_checkin(db, orch: Orchestrator, user: dict) -> None:
    hm = user.get("health_mode", "general")

    st.markdown(
        '<div style="font-size:0.86rem;color:var(--text-muted);'
        'margin-bottom:1rem;">Como você está agora? '
        'Leva menos de 30 segundos.</div>',
        unsafe_allow_html=True,
    )

    # ── BLOCO 1: COMO ESTÁ ───────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        humor = st.select_slider(
            "😊 Humor",
            options=[1, 2, 3, 4, 5],
            value=3, key="ci_humor",
        )
    with col2:
        energia = st.select_slider(
            "⚡ Energia",
            options=[1, 2, 3, 4, 5],
            value=3, key="ci_energia",
        )

    sono = st.select_slider(
        "😴 Qualidade do sono",
        options=[1, 2, 3, 4, 5],
        value=3,
        format_func=lambda x: {
            1: "😖 Péssimo", 2: "😕 Ruim",
            3: "😐 Regular", 4: "🙂 Bom", 5: "😄 Ótimo",
        }[x],
        key="ci_sono",
    )

    # ── BLOCO 2: HÁBITO DO DIA ───────────────────────────────────────────────
    habitos = db.get_habitos()
    feitos  = db.get_registros_hoje()
    habito_id_sel = None

    if habitos:
        pendentes = [h for h in habitos if h.get("id") not in feitos]
        if pendentes:
            st.markdown(
                '<div style="margin-top:0.8rem;font-size:0.80rem;'
                'font-weight:600;color:var(--text-muted);">'
                '📋 Principal hábito de hoje</div>',
                unsafe_allow_html=True,
            )
            nomes = [
                f'{h.get("icone","")} {h.get("nome","")}'
                for h in pendentes
            ]
            idx = st.selectbox(
                "Hábito",
                range(len(nomes)),
                format_func=lambda i: nomes[i],
                key="ci_habito_idx",
                label_visibility="collapsed",
            )
            habito_id_sel = pendentes[idx].get("id")

    # ── BLOCO 3: PEQUENA VITÓRIA ──────────────────────────────────────────────
    st.markdown(
        '<div style="margin-top:0.8rem;font-size:0.80rem;'
        'font-weight:600;color:var(--text-muted);">'
        '🌟 Pequena vitória de hoje (opcional)</div>',
        unsafe_allow_html=True,
    )
    vitoria = st.text_input(
        "Vitória",
        placeholder="Ex: Tomei água antes do café, dormi antes das 23h...",
        key="ci_vitoria",
        label_visibility="collapsed",
    )

    # ── BLOCO 4: CONTEXTO DO PILAR ────────────────────────────────────────────
    dificuldade = ""
    if hm == "glp1":
        dificuldade = st.text_input(
            "💉 Algo sobre o tratamento hoje?",
            placeholder="Sintomas, dose, sensações...",
            key="ci_glp1_ctx",
        )
    elif hm == "bariatric":
        dificuldade = st.text_input(
            "🔪 Como está a alimentação hoje?",
            placeholder="Volume, tolerâncias, dificuldades...",
            key="ci_bar_ctx",
        )
    else:
        dificuldade = st.text_input(
            "Dificuldade ou observação (opcional)",
            placeholder="O que tornou hoje desafiador?",
            key="ci_dific",
        )

    # ── BOTÃO ────────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="margin-top:1rem;"></div>', unsafe_allow_html=True
    )
    if st.button(
        "✅ Fazer check-in",
        type="primary",
        use_container_width=True,
        key="ci_salvar",
    ):
        # 1. Salvar check-in na tabela checkins
        obs = " | ".join(filter(None, [vitoria, dificuldade]))
        ok  = db.save_checkin(humor, energia, float(sono), obs)

        if not ok:
            st.toast("Erro ao salvar check-in.", icon="❌")
            return

        # 2. Disparar Orchestrator com payload completo
        payload = {
            "humor":     humor,
            "energia":   energia,
            "sono":      sono,
            "habito_id": habito_id_sel,
            "vitoria":   vitoria,
        }
        result = orch.processar("checkin", user, payload)

        # 3. Feedback imediato
        st.toast(
            f"✅ Check-in feito! +{result.xp_ganho} XP",
            icon="🔥",
        )
        show_new_achievements(result.badges_novos)
        for _, msg in result.alertas:
            st.toast(msg, icon="⚠️")

        # 4. Persiste resultado na sessão para exibir tela de conclusão
        st.session_state["ci_result"] = result
        st.rerun()


