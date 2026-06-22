"""
Melshape — Recuperação de Senha.
Token de 32 chars, expira em 15 min, validado via email_service.
"""
import streamlit as st


def render(services: dict) -> None:
    db = services["db"]

    # Veio de link de reset na URL?
    params = st.query_params
    if "reset_token" in params and "email" in params:
        _nova_senha(db, params["email"], params["reset_token"])
        return

    _solicitar(db)


def _solicitar(db) -> None:
    st.markdown(
        '<div style="max-width:420px;margin:2rem auto 0;">'
        '<h2 style="font-family:var(--font-display);font-weight:800;'
        'color:var(--text);text-align:center;">🔒 Recuperar Senha</h2>'
        '<p style="text-align:center;color:var(--text-muted);'
        'margin-bottom:1.5rem;">Enviaremos um link para seu email.</p>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("reset_email_sent"):
        st.success(
            "✅ Email enviado! Verifique sua caixa de entrada e spam. "
            "O link expira em **15 minutos**."
        )
        if st.button("← Voltar ao Login", use_container_width=True,
                     key="fp_back_ok"):
            st.session_state.pop("reset_email_sent", None)
            st.session_state.page = "login"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    with st.form("forgot_form", clear_on_submit=False):
        email  = st.text_input("Email cadastrado",
                               placeholder="seu@email.com", key="fp_email")
        submit = st.form_submit_button(
            "Enviar link →", type="primary", use_container_width=True
        )

    if submit:
        if not email.strip() or "@" not in email:
            st.error("Digite um email válido.")
            return
        # Gera e envia token (retorna True mesmo se email não existe — segurança)
        try:
            import streamlit as _st
            base_url = _st.secrets.get("APP_URL", "http://localhost:8501")
            from services.email_service import request_password_reset
            request_password_reset(email.strip().lower(),
                                   email.split("@")[0], base_url)
        except Exception:
            pass
        st.session_state.reset_email_sent = True
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Voltar", use_container_width=True, key="fp_back"):
        st.session_state.page = "login"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def _nova_senha(db, email: str, token: str) -> None:
    st.markdown(
        '<div style="max-width:420px;margin:2rem auto 0;">'
        '<h2 style="font-family:var(--font-display);font-weight:800;'
        'color:var(--text);text-align:center;">🔒 Nova Senha</h2>',
        unsafe_allow_html=True,
    )

    from services.email_service import validate_reset_token, consume_reset_token

    if not validate_reset_token(email, token):
        st.error("❌ Link inválido ou expirado. Solicite um novo link.")
        if st.button("Solicitar novo link", type="primary",
                     use_container_width=True, key="fp_novo_link"):
            st.query_params.clear()
            st.session_state.page = "forgot_password"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    with st.form("new_pwd_form", clear_on_submit=False):
        st.markdown(f"**Redefinindo senha para:** `{email}`")
        pwd  = st.text_input("Nova senha (mín. 6 caracteres)",
                             type="password", key="fp_new_pwd")
        pwd2 = st.text_input("Confirmar nova senha",
                             type="password", key="fp_new_pwd2")

        if st.form_submit_button(
            "Salvar senha →", type="primary", use_container_width=True
        ):
            if len(pwd) < 6:
                st.error("Senha mínima de 6 caracteres.")
                return
            if pwd != pwd2:
                st.error("As senhas não coincidem.")
                return

            if consume_reset_token(email, token):
                from core.security import hash_password
                users = st.session_state.get("mock_db", {}).get("users", {})
                if email.lower() in users:
                    users[email.lower()]["password_hash"] = hash_password(pwd)
                st.query_params.clear()
                st.success("✅ Senha redefinida! Faça login.")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error("Erro ao redefinir. Solicite novo link.")

    st.markdown("</div>", unsafe_allow_html=True)
