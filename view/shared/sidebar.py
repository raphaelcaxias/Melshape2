"""
Melshape — Sidebar do paciente.
Menu: Jornada, Check-in, Registrar, Evolução, Conquistas + pilar + perfil.
Dark mode com persistência no banco.
"""
import streamlit as st
import config
from views.shared.sidebar_nav import render_pilar_perfil, _clear_session

MENU = [
    ("🏠", "Home",       "home"),
    ("🗺️", "Jornada",    "journey"),
    ("✅", "Check-in",   "checkin"),
    ("➕", "Registrar",  "meals"),
    ("📋", "Hábitos",    "habits"),
    ("🎯", "Metas",      "goals"),
    ("📈", "Evolução",   "dashboard"),
    ("🏆", "Conquistas", "analysis"),
]

_MODE_LABELS = {
    "general":   ("⚖️", "Emagrecimento", "general"),
    "fitness":   ("💪", "Fitness",        "fitness"),
    "bariatric": ("🔪", "Pós-Bariátrica", "bariatric"),
    "glp1":      ("💉", "GLP-1",          "glp1"),
}

_PLAN_LABELS = {
    "free":      "🆓 FREE",
    "essencial": "💎 ESSENCIAL",
    "pro":       "⭐ PRO",
    "lifetime":  "👑 VITALÍCIO",
}


def _apply_dark_mode(dark: bool) -> None:
    theme = "dark" if dark else "light"
    st.markdown(
        f'<script>document.documentElement.setAttribute("data-theme","{theme}")</script>',
        unsafe_allow_html=True,
    )


def render(services: dict) -> None:
    u    = st.session_state.user
    db   = services["db"]
    nutr = services["nutrition"]
    gami = services["gamification"]
    plan = services["plan"]

    from core.models import User
    u_obj    = User.from_dict(u)
    eff_plan = u_obj.effective_plan()
    dark     = bool(u.get("dark_mode", False))

    _apply_dark_mode(dark)

    with st.sidebar:
        # Logo
        st.markdown(
            '<div class="sidebar-logo">'
            '<div style="font-size:2rem;">🔥</div>'
            '<div class="sidebar-logo-name">Melshape</div>'
            '<div class="sidebar-logo-tag">Para quem está mudando de verdade.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Usuário + modo
        hm = u.get("health_mode", "general")
        icon, label, css = _MODE_LABELS.get(hm, _MODE_LABELS["general"])
        trial_str = (
            f" ({u_obj.trial_days_remaining()}d)"
            if eff_plan == "trial" else ""
        )
        plan_lbl = (
            f"⏳ TRIAL{trial_str}"
            if eff_plan == "trial"
            else _PLAN_LABELS.get(eff_plan, "🆓 FREE")
        )
        st.markdown(
            f'<div style="padding:0 0.2rem;margin-bottom:0.6rem;">'
            f'<div style="font-size:0.88rem;font-weight:700;'
            f'color:var(--text);margin-bottom:0.25rem;">'
            f'👤 {u.get("name","")}</div>'
            f'<span class="mode-badge mode-{css}">{icon} {label}</span>'
            f'&nbsp;<span class="plan-{eff_plan}">{plan_lbl}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        plan.trial_banner(u)

        # Stats rápidos
        sm        = nutr.daily_summary()
        hydration = db.get_hydration_today()
        stats     = gami.quick_stats()

        st.markdown(
            f'<div style="display:grid;grid-template-columns:1fr 1fr;'
            f'gap:0.4rem;margin:0.6rem 0;">'
            f'<div class="metric-card">'
            f'<div class="metric-value" style="font-size:1.3rem;">'
            f'{sm["calories"]}</div>'
            f'<div class="metric-label">🔥 kcal hoje</div></div>'
            f'<div class="metric-card">'
            f'<div class="metric-value" style="font-size:1.3rem;">'
            f'{sm["protein"]:.0f}g</div>'
            f'<div class="metric-label">🥩 proteína</div></div>'
            f'<div class="metric-card">'
            f'<div class="metric-value" style="font-size:1.3rem;">'
            f'{hydration}ml</div>'
            f'<div class="metric-label">💧 água</div></div>'
            f'<div class="metric-card">'
            f'<div class="metric-value" style="font-size:1.3rem;">'
            f'{stats["streak"]}d</div>'
            f'<div class="metric-label">📅 sequência</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # XP / nível
        pct = stats["progress_pct"]
        st.markdown(
            f'<div style="margin-bottom:0.6rem;">'
            f'<span class="level-badge">'
            f'{stats["level_icon"]} Nível {stats["level_number"]} · '
            f'{stats["level_name"]}</span>'
            f'<div class="progress-wrap" style="margin-top:0.4rem;">'
            f'<div class="progress-track">'
            f'<div class="progress-fill" style="width:{pct}%;"></div>'
            f'</div>'
            f'<div class="progress-meta">'
            f'<span>{stats["xp"]} XP</span><span>{pct}%</span>'
            f'<span>{"→ " + stats["next_level"] if stats["next_level"] else "MAX"}'
            f'</span></div></div></div>',
            unsafe_allow_html=True,
        )

        # Menu principal
        st.markdown(
            '<div style="border-top:1px solid var(--border);'
            'padding-top:0.6rem;margin-bottom:0.4rem;"></div>',
            unsafe_allow_html=True,
        )
        cur = st.session_state.page
        for icon_m, label_m, key in MENU:
            kind = "primary" if cur == key else "secondary"
            if st.button(f"{icon_m} {label_m}", use_container_width=True,
                         type=kind, key=f"nav_{key}"):
                st.session_state.page = key
                st.rerun()

        # Link do pilar + perfil
        render_pilar_perfil(u, cur)

        # ── EVOLUÇÃO COMPLETA ─────────────────────────────────────────────────
        if st.button(
            "📊 Evolução Completa",
            use_container_width=True,
            key="nav_evolution",
            type="primary" if cur == "evolution" else "secondary",
        ):
            st.session_state.page = "evolution"
            st.rerun()

        # ── COMPARTILHAR CONQUISTA ────────────────────────────────────────────
        if st.button(
            "📤 Compartilhar Conquista",
            use_container_width=True,
            key="nav_share",
            type="primary" if cur == "share" else "secondary",
        ):
            st.session_state.page = "share"
            st.rerun()

        # Dark mode toggle
        novo_dark = st.toggle("🌙 Modo escuro", value=dark,
                              key="dark_mode_toggle")
        if novo_dark != dark:
            db.update_user({"dark_mode": novo_dark})
            st.session_state.user["dark_mode"] = novo_dark
            st.rerun()

        # Sair
        if st.button("🚪 Sair", use_container_width=True, key="nav_logout"):
            _clear_session()

        if u.get("email") == config.DEMO_EMAIL:
            st.markdown(
                '<div style="background:var(--primary-light);'
                'border:1px solid var(--primary-border);'
                'border-radius:var(--radius-sm);padding:0.3rem;'
                'text-align:center;font-size:0.72rem;'
                'color:var(--primary);margin-top:0.4rem;">'
                '🎮 Modo Demo</div>',
                unsafe_allow_html=True,
            )
