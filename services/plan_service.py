"""
Melshape — Serviço de Planos e Trial.

Controla acesso a funcionalidades por plano.
Trial de 10 dias automático para novos usuários.

Planos: free | trial | pro | clinic
"""
import streamlit as st
from datetime import date, datetime
from typing import Optional
import config


# Mapa de features por plano
_FEATURES = {
    "charts":        [config.PLAN_TRIAL, config.PLAN_PRO, config.PLAN_CLINIC],
    "export":        [config.PLAN_PRO, config.PLAN_CLINIC],
    "professional":  [config.PLAN_PRO, config.PLAN_CLINIC],
    "evolution":     [config.PLAN_TRIAL, config.PLAN_PRO, config.PLAN_CLINIC],
    "glp1":          [config.PLAN_TRIAL, config.PLAN_PRO, config.PLAN_CLINIC],
    "bariatric":     [config.PLAN_TRIAL, config.PLAN_PRO, config.PLAN_CLINIC],
    "gamification":  [config.PLAN_TRIAL, config.PLAN_PRO, config.PLAN_CLINIC],
    "notifications": [config.PLAN_PRO, config.PLAN_CLINIC],
    "executive":     [config.PLAN_CLINIC],
}


class PlanService:

    def __init__(self, db):
        self.db = db

    # ── PLANO ATUAL ───────────────────────────────────────────────────────────
    def get_plan(self, user: dict) -> str:
        """Retorna plano atual do usuário."""
        plan = user.get("plan", config.PLAN_FREE)
        # Trial ativo?
        if plan == config.PLAN_TRIAL:
            if self.trial_days_remaining(user) <= 0:
                return config.PLAN_FREE
        return plan

    def trial_days_remaining(self, user: dict) -> int:
        """Dias restantes de trial. 0 se expirado ou não é trial."""
        if user.get("plan") != config.PLAN_TRIAL:
            return 0
        created = user.get("created_at", "") or user.get("trial_start", "")
        if not created:
            return config.TRIAL_DAYS
        try:
            start = datetime.fromisoformat(created[:10]).date()
            elapsed = (date.today() - start).days
            return max(0, config.TRIAL_DAYS - elapsed)
        except Exception:
            return 0

    # ── VERIFICAÇÃO DE ACESSO ─────────────────────────────────────────────────
    def can_use(self, user: dict, feature: str) -> bool:
        """Verifica se usuário tem acesso à feature."""
        plan = self.get_plan(user)
        # Demo tem acesso total
        if user.get("email") == config.DEMO_EMAIL:
            return True
        allowed = _FEATURES.get(feature, [])
        return plan in allowed

    # ── BANNER DE TRIAL ───────────────────────────────────────────────────────
    def trial_banner(self, user: dict) -> None:
        """Exibe banner de trial na parte superior da tela."""
        plan = user.get("plan", "")
        if plan != config.PLAN_TRIAL:
            return
        days = self.trial_days_remaining(user)
        if days <= 0:
            st.warning(
                "⏰ Seu trial expirou. Assine o Pro para continuar.",
                icon="🔒",
            )
            if st.button("Assinar agora →", key="trial_expired_cta",
                         type="primary"):
                st.session_state.page = "profile"
                st.rerun()
            return
        if days <= 3:
            st.warning(
                f"⏰ **{days} dia(s)** de trial restantes. "
                f"Assine para não perder seu progresso.",
                icon="⚠️",
            )

    # ── PAYWALL ───────────────────────────────────────────────────────────────
    def show_paywall(self, feature_name: str, user: dict) -> None:
        """Exibe tela de paywall para features bloqueadas."""
        plan = self.get_plan(user)
        st.markdown(
            f'<div style="text-align:center;padding:2rem 1rem;">'
            f'<div style="font-size:3rem;">🔒</div>'
            f'<h3 style="font-family:var(--font-display);color:var(--text);">'
            f'{feature_name}</h3>'
            f'<p style="color:var(--text-muted);max-width:400px;margin:0 auto;">'
            f'Este recurso está disponível no plano '
            f'<b>Melshape Pro</b> por apenas '
            f'<b>R${config.PLAN_PRICE_PRO:.2f}/mês</b>.</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "🚀 Assinar o Melshape Pro",
                type="primary",
                use_container_width=True,
                key=f"paywall_{feature_name}",
            ):
                st.session_state.page = "profile"
                st.rerun()
            if plan == config.PLAN_FREE:
                st.markdown(
                    '<div style="text-align:center;font-size:0.78rem;'
                    'color:var(--text-muted);margin-top:0.5rem;">'
                    '✨ Inicie com 10 dias de trial grátis</div>',
                    unsafe_allow_html=True,
                )
