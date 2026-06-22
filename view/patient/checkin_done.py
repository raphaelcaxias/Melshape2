"""Melshape — Check-in: tela de já feito hoje."""
import streamlit as st
from views.components.cards import metric_card

# ── JÁ FEZ CHECK-IN ──────────────────────────────────────────────────────────
def _tela_ja_feito(ci: dict, db, user: dict) -> None:
    streak = db.get_checkin_streak()

    st.markdown(
        f'<div class="metric-card fade-in" style="border-color:var(--success);">'
        f'<div style="font-size:2rem;margin-bottom:0.3rem;">✅</div>'
        f'<div style="font-weight:800;font-size:1.1rem;color:var(--success);">'
        f'Check-in feito hoje!</div>'
        f'<div style="font-size:0.84rem;color:var(--text-muted);margin-top:0.3rem;">'
        f'Sequência atual: <b style="color:var(--primary);">{streak} dias</b>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # Exibe resultado do Orchestrator se disponível
    result = st.session_state.get("ci_result")
    if result:
        render_resultado(result, user)
        if st.button("Limpar", key="ci_limpar_result"):
            st.session_state.pop("ci_result", None)
            st.rerun()
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card(str(ci.get("humor", "-")), "Humor", "😊")
        with c2:
            metric_card(str(ci.get("energia", "-")), "Energia", "⚡")
        with c3:
            metric_card(str(ci.get("qualidade_sono", "-")), "Sono", "😴")
