"""
Melshape — Hábitos: Aba de Suplementos.
Fundido de supplements.py — suplementos são hábitos clínicos.
Integrado ao Orchestrator via db.add_xp e db.save_supplement.
"""
import streamlit as st
from datetime import date
from views.components.cards import empty_state, alert


def render_tab_suplementos(db, user: dict) -> None:
    st.markdown("##### 💊 Suplementos de Hoje")

    suplementos = db.get_supplements_today()

    if suplementos:
        for s in suplementos:
            nome  = getattr(s, "name", "") or s.get("name", "")
            dose  = getattr(s, "dose", "") or s.get("dose", "")
            unit  = getattr(s, "unit", "") or s.get("unit", "")
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;padding:0.5rem 0;'
                f'border-bottom:1px solid var(--border-subtle);">'
                f'<span style="font-weight:600;color:var(--text);">💊 {nome}</span>'
                f'<span style="font-size:0.84rem;color:var(--text-muted);">'
                f'{dose} {unit}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        empty_state("💊", "Nenhum suplemento registrado hoje")

    # Alerta para bariátrico — suplementação obrigatória
    hm = user.get("health_mode", "general")
    if hm == "bariatric":
        from services.bariatric_service import BariatricService
        svc    = BariatricService(db)
        resumo = svc.resumo(user)
        supls  = resumo.get("suplementos", [])
        if supls and not suplementos:
            nomes = " · ".join(s["name"] for s in supls[:3])
            alert(
                f"⚕️ Fase {resumo['fase']['nome']} — "
                f"suplementação obrigatória: {nomes}",
                "warning",
            )

    st.markdown("---")
    st.markdown("##### ➕ Registrar Suplemento")

    col1, col2 = st.columns(2)
    with col1:
        nome_input = st.text_input(
            "Nome",
            placeholder="Ex: Vitamina D3",
            key="supl_nome",
        )
    with col2:
        dose_input = st.text_input(
            "Dose",
            placeholder="Ex: 2000",
            key="supl_dose",
        )

    col3, col4 = st.columns(2)
    with col3:
        unidade = st.selectbox(
            "Unidade",
            ["mg", "g", "ml", "UI", "cápsula", "comprimido"],
            key="supl_unit",
        )
    with col4:
        observacao = st.text_input(
            "Observação (opcional)",
            key="supl_obs",
        )

    if st.button(
        "💊 Registrar suplemento",
        type="primary",
        use_container_width=True,
        key="supl_save",
    ):
        if not nome_input.strip() or not dose_input.strip():
            st.toast("Preencha nome e dose.", icon="⚠️")
            return
        from core.models import Supplement
        supl = Supplement(
            name=nome_input.strip(),
            dose=dose_input.strip(),
            unit=unidade,
            notes=observacao,
            log_date=date.today().isoformat(),
        )
        ok = db.save_supplement(supl)
        if ok:
            st.toast("💊 Suplemento registrado!", icon="✅")
            db.add_xp(10, motivo="suplemento")
            st.rerun()
        else:
            st.toast("Erro ao registrar.", icon="❌")
