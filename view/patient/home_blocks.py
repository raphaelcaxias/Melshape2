"""
Melshape — Home: blocos de progresso, XP, desafio e peso.
Usa contextualizer para nunca exibir número cru sem narrativa.
"""
import streamlit as st
from datetime import date

from views.components.cards import (
    empty_state, challenge_card, motivational_quote, alert, metric_card,
)
from services.contextualizer import ctx
import config
from views.patient.home_helpers import (
    _get_last_weight, _get_dashboard_paciente, _historico_checkins,
)


# ── PROGRESSO DO DIA ──────────────────────────────────────────────────────────
def _bloco_progresso_dia(sm: dict, hydration: int,
                          user: dict, nutr) -> None:
    st.markdown(
        '<p style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;'
        'color:var(--text-faint);text-transform:uppercase;margin-bottom:0.6rem;">'
        'Progresso de Hoje</p>',
        unsafe_allow_html=True,
    )

    weight = user.get("current_weight")
    height = user.get("height")
    age    = user.get("age")
    gender = user.get("gender", "female")
    hm     = user.get("health_mode", "general")
    goal   = user.get("goal", "lose")
    activ  = user.get("activity_level", "moderate")

    tmb       = nutr.calc_tmb(weight, height, age, gender)
    goal_cal  = nutr.calc_goal_calories(tmb, activ, goal, hm)
    goal_prot = nutr.calc_protein_goal(weight, hm)
    goal_agua = config.HYDRATION_GOAL_ML

    cal_hoje  = sm.get("calories", 0)
    prot_hoje = sm.get("protein", 0)

    # Narrativas via contextualizer
    msg_cal  = ctx.calories(cal_hoje, goal_cal)
    msg_prot = ctx.protein(prot_hoje, goal_prot)
    msg_agua = ctx.hydration(hydration, goal_agua)

    pct_cal  = min(100, int(cal_hoje / goal_cal * 100))  if goal_cal  else 0
    pct_prot = min(100, int(prot_hoje / goal_prot * 100)) if goal_prot else 0
    pct_agua = min(100, int(hydration / goal_agua * 100)) if goal_agua else 0

    cor_cal  = "danger"  if pct_cal  >= 100 else "warning" if pct_cal  >= 85 else ""
    cor_prot = "success" if pct_prot >= 80  else ""

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f'<div class="metric-card fade-in">'
            f'<div class="metric-value" style="font-size:1.5rem;">'
            f'{cal_hoje:.0f} kcal</div>'
            f'<div style="font-size:0.76rem;color:var(--text-muted);'
            f'margin-bottom:0.4rem;">{msg_cal}</div>'
            f'<div class="progress-track">'
            f'<div class="progress-fill {cor_cal}" style="width:{pct_cal}%"></div>'
            f'</div>'
            f'<div style="font-size:0.70rem;color:var(--text-faint);'
            f'margin-top:0.2rem;">{pct_cal}% da meta</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f'<div class="metric-card fade-in">'
            f'<div class="metric-value" style="font-size:1.5rem;">'
            f'{prot_hoje:.0f}g</div>'
            f'<div style="font-size:0.76rem;color:var(--text-muted);'
            f'margin-bottom:0.4rem;">{msg_prot}</div>'
            f'<div class="progress-track">'
            f'<div class="progress-fill {cor_prot}" style="width:{pct_prot}%"></div>'
            f'</div>'
            f'<div style="font-size:0.70rem;color:var(--text-faint);'
            f'margin-top:0.2rem;">{pct_prot}% da meta</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f'<div class="metric-card fade-in">'
            f'<div class="metric-value" style="font-size:1.5rem;color:var(--info);">'
            f'{hydration}ml</div>'
            f'<div style="font-size:0.76rem;color:var(--text-muted);'
            f'margin-bottom:0.4rem;">{msg_agua}</div>'
            f'<div class="progress-track">'
            f'<div class="progress-fill" '
            f'style="width:{pct_agua}%;background:var(--info);"></div>'
            f'</div>'
            f'<div style="font-size:0.70rem;color:var(--text-faint);'
            f'margin-top:0.2rem;">{pct_agua}% da meta</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    al_cal  = nutr.calorie_alert(cal_hoje, goal_cal)
    al_prot = nutr.protein_alert(prot_hoje, goal_prot)
    if al_cal:
        alert(al_cal, "warning")
    if al_prot:
        alert(al_prot, "warning")


# ── XP / NÍVEL ────────────────────────────────────────────────────────────────
def _bloco_xp(stats: dict, dash_pac: dict) -> None:
    st.markdown(
        '<p style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;'
        'color:var(--text-faint);text-transform:uppercase;margin-bottom:0.6rem;">'
        'Sua Evolução</p>',
        unsafe_allow_html=True,
    )
    pct     = stats["progress_pct"]
    next_lv = stats.get("next_level", "MAX")
    xp_next = stats.get("xp_to_next", 0)
    badges  = dash_pac.get("total_badges", stats.get("total_badges", 0))
    desafios = dash_pac.get("desafios_concluidos", 0)

    st.markdown(
        f'<div class="metric-card fade-in">'
        f'<div style="display:flex;align-items:center;gap:0.6rem;'
        f'margin-bottom:0.5rem;">'
        f'<span style="font-size:1.8rem;">{stats["level_icon"]}</span>'
        f'<div>'
        f'<div style="font-weight:800;font-size:1rem;color:var(--text);">'
        f'Nível {stats["level_number"]} — {stats["level_name"]}</div>'
        f'<div style="font-size:0.78rem;color:var(--text-muted);">'
        f'{stats["xp"]} XP total</div>'
        f'</div></div>'
        f'<div class="progress-track">'
        f'<div class="progress-fill" style="width:{pct}%"></div>'
        f'</div>'
        f'<div class="progress-meta">'
        f'<span>Progresso</span><span>{pct}%</span>'
        f'<span>{"→ " + next_lv if next_lv else "MAX"}</span>'
        f'</div>'
        f'{"<div style=font-size:0.76rem;color:var(--text-faint);margin-top:0.3rem;>" + str(xp_next) + " XP para o próximo nível</div>" if xp_next else ""}'
        f'<div style="display:flex;gap:1rem;margin-top:0.5rem;">'
        f'<span style="font-size:0.78rem;color:var(--text-muted);">'
        f'🏅 {badges} conquistas</span>'
        f'<span style="font-size:0.78rem;color:var(--text-muted);">'
        f'🎯 {desafios} desafios</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── DESAFIO DA SEMANA ─────────────────────────────────────────────────────────
def _bloco_desafio(gami) -> None:
    st.markdown(
        '<p style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;'
        'color:var(--text-faint);text-transform:uppercase;margin-bottom:0.6rem;">'
        'Desafio da Semana</p>',
        unsafe_allow_html=True,
    )
    desafios = gami.weekly_challenges()
    if not desafios:
        empty_state("🎯", "Nenhum desafio ativo")
        return
    for d in desafios[:2]:
        challenge_card(d["emoji"], d["title"], d["xp"])
    if st.button("Ver todos os desafios →", use_container_width=True,
                 key="home_ver_desafios"):
        st.session_state.page = "analysis"
        st.rerun()


# ── PESO ──────────────────────────────────────────────────────────────────────
def _bloco_peso(last_weight, user: dict) -> None:
    st.markdown(
        '<p style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;'
        'color:var(--text-faint);text-transform:uppercase;margin-bottom:0.6rem;">'
        'Peso</p>',
        unsafe_allow_html=True,
    )
    if last_weight is None:
        empty_state("⚖️", "Sem pesagens", "Registre seu peso para ver a evolução")
        return

    goal_w  = user.get("goal_weight")
    msg_peso = ctx.weight(last_weight, goal=float(goal_w) if goal_w else None)

    st.markdown(
        f'<div class="metric-card fade-in">'
        f'<div class="metric-value" style="font-size:2rem;">'
        f'{last_weight:.1f} kg</div>'
        f'<div style="font-size:0.80rem;color:var(--text-muted);'
        f'margin-top:0.3rem;">{msg_peso}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if st.button("Registrar peso →", use_container_width=True,
                 key="home_reg_peso"):
        st.session_state.page     = "meals"
        st.session_state.hub_tipo = "weight"
        st.rerun()
