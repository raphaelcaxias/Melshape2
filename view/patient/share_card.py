"""
Melshape — Card de Conquista para Compartilhamento.

Gera um card visual (HTML → st.components) que o paciente
pode capturar e compartilhar no Instagram, WhatsApp, etc.

Aquisição orgânica zero custo.
Gatilho: nova badge, streak especial (7, 14, 30, 90 dias), meta concluída.
"""
import streamlit as st
from views.components.cards import section_header, empty_state


def render(services: dict, user: dict) -> None:
    db   = services["db"]
    gami = services["gamification"]
    nome = user.get("name", "").split()[0]
    hm   = user.get("health_mode", "general")

    section_header(
        "📤 Compartilhar Conquista",
        "Mostre seu progresso para o mundo",
    )

    streak      = db.get_checkin_streak()
    conquistas  = db.get_achievements()
    ultima_ach  = conquistas[-1] if conquistas else None
    stats       = gami.quick_stats()

    tab_streak, tab_badge, tab_meta = st.tabs([
        "🔥 Sequência",
        "🏅 Badge",
        "🎯 Meta",
    ])

    with tab_streak:
        _card_streak(nome, streak, hm, stats)

    with tab_badge:
        _card_badge(nome, ultima_ach, stats)

    with tab_meta:
        _card_meta(nome, db, hm, stats)


# ── CARD DE STREAK ────────────────────────────────────────────────────────────
def _card_streak(nome: str, streak: int,
                  hm: str, stats: dict) -> None:
    if streak < 3:
        st.markdown(
            '<div style="font-size:0.84rem;color:var(--text-muted);">'
            'Complete pelo menos 3 dias seguidos para gerar seu card.</div>',
            unsafe_allow_html=True,
        )
        return

    _PILARES = {
        "general":   ("⚖️", "Emagrecimento"),
        "fitness":   ("💪", "Fitness"),
        "bariatric": ("🔪", "Pós-Bariátrica"),
        "glp1":      ("💉", "GLP-1"),
    }
    icon_p, label_p = _PILARES.get(hm, ("🔥", "Transformação"))
    nivel = stats.get("level_name", "Iniciante")
    xp    = stats.get("xp", 0)

    html = _base_card(f"""
        <div style="font-size:3.5rem;margin-bottom:0.5rem;">🔥</div>
        <div style="font-size:1rem;color:rgba(255,255,255,.8);
        margin-bottom:0.3rem;">{nome}</div>
        <div style="font-size:4rem;font-weight:900;
        font-family:Sora,sans-serif;line-height:1;">
            {streak}
        </div>
        <div style="font-size:1.1rem;color:rgba(255,255,255,.9);">
            dias consecutivos
        </div>
        <div style="margin-top:1rem;font-size:0.85rem;
        color:rgba(255,255,255,.7);">
            {icon_p} {label_p} · Nível {nivel} · {xp} XP
        </div>
        <div style="margin-top:1.5rem;font-size:0.75rem;
        color:rgba(255,255,255,.5);">
            melshape.com.br
        </div>
    """)

    st.components.v1.html(html, height=420)
    _instrucoes_compartilhamento()


# ── CARD DE BADGE ─────────────────────────────────────────────────────────────
def _card_badge(nome: str, conquista: dict,
                 stats: dict) -> None:
    if not conquista:
        empty_state("🏅", "Nenhuma conquista ainda",
                    "Complete hábitos e check-ins para desbloquear badges")
        return

    titulo = conquista.get("title",
             conquista.get("achievement_name", "Conquista"))
    data   = conquista.get("unlocked_at", "")[:10]
    nivel  = stats.get("level_name", "Iniciante")

    html = _base_card(f"""
        <div style="font-size:3.5rem;margin-bottom:0.5rem;">🏅</div>
        <div style="font-size:1rem;color:rgba(255,255,255,.8);
        margin-bottom:0.5rem;">{nome} conquistou</div>
        <div style="font-size:1.4rem;font-weight:800;
        font-family:Sora,sans-serif;line-height:1.2;
        padding:0 1rem;">
            {titulo}
        </div>
        <div style="margin-top:0.8rem;font-size:0.85rem;
        color:rgba(255,255,255,.7);">
            Nível {nivel}
        </div>
        <div style="margin-top:0.4rem;font-size:0.78rem;
        color:rgba(255,255,255,.55);">
            {data}
        </div>
        <div style="margin-top:1.5rem;font-size:0.75rem;
        color:rgba(255,255,255,.5);">
            melshape.com.br
        </div>
    """, cor_inicio="#6366F1", cor_fim="#3D5A73")

    st.components.v1.html(html, height=420)
    _instrucoes_compartilhamento()


# ── CARD DE META ──────────────────────────────────────────────────────────────
def _card_meta(nome: str, db, hm: str, stats: dict) -> None:
    try:
        jornada = db.get_jornada_ativa()
        if not jornada:
            empty_state("🎯", "Nenhuma jornada ativa")
            return
        metas = db.get_metas(jornada["id"])
        concluidas = [m for m in metas if m.get("concluida")]
    except Exception:
        concluidas = []

    if not concluidas:
        empty_state("🎯", "Nenhuma meta concluída ainda",
                    "Conclua sua primeira meta para gerar o card")
        return

    meta   = concluidas[-1]
    titulo = meta.get("titulo", "Meta concluída")
    nivel  = stats.get("level_name", "Iniciante")
    xp     = stats.get("xp", 0)

    html = _base_card(f"""
        <div style="font-size:3.5rem;margin-bottom:0.5rem;">🎯</div>
        <div style="font-size:1rem;color:rgba(255,255,255,.8);
        margin-bottom:0.5rem;">{nome} concluiu a meta</div>
        <div style="font-size:1.3rem;font-weight:800;
        font-family:Sora,sans-serif;line-height:1.3;
        padding:0 1rem;">
            {titulo}
        </div>
        <div style="margin-top:1rem;font-size:0.85rem;
        color:rgba(255,255,255,.7);">
            {xp} XP acumulados · Nível {nivel}
        </div>
        <div style="margin-top:1.5rem;font-size:0.75rem;
        color:rgba(255,255,255,.5);">
            melshape.com.br
        </div>
    """, cor_inicio="#10B981", cor_fim="#065F46")

    st.components.v1.html(html, height=420)
    _instrucoes_compartilhamento()


# ── BASE DO CARD ──────────────────────────────────────────────────────────────
def _base_card(conteudo: str,
               cor_inicio: str = "#C9A84C",
               cor_fim:    str = "#3D5A73") -> str:
    return f"""
    <div style="
        width:360px;height:400px;
        background:linear-gradient(135deg,{cor_inicio},{cor_fim});
        border-radius:24px;
        display:flex;flex-direction:column;
        align-items:center;justify-content:center;
        text-align:center;
        color:white;
        font-family:'DM Sans',Arial,sans-serif;
        padding:2rem;
        box-shadow:0 20px 60px rgba(0,0,0,.3);
        margin:0 auto;
    ">
        {conteudo}
    </div>
    """


def _instrucoes_compartilhamento() -> None:
    st.markdown(
        '<div style="font-size:0.78rem;color:var(--text-muted);'
        'text-align:center;margin-top:0.8rem;">'
        '📸 Tire um print da tela e compartilhe no Instagram, '
        'WhatsApp ou Stories!</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-size:0.74rem;color:var(--text-faint);'
        'text-align:center;margin-top:0.3rem;">'
        '#Melshape #Transformação #Consistência</div>',
        unsafe_allow_html=True,
    )
