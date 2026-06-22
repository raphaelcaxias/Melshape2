"""
Melshape — Tela GLP-1.

Para pacientes usando Ozempic, Wegovy, Mounjaro, Saxenda etc.
Registro de dose, monitoramento de sintomas, adesão e evolução.
"""
import streamlit as st

from services.glp1_service import GLP1Service
from views.components.cards import (
    section_header, empty_state, metric_card, alert,
    xp_toast, show_new_achievements,
)
from views.patient.glp1_forms import render_form_dose, render_form_sintomas
import config


def render(services: dict, user: dict) -> None:
    db   = services["db"]
    gami = services["gamification"]
    svc  = GLP1Service(db)

    # Valida pilar
    if user.get("health_mode") != "glp1" and not user.get("uses_glp1"):
        _tela_nao_glp1()
        return

    section_header("💉 Acompanhamento GLP-1", "Monitore seu tratamento e evolução")

    resumo = svc.resumo(user)
    _bloco_resumo(resumo)

    # Alertas de sintomas graves no topo
    alertas = svc.alertas_sintomas()
    for al in alertas:
        alert(al, "error" if "⚠️" in al else "warning")

    st.markdown(
        '<div style="border-top:1px solid var(--border);margin:0.8rem 0;"></div>',
        unsafe_allow_html=True,
    )

    tab_dose, tab_sint, tab_hist = st.tabs([
        "💉 Registrar Dose",
        "📋 Sintomas",
        "📈 Histórico",
    ])

    with tab_dose:
        render_form_dose(db, svc, gami, user, resumo)

    with tab_sint:
        render_form_sintomas(db, svc, gami, user)

    with tab_hist:
        _tab_historico(db, svc)


# ── BLOCO RESUMO ─────────────────────────────────────────────────────────────
def _bloco_resumo(resumo: dict) -> None:
    fase  = resumo["fase"]
    dias  = resumo["dias"]
    ades  = resumo["adesao"]
    med   = resumo["medicamento"] or "—"
    dose  = resumo["dose_atual"]  or "—"
    prox  = resumo["proxima_dose"] or "—"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="metric-card fade-in">'
            f'<div style="font-size:1.4rem;">{fase["icon"]}</div>'
            f'<div style="font-weight:700;font-size:0.92rem;color:var(--text);">'
            f'{fase["label"]}</div>'
            f'<div style="font-size:0.74rem;color:var(--text-muted);">'
            f'{fase["desc"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        metric_card(
            f"{dias}d" if dias is not None else "—",
            "Dias de tratamento", "📅",
        )
    with c3:
        cor_ades = (
            "success" if ades["pct"] >= 80
            else "warning" if ades["pct"] >= 50
            else "error"
        )
        metric_card(f"{ades['pct']}%", "Adesão (4 sem.)", "✅", cor_ades)
    with c4:
        st.markdown(
            f'<div class="metric-card fade-in">'
            f'<div style="font-size:0.78rem;color:var(--text-muted);">'
            f'Medicamento</div>'
            f'<div style="font-weight:700;font-size:0.88rem;color:var(--text);">'
            f'{med}</div>'
            f'<div style="font-size:0.76rem;color:var(--primary);">'
            f'Dose: {dose}</div>'
            f'<div style="font-size:0.74rem;color:var(--text-muted);">'
            f'Próxima: {prox}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── HISTÓRICO ─────────────────────────────────────────────────────────────────
def _tab_historico(db, svc: GLP1Service) -> None:
    doses = db.get_doses_glp1(days=90)

    if not doses:
        empty_state(
            "💉", "Nenhuma dose registrada",
            "Registre sua primeira dose na aba 'Registrar Dose'",
        )
        return

    st.markdown(
        f'<div style="font-size:0.82rem;color:var(--text-muted);'
        f'margin-bottom:0.8rem;">'
        f'<b>{len(doses)}</b> dose(s) nos últimos 90 dias</div>',
        unsafe_allow_html=True,
    )

    for d in doses:
        data   = d.get("data_aplicacao", "")[:10]
        med    = d.get("medicamento", "—")
        dose   = d.get("dose", "—")
        fase   = d.get("fase", "")
        obs    = d.get("observacao", "")
        fases  = {
            "adapting": "🔬 Adaptação", "maintenance": "✅ Manutenção",
            "tapering":  "📉 Desmame",  "stopped": "⏹️ Parado",
        }
        fase_label = fases.get(fase, fase)

        st.markdown(
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:flex-start;padding:0.6rem 0.8rem;'
            f'border:1px solid var(--border);border-radius:var(--radius-md);'
            f'margin-bottom:0.4rem;background:var(--surface);">'
            f'<div>'
            f'<div style="font-weight:600;font-size:0.90rem;color:var(--text);">'
            f'💉 {dose} — {med}</div>'
            f'<div style="font-size:0.76rem;color:var(--text-muted);">'
            f'{fase_label}'
            f'{"  ·  " + obs if obs else ""}</div>'
            f'</div>'
            f'<div style="font-size:0.78rem;color:var(--text-faint);">'
            f'{data}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── TELA PARA NÃO GLP-1 ───────────────────────────────────────────────────────
def _tela_nao_glp1() -> None:
    section_header("💉 GLP-1", "Acompanhamento de medicamentos")
    alert(
        "Esta seção é para pacientes usando medicamentos GLP-1 "
        "(Ozempic, Wegovy, Mounjaro, Saxenda). "
        "Atualize seu perfil para ativar este módulo.",
        "info",
    )
    if st.button("Ir para o Perfil →", use_container_width=True,
                 key="glp1_go_profile"):
        st.session_state.page = "profile"
        st.rerun()


def _mostrar_ultimos_sintomas_hoje(db) -> None:
    """Exibe os sintomas de GLP-1 registrados hoje."""
    import json
    sint = db.get_sintomas_glp1(days=1)
    if not sint:
        return
    s    = sint[0]
    lst  = s.get("sintomas", [])
    if isinstance(lst, str):
        try:
            lst = json.loads(lst)
        except Exception:
            lst = []
    from core.models import SYMPTOM_LIST as SL
    nomes = [label for cod, label in SL if cod in lst]
    sev   = s.get("severidade", 1)
    if nomes:
        st.markdown(
            f'<div style="font-size:0.84rem;color:var(--text-muted);">'
            f'Sintomas: {", ".join(nomes)} · Severidade: {sev}/3</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="font-size:0.84rem;color:var(--success);">'
            '✅ Sem sintomas hoje</div>',
            unsafe_allow_html=True,
        )
