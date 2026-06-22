"""Melshape — Perfil: abas de plano, preferências e conta."""
import streamlit as st
import config
from views.components.cards import alert

# ── TAB 2: PLANO ──────────────────────────────────────────────────────────────
def _tab_plano(plan_svc, user: dict) -> None:
    st.markdown("##### 💳 Meu Plano")

    plan = user.get("plan", config.PLAN_FREE)

    _PLAN_LABELS = {
        config.PLAN_FREE:   ("🔓", "Gratuito",  "Funcionalidades básicas"),
        config.PLAN_TRIAL:  ("✨", "Trial Pro", f"{config.TRIAL_DAYS} dias grátis"),
        config.PLAN_PRO:    ("🚀", "Pro",        "Acesso completo"),
        config.PLAN_CLINIC: ("🏥", "Clínica",    "Gestão de equipe"),
    }

    icon, label, desc = _PLAN_LABELS.get(plan, ("🔓", plan, ""))

    st.markdown(
        f'<div class="metric-card fade-in" style="margin-bottom:1rem;">'
        f'<div style="display:flex;align-items:center;gap:0.8rem;">'
        f'<span style="font-size:2rem;">{icon}</span>'
        f'<div>'
        f'<div style="font-weight:800;font-size:1.1rem;color:var(--text);">'
        f'Plano {label}</div>'
        f'<div style="font-size:0.80rem;color:var(--text-muted);">{desc}</div>'
        f'</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if plan == config.PLAN_TRIAL and plan_svc:
        days = plan_svc.trial_days_remaining(user)
        if days > 0:
            alert(f"⏳ {days} dia(s) de trial restantes.", "info")
        else:
            alert("⏰ Trial expirado. Assine o Pro para continuar.", "warning")

    if plan in (config.PLAN_FREE, config.PLAN_TRIAL):
        st.markdown("---")
        st.markdown("##### 🚀 Assinar Melshape Pro")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f'<div class="metric-card fade-in">'
                f'<div style="font-weight:800;font-size:1.3rem;'
                f'color:var(--primary);">R${config.PLAN_PRICE_PRO:.2f}/mês</div>'
                f'<div style="font-size:0.80rem;color:var(--text-muted);">'
                f'Plano Pro — acesso completo</div>'
                f'<ul style="font-size:0.78rem;color:var(--text-muted);'
                f'padding-left:1rem;margin:0.5rem 0 0;">'
                f'<li>Gráficos e análises</li>'
                f'<li>Exportação de dados</li>'
                f'<li>Notificações por email</li>'
                f'<li>Evolução completa</li>'
                f'</ul></div>',
                unsafe_allow_html=True,
            )
            if st.button("Assinar Pro →", type="primary",
                         use_container_width=True, key="pf_assinar_pro"):
                st.info("🔗 Integração com Stripe/Hotmart em breve.")

        with col2:
            st.markdown(
                f'<div class="metric-card fade-in">'
                f'<div style="font-weight:800;font-size:1.3rem;'
                f'color:var(--primary);">R${config.PLAN_PRICE_CLINIC:.2f}/mês</div>'
                f'<div style="font-size:0.80rem;color:var(--text-muted);">'
                f'Plano Clínica — gestão de equipe</div>'
                f'<ul style="font-size:0.78rem;color:var(--text-muted);'
                f'padding-left:1rem;margin:0.5rem 0 0;">'
                f'<li>Dashboard executivo</li>'
                f'<li>Múltiplos profissionais</li>'
                f'<li>Relatórios por paciente</li>'
                f'<li>Suporte prioritário</li>'
                f'</ul></div>',
                unsafe_allow_html=True,
            )
            if st.button("Falar com equipe →",
                         use_container_width=True, key="pf_clinic_cta"):
                st.info("📧 contato@melshape.com.br")


# ── TAB 3: PREFERÊNCIAS ───────────────────────────────────────────────────────
def _tab_preferencias(db, user: dict) -> None:
    st.markdown("##### 🔔 Preferências")

    notif = st.toggle(
        "Receber lembretes por email",
        value=not user.get("disable_reminders", False),
        key="pf_notif",
    )
    dark  = st.toggle(
        "Modo escuro",
        value=user.get("dark_mode", False),
        key="pf_dark",
    )

    if st.button("💾 Salvar preferências", type="primary",
                 use_container_width=True, key="pf_pref_save"):
        upd = {
            "disable_reminders": not notif,
            "dark_mode":         dark,
        }
        try:
            db.update_user(upd)
            st.session_state.user.update(upd)
            st.toast("💾 Preferências salvas!", icon="✅")
            st.rerun()
        except Exception as e:
            st.toast(f"Erro: {e}", icon="❌")


# ── TAB 4: CONTA ──────────────────────────────────────────────────────────────
def _tab_conta(db, user: dict) -> None:
    st.markdown("##### 🚪 Gerenciar Conta")

    email = user.get("email", "—")
    st.markdown(
        f'<div style="font-size:0.84rem;color:var(--text-muted);'
        f'margin-bottom:1rem;">Email: <b>{email}</b></div>',
        unsafe_allow_html=True,
    )

    # Logout
    if st.button("🚪 Sair da conta", use_container_width=True,
                 key="pf_logout"):
        for key in ["user", "professional", "page", "demo_loaded",
                    "onboarding_step", "onboarding_mode"]:
            st.session_state.pop(key, None)
        st.session_state.page = "landing"
        st.rerun()

    st.markdown("---")

    # Exclusão de conta
    st.markdown(
        '<div style="font-size:0.80rem;color:var(--text-muted);">'
        '⚠️ A exclusão é permanente e remove todos os seus dados.</div>',
        unsafe_allow_html=True,
    )

    confirmar = st.checkbox("Confirmo que quero excluir minha conta",
                             key="pf_del_confirm")
    if confirmar:
        if st.button("🗑️ Excluir minha conta", use_container_width=True,
                     key="pf_del_btn",
                     help="Ação irreversível"):
            try:
                db.delete_user(email)
            except Exception:
                pass
            for key in list(st.session_state.keys()):
                st.session_state.pop(key, None)
            st.session_state.page = "landing"
            st.rerun()
