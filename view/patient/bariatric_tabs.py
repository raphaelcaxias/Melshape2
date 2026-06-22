"""Melshape — Bariátrica: tabs de suplementação e histórico."""
import streamlit as st
from views.components.cards import empty_state, alert
import config

# ── SUPLEMENTAÇÃO ──────────────────────────────────────────────────────────────
def _tab_suplementos(resumo: dict) -> None:
    supls = resumo["suplementos"]
    fase  = resumo["fase"]["nome"]

    st.markdown(
        f'<div style="font-size:0.82rem;color:var(--text-muted);'
        f'margin-bottom:0.8rem;">'
        f'💊 Suplementação obrigatória — fase <b>{fase}</b></div>',
        unsafe_allow_html=True,
    )

    if not supls:
        empty_state("💊", "Sem suplementos para esta fase")
        return

    for s in supls:
        dose_str = f'{s.get("dose","—")} {s.get("unit","")}'.strip()
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;padding:0.55rem 0.8rem;'
            f'border:1px solid var(--border);border-radius:var(--radius-md);'
            f'margin-bottom:0.35rem;background:var(--surface);">'
            f'<div>'
            f'<div style="font-weight:600;font-size:0.90rem;color:var(--text);">'
            f'💊 {s["name"]}</div>'
            f'</div>'
            f'<span style="font-size:0.80rem;color:var(--primary);'
            f'font-weight:600;">{dose_str}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    alert(
        "⚕️ Suplementação conforme orientação médica. "
        "Doses podem variar por prescrição individual.",
        "info",
    )


# ── HISTÓRICO DE FASES ────────────────────────────────────────────────────────
def _tab_historico(db, resumo: dict) -> None:
    hist  = db.get_historico_fases()
    cirug = resumo.get("cirurgia")

    if cirug:
        st.markdown(
            f'<div class="metric-card fade-in" style="margin-bottom:0.8rem;">'
            f'<div style="font-weight:700;color:var(--text);">'
            f'🔪 Cirurgia: {resumo["tipo"]}</div>'
            f'<div style="font-size:0.80rem;color:var(--text-muted);">'
            f'Data: {cirug.get("data_cirurgia","—")[:10]} · '
            f'Peso pré: {cirug.get("peso_pre_cirurgia","—")} kg</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if not hist:
        empty_state("📅", "Sem histórico de fases", "")
        return

    for h in hist:
        fase_key  = h.get("fase", "")
        nome      = config.BARIATRIC_PHASES.get(
            fase_key, {}
        ).get("name", fase_key)
        data      = h.get("iniciada_em", "")[:10]
        obs       = h.get("observacao", "")
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;'
            f'padding:0.5rem 0;border-bottom:1px solid var(--border-subtle);">'
            f'<div>'
            f'<div style="font-weight:600;font-size:0.88rem;">{nome}</div>'
            f'{"<div style=font-size:0.76rem;color:var(--text-muted);>" + obs + "</div>" if obs else ""}'
            f'</div>'
            f'<span style="font-size:0.76rem;color:var(--text-faint);">{data}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


