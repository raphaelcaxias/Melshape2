"""Melshape — Evolução: aba clínica (exames + estagnação)."""
import streamlit as st
from services.evolution_service import EvolutionService
from views.components.cards import empty_state, alert

# ── ABA 2: CLÍNICO ────────────────────────────────────────────────────────────
def _tab_clinico(svc: EvolutionService, user: dict) -> None:
    st.markdown("##### 🧪 Indicadores Clínicos (Exames)")

    col1, col2, col3 = st.columns(3)
    with col1:
        glicemia = st.number_input(
            "Glicemia (mg/dL)", min_value=0.0, max_value=500.0,
            value=90.0, step=1.0, key="ev_glic",
        )
    with col2:
        col_total = st.number_input(
            "Colesterol Total", min_value=0.0, max_value=500.0,
            value=190.0, step=1.0, key="ev_col",
        )
    with col3:
        hdl = st.number_input(
            "HDL (mg/dL)", min_value=0.0, max_value=200.0,
            value=45.0, step=1.0, key="ev_hdl",
        )

    col4, col5, col6 = st.columns(3)
    with col4:
        trig = st.number_input(
            "Triglicerídeos", min_value=0.0, max_value=1000.0,
            value=150.0, step=1.0, key="ev_trig",
        )
    with col5:
        vit_d = st.number_input(
            "Vitamina D (ng/mL)", min_value=0.0, max_value=200.0,
            value=30.0, step=0.5, key="ev_vitd",
        )
    with col6:
        b12 = st.number_input(
            "B12 (pg/mL)", min_value=0.0, max_value=2000.0,
            value=400.0, step=10.0, key="ev_b12",
        )

    # Campos específicos para bariátrica
    hm = user.get("health_mode", "general")
    ferritina = tsh = None
    if hm == "bariatric":
        col7, col8 = st.columns(2)
        with col7:
            ferritina = st.number_input(
                "Ferritina (ng/mL)", min_value=0.0, max_value=1000.0,
                value=50.0, step=1.0, key="ev_ferr",
            )
        with col8:
            tsh = st.number_input(
                "TSH (mUI/L)", min_value=0.0, max_value=50.0,
                value=2.5, step=0.1, key="ev_tsh",
            )

    if st.button("🧪 Salvar exames", type="primary",
                 use_container_width=True, key="ev_save_exames"):
        ok = svc.salvar_indicador({
            "glicemia":        glicemia,
            "colesterol_total": col_total,
            "hdl":             hdl,
            "triglicerideos":  trig,
            "vitamina_d":      vit_d,
            "b12":             b12,
            "ferritina":       ferritina,
            "tsh":             tsh,
        })
        if ok:
            st.toast("🧪 Exames salvos!", icon="✅")
            st.rerun()
        else:
            st.toast("Erro ao salvar.", icon="❌")

    # Histórico de exames
    st.markdown("---")
    indicadores = svc.get_indicadores(days=365)
    if indicadores:
        for ind in indicadores[:5]:
            data     = ind.get("data_coleta", "")[:10]
            glic_val = ind.get("glicemia_jejum")

            # Narrativa via contextualizer
            if glic_val:
                if glic_val < 100:
                    glic_msg = f"🟢 {glic_val} mg/dL — ótimo"
                elif glic_val < 126:
                    glic_msg = f"🟡 {glic_val} mg/dL — atenção"
                else:
                    glic_msg = f"🔴 {glic_val} mg/dL — avaliar com profissional"
            else:
                glic_msg = "—"

            col_val  = ind.get("colesterol_total") or "—"
            st.markdown(
                f'<div style="padding:0.45rem 0;'
                f'border-bottom:1px solid var(--border-subtle);">'
                f'<div style="font-weight:600;font-size:0.88rem;">{data}</div>'
                f'<div style="font-size:0.78rem;color:var(--text-muted);">'
                f'Glicemia: {glic_msg} · Colesterol: {col_val} mg/dL'
                f'</div></div>',
                unsafe_allow_html=True,
            )
    else:
        empty_state("🧪", "Nenhum exame registrado",
                    "Registre seus exames para acompanhar sua saúde clínica")

    # Estagnação
    st.markdown("---")
    st.markdown("##### ⏸️ Monitoramento de Estagnação")
    estag = svc.get_estagnacao()
    if estag:
        dias = int(estag.get("dias_estagnado", 0))
        if dias >= 14:
            alert(
                f"⏸️ Seu peso está estagnado há {dias} dias. "
                f"Isso pode indicar adaptação metabólica — "
                f"considere revisar o plano com seu profissional.",
                "warning",
            )
            st.markdown(
                '<div style="font-size:0.82rem;color:var(--text-muted);">'
                '💡 Sugestão: aumente a ingestão de proteína ou '
                'revise sua rotina de treinos.</div>',
                unsafe_allow_html=True,
            )
        elif dias >= 7:
            alert(
                f"📊 {dias} dias sem variação de peso. "
                f"Normal em alguns momentos da jornada — mantenha a consistência.",
                "info",
            )
        else:
            alert("📈 Sem sinais de estagnação. Continue assim!", "success")
    else:
        alert("📈 Dados insuficientes para detectar estagnação.", "info")


