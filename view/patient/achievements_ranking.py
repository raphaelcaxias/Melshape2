"""
Melshape — Ranking de Gamificação.
View usada: vw_ranking_gamificacao
"""
import streamlit as st
from views.components.cards import empty_state, metric_card


_MEDALHAS = {1: "🥇", 2: "🥈", 3: "🥉"}


def render_ranking(db, user: dict) -> None:
    nome_atual = user.get("name", "")
    ranking    = _buscar_ranking(db)

    if not ranking:
        empty_state(
            "🏆", "Ranking em construção",
            "Seja o primeiro a aparecer aqui!",
        )
        # Mostra posição do próprio usuário mesmo sem ranking
        xp_proprio = db.get_xp()
        if xp_proprio > 0:
            metric_card(str(xp_proprio), "Seu XP total", "⭐")
        return

    # Posição do usuário no ranking
    pos_atual = next(
        (i + 1 for i, r in enumerate(ranking)
         if r.get("nome_completo", "") == nome_atual),
        None,
    )
    if pos_atual:
        st.markdown(
            f'<div class="metric-card fade-in" style="'
            f'border-color:var(--primary);margin-bottom:0.8rem;">'
            f'<div style="font-size:0.76rem;color:var(--text-muted);'
            f'margin-bottom:0.2rem;">Sua posição</div>'
            f'<div style="font-size:2rem;font-weight:800;color:var(--primary);">'
            f'#{pos_atual}</div>'
            f'<div style="font-size:0.80rem;color:var(--text-muted);">'
            f'de {len(ranking)} participantes</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="font-size:0.82rem;color:var(--text-muted);'
        f'margin-bottom:0.6rem;">'
        f'Top <b>{len(ranking)}</b> · atualizado agora</div>',
        unsafe_allow_html=True,
    )

    for i, row in enumerate(ranking):
        pos       = i + 1
        nome      = row.get("nome_completo", "—")
        xp        = int(row.get("xp_total") or 0)
        nivel     = row.get("nivel", "Iniciante")
        badges    = int(row.get("total_badges") or 0)
        eh_eu     = nome == nome_atual
        medalha   = _MEDALHAS.get(pos, f"#{pos}")
        destaque  = "border-color:var(--primary);" if eh_eu else ""
        bg        = "background:var(--primary-light);" if eh_eu else ""

        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0.75rem;'
            f'padding:0.65rem 0.8rem;border:1px solid var(--border);'
            f'border-radius:var(--radius-md);margin-bottom:0.4rem;'
            f'background:var(--surface);{destaque}{bg}">'
            f'<div style="font-size:1.2rem;width:28px;text-align:center;'
            f'flex-shrink:0;">{medalha}</div>'
            f'<div style="flex:1;">'
            f'<div style="font-weight:{"800" if eh_eu else "600"};'
            f'font-size:0.92rem;color:var(--text);">'
            f'{nome}{"  👈 você" if eh_eu else ""}</div>'
            f'<div style="font-size:0.75rem;color:var(--text-muted);">'
            f'{nivel} · {badges} badges</div>'
            f'</div>'
            f'<div style="font-weight:700;color:var(--primary);'
            f'font-size:0.95rem;">{xp} XP</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _buscar_ranking(db) -> list:
    if db.is_real and db.client:
        try:
            r = (db.client.table("vw_ranking_gamificacao")
                 .select("nome_completo,xp_total,nivel,total_badges")
                 .order("xp_total", desc=True)
                 .limit(50)
                 .execute())
            return r.data or []
        except Exception as e:
            import logging
            logging.getLogger("Melshape.Ranking").warning(f"ranking: {e}")
    return []
