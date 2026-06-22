"""Melshape — Detalhe do Paciente: score, conquistas e helpers."""
import streamlit as st
import plotly.graph_objects as go
from views.components.cards import empty_state, metric_card, achievement_card

# ── SCORE DE TRANSFORMAÇÃO ────────────────────────────────────────────────────
def _tab_score(db, perfil_id: str) -> None:
    score_data = _query_perfil(db, "vw_score_transformacao",
                                "score_global", perfil_id)
    if score_data:
        score = float(score_data[0].get("score_global") or 0)
        cor   = "success" if score >= 70 else "warning" if score >= 40 else "error"
        metric_card(f"{score:.0f}/100", "Score de Transformação", "🏆", cor)

        # Gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            gauge={
                "axis":       {"range": [0, 100]},
                "bar":        {"color": "#C9A84C"},
                "steps": [
                    {"range": [0, 40],  "color": "rgba(220,38,38,0.15)"},
                    {"range": [40, 70], "color": "rgba(217,119,6,0.15)"},
                    {"range": [70, 100],"color": "rgba(22,163,74,0.15)"},
                ],
                "threshold": {
                    "line": {"color": "#C9A84C", "width": 3},
                    "thickness": 0.75,
                    "value": score,
                },
            },
            title={"text": "Score Global de Transformação"},
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#6B6B6B",
            height=280,
            margin=dict(t=30, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(
            '<div style="font-size:0.82rem;color:var(--text-muted);">'
            'Score calculado por: aderência (25%) + engajamento (20%) + '
            'nutrição (20%) + comportamento (15%) + indicadores clínicos (20%)'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        empty_state("🏆", "Score não disponível",
                    "O paciente precisa de mais registros para gerar o score")


# ── CONQUISTAS ────────────────────────────────────────────────────────────────
def _tab_conquistas(db, perfil_id: str) -> None:
    conquistas = _query_perfil(db, "vw_conquistas_usuario",
                                "badge,categoria,conquistado_em", perfil_id)
    if not conquistas:
        empty_state("🎖️", "Nenhuma conquista ainda",
                    "O paciente ainda não desbloqueou badges")
        return

    metric_card(str(len(conquistas)), "Conquistas desbloqueadas", "🏅")
    st.markdown("<br>", unsafe_allow_html=True)

    cols = st.columns(2)
    for i, c in enumerate(conquistas):
        data = c.get("conquistado_em", "")
        data_str = data[:10] if data else "—"
        with cols[i % 2]:
            achievement_card(c.get("badge", "—"), data_str)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _get_perfil(db, nome: str) -> dict:
    if db.is_real and db.client:
        try:
            r = (db.client.table("perfis")
                 .select("id, nome_completo, tipo_jornada, peso_atual")
                 .ilike("nome_completo", f"%{nome}%")
                 .limit(1).execute())
            return r.data[0] if r.data else {}
        except Exception:
            pass
    # fallback mock
    for u in db._mock().get("users", {}).values():
        if nome.lower() in u.get("name", "").lower():
            return {"id": u.get("email"), "nome_completo": u.get("name", "")}
    return {}


def _query_perfil(db, tabela: str, colunas: str,
                  perfil_id: str, ordem: str = "") -> list:
    if db.is_real and db.client:
        try:
            q = (db.client.table(tabela)
                 .select(colunas)
                 .eq("perfil_id", perfil_id))
            if ordem:
                q = q.order(ordem)
            return q.limit(200).execute().data or []
        except Exception as e:
            import logging
            logging.getLogger("Melshape.PatientDetail").warning(
                f"{tabela}: {e}"
            )
    return []
