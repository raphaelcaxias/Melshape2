"""
Melshape — Tela de Conquistas, Ranking e Desafios.

Views usadas:
  vw_ranking_gamificacao   → ranking global de XP
  vw_conquistas_usuario    → badges do paciente
  vw_recompensa_pendente   → XP a resgatar

Tabelas:
  badges                   → catálogo completo de badges
  desafios, desafios_usuario → desafios ativos e progresso
"""
import streamlit as st

from services.gamification_service import GamificationService, ACHIEVEMENTS
from views.components.cards import (
    section_header, empty_state, metric_card,
    achievement_card, challenge_card, show_new_achievements,
)
from views.patient.achievements_ranking import render_ranking
from views.patient.achievements_challenges import render_desafios


def render(services: dict, user: dict) -> None:
    db   = services["db"]
    gami = GamificationService(db)

    section_header("🏆 Conquistas", "Seu histórico de vitórias e evolução")

    # Verifica conquistas novas ao entrar
    novos = gami.check_achievements(user)
    show_new_achievements(novos)

    stats = gami.quick_stats()

    # ── HEADER DE STATS ───────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card(str(stats["xp"]), "XP Total", "⭐")
    with c2:
        metric_card(
            f'{stats["level_icon"]} {stats["level_number"]}',
            stats["level_name"], "🎖️",
        )
    with c3:
        metric_card(str(stats["total_badges"]), "Badges", "🏅")
    with c4:
        metric_card(
            f'{stats["streak"]}d', "Sequência", "🔥",
            "success" if stats["streak"] >= 7 else "",
        )

    # Barra XP → próximo nível
    pct     = stats["progress_pct"]
    next_lv = stats.get("next_level", "MAX")
    xp_next = stats.get("xp_to_next", 0)
    st.markdown(
        f'<div style="margin:0.6rem 0;">'
        f'<div style="font-size:0.76rem;color:var(--text-muted);'
        f'margin-bottom:0.3rem;">'
        f'{"→ " + next_lv + " — faltam " + str(xp_next) + " XP" if next_lv else "Nível máximo!"}'
        f'</div>'
        f'<div class="progress-track">'
        f'<div class="progress-fill" style="width:{pct}%;"></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="border-top:1px solid var(--border);margin:0.8rem 0;"></div>',
        unsafe_allow_html=True,
    )

    tab_badges, tab_desafios, tab_ranking = st.tabs([
        "🏅 Badges",
        "🎯 Desafios",
        "🏆 Ranking",
    ])

    with tab_badges:
        _tab_badges(db, gami)

    with tab_desafios:
        render_desafios(db, gami)

    with tab_ranking:
        render_ranking(db, user)


# ── BADGES ────────────────────────────────────────────────────────────────────
def _tab_badges(db, gami: GamificationService) -> None:
    conquistadas = {
        a.get("achievement_name", "") for a in db.get_achievements()
    }
    total_cat    = len(ACHIEVEMENTS)
    total_ganhas = len(conquistadas)

    st.markdown(
        f'<div style="font-size:0.82rem;color:var(--text-muted);'
        f'margin-bottom:0.8rem;">'
        f'<b>{total_ganhas}</b> de <b>{total_cat}</b> badges desbloqueadas</div>',
        unsafe_allow_html=True,
    )

    # Desbloqueadas primeiro
    desbloqueadas = [a for a in ACHIEVEMENTS if a["name"] in conquistadas]
    bloqueadas    = [a for a in ACHIEVEMENTS if a["name"] not in conquistadas]

    if desbloqueadas:
        st.markdown(
            '<div style="font-size:0.74rem;font-weight:700;'
            'letter-spacing:0.06em;color:var(--text-faint);'
            'text-transform:uppercase;margin-bottom:0.4rem;">'
            'Conquistadas</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(2)
        for i, a in enumerate(desbloqueadas):
            with cols[i % 2]:
                achievement_card(a["title"], f'+{a["xp"]} XP')

    if bloqueadas:
        st.markdown(
            '<div style="font-size:0.74rem;font-weight:700;'
            'letter-spacing:0.06em;color:var(--text-faint);'
            'text-transform:uppercase;margin:0.8rem 0 0.4rem;">'
            'Ainda não desbloqueadas</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(2)
        for i, a in enumerate(bloqueadas):
            with cols[i % 2]:
                st.markdown(
                    f'<div style="background:var(--surface-2);'
                    f'border:1px solid var(--border);'
                    f'border-radius:var(--radius-md);'
                    f'padding:0.65rem 0.8rem;margin-bottom:0.4rem;'
                    f'opacity:0.55;">'
                    f'<div style="font-size:1.1rem;">🔒</div>'
                    f'<div style="font-size:0.82rem;font-weight:600;'
                    f'color:var(--text-muted);margin-top:0.2rem;">'
                    f'{a["title"]}</div>'
                    f'<div style="font-size:0.72rem;color:var(--text-faint);">'
                    f'{a["desc"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    if not desbloqueadas and not bloqueadas:
        empty_state("🏅", "Sem badges ainda", "Continue usando o app!")
