"""
Melshape — Resultado do Check-in.

Exibido após o check-in ser processado pelo Orchestrator.
Mostra XP ganho, badges, próximo passo e se a jornada avançou.
"""
import streamlit as st
from services.orchestrator import OrchestratorResult
from views.components.cards import alert


def render_resultado(result: OrchestratorResult, user: dict) -> None:
    """Renderiza o resultado do Orchestrator após check-in."""
    nome = user.get("name", "").split()[0]

    # XP ganho
    if result.xp_ganho > 0:
        st.markdown(
            f'<div style="background:var(--primary-light);'
            f'border:1px solid var(--primary-border);'
            f'border-radius:var(--radius-lg);padding:1rem;'
            f'text-align:center;margin-bottom:0.6rem;">'
            f'<div style="font-size:2rem;font-weight:800;'
            f'color:var(--primary);">+{result.xp_ganho} XP</div>'
            f'<div style="font-size:0.82rem;color:var(--text-muted);">'
            f'Ganhos com o check-in de hoje</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Jornada avançou
    if result.jornada_avancou:
        st.markdown(
            '<div class="alert-success">'
            '🗺️ Você avançou para a próxima etapa da sua jornada!'
            '</div>',
            unsafe_allow_html=True,
        )

    # Marcos novos
    for marco in result.marcos_novos:
        st.markdown(
            f'<div class="alert-success">🏁 {marco}</div>',
            unsafe_allow_html=True,
        )

    # Badges novas (que não são marcos)
    badges_visuais = [
        b for b in result.badges_novos
        if b not in result.marcos_novos
    ]
    if badges_visuais:
        st.markdown(
            '<div style="margin:0.5rem 0;">', unsafe_allow_html=True
        )
        for badge in badges_visuais[:3]:
            st.markdown(
                f'<div style="background:var(--primary-light);'
                f'border:1px solid var(--primary-border);'
                f'border-radius:var(--radius-md);'
                f'padding:0.5rem 0.8rem;margin-bottom:0.3rem;'
                f'font-size:0.88rem;font-weight:600;color:var(--text);">'
                f'{badge}</div>',
                unsafe_allow_html=True,
            )

    # Alertas
    for kind, msg in result.alertas:
        alert(msg, kind)

    # Próximo passo — sempre presente e acionável
    if result.proximo_passo:
        st.markdown(
            '<div style="margin-top:0.8rem;padding:0.8rem;'
            'background:var(--surface-2);'
            'border-radius:var(--radius-md);">'
            '<div style="font-size:0.74rem;font-weight:700;'
            'letter-spacing:0.06em;color:var(--text-faint);'
            'text-transform:uppercase;margin-bottom:0.3rem;">'
            'Próximo passo</div>'
            f'<div style="font-size:0.92rem;font-weight:600;'
            f'color:var(--text);">{result.proximo_passo}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if result.proximo_hub:
            if st.button(
                "Fazer agora →",
                type="primary",
                use_container_width=True,
                key="ci_result_cta",
            ):
                st.session_state.page     = result.proximo_hub
                st.session_state.hub_tipo = result.proximo_tipo
                st.session_state.pop("ci_result", None)
                st.rerun()

    # Mensagem motivacional por streak
    streak = result.streak
    if streak >= 30:
        _quote("🏆 30 dias. Isso já é mais do que a maioria das pessoas faz na vida.")
    elif streak >= 7:
        _quote(f"🔥 {streak} dias seguidos. A consistência está virando parte de você.")
    elif streak >= 3:
        _quote(f"⚡ {streak} dias. O hábito está começando a se formar.")
    elif streak == 1:
        _quote("🌱 O primeiro passo de volta. Amanhã será mais fácil.")


def _quote(text: str) -> None:
    st.markdown(
        f'<div style="font-style:italic;font-size:0.84rem;'
        f'color:var(--text-muted);padding:0.6rem 0.8rem;'
        f'border-left:3px solid var(--primary);'
        f'margin-top:0.8rem;">{text}</div>',
        unsafe_allow_html=True,
    )
