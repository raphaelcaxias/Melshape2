"""
Melshape — Tela de Jornada do Paciente.

O paciente vê:
1. Em qual etapa da jornada está
2. O que já conquistou (marcos)
3. O próximo passo concreto e acionável
4. Linha do tempo de eventos

Importa: journey_timeline.py para a linha do tempo
"""
import streamlit as st

from services.journey_service import JourneyService
from views.components.cards import (
    section_header, empty_state, alert,
    show_new_achievements, metric_card,
)
from views.patient.journey_timeline import (
    _tab_todas_etapas,
    render_linha_do_tempo, render_marcos,
)

_MODE_LABELS = {
    "general":   ("⚖️", "Emagrecimento", "general"),
    "fitness":   ("💪", "Fitness",        "fitness"),
    "bariatric": ("🔪", "Pós-Bariátrica", "bariatric"),
    "glp1":      ("💉", "GLP-1",          "glp1"),
}


def render(services: dict, user: dict) -> None:
    db   = services["db"]
    svc  = JourneyService(db)

    hm          = user.get("health_mode", "general")
    icon_hm, label_hm, _ = _MODE_LABELS.get(hm, ("⚖️", "Geral", "general"))

    section_header(
        f"{icon_hm} Sua Jornada",
        f"Jornada {label_hm} — cada etapa é uma transformação real",
    )

    # Garante que jornada existe
    jornada = svc.garantir_jornada(user)
    if not jornada:
        empty_state(
            "🗺️", "Não foi possível carregar sua jornada",
            "Tente recarregar a página",
        )
        return

    jornada_id = jornada.get("id", "")
    prog       = svc.progresso_jornada(jornada_id, hm)

    # Marcos automáticos
    novos_marcos = svc.verificar_marcos_automaticos(jornada_id, user)
    if novos_marcos:
        for m in novos_marcos:
            st.toast(f"🏁 Marco alcançado: {m}", icon="🎉")

    # ── PROGRESSO GERAL ───────────────────────────────────────────────────────
    _bloco_progresso_geral(prog, jornada)

    st.markdown(
        '<div style="border-top:1px solid var(--border);margin:1.2rem 0;"></div>',
        unsafe_allow_html=True,
    )

    # ── ETAPA ATUAL + PRÓXIMO PASSO ───────────────────────────────────────────
    col_etapa, col_prox = st.columns([3, 2])

    with col_etapa:
        _bloco_etapa_atual(prog)

    with col_prox:
        _bloco_proximo_passo(svc, prog, user)

    st.markdown(
        '<div style="border-top:1px solid var(--border);margin:1.2rem 0;"></div>',
        unsafe_allow_html=True,
    )

    # ── TABS: TODAS AS ETAPAS / MARCOS / EVENTOS ──────────────────────────────
    tab_etapas, tab_marcos, tab_eventos, tab_historia = st.tabs([
        "📋 Todas as Etapas",
        "🏁 Marcos Alcançados",
        "📅 Linha do Tempo",
        "💛 Minha História",
    ])

    with tab_etapas:
        _tab_todas_etapas(prog)

    with tab_marcos:
        render_marcos(db, jornada_id)

    with tab_eventos:
        render_linha_do_tempo(db, jornada_id)

    with tab_historia:
        from views.patient.journey_story import render as render_story
        render_story(services, user)


# ── PROGRESSO GERAL ───────────────────────────────────────────────────────────
def _bloco_progresso_geral(prog: dict, jornada: dict) -> None:
    pct      = prog["pct_geral"]
    total    = prog["total"]
    concl    = len(prog["concluidas"])
    nome_j   = jornada.get("nome", "Minha Jornada")
    iniciada = jornada.get("iniciada_em", "")
    inicio_str = iniciada[:10] if iniciada else "—"

    st.markdown(
        f'<div class="metric-card fade-in">'
        f'<div style="display:flex;justify-content:space-between;'
        f'align-items:flex-start;margin-bottom:0.6rem;">'
        f'<div>'
        f'<div style="font-weight:800;font-size:1.05rem;color:var(--text);">'
        f'{nome_j}</div>'
        f'<div style="font-size:0.78rem;color:var(--text-muted);'
        f'margin-top:0.15rem;">Iniciada em {inicio_str}</div>'
        f'</div>'
        f'<div style="text-align:right;">'
        f'<div style="font-size:1.6rem;font-weight:800;color:var(--primary);">'
        f'{concl}/{total}</div>'
        f'<div style="font-size:0.74rem;color:var(--text-muted);">etapas</div>'
        f'</div>'
        f'</div>'
        f'<div class="progress-track">'
        f'<div class="progress-fill" style="width:{pct}%;"></div>'
        f'</div>'
        f'<div class="progress-meta">'
        f'<span>Progresso geral</span>'
        f'<span>{pct}%</span>'
        f'<span>{"🏆 Completo!" if pct == 100 else f"{total - concl} etapas restantes"}</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── ETAPA ATUAL ───────────────────────────────────────────────────────────────
from views.patient.journey_blocks import _bloco_etapa_atual, _bloco_proximo_passo
