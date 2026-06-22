"""Melshape — Prescrição alimentar do profissional."""
import streamlit as st
from views.components.cards import alert, empty_state

            st.toast("Digite a observação.", icon="⚠️")
            return
        ok = db.registrar_observacao(perfil_id, obs_texto.strip(), privada)
        if ok:
            st.toast("📝 Observação salva!", icon="✅")
            st.rerun()
        else:
            st.toast("Erro ao salvar.", icon="❌")


# ── PRESCRIÇÃO ────────────────────────────────────────────────────────────────
def _tab_prescricao(db, perfil_id: str, nome: str) -> None:
    st.markdown(f"##### 🥗 Prescrição para {nome}")

    presc_ativa = db.get_prescricao_ativa(perfil_id)
    if presc_ativa:
        st.markdown(
            f'<div class="alert-success">'
            f'✅ Prescrição ativa desde '
            f'{presc_ativa.get("data_inicio","—")[:10]}<br>'
            f'Objetivo: <b>{presc_ativa.get("objetivo","—")}</b>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")

    objetivo = st.text_input(
        "Objetivo da prescrição",
        placeholder="Ex: Déficit calórico moderado com alta proteína",
        key=f"presc_obj_{perfil_id}",
    )

    # Modelos disponíveis do profissional
    modelos = db.get_modelos_profissional()
    if modelos:
        st.markdown(
            '<div style="font-size:0.80rem;color:var(--text-muted);">'
            'Vincular modelo de refeição (opcional):</div>',
            unsafe_allow_html=True,
        )
        nomes_m = ["— Sem modelo —"] + [m.get("nome", "—") for m in modelos]
        idx_m   = st.selectbox("Modelo", range(len(nomes_m)),
                               format_func=lambda i: nomes_m[i],
                               key=f"presc_modelo_{perfil_id}",
                               label_visibility="collapsed")
    else:
        alert("Crie modelos de refeição no seu perfil profissional "
              "para vinculá-los a prescrições.", "info")

    if st.button("🥗 Criar prescrição", type="primary",
                 use_container_width=True, key=f"presc_save_{perfil_id}"):
        if not objetivo.strip():
            st.toast("Digite o objetivo da prescrição.", icon="⚠️")
            return
        ok = db.criar_prescricao(perfil_id, objetivo.strip())
        if ok:
            st.toast("🥗 Prescrição criada!", icon="✅")
            st.rerun()
        else:
            st.toast("Erro ao criar.", icon="❌")
