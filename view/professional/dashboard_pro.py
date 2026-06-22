"""
Melshape — Dashboard Profissional.

Views: vw_dashboard_profissional, vw_fila_atendimento,
       vw_alertas_abertos, vw_pacientes_inativos,
       vw_sem_checkin_recente, vw_pacientes_para_notificar
"""
import streamlit as st
import plotly.express as px

from views.components.cards import section_header, metric_card, empty_state
from views.professional.dashboard_pro_tabs import (
    _tab_alertas, _tab_inativos, _query, _pro_email,
)


def render(services: dict, professional) -> None:
    db  = services["db"]
    pro_name = getattr(professional, "name", "") or professional.get("name", "")
    section_header(f"👨‍⚕️ Painel — {pro_name}", "Visão clínica dos seus pacientes")

    # ── AÇÕES PROATIVAS (RiskService) ──────────────────────────────────────────
    try:
        from services.risk_service import RiskService
        acoes = RiskService(db).acoes_profissional()
        if acoes:
            urgentes = [a for a in acoes if a["urgencia"] == "alta"]
            if urgentes:
                for a in urgentes[:3]:
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;'
                        f'align-items:center;padding:0.55rem 0.9rem;'
                        f'border-left:4px solid var(--error);'
                        f'background:var(--error-bg);'
                        f'border-radius:var(--radius-md);margin-bottom:0.3rem;">'
                        f'<div>'
                        f'<div style="font-weight:600;font-size:0.88rem;">'
                        f'{a["icone"]} {a["paciente"]}</div>'
                        f'<div style="font-size:0.74rem;color:var(--text-muted);">'
                        f'{a["motivo"]}</div>'
                        f'</div>'
                        f'<span style="font-size:0.76rem;font-weight:700;'
                        f'color:var(--error);">{a["acao"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    '<div style="border-top:1px solid var(--border);'
                    'margin:0.8rem 0;"></div>',
                    unsafe_allow_html=True,
                )
    except Exception:
        pass

    tab_geral, tab_fila, tab_alertas_t, tab_inativos_t, tab_risco = st.tabs([
        "📊 Visão Geral",
        "🏥 Fila de Atendimento",
        "🚨 Alertas Clínicos",
        "📵 Inativos",
        "⚠️ Em Risco",
    ])

    with tab_geral:
        _tab_geral(db)

    with tab_fila:
        _tab_fila(db)

    with tab_alertas_t:
        _tab_alertas(db)

    with tab_inativos_t:
        _tab_inativos(db)

    with tab_risco:
        from views.components.notification_inbox import render_pacientes_risco_pro
        render_pacientes_risco_pro(services)

    st.sidebar.markdown("---")
    if st.sidebar.button("🎯 Triagem", use_container_width=True):
        st.session_state.page = "pro_triagem"
        st.rerun()
    if st.sidebar.button("🏥 Dashboard Executivo",
                          use_container_width=True,
                          key="pro_executive_btn"):
        st.session_state.page = "pro_executive"
        st.rerun()
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        st.session_state.pop("professional", None)
        st.session_state.page = "landing"
        st.rerun()


def _tab_geral(db) -> None:
    dados = _query(db, "vw_dashboard_profissional",
                   "total_pacientes,aderencia_media,consistencia_media,risco_abandono_medio")
    if dados:
        row = dados[0]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card(str(row.get("total_pacientes", 0)), "Total de Pacientes", "👥")
        with c2:
            ader = float(row.get("aderencia_media") or 0)
            metric_card(f"{ader:.0f}%", "Aderência Média", "📋",
                        "success" if ader >= 70 else "warning")
        with c3:
            cons = float(row.get("consistencia_media") or 0)
            metric_card(f"{cons:.0f}%", "Consistência Média", "🔥",
                        "success" if cons >= 70 else "warning")
        with c4:
            risco = float(row.get("risco_abandono_medio") or 0)
            metric_card(f"{risco:.0f}%", "Risco de Abandono", "⚠️",
                        "error" if risco >= 50 else "warning")
    st.markdown("---")
    pacientes = _query(db, "perfis", "tipo_jornada", filtro_pro=True)
    if pacientes:
        from collections import Counter
        contagem = Counter(p.get("tipo_jornada", "general") for p in pacientes)
        labels   = {
            "general": "⚖️ Emagrecimento", "fitness": "💪 Fitness",
            "bariatric": "🔪 Pós-Bariátrica", "glp1": "💉 GLP-1",
        }
        df_data = {
            "Jornada": [labels.get(k, k) for k in contagem],
            "Total":   list(contagem.values()),
        }
        fig = px.pie(df_data, names="Jornada", values="Total",
                     title="Distribuição por Jornada",
                     color_discrete_sequence=["#C9A84C","#6366F1","#8B5CF6","#10B981"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#6B6B6B",
                          margin=dict(t=40,b=10,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        empty_state("📊", "Nenhum paciente cadastrado ainda")


def _tab_fila(db) -> None:
    fila = _query(db, "vw_fila_atendimento",
                  "nome_completo,score_prioridade,prioridade")
    if not fila:
        empty_state("🏥", "Fila vazia", "Nenhum paciente requer atenção agora")
        return
    _EMOJI = {"URGENTE": "🚨", "ALTA": "⚠️", "MODERADA": "📋", "BAIXA": "✅"}
    _COR   = {"URGENTE": "error", "ALTA": "warning", "MODERADA": "info", "BAIXA": "success"}
    grupos: dict = {"URGENTE": [], "ALTA": [], "MODERADA": [], "BAIXA": []}
    for p in fila:
        grupos.get(p.get("prioridade", "BAIXA"), grupos["BAIXA"]).append(p)
    for nivel in ["URGENTE", "ALTA", "MODERADA", "BAIXA"]:
        pacs = grupos[nivel]
        if not pacs:
            continue
        st.markdown(
            f'<div class="alert-{_COR[nivel]}" style="margin-bottom:0.4rem;">'
            f'{_EMOJI[nivel]} <b>{nivel}</b> — {len(pacs)} paciente(s)</div>',
            unsafe_allow_html=True,
        )
        for p in pacs:
            nome  = p.get("nome_completo", "—")
            score = p.get("score_prioridade", 0)
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(
                    f'<div style="font-weight:600;font-size:0.92rem;">{nome}</div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f'<div style="font-size:0.80rem;color:var(--text-muted);">'
                    f'Score: {float(score):.0f}</div>',
                    unsafe_allow_html=True,
                )
            with c3:
                if st.button("Ver →", key=f"fila_{nome}", use_container_width=True):
                    st.session_state["pro_selected_patient"] = nome
                    st.session_state.page = "pro_patient_detail"
                    st.rerun()
        st.markdown(
            '<div style="border-bottom:1px solid var(--border);margin:0.5rem 0;"></div>',
            unsafe_allow_html=True,
        )
