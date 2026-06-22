"""Melshape — Detalhe do Paciente: gráficos de peso e nutrição."""
import streamlit as st
import plotly.graph_objects as go
from views.components.cards import empty_state, metric_card

    with tab_acoes:
        render_acoes(services, professional, perfil)


# ── EVOLUÇÃO DE PESO ──────────────────────────────────────────────────────────
def _tab_peso(db, perfil_id: str, nome: str) -> None:
    pesos = _query_perfil(db, "vw_evolucao_peso",
                           "peso,criado_em", perfil_id,
                           ordem="criado_em")
    if not pesos:
        empty_state("⚖️", "Sem pesagens registradas",
                    "O paciente ainda não registrou o peso")
        return

    # Métricas rápidas
    valores = [float(p.get("peso") or 0) for p in pesos if p.get("peso")]
    if valores:
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card(f"{valores[-1]:.1f} kg", "Peso Atual", "⚖️")
        with c2:
            diff = valores[-1] - valores[0]
            cor  = "success" if diff < 0 else "warning"
            metric_card(f"{diff:+.1f} kg", "Variação Total", "📉", cor)
        with c3:
            metric_card(str(len(valores)), "Pesagens", "📊")

    # Gráfico
    datas  = [p.get("criado_em", "")[:10] for p in pesos]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=datas, y=valores,
        mode="lines+markers",
        name=nome,
        line=dict(color="#C9A84C", width=2),
        marker=dict(size=5, color="#C9A84C"),
        fill="tozeroy",
        fillcolor="rgba(201,168,76,0.08)",
    ))
    fig.update_layout(
        title="Evolução de Peso",
        xaxis_title="Data",
        yaxis_title="Peso (kg)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#6B6B6B",
        showlegend=False,
        margin=dict(t=40, b=30, l=30, r=10),
    )
    fig.update_xaxes(gridcolor="rgba(0,0,0,0.05)")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.05)")
    st.plotly_chart(fig, use_container_width=True)


# ── NUTRIÇÃO ──────────────────────────────────────────────────────────────────
def _tab_nutricao(db, perfil_id: str) -> None:
    consumo = _query_perfil(db, "vw_consumo_diario",
                             "dia,calorias,proteina,carboidratos,gorduras",
                             perfil_id, ordem="dia")
    if not consumo:
        empty_state("🍽️", "Sem registros nutricionais",
                    "O paciente ainda não registrou refeições")
        return

    # Últimos 14 dias
    ultimos = consumo[-14:] if len(consumo) > 14 else consumo
    datas   = [r.get("dia", "") for r in ultimos]
    calorias = [float(r.get("calorias") or 0) for r in ultimos]
    proteina = [float(r.get("proteina") or 0) for r in ultimos]

    # Métricas médias
    c1, c2, c3 = st.columns(3)
    with c1:
        media_cal = round(sum(calorias) / len(calorias), 0) if calorias else 0
        metric_card(f"{media_cal:.0f} kcal", "Média Diária (14d)", "🔥")
    with c2:
        media_prot = round(sum(proteina) / len(proteina), 1) if proteina else 0
        metric_card(f"{media_prot:.0f}g", "Proteína Média (14d)", "🥩")
    with c3:
        dias_reg = len([c for c in calorias if c > 0])
        metric_card(f"{dias_reg}/{len(ultimos)}", "Dias com Registro", "📅")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=datas, y=calorias, name="Calorias",
        marker_color="rgba(201,168,76,0.75)",
    ))
    fig.add_trace(go.Scatter(
        x=datas, y=proteina, name="Proteína (g)",
        yaxis="y2", mode="lines+markers",
        line=dict(color="#10B981", width=2),
        marker=dict(size=5),
    ))
    fig.update_layout(
        title="Consumo Nutricional (últimos 14 dias)",
        yaxis=dict(title="Calorias (kcal)", gridcolor="rgba(0,0,0,0.05)"),
        yaxis2=dict(title="Proteína (g)", overlaying="y", side="right",
                    gridcolor="rgba(0,0,0,0)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#6B6B6B",
        legend=dict(orientation="h", y=1.1),
        margin=dict(t=50, b=30, l=30, r=50),
    )
    st.plotly_chart(fig, use_container_width=True)


