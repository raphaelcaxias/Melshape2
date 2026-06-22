"""Melshape — Onboarding: steps 1-4 e finalização."""
import streamlit as st
import config
from views.components.cards import alert

# ── PASSO 1: PILAR ────────────────────────────────────────────────────────────
def _step_pilar() -> None:
    st.markdown(
        '<h2 style="font-family:var(--font-display);font-weight:800;'
        'color:var(--text);margin-bottom:0.3rem;">Qual é sua jornada?</h2>'
        '<p style="color:var(--text-muted);margin-bottom:1.2rem;">'
        'O Melshape personaliza tudo com base na sua resposta.</p>',
        unsafe_allow_html=True,
    )

    cols = st.columns(2)
    for i, (key, p) in enumerate(_PILARES.items()):
        with cols[i % 2]:
            selecionado = st.session_state.get("onboarding_mode") == key
            borda = "var(--primary)" if selecionado else "var(--border)"
            st.markdown(
                f'<div style="border:2px solid {borda};border-radius:var(--radius-lg);'
                f'padding:1rem;margin-bottom:0.6rem;cursor:pointer;">'
                f'<div style="font-size:1.6rem;">{p["icon"]}</div>'
                f'<div style="font-weight:700;color:var(--text);">{p["nome"]}</div>'
                f'<div style="font-size:0.78rem;color:var(--text-muted);">'
                f'{p["desc"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(
                f'{"✅ " if selecionado else ""}Escolher {p["nome"]}',
                key=f"ob_pilar_{key}",
                use_container_width=True,
                type="primary" if selecionado else "secondary",
            ):
                st.session_state.onboarding_mode = key
                st.rerun()

    if st.session_state.get("onboarding_mode"):
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Continuar →", type="primary",
                     use_container_width=True, key="ob_p1_next"):
            st.session_state.onboarding_step = 2
            st.rerun()


# ── PASSO 2: DADOS PESSOAIS ───────────────────────────────────────────────────
def _step_dados(user: dict) -> None:
    st.markdown(
        '<h2 style="font-family:var(--font-display);font-weight:800;'
        'color:var(--text);margin-bottom:0.3rem;">Seus dados</h2>'
        '<p style="color:var(--text-muted);margin-bottom:1.2rem;">'
        'Usados para calcular suas metas nutricionais.</p>',
        unsafe_allow_html=True,
    )

    with st.form("ob_dados", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            peso   = st.number_input("Peso atual (kg)", 30.0, 300.0,
                                     float(user.get("current_weight") or 80),
                                     0.1, key="ob_peso")
            altura = st.number_input("Altura (cm)", 100, 250,
                                     int(user.get("height") or 170),
                                     key="ob_altura")
        with col2:
            idade  = st.number_input("Idade", 16, 99,
                                     int(user.get("age") or 30),
                                     key="ob_idade")
            genero = st.selectbox(
                "Gênero",
                ["female", "male", "other"],
                format_func=lambda x: {
                    "female": "Feminino", "male": "Masculino",
                    "other": "Outro"
                }[x],
                key="ob_genero",
            )

        objetivo = st.selectbox(
            "Objetivo principal",
            ["lose", "maintain", "gain"],
            format_func=lambda x: {
                "lose":     "⬇️ Perder peso",
                "maintain": "⚖️ Manter peso",
                "gain":     "⬆️ Ganhar massa",
            }[x],
            key="ob_objetivo",
        )

        peso_meta = st.number_input(
            "Peso desejado (kg)",
            30.0, 300.0,
            float(user.get("goal_weight") or max(30, (user.get("current_weight") or 80) - 5)),
            0.1, key="ob_peso_meta",
        )

        if st.form_submit_button("Continuar →", type="primary",
                                  use_container_width=True):
            # Salva no perfil
            try:
                db_ref = st.session_state.get("_db_ref")
                upd = {
                    "current_weight": peso,
                    "height":         altura,
                    "age":            idade,
                    "gender":         genero,
                    "goal":           objetivo,
                    "goal_weight":    peso_meta,
                    "health_mode":    st.session_state.get("onboarding_mode","general"),
                }
                st.session_state.user.update(upd)
            except Exception:
                pass
            st.session_state.onboarding_step = 3
            st.rerun()

    if st.button("← Voltar", key="ob_p2_back"):
        st.session_state.onboarding_step = 1
        st.rerun()





# ── (consolidado de onboarding_steps_b.py) ──
    try:
        # 1. Atualizar perfil com health_mode e onboarding_done
        upd = {
            "health_mode":    hm,
            "onboarding_done": True,
            **{k: v for k, v in st.session_state.get("user", {}).items()
               if k in ("current_weight", "height", "age", "gender",
                        "goal", "goal_weight")},
        }
        db.update_user(upd)
        st.session_state.user.update(upd)

        # 2. Criar hábitos iniciais do pilar
        from services.habit_service import HabitService
        svc = HabitService(db)
        svc.inicializar_habitos_padrao(hm)

        # 3. Salvar motivo da jornada
        motivo = st.session_state.get("ob_porque_salvo", "")
        if motivo:
            jornada = db.get_jornada_ativa()
            if not jornada:
                from services.journey_service import JourneyService
                jornada = JourneyService(db).garantir_jornada(
                    st.session_state.user
                )
            if jornada:
                db.salvar_motivo(jornada["id"], motivo)

        # 4. Ir para home
        st.session_state.onboarding_step = 1
        st.session_state.page = "home"
        st.rerun()

    except Exception as e:
        import logging
        logging.getLogger("Melshape").error(f"Onboarding finalizar: {e}")
        # Mesmo com erro, vai para home
        st.session_state.user["onboarding_done"] = True
        st.session_state.page = "home"
        st.rerun()
