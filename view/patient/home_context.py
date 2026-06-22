"""
Melshape — Home Contextual por Pilar (UNIFICADO).

Elimina home_context_b.py — sem import circular.
Cada health_mode gera um bloco diferente na home.

GLP-1     → próxima dose, adesão, sintomas de ontem
Bariátrica → fase, volume do dia, suplementos pendentes
Fitness   → meta proteica, treino de hoje, variação de peso
Geral     → etapa da jornada, progresso, próximo passo
"""
import streamlit as st
from views.components.cards import metric_card, alert, empty_state


def render_contexto_pilar(services: dict, user: dict) -> None:
    """Renderiza o bloco contextual correto para o health_mode do paciente."""
    hm = user.get("health_mode", "general")
    db = services["db"]

    st.markdown(
        '<p style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;'
        'color:var(--text-faint);text-transform:uppercase;margin-bottom:0.6rem;">'
        'Seu Contexto de Hoje</p>',
        unsafe_allow_html=True,
    )

    if hm == "glp1":
        _ctx_glp1(db, user)
    elif hm == "bariatric":
        _ctx_bariatric(db, user, services)
    elif hm == "fitness":
        _ctx_fitness(db, user)
    else:
        _ctx_geral(db, user, services)


# ── GLP-1 ────────────────────────────────────────────────────────────────────
def _ctx_glp1(db, user: dict) -> None:
    from services.glp1_service import GLP1Service
    svc    = GLP1Service(db)
    resumo = svc.resumo(user)
    fase   = resumo["fase"]
    ades   = resumo["adesao"]
    prox   = resumo["proxima_dose"] or "—"
    dias   = resumo["dias"]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="metric-card fade-in">'
            f'<div style="font-size:1.2rem;">{fase["icon"]}</div>'
            f'<div style="font-weight:700;font-size:0.88rem;color:var(--text);">'
            f'{fase["label"]}</div>'
            f'<div style="font-size:0.72rem;color:var(--text-muted);">'
            f'{dias or "?"} dias de tratamento</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        cor = "success" if ades["pct"] >= 80 else "warning"
        metric_card(f'{ades["pct"]}%', "Adesão (4 sem.)", "✅", cor)
    with c3:
        st.markdown(
            f'<div class="metric-card fade-in">'
            f'<div style="font-size:0.78rem;color:var(--text-muted);">Próxima dose</div>'
            f'<div style="font-weight:700;font-size:0.92rem;color:var(--primary);">'
            f'{prox}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    sint = db.get_sintomas_glp1(days=1)
    if sint:
        sev = sint[0].get("severidade", 1)
        if sev >= 2:
            alert(
                f"⚠️ Sintomas de ontem com severidade {sev}/3. Monitore hoje.",
                "warning",
            )
    else:
        if st.button("📋 Registrar sintomas de hoje →",
                     use_container_width=True, key="ctx_glp1_sint"):
            st.session_state.page = "glp1"
            st.rerun()


# ── BARIÁTRICA ────────────────────────────────────────────────────────────────
def _ctx_bariatric(db, user: dict, services: dict) -> None:
    from services.bariatric_service import BariatricService
    from services.nutrition_service import NutritionService
    svc    = BariatricService(db)
    resumo = svc.resumo(user)
    fase   = resumo["fase"]
    sm     = NutritionService(db).daily_summary()
    vol    = sm.get("volume_ml", 0)
    cal    = sm.get("calories", 0)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="metric-card fade-in">'
            f'<div style="font-weight:700;color:var(--primary);">{fase["nome"]}</div>'
            f'<div style="font-size:0.74rem;color:var(--text-muted);">Dias {fase["dias"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        max_ml  = fase["max_ml"]
        cor_vol = "error" if vol > max_ml else "success" if vol > 0 else ""
        metric_card(f"{vol:.0f}ml", f"Volume (máx {max_ml}ml)", "🥄", cor_vol)
    with c3:
        max_cal = fase["max_cal"]
        cor_cal = "error" if cal > max_cal else ""
        metric_card(f"{cal:.0f}", f"kcal (máx {max_cal})", "🔥", cor_cal)

    supls = resumo["suplementos"][:3]
    if supls:
        nomes = " · ".join(s["name"] for s in supls)
        alert(f"💊 Suplementos de hoje: {nomes}", "info")


# ── FITNESS ───────────────────────────────────────────────────────────────────
def _ctx_fitness(db, user: dict) -> None:
    from services.nutrition_service import NutritionService
    nutr      = NutritionService(db)
    sm        = nutr.daily_summary()
    peso      = user.get("current_weight", 70) or 70
    meta_prot = nutr.calc_protein_goal(peso, "fitness")
    prot_hoje = sm.get("protein", 0)
    pct_prot  = min(100, int(prot_hoje / meta_prot * 100)) if meta_prot else 0
    treino    = db.get_workout_today()

    c1, c2, c3 = st.columns(3)
    with c1:
        cor = "success" if pct_prot >= 80 else "warning" if pct_prot >= 50 else "error"
        metric_card(f"{prot_hoje:.0f}g", f"Proteína (meta {meta_prot:.0f}g)", "🥩", cor)
    with c2:
        if treino:
            from core.models import WORKOUT_TYPES
            label = WORKOUT_TYPES.get(treino.workout_type, "Treino")
            metric_card(label, "Treino de hoje", "🏋️", "success")
        else:
            metric_card("—", "Treino não registrado", "🏋️")
    with c3:
        df_peso = db.get_weights(90)
        if not df_peso.empty and len(df_peso) >= 2:
            diff = float(df_peso.iloc[-1]["weight"]) - float(df_peso.iloc[0]["weight"])
            cor  = "success" if diff < 0 else "warning"
            metric_card(f"{diff:+.1f}kg", "Variação 90d", "📊", cor)
        else:
            metric_card("—", "Variação de peso", "📊")

    if not treino:
        if st.button("🏋️ Registrar treino →",
                     use_container_width=True, key="ctx_fit_treino"):
            st.session_state.page = "habits"
            st.rerun()


# ── GERAL / EMAGRECIMENTO ─────────────────────────────────────────────────────
def _ctx_geral(db, user: dict, services: dict) -> None:
    from services.journey_service import JourneyService
    svc     = JourneyService(db)
    jornada = db.get_jornada_ativa()

    if not jornada:
        empty_state("🗺️", "Jornada não iniciada", "Acesse 'Jornada' para começar")
        return

    hm    = user.get("health_mode", "general")
    prog  = svc.progresso_jornada(jornada["id"], hm)
    etapa = prog["etapa_atual"]
    passo = svc.proximo_passo(etapa, user)
    pct   = prog["pct_geral"]

    st.markdown(
        f'<div class="metric-card fade-in">'
        f'<div style="display:flex;justify-content:space-between;'
        f'align-items:center;margin-bottom:0.5rem;">'
        f'<div style="font-weight:700;color:var(--text);">'
        f'{etapa.get("icone","📍")} {etapa.get("nome","")}</div>'
        f'<div style="font-size:1.2rem;font-weight:800;color:var(--primary);">'
        f'{pct}%</div>'
        f'</div>'
        f'<div class="progress-track">'
        f'<div class="progress-fill" style="width:{pct}%;"></div>'
        f'</div>'
        f'<div style="font-size:0.80rem;color:var(--text-muted);margin-top:0.4rem;">'
        f'➡️ {passo["acao"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if passo.get("pagina"):
        if st.button(
            f'{passo["icone"]} {passo["acao"]}',
            type="primary",
            use_container_width=True,
            key="ctx_geral_cta",
        ):
            st.session_state.page     = passo["pagina"]
            st.session_state.hub_tipo = passo.get("hub_tipo", "")
            st.rerun()
