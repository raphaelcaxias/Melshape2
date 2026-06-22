"""
Melshape — Dashboard Executivo.

Para gestores e clínicas. Responde:
- Quantos pacientes estamos retendo?
- Qual pilar tem melhor aderência?
- Quais profissionais têm mais impacto?
- Onde estão os riscos?

Usa: vw_resumo_executivo, vw_prioridade_intervencao,
     vw_campeoes_transformacao, vw_estagnacao_clinica
"""
import streamlit as st
from views.components.cards import (
    section_header, metric_card, empty_state, alert,
)


def render(services: dict) -> None:
    db = services["db"]

    section_header(
        "🏥 Dashboard Executivo",
        "Visão estratégica da clínica",
    )

    tab_visao, tab_retencao, tab_profissionais, tab_campeoes = st.tabs([
        "📊 Visão Geral",
        "🔄 Retenção",
        "👨‍⚕️ Profissionais",
        "🏆 Campeões",
    ])

    with tab_visao:
        _tab_visao_geral(db)

    with tab_retencao:
        _tab_retencao(db)

    with tab_profissionais:
        _tab_profissionais(db)

    with tab_campeoes:
        _tab_campeoes(db)


# ── TAB 1: VISÃO GERAL ────────────────────────────────────────────────────────
def _tab_visao_geral(db) -> None:
    resumo = _query(db, "vw_resumo_executivo",
                    "total_pacientes, aderencia_media, consistencia_media, "
                    "risco_abandono_medio, receita_mensal, pacientes_ativos")

    if not resumo:
        _mock_visao_geral(db)
        return

    row = resumo[0]
    total   = int(row.get("total_pacientes",    0))
    ativos  = int(row.get("pacientes_ativos",   0))
    ader    = float(row.get("aderencia_media",  0))
    consist = float(row.get("consistencia_media", 0))
    risco   = float(row.get("risco_abandono_medio", 0))
    receita = float(row.get("receita_mensal",   0))

    pct_ativos = round(ativos / total * 100) if total else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card(str(total), "Total de Pacientes", "👥")
    with c2:
        cor = "success" if pct_ativos >= 70 else "warning"
        metric_card(f"{ativos} ({pct_ativos}%)",
                    "Pacientes Ativos (7d)", "✅", cor)
    with c3:
        cor = "success" if ader >= 70 else "warning" if ader >= 50 else "error"
        metric_card(f"{ader:.0f}%", "Aderência Média", "📋", cor)
    with c4:
        cor = "error" if risco >= 50 else "warning" if risco >= 30 else "success"
        metric_card(f"{risco:.0f}%", "Risco de Abandono", "⚠️", cor)

    # Receita estimada
    if receita > 0:
        st.markdown("---")
        st.markdown(
            f'<div class="metric-card fade-in" style="text-align:center;">'
            f'<div style="font-size:0.74rem;color:var(--text-muted);'
            f'text-transform:uppercase;letter-spacing:0.08em;">'
            f'Receita Estimada/Mês</div>'
            f'<div style="font-size:2rem;font-weight:800;color:var(--primary);">'
            f'R$ {receita:,.2f}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Distribuição por pilar
    st.markdown("---")
    st.markdown("##### 🗺️ Distribuição por Pilar")
    _grafico_pilares(db)

    # Consistência média
    st.markdown("---")
    st.markdown(
        f'<div class="metric-card fade-in">'
        f'<div style="display:flex;justify-content:space-between;'
        f'align-items:center;margin-bottom:0.5rem;">'
        f'<span style="font-weight:600;">Consistência Média da Clínica</span>'
        f'<span style="font-weight:800;font-size:1.2rem;color:var(--primary);">'
        f'{consist:.0f}%</span>'
        f'</div>'
        f'<div class="progress-track">'
        f'<div class="progress-fill" '
        f'style="width:{consist}%;"></div>'
        f'</div>'
        f'<div style="font-size:0.78rem;color:var(--text-muted);margin-top:0.4rem;">'
        f'{"✅ Consistência saudável" if consist >= 70 else "⚠️ Abaixo do esperado — revisar estratégias"}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _mock_visao_geral(db) -> None:
    """Fallback quando vw_resumo_executivo não retorna dados."""
    pacientes = _query(db, "perfis",
                       "id, tipo_jornada", limit=200)
    total = len(pacientes)
    if total == 0:
        empty_state("🏥", "Nenhum paciente cadastrado ainda",
                    "Os dados aparecerão conforme os pacientes usam o sistema")
        return

    from collections import Counter
    pilares = Counter(p.get("tipo_jornada", "general") for p in pacientes)

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card(str(total), "Total de Pacientes", "👥")
    with c2:
        metric_card("—", "Aderência Média", "📋")
    with c3:
        metric_card("—", "Risco de Abandono", "⚠️")

    _grafico_pilares_local(pilares)


def _grafico_pilares(db) -> None:
    pacientes = _query(db, "perfis", "tipo_jornada", limit=500)
    if not pacientes:
        return
    from collections import Counter
    pilares = Counter(p.get("tipo_jornada", "general")
                      for p in pacientes)
    _grafico_pilares_local(pilares)


def _grafico_pilares_local(pilares: dict) -> None:
    _LABELS = {
        "general":   "⚖️ Emagrecimento",
        "fitness":   "💪 Fitness",
        "bariatric": "🔪 Pós-Bariátrica",
        "glp1":      "💉 GLP-1",
    }
    total = sum(pilares.values()) or 1
    for key, label in _LABELS.items():
        n   = pilares.get(key, 0)
        pct = round(n / total * 100)
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0.8rem;'
            f'margin-bottom:0.5rem;">'
            f'<div style="width:120px;font-size:0.82rem;color:var(--text);">'
            f'{label}</div>'
            f'<div class="progress-track" style="flex:1;">'
            f'<div class="progress-fill" style="width:{pct}%;"></div>'
            f'</div>'
            f'<div style="width:50px;text-align:right;font-weight:700;'
            f'font-size:0.82rem;color:var(--text);">{n} ({pct}%)</div>'
            f'</div>',
            unsafe_allow_html=True,
        )



    _tab_retencao, _tab_profissionais, _tab_campeoes, _query
)


# ── (consolidado de executive_dashboard_b.py) ──
