"""
Melshape — Perfil do Paciente.

Abas:
  👤 Meus Dados     → peso, altura, objetivo, modo de saúde
  💳 Meu Plano      → trial, upgrade, histórico
  🔔 Preferências   → notificações, dark mode, lembretes
  🚪 Conta          → logout, exclusão
"""
import streamlit as st
from datetime import date
import config
from views.components.cards import section_header, alert, metric_card


def render(services: dict, user: dict) -> None:
    db       = services["db"]
    plan_svc = services.get("plan") or services.get("plan_service")
    nome     = user.get("name", "").split()[0]

    section_header(f"👤 Perfil — {nome}", "Seus dados e configurações")

    tab_dados, tab_plano, tab_pref, tab_conta = st.tabs([
        "👤 Meus Dados",
        "💳 Meu Plano",
        "🔔 Preferências",
        "🚪 Conta",
    ])

    with tab_dados:
        _tab_dados(db, user)

    with tab_plano:
        _tab_plano(plan_svc, user)

    with tab_pref:
        _tab_preferencias(db, user)

    with tab_conta:
        _tab_conta(db, user)


# ── TAB 1: DADOS PESSOAIS ─────────────────────────────────────────────────────
def _tab_dados(db, user: dict) -> None:
    st.markdown("##### 👤 Dados Pessoais")

    _MODE_LABELS = {
        "general":   "⚖️ Emagrecimento",
        "fitness":   "💪 Fitness",
        "bariatric": "🔪 Pós-Bariátrica",
        "glp1":      "💉 GLP-1",
    }

    with st.form("profile_dados", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            nome   = st.text_input("Nome completo",
                                   value=user.get("name", ""),
                                   key="pf_nome")
            peso   = st.number_input("Peso atual (kg)",
                                     min_value=20.0, max_value=300.0,
                                     value=float(user.get("current_weight") or 70),
                                     step=0.1, key="pf_peso")
            altura = st.number_input("Altura (cm)",
                                     min_value=100, max_value=250,
                                     value=int(user.get("height") or 170),
                                     key="pf_altura")
        with col2:
            idade  = st.number_input("Idade",
                                     min_value=16, max_value=99,
                                     value=int(user.get("age") or 30),
                                     key="pf_idade")
            genero = st.selectbox(
                "Gênero",
                ["female", "male", "other"],
                index=["female","male","other"].index(
                    user.get("gender","female")
                ),
                format_func=lambda x: {
                    "female":"Feminino","male":"Masculino","other":"Outro"
                }[x],
                key="pf_genero",
            )
            objetivo = st.selectbox(
                "Objetivo",
                ["lose","maintain","gain"],
                index=["lose","maintain","gain"].index(
                    user.get("goal","lose")
                ),
                format_func=lambda x: {
                    "lose":"⬇️ Perder peso",
                    "maintain":"⚖️ Manter peso",
                    "gain":"⬆️ Ganhar massa",
                }[x],
                key="pf_objetivo",
            )

        peso_meta = st.number_input(
            "Peso desejado (kg)",
            min_value=20.0, max_value=300.0,
            value=float(user.get("goal_weight") or 65),
            step=0.1, key="pf_peso_meta",
        )

        hm_atual = user.get("health_mode", "general")
        hm = st.selectbox(
            "Modo de saúde",
            list(_MODE_LABELS.keys()),
            index=list(_MODE_LABELS.keys()).index(hm_atual),
            format_func=lambda k: _MODE_LABELS[k],
            key="pf_hm",
        )

        if st.form_submit_button("💾 Salvar dados", type="primary",
                                  use_container_width=True):
            upd = {
                "name":           nome.strip(),
                "current_weight": peso,
                "height":         altura,
                "age":            idade,
                "gender":         genero,
                "goal":           objetivo,
                "goal_weight":    peso_meta,
                "health_mode":    hm,
            }
            try:
                db.update_user(upd)
                st.session_state.user.update(upd)
                st.toast("💾 Dados salvos!", icon="✅")
                st.rerun()
            except Exception as e:
                st.toast(f"Erro: {e}", icon="❌")



from views.patient.profile_tabs import (
    _tab_plano, _tab_preferencias, _tab_conta
)
