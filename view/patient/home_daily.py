"""Melshape — Home: blocos diários de hábitos, comportamento, consequências e score."""
import streamlit as st
from datetime import date

from views.components.cards import empty_state, motivational_quote
from services.contextualizer import ctx
import config

# ── BLOCO 2 — HÁBITOS DE HOJE ─────────────────────────────────────────────────
def _bloco_habitos_hoje(db, user: dict) -> None:
    st.markdown(
        '<p style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;'
        'color:var(--text-faint);text-transform:uppercase;'
        'margin-bottom:0.6rem;">📋 Hábitos de Hoje</p>',
        unsafe_allow_html=True,
    )
    habitos   = db.get_habitos()
    if not habitos:
        empty_state("📋", "Nenhum hábito criado ainda",
                    "Crie hábitos na tela de Hábitos")
        if st.button("Ir para Hábitos →", use_container_width=True,
                     key="home_hab_cta"):
            st.session_state.page = "habits"
            st.rerun()
        return

    feitos    = db.get_registros_hoje()
    concluidos = sum(1 for h in habitos if h.get("id") in feitos)
    total      = len(habitos)
    pct        = int(concluidos / total * 100) if total else 0

    st.markdown(
        f'<div style="font-size:0.80rem;color:var(--text-muted);'
        f'margin-bottom:0.4rem;">'
        f'{concluidos} de {total} hábitos ({pct}%)</div>'
        f'<div class="progress-track" style="margin-bottom:0.6rem;">'
        f'<div class="progress-fill" style="width:{pct}%;"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    for h in habitos[:4]:
        hid   = h.get("id", "")
        nome  = h.get("nome", "")
        icone = h.get("icone", "⭐")
        feito = hid in feitos
        cor   = "var(--success)" if feito else "var(--border)"
        sinal = "✅" if feito else "⬜"

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.5rem;'
                f'padding:0.3rem 0;border-bottom:1px solid var(--border-subtle);">'
                f'<span>{icone}</span>'
                f'<span style="color:{cor};font-weight:'
                f'{"400" if feito else "600"};">{nome}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col2:
            if not feito:
                if st.button("✓", key=f"home_hab_{hid}",
                             help="Marcar como concluído"):
                    from services.habit_service import HabitService
                    res = HabitService(db).registrar(hid)
                    if res["ok"]:
                        st.toast(
                            f"{icone} {nome} — +{res['xp_ganho']} XP",
                            icon="✅",
                        )
                        if res.get("bonus_msg"):
                            st.toast(res["bonus_msg"], icon="🎉")
                        st.rerun()

    if st.button("Ver todos os hábitos →", use_container_width=True,
                 key="home_ver_habitos"):
        st.session_state.page = "habits"
        st.rerun()


# ── BLOCO 3 — COMPORTAMENTO ───────────────────────────────────────────────────
def _bloco_comportamento(checkin) -> None:
    st.markdown(
        '<p style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;'
        'color:var(--text-faint);text-transform:uppercase;'
        'margin-bottom:0.6rem;">💭 Como Você Está</p>',
        unsafe_allow_html=True,
    )
    if not checkin:
        st.markdown(
            '<div style="font-size:0.84rem;color:var(--text-muted);">'
            'Faça o check-in para registrar como você está hoje.</div>',
            unsafe_allow_html=True,
        )
        return

    humor  = checkin.get("humor", 0)
    energia = checkin.get("energia", 0)
    sono   = checkin.get("qualidade_sono", 0)

    _H = {1:"😖",2:"😕",3:"😐",4:"🙂",5:"😄"}
    _E = {1:"😴",2:"🥱",3:"⚡",4:"💪",5:"🚀"}
    _S = {1:"😫",2:"😕",3:"😐",4:"🙂",5:"😴✨"}

    c1, c2, c3 = st.columns(3)
    for col, val, dmap, label in [
        (c1, humor,   _H, "Humor"),
        (c2, energia, _E, "Energia"),
        (c3, sono,    _S, "Sono"),
    ]:
        with col:
            emoji = dmap.get(int(val), "—") if val else "—"
            st.markdown(
                f'<div class="metric-card fade-in" style="text-align:center;">'
                f'<div style="font-size:1.8rem;">{emoji}</div>'
                f'<div class="metric-label">{label}: {val}/5</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── BLOCO 5 — CONSEQUÊNCIAS ───────────────────────────────────────────────────
def _bloco_consequencias(sm: dict, hydration: int, user: dict,
                          nutr, last_weight) -> None:
    st.markdown(
        '<p style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;'
        'color:var(--text-faint);text-transform:uppercase;'
        'margin-bottom:0.6rem;">📊 Consequências de Hoje</p>',
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

    pct_cal  = min(100, int(cal_hoje / goal_cal * 100))  if goal_cal  else 0
    pct_prot = min(100, int(prot_hoje / goal_prot * 100)) if goal_prot else 0
    pct_agua = min(100, int(hydration / goal_agua * 100)) if goal_agua else 0

    c1, c2, c3, c4 = st.columns(4)
    itens = [
        (c1, f"{cal_hoje:.0f}",  "🔥 kcal",     pct_cal,  ""),
        (c2, f"{prot_hoje:.0f}g","🥩 proteína",  pct_prot, "success" if pct_prot>=80 else ""),
        (c3, f"{hydration}ml",   "💧 água",      pct_agua, "info"),
        (c4, f"{last_weight:.1f}kg" if last_weight else "—",
             "⚖️ peso", 0, ""),
    ]
    for col, val, label, pct, cor in itens:
        with col:
            fill_css = (
                f'background:var(--{cor});' if cor in ("success","info")
                else ""
            )
            st.markdown(
                f'<div class="metric-card fade-in">'
                f'<div style="font-weight:700;font-size:1.1rem;'
                f'color:var(--text);">{val}</div>'
                f'<div style="font-size:0.74rem;color:var(--text-muted);">'
                f'{label}</div>'
                f'{"<div class=progress-track style=margin-top:0.3rem;><div class=progress-fill style=width:" + str(pct) + "%;" + fill_css + "></div></div>" if pct > 0 else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )




# ── (consolidado de home_score_helpers.py) ──

def _bloco_score(services: dict, user: dict) -> None:
    """Score narrativo de transformação."""
    try:
        from services.score_service import ScoreService
        narrativa = ScoreService(services["db"]).narrativa_paciente(user)
        if narrativa.get("icone") == "🗺️":
            return
        st.markdown(
            f'<div class="metric-card fade-in" style="'
            f'border-left:4px solid {narrativa["cor"]};">'
            f'<div style="display:flex;gap:0.7rem;align-items:center;">'
            f'<span style="font-size:1.8rem;">{narrativa["icone"]}</span>'
            f'<div>'
            f'<div style="font-weight:700;font-size:0.92rem;color:var(--text);">'
            f'{narrativa["titulo"]}</div>'
            f'<div style="font-size:0.80rem;color:var(--text-muted);">'
            f'{narrativa["mensagem"]}</div>'
            f'</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    except Exception:
        pass


def _div() -> None:
    st.markdown(
        '<div style="border-top:1px solid var(--border);margin:1rem 0;"></div>',
        unsafe_allow_html=True,
    )


def _turno() -> str:
    from datetime import datetime
    h = datetime.now().hour
    return "Bom dia" if h < 12 else "Boa tarde" if h < 18 else "Boa noite"


def _data_br() -> str:
    from datetime import date
    meses = ["jan","fev","mar","abr","mai","jun",
             "jul","ago","set","out","nov","dez"]
    dias  = ["Segunda","Terça","Quarta","Quinta",
             "Sexta","Sábado","Domingo"]
    hoje  = date.today()
    return f"{dias[hoje.weekday()]}, {hoje.day} de {meses[hoje.month-1]}"
