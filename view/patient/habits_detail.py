"""
Melshape — Detalhe de Hábito.
Calendário visual 21 dias, streak, aderência e melhor sequência.
Importado por habits.py.
"""
import streamlit as st
from services.habit_service import HabitService
from views.components.cards import metric_card


def render_detalhe_habito(habito: dict, svc: HabitService) -> None:
    hid   = habito.get("id", "")
    nome  = habito.get("nome", "")
    icone = habito.get("icone", "⭐")

    streak  = svc.streak_habito(hid)
    melhor  = svc.melhor_streak(hid)
    ader_7  = svc.aderencia(hid, days=7)
    ader_30 = svc.aderencia(hid, days=30)

    st.markdown(
        f'<div style="font-weight:700;font-size:1rem;color:var(--text);'
        f'margin-bottom:0.8rem;">{icone} {nome}</div>',
        unsafe_allow_html=True,
    )

    # Métricas
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card(
            f"{streak}d", "Streak atual", "🔥",
            "success" if streak >= 7 else "warning" if streak >= 3 else "",
        )
    with c2:
        metric_card(f"{melhor}d", "Melhor sequência", "🏆")
    with c3:
        metric_card(
            f"{ader_7:.0f}%", "Aderência 7d", "📊",
            "success" if ader_7 >= 80 else "warning" if ader_7 >= 50 else "error",
        )
    with c4:
        metric_card(
            f"{ader_30:.0f}%", "Aderência 30d", "📅",
            "success" if ader_30 >= 80 else "warning" if ader_30 >= 50 else "error",
        )

    st.markdown(
        '<div style="margin:0.8rem 0;font-size:0.80rem;font-weight:700;'
        'color:var(--text-faint);text-transform:uppercase;'
        'letter-spacing:0.06em;">Calendário — últimos 21 dias</div>',
        unsafe_allow_html=True,
    )

    # Calendário em grade 7×3
    cal = svc.calendario(hid, days=21)
    _render_calendario(cal)

    # Mensagem motivacional por streak
    if streak >= 30:
        st.markdown(
            '<div class="alert-success">'
            '🏆 Incrível! 30+ dias seguidos. Esse hábito já é parte de você.'
            '</div>',
            unsafe_allow_html=True,
        )
    elif streak >= 7:
        st.markdown(
            '<div class="alert-success">'
            f'🔥 {streak} dias seguidos! Você está construindo algo sólido.'
            '</div>',
            unsafe_allow_html=True,
        )
    elif streak == 0 and ader_7 < 50:
        st.markdown(
            '<div class="alert-warning">'
            '⚡ Aderência baixa esta semana. Que tal começar hoje?'
            '</div>',
            unsafe_allow_html=True,
        )


def _render_calendario(cal: list) -> None:
    """Renderiza calendário em grade 7 colunas × N semanas."""
    semanas = [cal[i:i + 7] for i in range(0, len(cal), 7)]

    # Cabeçalho dos dias
    dias_label = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    header_html = "".join(
        f'<div style="text-align:center;font-size:0.68rem;'
        f'color:var(--text-faint);font-weight:600;">{d}</div>'
        for d in dias_label
    )
    st.markdown(
        f'<div style="display:grid;grid-template-columns:repeat(7,1fr);'
        f'gap:4px;margin-bottom:4px;">{header_html}</div>',
        unsafe_allow_html=True,
    )

    # Células
    for semana in semanas:
        cells_html = ""
        for dia in semana:
            if dia["futuro"]:
                bg  = "var(--surface-2)"
                bdr = "var(--border)"
                txt = ""
            elif dia["concluido"]:
                bg  = "var(--success)"
                bdr = "var(--success)"
                txt = "✓"
            else:
                bg  = "var(--error-bg)"
                bdr = "var(--error)"
                txt = "·"

            data_short = dia["data"][8:]  # dia do mês
            cells_html += (
                f'<div style="background:{bg};border:1px solid {bdr};'
                f'border-radius:var(--radius-sm);padding:0.3rem;'
                f'text-align:center;min-height:36px;">'
                f'<div style="font-size:0.65rem;color:var(--text-faint);">'
                f'{data_short}</div>'
                f'<div style="font-size:0.80rem;color:#fff;font-weight:700;">'
                f'{txt}</div>'
                f'</div>'
            )

        st.markdown(
            f'<div style="display:grid;grid-template-columns:repeat(7,1fr);'
            f'gap:4px;margin-bottom:4px;">{cells_html}</div>',
            unsafe_allow_html=True,
        )

    # Legenda
    st.markdown(
        '<div style="display:flex;gap:1rem;margin-top:0.5rem;'
        'font-size:0.74rem;color:var(--text-muted);">'
        '<span style="display:flex;align-items:center;gap:0.3rem;">'
        '<span style="width:12px;height:12px;border-radius:3px;'
        'background:var(--success);display:inline-block;"></span>Concluído</span>'
        '<span style="display:flex;align-items:center;gap:0.3rem;">'
        '<span style="width:12px;height:12px;border-radius:3px;'
        'background:var(--error-bg);border:1px solid var(--error);'
        'display:inline-block;"></span>Não feito</span>'
        '<span style="display:flex;align-items:center;gap:0.3rem;">'
        '<span style="width:12px;height:12px;border-radius:3px;'
        'background:var(--surface-2);border:1px solid var(--border);'
        'display:inline-block;"></span>Futuro</span>'
        '</div>',
        unsafe_allow_html=True,
    )
