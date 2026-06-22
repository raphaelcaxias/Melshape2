"""
Melshape — GLP-1: formulários de dose e sintomas.
Importado por glp1.py.
"""
import streamlit as st
from datetime import date

from services.glp1_service import GLP1Service
from views.components.cards import alert, xp_toast, show_new_achievements
from core.models import SYMPTOM_LIST, SEVERE_SYMPTOMS
import config


# ── FORMULÁRIO DE DOSE ────────────────────────────────────────────────────────
def render_form_dose(db, svc: GLP1Service, gami,
                      user: dict, resumo: dict) -> None:
    st.markdown("##### 💉 Registrar Aplicação")

    med_atual  = resumo.get("medicamento", "")
    dose_atual = resumo.get("dose_atual", "")
    fase_atual = resumo.get("fase", {}).get("key", "adapting")

    # Seleciona medicamento
    meds    = config.GLP1_MEDICATIONS
    med_idx = meds.index(med_atual) if med_atual in meds else 0
    med_sel = st.selectbox(
        "Medicamento",
        meds,
        index=med_idx,
        key="glp1_med",
    )

    # Doses disponíveis para o medicamento
    doses_disp = config.GLP1_DOSES.get(med_sel, ["Personalizado"])
    dose_idx   = (
        doses_disp.index(dose_atual)
        if dose_atual in doses_disp else 0
    )
    dose_sel = st.selectbox(
        "Dose",
        doses_disp,
        index=dose_idx,
        key="glp1_dose_sel",
    )

    # Fase
    fases = config.GLP1_PHASES
    fase_labels = {k: v for k, v in fases.items()}
    fase_sel = st.selectbox(
        "Fase atual",
        list(fases.keys()),
        index=list(fases.keys()).index(fase_atual)
        if fase_atual in fases else 0,
        format_func=lambda k: fases[k],
        key="glp1_fase",
    )

    obs = st.text_input(
        "Observação (opcional)",
        placeholder="Ex: Aplicada no abdômen, sem reações",
        key="glp1_obs",
    )

    if st.button(
        "💉 Registrar dose",
        type="primary",
        use_container_width=True,
        key="glp1_save_dose",
    ):
        # Garante que protocolo existe
        proto = db.get_protocolo_ativo()
        if not proto:
            proto = db.criar_protocolo(med_sel, dose_sel)

        proto_id = proto.get("id", "") if proto else ""
        ok = db.registrar_dose_glp1(
            medicamento=med_sel,
            dose=dose_sel,
            fase=fase_sel,
            observacao=obs,
            protocolo_id=proto_id,
        )
        if ok:
            st.toast(f"💉 Dose {dose_sel} registrada!", icon="✅")
            db.add_xp(25, "dose_glp1")
            xp_toast(25, "registro de dose")
            # Atualiza dados do perfil
            db.update_user({
                "glp1_medication": med_sel,
                "glp1_dose":       dose_sel,
                "glp1_phase":      fase_sel,
                "uses_glp1":       True,
            })
            novos = gami.check_achievements(user)
            show_new_achievements(novos)
            st.rerun()
        else:
            st.toast("Erro ao registrar dose.", icon="❌")


# ── FORMULÁRIO DE SINTOMAS ────────────────────────────────────────────────────
def render_form_sintomas(db, svc: GLP1Service, gami, user: dict) -> None:
    st.markdown("##### 📋 Registrar Sintomas de Hoje")

    # Sintomas de hoje já registrados?
    hoje        = date.today().isoformat()
    sint_hoje   = db.get_sintomas_glp1(days=1)
    ja_registrou = any(
        s.get("data_registro", "")[:10] == hoje
        for s in sint_hoje
    )

    if ja_registrou:
        alert("✅ Sintomas de hoje já registrados.", "success")
        from views.patient.glp1 import _mostrar_ultimos_sintomas_hoje; _mostrar_ultimos_sintomas_hoje(db)
        return

    st.markdown(
        '<div style="font-size:0.80rem;color:var(--text-muted);'
        'margin-bottom:0.6rem;">Marque todos que está sentindo hoje:</div>',
        unsafe_allow_html=True,
    )

    selecionados = []
    cols = st.columns(2)
    for i, (cod, label) in enumerate(SYMPTOM_LIST):
        with cols[i % 2]:
            if st.checkbox(label, key=f"sint_{cod}"):
                selecionados.append(cod)

    # Alerta de sintomas graves
    graves = [cod for cod in selecionados if cod in SEVERE_SYMPTOMS]
    if graves:
        from core.models import SYMPTOM_LIST as SL
        nomes_graves = [
            label for cod, label in SL if cod in graves
        ]
        alert(
            f"🚨 Sintomas graves identificados: "
            f"{', '.join(nomes_graves)}. "
            f"Considere contatar seu médico.",
            "error",
        )

    severidade = st.select_slider(
        "Severidade geral",
        options=[1, 2, 3],
        value=1,
        format_func=lambda x: {
            1: "1 — Leve", 2: "2 — Moderada", 3: "3 — Grave"
        }[x],
        key="glp1_sev",
    )
    obs = st.text_area(
        "Observações (opcional)",
        height=70,
        key="glp1_sint_obs",
        placeholder="Descreva como está se sentindo...",
    )

    btn_label = (
        "Registrar sem sintomas" if not selecionados
        else f"Registrar {len(selecionados)} sintoma(s)"
    )
    if st.button(
        f"📋 {btn_label}",
        type="primary",
        use_container_width=True,
        key="glp1_save_sint",
    ):
        ok = db.registrar_sintomas_glp1(selecionados, severidade, obs)
        if ok:
            st.toast("📋 Sintomas registrados!", icon="✅")
            db.add_xp(10, "monitoramento_glp1")
            st.rerun()
        else:
            st.toast("Erro ao registrar.", icon="❌")


