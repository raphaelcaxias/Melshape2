"""
Melshape — Tela de Login.
Paciente e profissional entram pelo mesmo formulário.
"""
import streamlit as st


def render(services: dict) -> None:
    db = services["db"]

    st.markdown(
        '<div style="max-width:420px;margin:2rem auto 0;">'
        '<h2 style="font-family:var(--font-display);font-weight:800;'
        'color:var(--text);text-align:center;margin-bottom:1.5rem;">'
        '🔥 Entrar no Melshape</h2>',
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        email    = st.text_input("Email", placeholder="seu@email.com",
                                 key="login_email")
        password = st.text_input("Senha", type="password",
                                 key="login_password")
        submit   = st.form_submit_button(
            "Entrar →", type="primary", use_container_width=True
        )

    if submit:
        if not email.strip() or not password.strip():
            st.error("Preencha email e senha.")
            return

        # Tenta login como profissional primeiro
        pro = db.get_professional(email.strip(), password)
        if pro:
            st.session_state.professional = (
                pro.to_dict() if hasattr(pro, "to_dict") else pro
            )
            st.session_state.page = "pro_dashboard"
            st.rerun()
            return

        # Tenta login como paciente
        user = db.get_user(email.strip(), password)
        if user:
            st.session_state.user = (
                user.to_dict() if hasattr(user, "to_dict") else user
            )
            st.session_state.page = (
                "home" if user.get("onboarding_done") else "onboarding"
            )
            st.rerun()
            return

        st.error("Email ou senha incorretos.")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Voltar", use_container_width=True, key="login_back"):
            st.session_state.page = "landing"
            st.rerun()
    with col2:
        if st.button("Esqueci a senha", use_container_width=True,
                     key="login_forgot"):
            st.session_state.page = "forgot_password"
            st.rerun()

    st.markdown(
        '<div style="text-align:center;margin-top:1rem;'
        'font-size:0.82rem;color:var(--text-muted);">Não tem conta?</div>',
        unsafe_allow_html=True,
    )
    if st.button("Criar conta grátis →", use_container_width=True,
                 key="login_register"):
        st.session_state.page = "register"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
