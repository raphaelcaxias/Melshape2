"""
Melshape — Home do Paciente (Reorganizada — Nível 5).

HIERARQUIA ABSOLUTA:
  1. Consistência (streak + check-in)
  2. Hábitos de Hoje
  3. Comportamento (check-in emocional)
  4. Consequências (calorias, proteína, água, peso)

Peso e calorias são consequências — nunca a primeira coisa que o paciente vê.
"""
import streamlit as st
from datetime import date
import random

from views.components.next_step import render_next_step
from views.patient.home_consistency import _bloco_consistencia, _historico_checkins
from views.patient.home_blocks import _bloco_xp, _bloco_desafio, _bloco_peso
from views.patient.home_helpers import _get_last_weight, _get_dashboard_paciente
from views.patient.home_context import render_contexto_pilar
from views.components.notification_inbox import exibir_notificacoes
from views.components.cards import (
    motivational_quote, alert, empty_state,
    achievement_card, show_new_achievements,
)
from services.contextualizer import ctx
import config

_MODE_LABELS = {
    "general":   ("⚖️", "Emagrecimento"),
    "fitness":   ("💪", "Fitness"),
    "bariatric": ("🔪", "Pós-Bariátrica"),
    "glp1":      ("💉", "GLP-1"),
}
_QUOTES = {
    "general":  [
        "Consistência bate perfeição todos os dias.",
        "Um dia de cada vez. Isso é tudo que precisa.",
        "Você não precisa ser extremo. Só precisa ser constante.",
    ],
    "fitness":  [
        "O corpo muda devagar. A disciplina muda rápido.",
        "Cada treino é uma promessa cumprida com você mesmo.",
    ],
    "bariatric":[
        "Cada refeição certa é uma vitória clínica real.",
        "Seu corpo está se reconstruindo. Respeite o processo.",
    ],
    "glp1":     [
        "O medicamento abre a porta. Você decide o que entra.",
        "Proteína primeiro. Sempre.",
    ],
}


def render(services: dict, user: dict) -> None:
    db    = services["db"]
    nutr  = services["nutrition"]
    gami  = services["gamification"]
    hm    = user.get("health_mode", "general")
    nome  = user.get("name", "").split()[0]
    icon_hm, _ = _MODE_LABELS.get(hm, ("⚖️", "Geral"))

    sm          = nutr.daily_summary()
    hydration   = db.get_hydration_today()
    checkin     = db.get_checkin_today()
    streak      = db.get_checkin_streak()
    stats       = gami.quick_stats()
    last_weight = _get_last_weight(db)
    dash_pac    = _get_dashboard_paciente(db)
    novos_ach   = gami.check_achievements(user)

    exibir_notificacoes(services, user)
    if novos_ach:
        show_new_achievements(novos_ach)

    # ── SAUDAÇÃO ──────────────────────────────────────────────────────────────
    turno = _turno()
    st.markdown(
        f'<div class="fade-in" style="margin-bottom:1rem;">'
        f'<h1 style="font-family:var(--font-display);font-weight:800;'
        f'font-size:1.7rem;color:var(--text);margin:0;">'
        f'{turno}, {nome} {icon_hm}</h1>'
        f'<p style="color:var(--text-muted);font-size:0.88rem;'
        f'margin:0.2rem 0 0;">{_data_br()}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── PRÓXIMO PASSO (Nível 4) ───────────────────────────────────────────────
    render_next_step(services, user)

    _div()

    # ── BLOCO 1: CONSISTÊNCIA ─────────────────────────────────────────────────
    _bloco_consistencia(streak, checkin, db, gami, user)

    _div()

    # ── BLOCO 2: HÁBITOS DE HOJE ──────────────────────────────────────────────
    _bloco_habitos_hoje(db, user)

    _div()

    # ── BLOCO 3: COMPORTAMENTO (check-in emocional) ───────────────────────────
    _bloco_comportamento(checkin)

    _div()

    # ── BLOCO 4: CONTEXTO DO PILAR ────────────────────────────────────────────
    render_contexto_pilar(services, user)

    _div()

    # ── BLOCO 5: CONSEQUÊNCIAS ────────────────────────────────────────────────
    _bloco_consequencias(sm, hydration, user, nutr, last_weight)

    _div()

    # ── BLOCO 6: GAMIFICAÇÃO + SCORE ─────────────────────────────────────────
    col_gami, col_desafio = st.columns([1, 1])
    with col_gami:
        _bloco_xp(stats, dash_pac)
    with col_desafio:
        _bloco_desafio(gami)

    _div()

    # ── BLOCO 7: SCORE NARRATIVO ──────────────────────────────────────────────
    _bloco_score(services, user)

    _div()

    # ── FRASE MOTIVACIONAL ────────────────────────────────────────────────────
    motivational_quote(random.choice(_QUOTES.get(hm, _QUOTES["general"])))

    # ── CTA CHECK-IN ─────────────────────────────────────────────────────────
    if not checkin:
        st.markdown('<div style="margin-top:0.8rem;"></div>',
                    unsafe_allow_html=True)
        alert(
            "Você ainda não fez o check-in de hoje. "
            "Leva menos de 30 segundos! ✅",
            "info",
        )
        if st.button("Fazer check-in agora →", type="primary",
                     use_container_width=True, key="home_checkin_cta"):
            st.session_state.page = "checkin"
            st.rerun()


from views.patient.home_daily import (
    _bloco_habitos_hoje, _bloco_comportamento,
    _bloco_consequencias, _bloco_score,
    _div, _turno, _data_br,
)
