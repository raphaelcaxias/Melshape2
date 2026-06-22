"""
Melshape — Jornada: linha do tempo, marcos e listagem de etapas.
Importado por journey.py.
"""
import streamlit as st
from views.components.cards import empty_state


# ── LINHA DO TEMPO ────────────────────────────────────────────────────────────
def render_linha_do_tempo(db, jornada_id: str) -> None:
    eventos = db.get_eventos(jornada_id, limit=20)

    if not eventos:
        empty_state(
            "📅", "Nenhum evento registrado ainda",
            "Suas ações vão aparecer aqui conforme você avança",
        )
        return

    st.markdown(
        f'<div style="font-size:0.82rem;color:var(--text-muted);'
        f'margin-bottom:0.8rem;">'
        f'<b>{len(eventos)}</b> evento(s) na sua jornada</div>',
        unsafe_allow_html=True,
    )

    _TIPO_CONFIG = {
        "checkin":    ("✅", "var(--success)"),
        "pesagem":    ("⚖️", "var(--primary)"),
        "refeicao":   ("🍽️", "var(--warning)"),
        "marco":      ("🏁", "var(--primary)"),
        "conquista":  ("🏅", "var(--primary)"),
        "agua":       ("💧", "var(--info)"),
        "habito":     ("📋", "var(--text-muted)"),
    }

    for ev in eventos:
        tipo   = ev.get("tipo", "outro")
        emoji, cor = _TIPO_CONFIG.get(tipo, ("📌", "var(--text-muted)"))
        data   = ev.get("criado_em", "")
        data_str = data[:16].replace("T", " ") if data else "—"
        desc   = ev.get("descricao", "")

        st.markdown(
            f'<div style="display:flex;gap:0.8rem;align-items:flex-start;'
            f'padding:0.6rem 0;border-bottom:1px solid var(--border-subtle);">'
            f'<div style="width:28px;height:28px;border-radius:50%;'
            f'background:{cor}20;border:2px solid {cor};'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:0.85rem;flex-shrink:0;">{emoji}</div>'
            f'<div style="flex:1;">'
            f'<div style="font-size:0.86rem;color:var(--text);'
            f'font-weight:500;">{desc}</div>'
            f'<div style="font-size:0.72rem;color:var(--text-faint);'
            f'margin-top:0.1rem;">{data_str}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── MARCOS ────────────────────────────────────────────────────────────────────
def render_marcos(db, jornada_id: str) -> None:
    marcos = db.get_marcos(jornada_id)

    if not marcos:
        empty_state(
            "🏁", "Nenhum marco alcançado ainda",
            "Continue consistente — os marcos chegam automaticamente",
        )
        return

    st.markdown(
        f'<div style="font-size:0.82rem;color:var(--text-muted);'
        f'margin-bottom:0.8rem;">'
        f'<b>{len(marcos)}</b> marco(s) alcançado(s)</div>',
        unsafe_allow_html=True,
    )

    for m in marcos:
        data    = m.get("data_marco", "")
        data_str = data[:10] if data else "—"
        titulo  = m.get("titulo", "Marco")
        desc    = m.get("descricao", "")

        st.markdown(
            f'<div class="metric-card fade-in" style="margin-bottom:0.5rem;">'
            f'<div style="display:flex;align-items:flex-start;gap:0.7rem;">'
            f'<span style="font-size:1.5rem;">🏁</span>'
            f'<div style="flex:1;">'
            f'<div style="font-weight:700;font-size:0.92rem;color:var(--text);">'
            f'{titulo}</div>'
            f'{"<div style=font-size:0.80rem;color:var(--text-muted);margin-top:0.1rem;>" + desc + "</div>" if desc else ""}'
            f'</div>'
            f'<div style="font-size:0.74rem;color:var(--text-faint);'
            f'flex-shrink:0;">{data_str}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── TODAS AS ETAPAS ───────────────────────────────────────────────────────────
def _tab_todas_etapas(prog: dict) -> None:
    todas = sorted(
        prog["concluidas"] + prog["pendentes"],
        key=lambda x: x.get("ordem", 0),
    )

    for etapa in todas:
        concluida = etapa.get("concluida", False)
        icone     = etapa.get("icone", "📍")
        cor_borda = "var(--success)" if concluida else "var(--border)"
        cor_texto = "var(--text-muted)" if concluida else "var(--text)"

        badge_html = ""
        if concluida:
            badge_html = (
                '<span style="padding:0.12rem 0.55rem;border-radius:9999px;'
                'font-size:0.72rem;font-weight:700;flex-shrink:0;'
                'background:var(--success-bg);color:var(--success);'
                'border:1px solid var(--success);">✅ Concluída</span>'
            )

        st.markdown(
            f'<div style="display:flex;align-items:flex-start;gap:0.8rem;'
            f'padding:0.8rem;border:1px solid {cor_borda};'
            f'border-radius:var(--radius-md);margin-bottom:0.5rem;'
            f'background:var(--surface);">'
            f'<span style="font-size:1.5rem;flex-shrink:0;">{icone}</span>'
            f'<div style="flex:1;">'
            f'<div style="font-weight:700;font-size:0.92rem;color:{cor_texto};">'
            f'Etapa {etapa.get("ordem","")} — {etapa.get("nome","")}</div>'
            f'<div style="font-size:0.80rem;color:var(--text-muted);'
            f'margin-top:0.1rem;">{etapa.get("descricao","")}</div>'
            f'</div>'
            f'{badge_html}'
            f'</div>',
            unsafe_allow_html=True,
        )
