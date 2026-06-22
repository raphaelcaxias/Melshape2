"""
Melshape — Hábitos: Aba de Treinos.
Fundido de workout.py — treino é um hábito de movimento.
Dispara Orchestrator via services["orchestrator"].processar("treino").
"""
import streamlit as st
from datetime import date
from views.components.cards import empty_state, metric_card


def render_tab_treinos(db, user: dict, services: dict = None) -> None:
    st.markdown("##### 🏋️ Treino de Hoje")

    treino = db.get_workout_today()

    if treino:
        from core.models import WORKOUT_TYPES
        tipo_label = WORKOUT_TYPES.get(
            getattr(treino, "workout_type", ""), "Treino"
        )
        dur   = getattr(treino, "duration", 0)
        intens = getattr(treino, "intensity", 0)
        obs   = getattr(treino, "notes", "")

        st.markdown(
            f'<div class="metric-card fade-in" '
            f'style="border-color:var(--success);">'
            f'<div style="font-weight:700;font-size:1rem;color:var(--text);">'
            f'🏋️ {tipo_label}</div>'
            f'<div style="font-size:0.84rem;color:var(--text-muted);'
            f'margin-top:0.2rem;">'
            f'Duração: {dur} min · Intensidade: {intens}/10</div>'
            f'{"<div style=font-size:0.80rem;color:var(--text-muted);>" + obs + "</div>" if obs else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        empty_state("🏋️", "Nenhum treino registrado hoje",
                    "Registre para manter seu histórico")

    st.markdown("---")
    st.markdown("##### ➕ Registrar Treino")

    from core.models import WORKOUT_TYPES
    col1, col2 = st.columns(2)
    with col1:
        tipo = st.selectbox(
            "Tipo",
            list(WORKOUT_TYPES.keys()),
            format_func=lambda k: WORKOUT_TYPES[k],
            key="workout_tipo",
        )
    with col2:
        duracao = st.number_input(
            "Duração (min)",
            min_value=1,
            max_value=300,
            value=30,
            step=5,
            key="workout_dur",
        )

    intensidade = st.select_slider(
        "Intensidade",
        options=list(range(1, 11)),
        value=5,
        format_func=lambda x: f"{x}/10 — "
        + {1:"Leve",2:"Leve",3:"Moderado",4:"Moderado",
           5:"Moderado",6:"Intenso",7:"Intenso",
           8:"Muito Intenso",9:"Máximo",10:"Máximo"}.get(x,""),
        key="workout_int",
    )
    obs_treino = st.text_input(
        "Observação (opcional)",
        placeholder="Ex: Foco em peito e ombros",
        key="workout_obs",
    )

    if st.button(
        "🏋️ Registrar treino",
        type="primary",
        use_container_width=True,
        key="workout_save",
    ):
        from core.models import WorkoutLog
        w = WorkoutLog(
            workout_type=tipo,
            duration=duracao,
            intensity=intensidade,
            notes=obs_treino,
            log_date=date.today().isoformat(),
        )
        ok = db.save_workout(w)
        if ok:
            st.toast("🏋️ Treino registrado!", icon="✅")
            # Dispara Orchestrator se disponível
            if services:
                orch = services.get("orchestrator")
                if orch:
                    user_data = st.session_state.get("user", {})
                    result = orch.processar(
                        "refeicao", user_data,
                        {"tipo": "treino", "duracao": duracao},
                    )
                    if result.xp_ganho:
                        from views.components.cards import xp_toast
                        xp_toast(result.xp_ganho, "treino")
            else:
                db.add_xp(20, motivo="treino")
            st.rerun()
        else:
            st.toast("Erro ao registrar.", icon="❌")
