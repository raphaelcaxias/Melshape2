"""
Melshape — Hub de Registro: formulários rápidos.
Água e Check-in diário.
Importado por register_hub.py.
"""
import streamlit as st
from datetime import date

from views.components.cards import (
    metric_card, show_new_achievements, xp_toast, alert,
)
import config


# ── ÁGUA ──────────────────────────────────────────────────────────────────────
def _form_agua(db, gami) -> None:
    st.markdown("#### 💧 Registrar Água")

    atual = db.get_hydration_today()
    meta  = config.HYDRATION_GOAL_ML
    pct   = min(100, int(atual / meta * 100)) if meta else 0

    st.markdown(
        f'<div class="metric-card fade-in" style="margin-bottom:0.8rem;">'
        f'<div style="font-size:1.4rem;font-weight:800;color:var(--info);">'
        f'{atual} ml</div>'
        f'<div style="font-size:0.80rem;color:var(--text-muted);">'
        f'de {meta} ml ({pct}%)</div>'
        f'<div class="progress-wrap" style="margin-top:0.5rem;">'
        f'<div class="progress-track"><div class="progress-fill" '
        f'style="width:{pct}%;background:var(--info);"></div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # Adição rápida em 1 clique
    from core.models import QUICK_ADD_ML
    st.markdown("**Adicionar rápido:**")
    cols = st.columns(4)
    for i, ml in enumerate(QUICK_ADD_ML):
        with cols[i]:
            if st.button(f"+{ml}ml", key=f"hub_agua_{ml}",
                         use_container_width=True):
                _registrar_agua(db, gami, ml)

    st.markdown(
        '<div style="border-top:1px solid var(--border);margin:0.6rem 0;"></div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        qtd_custom = st.number_input(
            "Quantidade personalizada (ml)",
            min_value=50, max_value=2000, value=200, step=50,
            key="hub_agua_custom",
        )
    with col2:
        fonte = st.selectbox(
            "Fonte",
            ["water", "juice", "tea", "other"],
            format_func=lambda x: {
                "water": "💧 Água", "juice": "🍊 Suco",
                "tea": "🍵 Chá", "other": "🥤 Outro",
            }.get(x, x),
            key="hub_agua_fonte",
        )

    if st.button("✅ Registrar", type="primary",
                 use_container_width=True, key="hub_save_agua"):
        _registrar_agua(db, gami, qtd_custom, fonte)


def _registrar_agua(db, gami, ml: int, fonte: str = "water",
                    services: dict = None, user: dict = None) -> None:
    from core.models import HydrationLog
    ok = db.save_hydration(HydrationLog(amount_ml=ml, source=fonte))
    if ok:
        st.toast(f"💧 +{ml}ml registrado!", icon="✅")
        if services and user:
            from services.orchestrator import Orchestrator
            orch   = services.get("orchestrator") or Orchestrator(db)
            result = orch.processar("agua", user, {"ml": ml})
            if result.xp_ganho:
                xp_toast(result.xp_ganho, "hidratação")
            show_new_achievements(result.badges_novos)
        else:
            novo_total = db.get_hydration_today()
            if novo_total >= config.HYDRATION_GOAL_ML:
                db.add_xp(30, "meta_agua")
                xp_toast(30, "meta de água atingida")
        st.rerun()
    else:
        st.toast("Erro ao registrar água.", icon="❌")


# ── CHECK-IN ──────────────────────────────────────────────────────────────────
def _form_checkin(db, gami) -> None:
    st.markdown("#### ✅ Check-in Diário")

    checkin_hoje = db.get_checkin_today()
    if checkin_hoje:
        st.markdown(
            '<div class="alert-success">✅ Check-in já realizado hoje!</div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        with c1: metric_card(str(checkin_hoje.get("humor", "-")),
                              "Humor", "😊")
        with c2: metric_card(str(checkin_hoje.get("energia", "-")),
                              "Energia", "⚡")
        with c3: metric_card(str(checkin_hoje.get("qualidade_sono", "-")),
                              "Sono (h)", "😴")
        return

    st.markdown(
        '<div style="font-size:0.86rem;color:var(--text-muted);'
        'margin-bottom:0.8rem;">'
        'Como você está hoje? (1 = péssimo · 5 = ótimo)</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        humor = st.select_slider(
            "😊 Humor", options=[1, 2, 3, 4, 5], value=3, key="hub_humor",
        )
    with col2:
        energia = st.select_slider(
            "⚡ Energia", options=[1, 2, 3, 4, 5], value=3, key="hub_energia",
        )
    with col3:
        sono = st.select_slider(
            "😴 Sono (h)",
            options=[4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            value=7.0, key="hub_sono",
        )

    obs = st.text_area(
        "Algo a destacar? (opcional)", key="hub_ci_obs", height=70,
        placeholder="Como foi o dia, treino, refeições...",
    )

    if st.button("✅ Fazer check-in", type="primary",
                 use_container_width=True, key="hub_save_checkin"):
        ok = db.save_checkin(humor, energia, float(sono), obs)
        if ok:
            streak = db.get_checkin_streak()
            st.toast(f"✅ Check-in feito! Sequência: {streak} dias", icon="🔥")
            db.xp_checkin()
            xp_toast(20, "check-in diário")
            novos = gami.check_achievements()
            show_new_achievements(novos)
            st.rerun()
        else:
            st.toast("Erro ao salvar check-in.", icon="❌")
