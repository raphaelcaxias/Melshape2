"""
Melshape — Tela de Hábitos.

O paciente vê seus hábitos do dia e marca com 1 clique.
Streak, aderência e calendário visual por hábito.
Cria hábitos padrão do pilar automaticamente na primeira vez.
"""
import streamlit as st

from services.habit_service import HabitService
from views.components.cards import (
    section_header, empty_state, metric_card,
    show_new_achievements, xp_toast, alert,
)
from views.patient.habits_detail import render_detalhe_habito
from views.patient.habits_form import _tab_novo
from views.patient.habits_suplementos import render_tab_suplementos
from views.patient.habits_treinos import render_tab_treinos

_CATEGORIAS = {
    "hidratacao":   ("💧", "Hidratação"),
    "nutricao":     ("🥩", "Nutrição"),
    "movimento":    ("🚶", "Movimento"),
    "treino":       ("🏋️", "Treino"),
    "sono":         ("😴", "Sono"),
    "registro":     ("✅", "Registro"),
    "suplementos":  ("💊", "Suplementos"),
    "saude":        ("🩺", "Saúde"),
    "medicamento":  ("💉", "Medicamento"),
    "alimentacao":  ("🍽️", "Alimentação"),
    "monitoramento":("📊", "Monitoramento"),
    "geral":        ("⭐", "Geral"),
}


def render(services: dict, user: dict) -> None:
    db   = services["db"]
    svc  = HabitService(db)
    gami = services["gamification"]
    hm   = user.get("health_mode", "general")

    section_header("📋 Hábitos", "Pequenas ações diárias que geram transformação")

    # Inicializa hábitos padrão se necessário
    criados = svc.inicializar_habitos_padrao(hm)
    if criados:
        st.toast(
            f"✨ {criados} hábitos do seu pilar foram criados!", icon="🎉"
        )

    habitos  = db.get_habitos()
    feitos_hoje = db.get_registros_hoje()

    # ── HEADER: ADERÊNCIA GERAL ───────────────────────────────────────────────
    if habitos:
        ader   = svc.aderencia_geral(days=7)
        total  = len(habitos)
        feitos = len(feitos_hoje)

        c1, c2, c3 = st.columns(3)
        with c1:
            cor = "success" if feitos == total else "warning" if feitos > 0 else ""
            metric_card(f"{feitos}/{total}", "Hábitos hoje", "✅", cor)
        with c2:
            cor2 = "success" if ader >= 80 else "warning" if ader >= 50 else "error"
            metric_card(f"{ader:.0f}%", "Aderência (7d)", "📊", cor2)
        with c3:
            streak_geral = _melhor_streak_geral(svc, habitos)
            metric_card(str(streak_geral), "Melhor streak", "🔥")

        if feitos == total and total > 0:
            alert("🎉 Todos os hábitos do dia concluídos!", "success")

    st.markdown(
        '<div style="border-top:1px solid var(--border);margin:0.8rem 0;"></div>',
        unsafe_allow_html=True,
    )

    # ── TABS ─────────────────────────────────────────────────────────────────
    tab_hoje, tab_detalhe, tab_novo, tab_supl, tab_treino = st.tabs([
        "📅 Hoje",
        "📈 Detalhe",
        "➕ Novo Hábito",
        "💊 Suplementos",
        "🏋️ Treinos",
    ])

    with tab_hoje:
        _tab_hoje(habitos, feitos_hoje, svc, gami, user)

    with tab_detalhe:
        _tab_detalhe(habitos, svc)

    with tab_novo:
        _tab_novo(db, svc, hm)

    with tab_supl:
        render_tab_suplementos(db, user)

    with tab_treino:
        render_tab_treinos(db, user, services)


from views.patient.habits_today import _tab_hoje, _tab_detalhe, _melhor_streak_geral
