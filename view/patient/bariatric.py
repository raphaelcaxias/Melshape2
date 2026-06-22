"""
Melshape — Tela Pós-Bariátrica.

Para pacientes em acompanhamento após cirurgia bariátrica.
Fase atual calculada automaticamente por dias pós-cirurgia.
Suplementação obrigatória por fase. Alertas de volume e proteína.
"""
import streamlit as st

from services.bariatric_service import BariatricService
from views.components.cards import (
    section_header, empty_state, metric_card, alert,
)
from views.patient.bariatric_tabs import _tab_suplementos, _tab_historico
from views.patient.bariatric_forms import (
    render_form_cirurgia, render_form_fase,
)
import config


def render(services: dict, user: dict) -> None:
    db  = services["db"]
    svc = BariatricService(db)

    if not user.get("is_bariatric") and not db.get_cirurgia():
        _tela_cadastro(db, svc, user)
        return

    section_header(
        "🔪 Acompanhamento Pós-Bariátrica",
        "Cada fase exige atenção diferente — vamos juntos",
    )

    resumo = svc.resumo(user)

    # ── ALERTAS CLÍNICOS ─────────────────────────────────────────────────────
    for kind, msg in svc.alertas(resumo["fase_key"], user):
        alert(msg, kind)

    # ── BLOCO PRINCIPAL ───────────────────────────────────────────────────────
    _bloco_resumo(resumo)

    st.markdown(
        '<div style="border-top:1px solid var(--border);margin:0.8rem 0;"></div>',
        unsafe_allow_html=True,
    )

    tab_fase, tab_supl, tab_hist = st.tabs([
        "📋 Fase Atual",
        "💊 Suplementação",
        "📅 Histórico",
    ])

    with tab_fase:
        _tab_fase(resumo, db, svc, user)

    with tab_supl:
        _tab_suplementos(resumo)

    with tab_hist:
        _tab_historico(db, resumo)


# ── RESUMO ────────────────────────────────────────────────────────────────────
def _bloco_resumo(resumo: dict) -> None:
    fase  = resumo["fase"]
    prog  = resumo["progresso"]
    dias  = resumo["dias"]
    tipo  = resumo["tipo"]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="metric-card fade-in">'
            f'<div style="font-size:0.76rem;color:var(--text-muted);">Fase atual</div>'
            f'<div style="font-weight:800;font-size:1.1rem;color:var(--primary);">'
            f'{fase["nome"]}</div>'
            f'<div style="font-size:0.74rem;color:var(--text-muted);">'
            f'Dias {fase["dias"]} · Máx {fase["max_ml"]}ml · '
            f'{fase["max_cal"]} kcal</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        metric_card(
            f"{dias}d" if dias is not None else "—",
            "Dias pós-cirurgia", "📅",
        )
    with c3:
        metric_card(str(prog["pct"]) + "%", "Progresso (365d)", "🎯",
                    "success" if prog["pct"] >= 50 else "")

    # Barra de progresso rumo a 1 ano
    pct = prog["pct"]
    st.markdown(
        f'<div style="margin:0.6rem 0;">'
        f'<div class="progress-track">'
        f'<div class="progress-fill" style="width:{pct}%;"></div>'
        f'</div>'
        f'<div class="progress-meta">'
        f'<span>{dias or 0} dias</span><span>{pct}%</span>'
        f'<span>Meta: 365 dias</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div style="font-size:0.80rem;color:var(--text-muted);">'
        f'Cirurgia: <b>{tipo}</b></div>',
        unsafe_allow_html=True,
    )


# ── FASE ATUAL ────────────────────────────────────────────────────────────────
def _tab_fase(resumo: dict, db, svc: BariatricService,
               user: dict) -> None:
    fase     = resumo["fase"]
    fase_key = resumo["fase_key"]

    # Todas as fases como linha do tempo
    fases_ordem = ["liquid", "pasty", "soft", "solid", "maintenance"]
    for fk in fases_ordem:
        fd      = svc.fase_data(fk)
        atual   = fk == fase_key
        passada = fases_ordem.index(fk) < fases_ordem.index(fase_key)
        cor     = (
            "var(--primary)"  if atual
            else "var(--success)" if passada
            else "var(--border)"
        )
        icon    = "📍" if atual else "✅" if passada else "○"
        peso_txt= "font-weight:800;" if atual else ""

        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0.7rem;'
            f'padding:0.55rem 0.8rem;border:1px solid {cor};'
            f'border-radius:var(--radius-md);margin-bottom:0.4rem;'
            f'background:var(--surface);">'
            f'<span style="font-size:1.1rem;flex-shrink:0;">{icon}</span>'
            f'<div style="flex:1;">'
            f'<div style="{peso_txt}font-size:0.92rem;color:var(--text);">'
            f'{fd["nome"]}</div>'
            f'<div style="font-size:0.74rem;color:var(--text-muted);">'
            f'Dias {fd["dias"]} · Máx {fd["max_ml"]}ml · {fd["max_cal"]} kcal'
            f'</div></div>'
            f'{"<span style=font-size:0.72rem;color:var(--primary);font-weight:700;>ATUAL</span>" if atual else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("**Atualizar fase manualmente:**")
    render_form_fase(db, svc, resumo)


def _tela_cadastro(db, svc: BariatricService, user: dict) -> None:
    section_header(
        "🔪 Pós-Bariátrica",
        "Registre sua cirurgia para começar o acompanhamento",
    )
    alert(
        "Você ainda não cadastrou sua cirurgia. "
        "Preencha os dados abaixo para ativar o módulo bariátrico.",
        "info",
    )
    render_form_cirurgia(db, svc, user)
