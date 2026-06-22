"""
Melshape — Bariátrica: formulários de cadastro de cirurgia e fase.
Importado por bariatric.py.
"""
import streamlit as st
from datetime import date

from services.bariatric_service import BariatricService
from views.components.cards import alert
import config


# ── CADASTRO DE CIRURGIA ──────────────────────────────────────────────────────
def render_form_cirurgia(db, svc: BariatricService,
                          user: dict) -> None:
    st.markdown("##### 🔪 Dados da Cirurgia")

    tipos = config.BARIATRIC_TYPES
    tipo_sel = st.selectbox(
        "Tipo de cirurgia",
        list(tipos.keys()),
        format_func=lambda k: tipos[k],
        key="bar_tipo",
    )

    col1, col2 = st.columns(2)
    with col1:
        data_cirug = st.date_input(
            "Data da cirurgia",
            value=date.today(),
            max_value=date.today(),
            key="bar_data",
        )
    with col2:
        peso_pre = st.number_input(
            "Peso pré-cirurgia (kg)",
            min_value=40.0, max_value=300.0,
            value=float(user.get("current_weight") or 100.0),
            step=0.5,
            key="bar_peso_pre",
        )

    obs = st.text_area(
        "Observações (opcional)",
        height=70,
        key="bar_obs",
        placeholder="Ex: Cirurgia no Hospital X, cirurgião Dr. Y...",
    )

    # Preview da fase automática
    dias_preview = (date.today() - data_cirug).days
    fase_preview = svc.fase_automatica(dias_preview)
    fase_nome    = config.BARIATRIC_PHASES.get(
        fase_preview, {}
    ).get("name", "—")
    st.markdown(
        f'<div style="font-size:0.80rem;background:var(--surface-2);'
        f'padding:0.5rem 0.8rem;border-radius:var(--radius-sm);">'
        f'Com esta data → fase automática: <b>{fase_nome}</b> '
        f'({dias_preview} dias pós-cirurgia)</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "🔪 Salvar cirurgia",
        type="primary",
        use_container_width=True,
        key="bar_salvar_cirug",
    ):
        ok = db.registrar_cirurgia(
            tipo=tipo_sel,
            data_cirurgia=data_cirug.isoformat(),
            peso_pre=peso_pre,
            observacoes=obs,
        )
        if ok:
            # Registra fase automática
            db.registrar_fase_bariatrica(fase_preview)
            st.toast("🔪 Cirurgia registrada!", icon="✅")
            db.add_xp(100, "cadastro_bariatrico")
            st.rerun()
        else:
            st.toast("Erro ao salvar.", icon="❌")


# ── ATUALIZAR FASE ────────────────────────────────────────────────────────────
def render_form_fase(db, svc: BariatricService, resumo: dict) -> None:
    fases       = config.BARIATRIC_PHASES
    fase_atual  = resumo.get("fase_key", "liquid")
    fases_lista = list(fases.keys())
    idx_atual   = (
        fases_lista.index(fase_atual)
        if fase_atual in fases_lista else 0
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        nova_fase = st.selectbox(
            "Fase",
            fases_lista,
            index=idx_atual,
            format_func=lambda k: f'{fases[k]["name"]} (dias {fases[k]["days"]})',
            key="bar_nova_fase",
        )
    with col2:
        obs_fase = st.text_input(
            "Obs",
            placeholder="Opcional",
            key="bar_fase_obs",
        )

    # Mostrar limites da fase selecionada
    fd = fases.get(nova_fase, {})
    if fd:
        st.markdown(
            f'<div style="font-size:0.78rem;color:var(--text-muted);">'
            f'Máx: {fd.get("max_ml", "—")}ml · '
            f'{fd.get("max_cal", "—")} kcal/dia</div>',
            unsafe_allow_html=True,
        )

    if nova_fase != fase_atual:
        if st.button(
            f"Mudar para fase '{fases[nova_fase]['name']}'",
            use_container_width=True,
            key="bar_atualizar_fase",
        ):
            ok = db.registrar_fase_bariatrica(nova_fase, obs_fase)
            if ok:
                st.toast(
                    f"✅ Fase atualizada para {fases[nova_fase]['name']}",
                    icon="✅",
                )
                st.rerun()
            else:
                st.toast("Erro ao atualizar fase.", icon="❌")
    else:
        st.markdown(
            f'<div style="font-size:0.80rem;color:var(--success);">'
            f'✅ Esta é a fase atual</div>',
            unsafe_allow_html=True,
        )
