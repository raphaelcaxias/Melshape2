"""
Melshape — Painel de Triagem Profissional.

Views usadas:
  vw_prioridade_intervencao → score ponderado por risco + engajamento
  vw_alertas_prioritarios   → alertas não visualizados por prioridade

Princípio: toda linha deve responder
"O que devo fazer com este paciente agora?"
"""
import streamlit as st
from views.components.cards import empty_state, section_header


def render_triagem(services: dict) -> None:
    db = services["db"]
    section_header(
        "🎯 Triagem de Pacientes",
        "Prioridade calculada por risco, engajamento e adesão",
    )

    tab_prioridade, tab_alertas = st.tabs([
        "📊 Fila por Prioridade",
        "🚨 Alertas Prioritários",
    ])

    with tab_prioridade:
        _tab_prioridade(db)

    with tab_alertas:
        _tab_alertas_prioritarios(db)


# ── PRIORIDADE DE INTERVENÇÃO ──────────────────────────────────────────────────
def _tab_prioridade(db) -> None:
    """
    vw_prioridade_intervencao: score = risco_abandono×0.5 +
    (100-engajamento)×0.25 + (100-adesao)×0.25
    """
    pacientes = _query_view(
        db, "vw_prioridade_intervencao",
        "id, nome_completo, risco_abandono, score_engajamento, "
        "score_adesao, score_prioridade",
    )

    if not pacientes:
        empty_state(
            "🎯", "Sem pacientes para triagem",
            "Os dados aparecem conforme os pacientes usam o sistema",
        )
        return

    st.markdown(
        f'<div style="font-size:0.82rem;color:var(--text-muted);'
        f'margin-bottom:0.8rem;">'
        f'<b>{len(pacientes)}</b> paciente(s) · ordenados por prioridade</div>',
        unsafe_allow_html=True,
    )

    for i, p in enumerate(pacientes[:20]):
        nome    = p.get("nome_completo", "—")
        score   = float(p.get("score_prioridade") or 0)
        risco   = float(p.get("risco_abandono") or 0)
        eng     = float(p.get("score_engajamento") or 0)
        ades    = float(p.get("score_adesao") or 0)

        cor_score = (
            "var(--error)"   if score >= 70
            else "var(--warning)" if score >= 40
            else "var(--success)"
        )
        urgencia = (
            "🚨 URGENTE" if score >= 70
            else "⚠️ ALTA" if score >= 40
            else "📋 NORMAL"
        )

        st.markdown(
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;padding:0.7rem 0.9rem;'
            f'border:1px solid var(--border);border-radius:var(--radius-md);'
            f'margin-bottom:0.4rem;background:var(--surface);">'
            f'<div style="flex:1;">'
            f'<div style="font-weight:700;font-size:0.92rem;color:var(--text);">'
            f'#{i+1} {nome}</div>'
            f'<div style="font-size:0.74rem;color:var(--text-muted);'
            f'margin-top:0.1rem;">'
            f'Risco: {risco:.0f}% · Eng: {eng:.0f}% · Ades: {ades:.0f}%'
            f'</div></div>'
            f'<div style="text-align:right;margin-left:0.8rem;">'
            f'<div style="font-size:1.2rem;font-weight:800;color:{cor_score};">'
            f'{score:.0f}</div>'
            f'<div style="font-size:0.70rem;color:{cor_score};">'
            f'{urgencia}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        if st.button("Ver paciente →", key=f"triage_{i}_{nome}",
                     use_container_width=True):
            st.session_state["pro_selected_patient"] = nome
            st.session_state.page = "pro_patient_detail"
            st.rerun()


# ── ALERTAS PRIORITÁRIOS ──────────────────────────────────────────────────────
def _tab_alertas_prioritarios(db) -> None:
    """vw_alertas_prioritarios: alertas não visualizados por prioridade."""
    alertas = _query_view(
        db, "vw_alertas_prioritarios",
        "nome_completo, categoria, titulo, prioridade, criado_em",
    )

    if not alertas:
        st.markdown(
            '<div class="alert-success">'
            '✅ Nenhum alerta prioritário aberto</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<div style="font-size:0.82rem;color:var(--text-muted);'
        f'margin-bottom:0.8rem;">'
        f'<b>{len(alertas)}</b> alerta(s) não visualizado(s)</div>',
        unsafe_allow_html=True,
    )

    for a in alertas:
        prioridade = int(a.get("prioridade") or 0)
        cor = (
            "var(--error)"   if prioridade >= 8
            else "var(--warning)" if prioridade >= 5
            else "var(--info)"
        )
        data = a.get("criado_em", "")[:10]
        st.markdown(
            f'<div style="display:flex;gap:0.7rem;align-items:flex-start;'
            f'padding:0.6rem 0;border-bottom:1px solid var(--border-subtle);">'
            f'<div style="width:4px;background:{cor};'
            f'border-radius:2px;flex-shrink:0;align-self:stretch;"></div>'
            f'<div style="flex:1;">'
            f'<div style="font-weight:600;font-size:0.90rem;color:var(--text);">'
            f'{a.get("nome_completo","—")}</div>'
            f'<div style="font-size:0.80rem;color:var(--text-muted);">'
            f'{a.get("titulo","")}</div>'
            f'<div style="font-size:0.72rem;color:var(--text-faint);">'
            f'{a.get("categoria","—")} · {data}</div>'
            f'</div>'
            f'<div style="font-size:1rem;font-weight:800;color:{cor};">'
            f'P{prioridade}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── HELPER ────────────────────────────────────────────────────────────────────
def _query_view(db, view: str, colunas: str) -> list:
    if db.is_real and db.client:
        try:
            r = (db.client.table(view)
                 .select(colunas)
                 .order("score_prioridade" if "score_prioridade" in colunas
                        else "prioridade", desc=True)
                 .limit(50)
                 .execute())
            return r.data or []
        except Exception as e:
            import logging
            logging.getLogger("Melshape").warning(f"{view}: {e}")
    return []
