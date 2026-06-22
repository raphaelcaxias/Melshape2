"""
Melshape — Cadastro de Paciente e Profissional.
Envia email de boas-vindas via email_service.
"""
import streamlit as st
import config


def render(services: dict) -> None:
    db     = services["db"]
    is_pro = st.session_state.get("page") == "register_pro"
    label  = "🏥 Profissional de Saúde" if is_pro else "👤 Paciente"

    st.markdown(
        f'<div style="max-width:480px;margin:1.5rem auto 0;">'
        f'<h2 style="font-family:var(--font-display);font-weight:800;'
        f'color:var(--text);text-align:center;margin-bottom:1rem;">'
        f'📝 Criar conta — {label}</h2>',
        unsafe_allow_html=True,
    )

    if is_pro:
        _form_pro(db)
    else:
        _form_paciente(db)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Voltar", use_container_width=True, key="reg_back"):
            st.session_state.page = "landing"
            st.rerun()
    with col2:
        label_alt = "Sou profissional" if not is_pro else "Sou paciente"
        if st.button(label_alt, use_container_width=True, key="reg_toggle"):
            st.session_state.page = (
                "register_pro" if not is_pro else "register"
            )
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def _form_paciente(db) -> None:
    with st.form("reg_paciente", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            name   = st.text_input("Nome completo", key="rp_name")
            email  = st.text_input("Email", key="rp_email")
        with col2:
            pwd    = st.text_input("Senha (mín. 6 caracteres)",
                                   type="password", key="rp_pwd")
            pwd2   = st.text_input("Confirmar senha",
                                   type="password", key="rp_pwd2")

        lgpd = st.checkbox(
            "Li e aceito os Termos de Uso e Política de Privacidade",
            key="rp_lgpd",
        )

        if st.form_submit_button(
            "Criar conta →", type="primary", use_container_width=True
        ):
            erros = _validar(name, email, pwd, pwd2, lgpd)
            if erros:
                for e in erros:
                    st.error(e)
                return

            ok = db.create_user(email.strip().lower(), pwd, name.strip())
            if ok:
                user = db.get_user(email.strip().lower(), pwd)
                if user:
                    st.session_state.user = (
                        user.to_dict() if hasattr(user, "to_dict") else user
                    )
                    st.session_state.page = "onboarding"
                    try:
                        from services.email_service import send_welcome
                        send_welcome(email.strip(), name.strip(),
                                     config.TRIAL_DAYS)
                    except Exception:
                        pass
                    st.rerun()
            else:
                st.error("❌ Email já cadastrado. Tente fazer login.")


def _form_pro(db) -> None:
    with st.form("reg_pro", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            name      = st.text_input("Nome completo", key="rpro_name")
            email     = st.text_input("Email profissional", key="rpro_email")
            specialty = st.selectbox(
                "Especialidade",
                ["nutritionist", "endocrinologist", "other"],
                format_func=lambda x: {
                    "nutritionist":    "🥗 Nutricionista",
                    "endocrinologist": "🩺 Endocrinologista",
                    "other":           "👨‍⚕️ Outro",
                }[x],
                key="rpro_spec",
            )
        with col2:
            pwd = st.text_input("Senha", type="password", key="rpro_pwd")
            crn = st.text_input("CRN / CRM / Registro", key="rpro_crn")

        lgpd = st.checkbox(
            "Li e aceito os Termos de Uso e Política de Privacidade",
            key="rpro_lgpd",
        )

        if st.form_submit_button(
            "Criar conta profissional →",
            type="primary", use_container_width=True,
        ):
            if not lgpd:
                st.error("Aceite os termos para continuar.")
                return
            if not all([name.strip(), email.strip(), pwd, crn.strip()]):
                st.error("Preencha todos os campos.")
                return
            if len(pwd) < 6:
                st.error("Senha mínima de 6 caracteres.")
                return

            ok = db.create_professional(
                email.strip().lower(), pwd, name.strip(), specialty, crn.strip()
            )
            if ok:
                pro = db.get_professional(email.strip().lower(), pwd)
                if pro:
                    st.session_state.professional = (
                        pro.to_dict() if hasattr(pro, "to_dict") else pro
                    )
                    st.session_state.page = "pro_dashboard"
                    try:
                        from services.email_service import send_welcome
                        send_welcome(email.strip(), name.strip(),
                                     config.TRIAL_DAYS)
                    except Exception:
                        pass
                    st.rerun()
            else:
                st.error("❌ Email já cadastrado.")


def _validar(name, email, pwd, pwd2, lgpd) -> list:
    erros = []
    if not name.strip():
        erros.append("Digite seu nome.")
    if not email.strip() or "@" not in email:
        erros.append("Email inválido.")
    if len(pwd) < 6:
        erros.append("Senha mínima de 6 caracteres.")
    if pwd != pwd2:
        erros.append("As senhas não coincidem.")
    if not lgpd:
        erros.append("Aceite os termos para continuar.")
    return erros
