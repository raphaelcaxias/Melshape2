"""
Melshape — Onboarding do Paciente.

4 passos em ~2 minutos:
  1. Escolha do pilar (general, fitness, bariatric, glp1)
  2. Dados pessoais (peso, altura, idade, gênero, objetivo)
  3. Por que você começou (salvo em motivos_jornada)
  4. Hábitos iniciais criados automaticamente

Regra: o paciente deve sentir que o sistema já o conhece
antes de chegar à home.
"""
import streamlit as st
import config
from views.components.cards import alert


_PILARES = {
    "general":   {
        "icon": "⚖️", "nome": "Emagrecimento",
        "desc": "Perda de peso com hábitos reais, sem restrições extremas.",
        "habitos": [
            ("Registrar refeições", "🍽️", "registro"),
            ("Beber 2L de água",    "💧", "hidratacao"),
            ("Check-in diário",    "✅", "registro"),
        ],
    },
    "fitness":   {
        "icon": "💪", "nome": "Fitness",
        "desc": "Composição corporal, proteína e performance.",
        "habitos": [
            ("Registrar treino",    "🏋️", "treino"),
            ("Meta proteica diária","🥩", "nutricao"),
            ("Check-in diário",    "✅", "registro"),
        ],
    },
    "bariatric": {
        "icon": "🔪", "nome": "Pós-Bariátrica",
        "desc": "Acompanhamento de fases, suplementação e exames.",
        "habitos": [
            ("Tomar suplementos",   "💊", "suplementos"),
            ("Controle de volume",  "🥄", "nutricao"),
            ("Check-in diário",    "✅", "registro"),
        ],
    },
    "glp1":      {
        "icon": "💉", "nome": "GLP-1",
        "desc": "Adesão ao tratamento, doses e sintomas.",
        "habitos": [
            ("Registrar dose",      "💉", "medicamento"),
            ("Proteína na refeição","🥩", "nutricao"),
            ("Check-in diário",    "✅", "registro"),
        ],
    },
}

_STEPS = ["Pilar", "Dados", "Porquê", "Hábitos"]


def render(services: dict, user: dict) -> None:
    db   = services["db"]
    step = st.session_state.get("onboarding_step", 1)

    # Barra de progresso
    pct = int((step - 1) / len(_STEPS) * 100)
    st.markdown(
        f'<div style="margin-bottom:1.5rem;">'
        f'<div style="display:flex;justify-content:space-between;'
        f'font-size:0.74rem;color:var(--text-muted);margin-bottom:0.3rem;">'
        f'<span>Passo {step} de {len(_STEPS)}: {_STEPS[step-1]}</span>'
        f'<span>{pct}%</span></div>'
        f'<div class="progress-track">'
        f'<div class="progress-fill" style="width:{pct}%;"></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    if step == 1:
        _step_pilar()
    elif step == 2:
        _step_dados(user)
    elif step == 3:
        _step_porque(db, user)
    elif step == 4:
        _step_habitos(db, user)



from views.patient.onboarding_steps import (
    _step_pilar, _step_dados, _step_porque, _step_habitos
)
