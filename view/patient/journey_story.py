"""
Melshape — Narrativa da Jornada (UNIFICADO).

Elimina journey_story_tabs.py — sem import circular.
O paciente vê: motivos, fotos, conquistas, eventos de vida.

Princípio: lembrar o "porquê" é o principal antídoto contra abandono.
"""
import streamlit as st

from views.components.cards import (
    section_header, empty_state, alert, motivational_quote,
)
from views.patient.journey_story_forms import (
    render_form_motivo, render_form_foto, render_form_evento,
)


def render(services: dict, user: dict) -> None:
    db   = services["db"]
    nome = user.get("name", "").split()[0]

    section_header("💛 Sua História", "Por que você começou. Quanto já evoluiu.")

    from services.journey_service import JourneyService
    jornada    = JourneyService(db).garantir_jornada(user)
    jornada_id = jornada.get("id", "") if jornada else ""

    tab_motivo, tab_fotos, tab_conquistas, tab_vida = st.tabs([
        "💛 Por que Comecei",
        "📸 Evolução Visual",
        "🏅 Conquistas",
        "📅 Momentos",
    ])

    with tab_motivo:
        _tab_motivo(db, jornada_id, nome)

    with tab_fotos:
        _tab_fotos(db, user)

    with tab_conquistas:
        _tab_conquistas(db, jornada_id)

    with tab_vida:
        _tab_eventos_vida(db)


# ── POR QUE COMECEI ───────────────────────────────────────────────────────────
def _tab_motivo(db, jornada_id: str, nome: str) -> None:
    motivos = db.get_motivos(jornada_id) if jornada_id else []

    if motivos:
        st.markdown(
            '<p style="font-size:0.72rem;font-weight:700;letter-spacing:0.06em;'
            'color:var(--text-faint);text-transform:uppercase;margin-bottom:0.8rem;">'
            'Seu porquê</p>',
            unsafe_allow_html=True,
        )
        for m in motivos:
            motivational_quote(m.get("motivo", ""))

        streak = db.get_checkin_streak()
        if streak == 0:
            alert(
                f"💛 {nome}, lembre-se do seu porquê. "
                f"Cada recomeço conta.",
                "info",
            )
    else:
        st.markdown(
            '<div style="font-size:0.86rem;color:var(--text-muted);'
            'margin-bottom:1rem;">'
            'Registre seu porquê. É o que vai te fazer voltar nos dias difíceis.'
            '</div>',
            unsafe_allow_html=True,
        )

    if jornada_id:
        render_form_motivo(db, jornada_id, has_motivo=bool(motivos))


# ── EVOLUÇÃO VISUAL ───────────────────────────────────────────────────────────
def _tab_fotos(db, user: dict) -> None:
    perfil_id = db.uid()
    fotos     = db.get_fotos(perfil_id)

    if fotos:
        st.markdown(
            f'<div style="font-size:0.82rem;color:var(--text-muted);'
            f'margin-bottom:0.8rem;">'
            f'<b>{len(fotos)}</b> foto(s) de evolução registrada(s)</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(2)
        for i, f in enumerate(fotos[:6]):
            with cols[i % 2]:
                url     = f.get("url_foto", "")
                legenda = f.get("legenda", "")
                data    = f.get("data_foto", "")[:10]
                peso    = f.get("peso_na_data")
                info    = f"{data}{' · ' + str(peso) + 'kg' if peso else ''}"
                if url.startswith("http"):
                    st.image(url, caption=legenda or info,
                             use_container_width=True)
                else:
                    st.markdown(
                        f'<div style="background:var(--surface-2);'
                        f'border:1px solid var(--border);'
                        f'border-radius:var(--radius-md);'
                        f'padding:1.2rem;text-align:center;'
                        f'color:var(--text-muted);font-size:0.80rem;">'
                        f'📸 {info}<br>{legenda}</div>',
                        unsafe_allow_html=True,
                    )
    else:
        empty_state(
            "📸", "Nenhuma foto ainda",
            "Registre sua evolução visual — é um motivador poderoso",
        )

    st.markdown("---")
    render_form_foto(db, perfil_id, user)


# ── CONQUISTAS DA JORNADA ─────────────────────────────────────────────────────
def _tab_conquistas(db, jornada_id: str) -> None:
    if not jornada_id:
        empty_state("🏅", "Jornada não iniciada")
        return

    conquistas = db.get_conquistas_jornada(jornada_id)

    if conquistas:
        st.markdown(
            f'<div style="font-size:0.82rem;color:var(--text-muted);'
            f'margin-bottom:0.8rem;">'
            f'🏅 <b>{len(conquistas)}</b> conquista(s) nesta jornada</div>',
            unsafe_allow_html=True,
        )
        for c in conquistas:
            data  = c.get("conquistado_em", "")[:10]
            titulo = c.get("titulo", "Conquista")
            desc   = c.get("descricao", "")
            st.markdown(
                f'<div style="display:flex;align-items:flex-start;gap:0.7rem;'
                f'padding:0.7rem;background:var(--primary-light);'
                f'border:1px solid var(--primary-border);'
                f'border-radius:var(--radius-md);margin-bottom:0.4rem;">'
                f'<span style="font-size:1.4rem;">🏅</span>'
                f'<div style="flex:1;">'
                f'<div style="font-weight:700;font-size:0.92rem;color:var(--text);">'
                f'{titulo}</div>'
                f'{"<div style=font-size:0.78rem;color:var(--text-muted);>" + desc + "</div>" if desc else ""}'
                f'</div>'
                f'<span style="font-size:0.74rem;color:var(--text-faint);">'
                f'{data}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        empty_state(
            "🏅", "Nenhuma conquista específica ainda",
            "Continue consistente — as conquistas chegam com o progresso",
        )


# ── MOMENTOS DE VIDA ──────────────────────────────────────────────────────────
def _tab_eventos_vida(db) -> None:
    _TIPO_ICON = {
        "marco":       "🏁",
        "desafio":     "⚡",
        "celebracao":  "🎉",
        "dificuldade": "💪",
        "inicio":      "🌱",
    }

    eventos = db.get_eventos_vida()

    if eventos:
        for ev in eventos:
            tipo   = ev.get("tipo", "marco")
            data   = ev.get("data_evento", "")[:10]
            titulo = ev.get("titulo", "Evento")
            desc   = ev.get("descricao", "")
            icon   = _TIPO_ICON.get(tipo, "📌")
            st.markdown(
                f'<div style="display:flex;gap:0.7rem;align-items:flex-start;'
                f'padding:0.6rem 0;border-bottom:1px solid var(--border-subtle);">'
                f'<span style="font-size:1.2rem;flex-shrink:0;">{icon}</span>'
                f'<div style="flex:1;">'
                f'<div style="font-weight:600;font-size:0.90rem;color:var(--text);">'
                f'{titulo}</div>'
                f'{"<div style=font-size:0.78rem;color:var(--text-muted);>" + desc + "</div>" if desc else ""}'
                f'</div>'
                f'<span style="font-size:0.74rem;color:var(--text-faint);'
                f'flex-shrink:0;">{data}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        empty_state(
            "📅", "Nenhum momento registrado",
            "Guarde os momentos importantes da sua transformação",
        )

    st.markdown("---")
    render_form_evento(db)
