"""Melshape — Next Step: renderização do card."""
import streamlit as st
from typing import Optional, Dict, Any

# ── RENDERIZAÇÃO ─────────────────────────────────────────────────────────────
def _render_card(acao: Dict[str, Any], marco: Optional[Dict[str, str]],
                 profissional: Optional[str]) -> None:
    _COR = {
        "alta":  "var(--error)",
        "media": "var(--warning)",
        "baixa": "var(--info)",
        "ok":    "var(--success)",
    }
    cor = _COR.get(acao.get("urgencia", "ok"), "var(--border)")

    marco_html = ""
    if marco:
        marco_html = (
            f'<span style="font-size:0.74rem;color:var(--primary);'
            f'background:var(--primary-light);padding:0.15rem 0.6rem;'
            f'border-radius:9999px;border:1px solid var(--primary-border);'
            f'white-space:nowrap;">→ {marco["titulo"]}</span>'
        )

    pro_html = ""
    if profissional:
        pro_html = (
            f'<span style="font-size:0.76rem;color:var(--text-muted);">'
            f'👤 {profissional}</span>'
        )

    st.markdown(
        f'<div class="fade-in" style="background:var(--surface-2);'
        f'border-radius:var(--radius-lg);padding:0.75rem 1rem;'
        f'margin-bottom:1rem;border:1px solid var(--border);'
        f'border-left:4px solid {cor};">'
        f'<div style="display:flex;align-items:center;'
        f'justify-content:space-between;flex-wrap:wrap;gap:0.5rem;">'
        f'<div style="display:flex;align-items:center;gap:0.6rem;">'
        f'<span style="font-size:1.4rem;">{acao["icone"]}</span>'
        f'<div>'
        f'<div style="font-size:0.70rem;color:var(--text-faint);'
        f'font-weight:700;text-transform:uppercase;letter-spacing:0.06em;">'
        f'Próximo passo</div>'
        f'<div style="font-weight:700;font-size:0.92rem;color:var(--text);">'
        f'{acao["texto"]}</div>'
        f'</div></div>'
        f'<div style="display:flex;align-items:center;gap:0.6rem;'
        f'flex-wrap:wrap;">{pro_html}{marco_html}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    if acao.get("pagina"):
        if st.button(
            f'{acao["icone"]} Fazer agora',
            type="primary",
            use_container_width=True,
            key="next_step_cta",
        ):
            st.session_state.page = acao["pagina"]
            if acao.get("hub_tipo"):
                st.session_state.hub_tipo = acao["hub_tipo"]
            st.rerun()
