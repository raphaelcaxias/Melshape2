"""
Melshape — Tela de Metas.

O paciente vê suas metas com progresso calculado
automaticamente a partir dos dados reais do banco.
Criação guiada por tipo com templates do pilar.
"""
import streamlit as st

from services.goals_service import GoalsService
from services.journey_service import JourneyService
from views.components.cards import (
    section_header, empty_state, metric_card,
    xp_toast, alert,
)
from views.patient.goals_form import render_form_meta


def render(services: dict, user: dict) -> None:
    db   = services["db"]
    svc  = GoalsService(db)
    jrn  = JourneyService(db)
    hm   = user.get("health_mode", "general")

    section_header("🎯 Metas", "Objetivos concretos com progresso real")

    # Busca jornada ativa para vincular metas
    jornada    = jrn.garantir_jornada(user)
    jornada_id = jornada.get("id", "") if jornada else ""
    metas      = db.get_metas(jornada_id) if jornada_id else []

    # ── RESUMO ────────────────────────────────────────────────────────────────
    if metas:
        concluidas = [m for m in metas if m.get("concluida")]
        ativas     = [m for m in metas if not m.get("concluida")]

        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card(str(len(metas)), "Metas totais", "🎯")
        with c2:
            metric_card(
                str(len(ativas)), "Em andamento", "⏳",
                "warning" if ativas else "success",
            )
        with c3:
            metric_card(
                str(len(concluidas)), "Concluídas", "✅",
                "success" if concluidas else "",
            )

    st.markdown(
        '<div style="border-top:1px solid var(--border);margin:0.8rem 0;"></div>',
        unsafe_allow_html=True,
    )

    tab_ativas, tab_concluidas, tab_nova = st.tabs([
        "⏳ Em Andamento",
        "✅ Concluídas",
        "➕ Nova Meta",
    ])

    with tab_ativas:
        _tab_ativas(
            [m for m in metas if not m.get("concluida")],
            svc, jornada_id,
        )

    with tab_concluidas:
        _tab_concluidas(
            [m for m in metas if m.get("concluida")], svc
        )

    with tab_nova:
        render_form_meta(db, svc, jornada_id, hm)


# ── METAS ATIVAS ─────────────────────────────────────────────────────────────
def _tab_ativas(metas: list, svc: GoalsService,
                jornada_id: str) -> None:
    if not metas:
        empty_state(
            "🎯", "Nenhuma meta ativa",
            "Crie sua primeira meta na aba 'Nova Meta'",
        )
        return

    for meta in metas:
        _card_meta(meta, svc, jornada_id, concluida=False)


def _card_meta(meta: dict, svc: GoalsService,
               jornada_id: str, concluida: bool) -> None:
    prog     = svc.calcular_progresso(meta)
    pct      = prog["pct"]
    titulo   = meta.get("titulo", "Meta")
    tipo     = meta.get("tipo", "livre")
    prazo    = meta.get("prazo")
    meta_id  = meta.get("id", "")

    tipo_labels = svc.tipo_labels()
    t_icon, t_label = tipo_labels.get(tipo, ("🎯", "Livre"))

    prazo_dias = svc.prazo_restante(prazo)
    prazo_html = ""
    if prazo_dias is not None:
        cor_prazo = (
            "var(--error)"   if prazo_dias <= 3
            else "var(--warning)" if prazo_dias <= 7
            else "var(--text-muted)"
        )
        prazo_html = (
            f'<span style="font-size:0.74rem;color:{cor_prazo};">'
            f'{"⏰ Vence em " + str(prazo_dias) + "d" if prazo_dias >= 0 else "⚠️ Prazo vencido"}'
            f'</span>'
        )

    cor_borda = (
        "var(--success)" if concluida or pct >= 100
        else "var(--primary)" if pct >= 75
        else "var(--border)"
    )
    cor_fill = (
        "" if pct < 75
        else "warning" if pct < 100
        else "success"
    )

    st.markdown(
        f'<div class="metric-card fade-in" '
        f'style="margin-bottom:0.7rem;border-color:{cor_borda};">'
        f'<div style="display:flex;justify-content:space-between;'
        f'align-items:flex-start;margin-bottom:0.5rem;">'
        f'<div>'
        f'<div style="font-weight:700;font-size:0.95rem;color:var(--text);">'
        f'{t_icon} {titulo}</div>'
        f'<div style="font-size:0.76rem;color:var(--text-muted);'
        f'margin-top:0.1rem;">{t_label} · {prog["delta_label"]}</div>'
        f'</div>'
        f'<div style="text-align:right;">'
        f'<div style="font-size:1.4rem;font-weight:800;color:var(--primary);">'
        f'{pct}%</div>'
        f'{prazo_html}'
        f'</div>'
        f'</div>'
        f'<div class="progress-track">'
        f'<div class="progress-fill {cor_fill}" style="width:{pct}%;"></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Ação: concluir se 100%
    if pct >= 100 and not concluida:
        if st.button(
            "🏆 Marcar como concluída",
            key=f"goal_done_{meta_id}",
            type="primary",
            use_container_width=True,
        ):
            ok = svc.concluir_meta(meta_id)
            if ok:
                st.toast(
                    f"🏆 Meta '{titulo}' concluída! +200 XP", icon="🎉"
                )
                xp_toast(200, "meta concluída")
                st.rerun()


# ── METAS CONCLUÍDAS ──────────────────────────────────────────────────────────
def _tab_concluidas(metas: list, svc: GoalsService) -> None:
    if not metas:
        empty_state(
            "✅", "Nenhuma meta concluída ainda",
            "Continue avançando — você vai chegar lá",
        )
        return

    st.markdown(
        f'<div style="font-size:0.82rem;color:var(--text-muted);'
        f'margin-bottom:0.8rem;">'
        f'🏆 <b>{len(metas)}</b> meta(s) concluída(s)</div>',
        unsafe_allow_html=True,
    )
    for meta in metas:
        data_c  = meta.get("concluida_em", "")[:10]
        titulo  = meta.get("titulo", "Meta")
        tipo    = meta.get("tipo", "livre")
        t_icon, _ = svc.tipo_labels().get(tipo, ("🎯", ""))
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;'
            f'padding:0.6rem 0.8rem;background:var(--success-bg);'
            f'border:1px solid var(--success);border-radius:var(--radius-md);'
            f'margin-bottom:0.4rem;">'
            f'<span style="font-weight:600;color:var(--text);">'
            f'{t_icon} {titulo}</span>'
            f'<span style="font-size:0.76rem;color:var(--success);">'
            f'✅ {data_c}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
