"""
Melshape — Ações do Profissional sobre o Paciente.

O profissional não apenas observa — age.
Registra condutas, observações e prescrições diretamente no sistema.

Princípio: toda informação deve responder
"O que devo fazer com este paciente agora?"
"""
import streamlit as st
from views.components.cards import empty_state, alert
from views.professional.patient_prescription import _tab_prescricao
from services.clinical_loop import ClinicalLoopService

_TIPOS_CONDUTA = {
    "orientacao":    "📋 Orientação",
    "ajuste_dieta":  "🥗 Ajuste de Dieta",
    "alerta":        "⚠️ Alerta Clínico",
    "encaminhamento":"🏥 Encaminhamento",
    "elogio":        "🌟 Reconhecimento",
    "revisao":       "🔄 Revisão de Protocolo",
}


def render(services: dict, professional, paciente: dict) -> None:
    db        = services["db"]
    perfil_id = paciente.get("id", "")
    nome      = paciente.get("nome_completo", "—")

    tab_conduta, tab_obs, tab_presc = st.tabs([
        "📋 Conduta",
        "📝 Observação",
        "🥗 Prescrição",
    ])

    with tab_conduta:
        _tab_conduta(db, perfil_id, nome)

    with tab_obs:
        _tab_observacao(db, perfil_id, nome)

    with tab_presc:
        _tab_prescricao(db, perfil_id, nome)


# ── CONDUTA ───────────────────────────────────────────────────────────────────
def _tab_conduta(db, perfil_id: str, nome: str) -> None:
    st.markdown(f"##### 📋 Conduta para {nome}")

    condutas = db.get_condutas(perfil_id)
    if condutas:
        st.markdown(
            f'<div style="font-size:0.78rem;color:var(--text-muted);'
            f'margin-bottom:0.5rem;">'
            f'<b>{len(condutas)}</b> conduta(s) registrada(s)</div>',
            unsafe_allow_html=True,
        )
        for c in condutas[:3]:
            tipo  = c.get("tipo", "orientacao")
            label = _TIPOS_CONDUTA.get(tipo, tipo)
            data  = c.get("data_conduta", "")[:10]
            st.markdown(
                f'<div style="padding:0.5rem 0.7rem;border-left:3px solid '
                f'var(--primary);margin-bottom:0.4rem;">'
                f'<div style="font-size:0.78rem;color:var(--text-muted);">'
                f'{label} · {data}</div>'
                f'<div style="font-size:0.88rem;color:var(--text);">'
                f'{c.get("titulo","")}</div>'
                f'<div style="font-size:0.80rem;color:var(--text-muted);">'
                f'{c.get("descricao","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    with col1:
        titulo = st.text_input(
            "Título da conduta",
            placeholder="Ex: Aumentar proteína para 1.8g/kg",
            key=f"cond_titulo_{perfil_id}",
        )
    with col2:
        tipo_sel = st.selectbox(
            "Tipo",
            list(_TIPOS_CONDUTA.keys()),
            format_func=lambda k: _TIPOS_CONDUTA[k],
            key=f"cond_tipo_{perfil_id}",
        )

    descricao = st.text_area(
        "Detalhes (opcional)",
        height=80,
        placeholder="Orientações, justificativa, próximos passos...",
        key=f"cond_desc_{perfil_id}",
    )

    if st.button("📋 Registrar conduta", type="primary",
                 use_container_width=True, key=f"cond_save_{perfil_id}"):
        if not titulo.strip():
            st.toast("Digite um título para a conduta.", icon="⚠️")
            return
        ok = db.registrar_conduta(
            perfil_id, titulo.strip(), descricao, tipo_sel
        )
        if ok:
            # Fecha o loop clínico — paciente é notificado
            pro_nome = ""
            pro = st.session_state.get("professional")
            if pro:
                pro_nome = (
                    getattr(pro, "name", "") or
                    pro.get("name", "") or ""
                )
            ClinicalLoopService(db).apos_conduta(
                perfil_id, titulo.strip(), descricao, tipo_sel, pro_nome
            )
            st.toast("📋 Conduta registrada — paciente notificado!", icon="✅")
            st.rerun()
        else:
            st.toast("Erro ao registrar.", icon="❌")


# ── OBSERVAÇÃO (COMPLETA) ─────────────────────────────────────────────────────
def _tab_observacao(db, perfil_id: str, nome: str) -> None:
    st.markdown(f"##### 📝 Observações sobre {nome}")

    observacoes = db.get_observacoes(perfil_id)
    if observacoes:
        for o in observacoes[:5]:
            data    = o.get("criado_em", "")[:10]
            privada = "🔒" if o.get("privada") else "👁️"
            st.markdown(
                f'<div style="padding:0.5rem 0;'
                f'border-bottom:1px solid var(--border-subtle);">'
                f'<div style="font-size:0.74rem;color:var(--text-faint);">'
                f'{privada} {data}</div>'
                f'<div style="font-size:0.86rem;color:var(--text);">'
                f'{o.get("observacao","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)
    else:
        empty_state("📝", "Nenhuma observação ainda")

    obs_texto = st.text_area(
        "Nova observação",
        height=100,
        placeholder="Anotação clínica, comportamental ou motivacional...",
        key=f"obs_texto_{perfil_id}",
    )
    privada = st.checkbox(
        "Observação privada (visível só para você)",
        value=True,
        key=f"obs_priv_{perfil_id}",
    )

    if st.button("📝 Salvar observação", type="primary",
                 use_container_width=True, key=f"obs_save_{perfil_id}"):
        if not obs_texto.strip():
            st.toast("Digite a observação.", icon="⚠️")
            return
        ok = db.registrar_observacao(
            perfil_id, obs_texto.strip(), privada
        )
        if ok:
            st.toast("📝 Observação salva!", icon="✅")
            st.rerun()
        else:
            st.toast("Erro ao salvar.", icon="❌")
