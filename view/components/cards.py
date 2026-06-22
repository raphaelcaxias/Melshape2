"""
Melshape — Componentes visuais reutilizáveis.
REGRA: zero cores hardcoded. Tudo via var(--css).
REGRA: usar st.toast() para feedback rápido, não st.success().
"""
import streamlit as st


def metric_card(value: str, label: str, icon: str = "📊",
                color: str = "") -> None:
    css = f"metric-value {color}".strip()
    st.markdown(
        f'<div class="metric-card fade-in">'
        f'<div class="{css}">{value}</div>'
        f'<div class="metric-label">{icon} {label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def progress_bar(current: float, maximum: float,
                 label_left: str = "", label_right: str = "",
                 color: str = "") -> None:
    pct = max(0, min(100, int(current / maximum * 100) if maximum > 0 else 0))
    if not color:
        color = "danger" if pct >= 100 else "warning" if pct >= 85 else ""
    st.markdown(
        f'<div class="progress-wrap">'
        f'<div class="progress-track">'
        f'<div class="progress-fill {color}" style="width:{pct}%"></div>'
        f'</div>'
        f'<div class="progress-meta">'
        f'<span>{label_left}</span><span>{pct}%</span><span>{label_right}</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def empty_state(icon: str, message: str, hint: str = "") -> None:
    hint_html = f'<p class="empty-hint">{hint}</p>' if hint else ""
    st.markdown(
        f'<div class="empty-state fade-in">'
        f'<div class="empty-icon">{icon}</div>'
        f'<p class="empty-msg">{message}</p>{hint_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def achievement_card(title: str, date_str: str = "") -> None:
    date_html = (
        f'<div style="font-size:0.72rem;color:var(--text-muted);'
        f'margin-top:0.2rem;">{date_str}</div>'
        if date_str else ""
    )
    st.markdown(
        f'<div class="achievement-card">'
        f'<div class="medal">🏅</div>'
        f'<div><div class="title">{title}</div>{date_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def challenge_card(emoji: str, title: str, xp: int) -> None:
    st.markdown(
        f'<div class="challenge-card">'
        f'<span class="challenge-title">{emoji} {title}</span>'
        f'<span class="xp-badge">+{xp} XP</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def meal_item(time: str, food: str, calories: int, score: int = 0) -> None:
    score_html = (
        f'<div class="meal-score">Score: {score}/100</div>' if score else ""
    )
    st.markdown(
        f'<div class="meal-item">'
        f'<div><div class="meal-name">{food}</div>'
        f'<div class="meal-time">⏰ {time}</div>{score_html}</div>'
        f'<div class="meal-cal">{calories} kcal</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def alert(message: str, kind: str = "warning") -> None:
    """kind: warning | error | success | info"""
    st.markdown(
        f'<div class="alert-{kind}">{message}</div>',
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "") -> None:
    sub = (
        f'<p style="color:var(--text-muted);font-size:0.86rem;'
        f'margin:0.18rem 0 0;">{subtitle}</p>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="margin-bottom:1.1rem;">'
        f'<h2 style="font-family:var(--font-display);font-weight:700;'
        f'color:var(--text);margin:0;">{title}</h2>{sub}'
        f'</div>',
        unsafe_allow_html=True,
    )


def feature_card(icon: str, title: str, description: str) -> None:
    st.markdown(
        f'<div class="feature-card">'
        f'<span class="icon">{icon}</span>'
        f'<h3>{title}</h3><p>{description}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


def mode_badge(health_mode: str, label: str) -> None:
    st.markdown(
        f'<span class="mode-badge mode-{health_mode}">{label}</span>',
        unsafe_allow_html=True,
    )


def motivational_quote(text: str) -> None:
    st.markdown(
        f'<div class="quote-card fade-in-fast">💬 {text}</div>',
        unsafe_allow_html=True,
    )


def medical_disclaimer() -> None:
    import config
    st.markdown(
        f'<div class="medical-disclaimer">{config.MEDICAL_DISCLAIMER}</div>',
        unsafe_allow_html=True,
    )


def hydration_bar(current_ml: int, goal_ml: int) -> None:
    pct   = min(100, int(current_ml / goal_ml * 100)) if goal_ml > 0 else 0
    drops = "💧" * min(8, max(1, pct // 13))
    st.markdown(
        f'<div class="hydration-bar">'
        f'<span class="hydration-drops">{drops}</span>'
        f'<span class="hydration-text">{current_ml} ml / {goal_ml} ml ({pct}%)</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def show_new_achievements(unlocked: list) -> None:
    """
    Exibe conquistas novas via st.toast() — não usar st.success().
    """
    if not unlocked:
        return
    for title in unlocked:
        st.toast(f"🏆 {title}", icon="🎉")


def fab_button(label: str = "+") -> None:
    """Botão flutuante para acesso rápido ao registro."""
    st.markdown(
        f'<div class="fab">{label}</div>',
        unsafe_allow_html=True,
    )


def xp_toast(amount: int, motivo: str = "") -> None:
    """Toast de XP ganho."""
    msg = f"⭐ +{amount} XP" + (f" — {motivo}" if motivo else "")
    st.toast(msg, icon="⭐")
