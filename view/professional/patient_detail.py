from views.patient.patient_detail_tabs import _tab_score, _tab_conquistas, _get_perfil, _query_perfil
from views.professional.patient_actions import render as render_acoes
"""
Melshape — Detalhe do Paciente (visão profissional).

Views Supabase utilizadas:
  vw_evolucao_peso          → histórico de peso
  vw_consumo_diario         → consumo nutricional diário
  vw_score_transformacao    → score global de transformação
  vw_conquistas_usuario     → badges conquistadas
  vw_dashboard_executivo    → resumo completo do paciente
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta

from views.components.cards import (
    section_header, metric_card, empty_state,
    achievement_card,
)


def render(services: dict, professional) -> None:
    db      = services["db"]
    paciente_nome = st.session_state.get("pro_selected_patient", "")

    # Botão voltar
    if st.button("← Voltar ao painel", key="pd_back"):
        st.session_state.page = "pro_dashboard"
        st.rerun()

    if not paciente_nome:
        empty_state("👤", "Nenhum paciente selecionado",
                    "Volte à fila e selecione um paciente")
        return

    section_header(f"👤 {paciente_nome}", "Histórico clínico completo")

    # Busca perfil_id pelo nome
    perfil = _get_perfil(db, paciente_nome)
    if not perfil:
        st.warning("Paciente não encontrado no banco.")
        return

    perfil_id = perfil.get("id", "")

    # ── RESUMO EXECUTIVO ──────────────────────────────────────────────────────
    exec_data = _query_perfil(db, "vw_dashboard_executivo",
                               "total_checkins,total_refeicoes,total_badges,"
                               "xp_total,motivacao_media,energia_media,"
                               "qualidade_sono_media,maior_peso,menor_peso",
                               perfil_id)

    if exec_data:
        row = exec_data[0]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card(str(row.get("total_refeicoes") or 0),
                        "Refeições registradas", "🍽️")
        with c2:
            metric_card(str(row.get("total_checkins") or 0),
                        "Check-ins totais", "✅")
        with c3:
            metric_card(str(row.get("total_badges") or 0),
                        "Conquistas", "🏅")
        with c4:
            xp = row.get("xp_total") or 0
            metric_card(str(xp), "XP Total", "⭐")

        # Médias comportamentais
        st.markdown("---")
        st.markdown("##### 🧠 Indicadores Comportamentais")
        c1, c2, c3 = st.columns(3)
        with c1:
            mot = float(row.get("motivacao_media") or 0)
            metric_card(f"{mot:.1f}/5", "Motivação Média", "😊",
                        "success" if mot >= 4 else "warning" if mot >= 3 else "error")
        with c2:
            ene = float(row.get("energia_media") or 0)
            metric_card(f"{ene:.1f}/5", "Energia Média", "⚡",
                        "success" if ene >= 4 else "warning" if ene >= 3 else "error")
        with c3:
            sono = float(row.get("qualidade_sono_media") or 0)
            metric_card(f"{sono:.1f}h", "Qualidade de Sono", "😴",
                        "success" if sono >= 7 else "warning" if sono >= 6 else "error")
    else:
        st.info("Dados resumidos não disponíveis para este paciente.")

    st.markdown("---")

    # ── TABS DE DETALHE ───────────────────────────────────────────────────────
    tab_peso, tab_nutri, tab_score, tab_conquistas, tab_acoes, tab_resumo = st.tabs([
        "⚖️ Evolução de Peso",
        "🍽️ Nutrição",
        "🏆 Score",
        "🎖️ Conquistas",
        "📋 Ações Clínicas",
        "📄 Resumo Pré-Consulta",
    ])

    with tab_peso:
        _tab_peso(db, perfil_id, paciente_nome)

    with tab_nutri:
        _tab_nutricao(db, perfil_id)

    with tab_score:
        _tab_score(db, perfil_id)

    with tab_conquistas:
        _tab_conquistas(db, perfil_id)

from views.professional.patient_detail_charts import _tab_peso, _tab_nutricao

    with tab_acoes:
        render_acoes(services, professional, perfil)

    with tab_resumo:
        from views.professional.consultation_summary_view import render as render_resumo
        render_resumo(services, professional, perfil)
