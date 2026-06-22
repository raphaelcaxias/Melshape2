"""Melshape — Jornada: blocos de etapa atual e próximo passo."""
import streamlit as st
from services.journey_service import JourneyService

def _bloco_etapa_atual(prog: dict) -> None:
    st.markdown(
        '<p style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;'
        'color:var(--text-faint);text-transform:uppercase;margin-bottom:0.6rem;">'
        'Etapa Atual</p>',
        unsafe_allow_html=True,
    )
    etapa = prog["etapa_atual"]
    pct   = prog["pct_etapa"]
    ordem = etapa.get("ordem", 1)
    total = prog["total"]

    cor = (
        "success" if pct >= 80
        else "warning" if pct >= 40
        else ""
    )

    st.markdown(
        f'<div class="metric-card fade-in">'
        f'<div style="display:flex;align-items:center;gap:0.6rem;'
        f'margin-bottom:0.5rem;">'
        f'<span style="font-size:2rem;">{etapa.get("icone", "📍")}</span>'
        f'<div>'
        f'<div style="font-weight:800;font-size:1rem;color:var(--text);">'
        f'Etapa {ordem} de {total}</div>'
        f'<div style="font-size:0.85rem;color:var(--primary);font-weight:600;">'
        f'{etapa.get("nome", "")}</div>'
        f'</div>'
        f'</div>'
        f'<div style="font-size:0.83rem;color:var(--text-muted);'
        f'margin-bottom:0.6rem;">{etapa.get("descricao", "")}</div>'
        f'<div class="progress-track">'
        f'<div class="progress-fill {cor}" style="width:{pct}%;"></div>'
        f'</div>'
        f'<div class="progress-meta">'
        f'<span>Progresso da etapa</span><span>{pct}%</span>'
        f'<span>{"✅ Pronto para avançar!" if pct >= 100 else ""}</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Critérios da etapa
    criterios = etapa.get("criterios", [])
    if criterios:
        st.markdown(
            '<div style="font-size:0.78rem;color:var(--text-muted);'
            'margin-top:0.4rem;font-weight:600;">Critérios:</div>',
            unsafe_allow_html=True,
        )
        for c in criterios:
            st.markdown(
                f'<div style="font-size:0.80rem;color:var(--text-muted);'
                f'padding:0.15rem 0;">• {c}</div>',
                unsafe_allow_html=True,
            )


# ── PRÓXIMO PASSO ─────────────────────────────────────────────────────────────
def _bloco_proximo_passo(svc: JourneyService, prog: dict,
                          user: dict) -> None:
    st.markdown(
        '<p style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;'
        'color:var(--text-faint);text-transform:uppercase;margin-bottom:0.6rem;">'
        'Próximo Passo</p>',
        unsafe_allow_html=True,
    )
    passo = svc.proximo_passo(prog["etapa_atual"], user)

    cor_urgencia = {
        "alta":  ("error",   "🚨"),
        "media": ("warning", "⚡"),
        "baixa": ("info",    "💡"),
        "ok":    ("success", "✅"),
    }.get(passo["urgencia"], ("info", "💡"))

    st.markdown(
        f'<div class="metric-card fade-in">'
        f'<div style="font-size:2rem;margin-bottom:0.5rem;">'
        f'{passo["icone"]}</div>'
        f'<div style="font-weight:700;font-size:0.95rem;color:var(--text);'
        f'margin-bottom:0.8rem;">{passo["acao"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if passo.get("pagina"):
        if st.button(
            f"{passo['icone']} Fazer agora →",
            type="primary",
            use_container_width=True,
            key="jrn_proximo_passo",
        ):
            st.session_state.page = passo["pagina"]
            if passo.get("hub_tipo"):
                st.session_state.hub_tipo = passo["hub_tipo"]
            st.rerun()

    # Próxima etapa (preview)
    if prog.get("etapa_seguinte"):
        prox = prog["etapa_seguinte"]
        st.markdown(
            f'<div style="margin-top:0.8rem;padding:0.6rem;'
            f'background:var(--surface-2);border-radius:var(--radius-md);'
            f'font-size:0.80rem;">'
            f'<div style="color:var(--text-faint);font-size:0.72rem;'
            f'margin-bottom:0.2rem;">A seguir:</div>'
            f'<div style="font-weight:600;color:var(--text);">'
            f'{prox.get("icone","")} {prox.get("nome","")}</div>'
            f'<div style="color:var(--text-muted);font-size:0.78rem;">'
            f'{prox.get("descricao","")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


