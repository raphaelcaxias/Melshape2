"""
Melshape — Tela Inicial (Landing).
Primeira impressão. Deve responder em 5s:
"O que é isso e por que devo me cadastrar?"
"""
import streamlit as st
import config


def render(services: dict) -> None:
    db = services["db"]

    # ── HERO ──────────────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="text-align:center;padding:3rem 1rem 2rem;">'
        f'<div style="font-size:3rem;">🔥</div>'
        f'<h1 style="font-family:var(--font-display);font-weight:800;'
        f'font-size:2.2rem;color:var(--text);margin:0.5rem 0 0.3rem;">'
        f'{config.APP_NAME}</h1>'
        f'<p style="font-size:1.1rem;color:var(--text-muted);'
        f'max-width:480px;margin:0 auto;">'
        f'{config.APP_TAGLINE}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── PILARES ───────────────────────────────────────────────────────────────
    pilares = [
        ("⚖️", "Emagrecimento", "Hábitos reais, não restrições"),
        ("💪", "Fitness",       "Proteína, treino e consistência"),
        ("🔪", "Pós-Bariátrica","Fases, suplementação e exames"),
        ("💉", "GLP-1",         "Dose, adesão e sintomas"),
    ]
    cols = st.columns(4)
    for col, (icon, titulo, desc) in zip(cols, pilares):
        with col:
            st.markdown(
                f'<div style="text-align:center;padding:1rem 0.5rem;'
                f'background:var(--surface-2);border-radius:var(--radius-lg);'
                f'border:1px solid var(--border);">'
                f'<div style="font-size:1.6rem;">{icon}</div>'
                f'<div style="font-weight:700;font-size:0.88rem;'
                f'color:var(--text);margin:0.3rem 0 0.2rem;">{titulo}</div>'
                f'<div style="font-size:0.76rem;color:var(--text-muted);">'
                f'{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── CTAs ──────────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            f"🚀 Começar grátis — {config.TRIAL_DAYS} dias de trial",
            type="primary",
            use_container_width=True,
            key="landing_register",
        ):
            st.session_state.page = "register"
            st.rerun()

        st.markdown(
            '<div style="text-align:center;margin:0.5rem 0;'
            'font-size:0.82rem;color:var(--text-muted);">Já tem conta?</div>',
            unsafe_allow_html=True,
        )

        if st.button(
            "Entrar",
            use_container_width=True,
            key="landing_login",
        ):
            st.session_state.page = "login"
            st.rerun()

        st.markdown(
            '<div style="text-align:center;margin:0.5rem 0;'
            'font-size:0.78rem;color:var(--text-faint);">ou</div>',
            unsafe_allow_html=True,
        )

        col_demo, col_pro = st.columns(2)
        with col_demo:
            if st.button("🎮 Ver demo",
                         use_container_width=True,
                         key="landing_demo"):
                user = db.get_user(config.DEMO_EMAIL, config.DEMO_PASSWORD)
                if user:
                    st.session_state.user = (
                        user.to_dict() if hasattr(user, "to_dict") else user
                    )
                    st.session_state.page = "home"
                    st.rerun()
        with col_pro:
            if st.button("🏥 Sou profissional",
                         use_container_width=True,
                         key="landing_pro"):
                st.session_state.page = "register_pro"
                st.rerun()

    # ── DESTAQUES ─────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    destaques = [
        ("✅", "Check-in diário",     "30 segundos. Mantém sua sequência ativa."),
        ("📊", "Score de transformação","Não é caloria. É consistência medida."),
        ("👨‍⚕️", "Profissional integrado","Seu nutricionista vê tudo em tempo real."),
        ("🔔", "Anti-abandono",        "O sistema busca você quando você some."),
    ]
    cols2 = st.columns(4)
    for col, (icon, titulo, desc) in zip(cols2, destaques):
        with col:
            st.markdown(
                f'<div style="text-align:center;padding:0.8rem 0.5rem;">'
                f'<div style="font-size:1.4rem;">{icon}</div>'
                f'<div style="font-weight:700;font-size:0.84rem;'
                f'color:var(--text);margin:0.3rem 0 0.15rem;">{titulo}</div>'
                f'<div style="font-size:0.74rem;color:var(--text-muted);">'
                f'{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        f'<div style="text-align:center;margin-top:2rem;'
        f'font-size:0.74rem;color:var(--text-faint);">'
        f'v{config.APP_VERSION} · Sem cartão · Cancele quando quiser</div>',
        unsafe_allow_html=True,
    )
