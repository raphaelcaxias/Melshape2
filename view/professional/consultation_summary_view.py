"""
Melshape — Tela de Resumo Pré-Consulta.

O profissional chega na consulta sabendo exatamente:
- Como o paciente evoluiu (peso, hábitos, nutrição)
- Como ele estava emocionalmente (check-ins)
- O que foi combinado na última consulta (condutas)
- O que precisa de atenção (alertas)

Elimina 30 min de trabalho por consulta.
Justifica pagamento mensal do profissional.
"""
import streamlit as st
from services.consultation_summary import ConsultationSummaryService
from views.components.cards import (
    section_header, empty_state, metric_card, alert,
)


def render(services: dict, professional, paciente: dict) -> None:
    db        = services["db"]
    perfil_id = paciente.get("id", "")
    nome      = paciente.get("nome_completo", "Paciente")

    svc    = ConsultationSummaryService(db)

    section_header(
        f"📋 Resumo Pré-Consulta — {nome}",
        "Últimos 30 dias em um olhar",
    )

    # Seletor de período
    col_per, col_btn = st.columns([2, 1])
    with col_per:
        dias = st.selectbox(
            "Período",
            [7, 14, 30, 60, 90],
            index=2,
            format_func=lambda x: f"Últimos {x} dias",
            key="cs_periodo",
            label_visibility="collapsed",
        )
    with col_btn:
        gerar = st.button(
            "🔄 Gerar resumo",
            type="primary",
            use_container_width=True,
            key="cs_gerar",
        )

    if "cs_resumo" not in st.session_state or gerar:
        with st.spinner("Gerando resumo..."):
            resumo = svc.gerar(perfil_id, dias=dias)
            st.session_state["cs_resumo"] = resumo

    resumo = st.session_state.get("cs_resumo", {})
    if not resumo:
        empty_state("📋", "Nenhum dado disponível",
                    "O paciente precisa ter registros no período selecionado")
        return

    _render_resumo(resumo, svc)


def _render_resumo(resumo: dict, svc: ConsultationSummaryService) -> None:
    peso   = resumo.get("peso",     {})
    nutr   = resumo.get("nutricao", {})
    hab    = resumo.get("habitos",  {})
    ci     = resumo.get("checkins", {})
    metas  = resumo.get("metas",    [])
    cond   = resumo.get("condutas", [])
    alertas = resumo.get("alertas", [])
    xp     = resumo.get("xp",       {})

    # ── ALERTAS NO TOPO ───────────────────────────────────────────────────────
    if alertas:
        for a in alertas:
            grav = int(a.get("gravidade", 1))
            tipo = "error" if grav >= 3 else "warning" if grav >= 2 else "info"
            alert(f"⚠️ {a.get('titulo','—')} "
                  f"(gravidade {grav}/3)", tipo)

    # ── MÉTRICAS RÁPIDAS ──────────────────────────────────────────────────────
    st.markdown(
        '<p style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;'
        'color:var(--text-faint);text-transform:uppercase;margin:1rem 0 0.5rem;">'
        'Visão Geral</p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    # Peso
    with c1:
        if peso.get("variacao") is not None:
            var   = peso["variacao"]
            sinal = "▼" if var < 0 else "▲"
            cor   = "success" if var <= 0 else "warning"
            metric_card(
                f"{sinal} {abs(var):.1f}kg",
                f"Variação de peso",
                "⚖️", cor,
            )
        else:
            metric_card("—", "Sem pesagens", "⚖️")

    # Aderência
    with c2:
        ader = hab.get("media_aderencia", 0)
        cor  = "success" if ader >= 70 else "warning" if ader >= 50 else "error"
        metric_card(f"{ader:.0f}%", "Aderência hábitos", "📋", cor)

    # Check-ins
    with c3:
        total_ci = ci.get("total", 0)
        per = resumo.get("periodo", {})
        dias_per = per.get("dias", 30)
        pct_ci = round(total_ci / dias_per * 100) if dias_per else 0
        cor = "success" if pct_ci >= 70 else "warning" if pct_ci >= 40 else "error"
        metric_card(f"{total_ci} check-ins",



# ── (consolidado de consultation_summary_detail.py) ──
