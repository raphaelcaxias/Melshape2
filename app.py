"""
Melshape v2.0 — Entry point principal.

Roteamento completo:
  - Recuperação de senha via URL (?reset_token=&email=)
  - Landing → Login → Register → Onboarding → Home
  - Profissional → Dashboard → Triagem → Paciente → Executivo
  - Paciente → 15 rotas mapeadas
  - Sidebar injetada em todas as telas autenticadas
  - Demo data carregado automaticamente
  - APScheduler para notificações em background
  - Trial banner em todas as telas do paciente
"""
import logging
import streamlit as st

import config
from core.database import Database
from services.nutrition_service import NutritionService
from services.gamification_service import GamificationService
from services.food_service import FoodService
from services.plan_service import PlanService
from services.professional_service import ProfessionalService
from services.journey_service import JourneyService
from services.orchestrator import Orchestrator
from services.notification_service import NotificationService, schedule_daily_reminders

# ── VIEWS AUTH ────────────────────────────────────────────────────────────────
from views.auth import landing as landing_view
from views.auth import login as login_view
from views.auth import register as register_view
from views.auth import forgot_password as forgot_password_view

# ── VIEWS COMPARTILHADAS ──────────────────────────────────────────────────────
from views.shared import sidebar as sidebar_view

# ── VIEWS PACIENTE ────────────────────────────────────────────────────────────
from views.patient import home as home_view
from views.patient import onboarding as onboarding_view
from views.patient import habits as habits_view
from views.patient import goals as goals_view
from views.patient import achievements as achievements_view
from views.patient import glp1 as glp1_view
from views.patient import bariatric as bariatric_view
from views.patient import checkin as checkin_view
from views.patient import journey_story as story_view
from views.patient import profile as profile_view
from views.patient.complete_evolution import render as evolution_view
from views.patient.share_card import render as share_view
from views.patient.register_hub import render as register_hub_view
from views.patient.journey import render as journey_view

# ── VIEWS PROFISSIONAL ────────────────────────────────────────────────────────
from views.professional import dashboard_pro as pro_dashboard_view
from views.professional import patient_detail as patient_detail_view
from views.professional.triage_panel import render_triagem as triage_view
from views.professional.executive_dashboard import render as executive_view

# ── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger("Melshape")

# ── PÁGINA ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{config.APP_NAME} — {config.APP_TAGLINE}",
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About":       f"{config.APP_NAME} v{config.APP_VERSION} · {config.APP_TAGLINE}",
        "Report a bug": "https://melshape.com.br/suporte",
    },
)

# ── SESSÃO ────────────────────────────────────────────────────────────────────
_SESSION_DEFAULTS: dict = {
    "user":                     None,
    "professional":             None,
    "page":                     "landing",
    "perfil_id":                None,
    "demo_loaded":              False,
    "onboarding_step":          1,
    "onboarding_mode":          "general",
    "ob_porque_texto":          "",
    "ob_porque_salvo":          "",
    "pro_page":                 "pro_patients",
    "pro_selected_patient":     None,
    "reset_email_sent":         False,
    "hub_tipo":                 "meal",
    "ci_result":                None,
    "cs_resumo":                None,
    "desafios_concluidos_local": set(),
}

# ── ROTAS DO PACIENTE ─────────────────────────────────────────────────────────
# Cada chave aparece exatamente uma vez.
# Rotas redirecionadas: weight → meals, supplements/workout → habits, etc.
_PATIENT_ROUTES: dict = {
    # Telas principais
    "home":        lambda s, u: home_view.render(s, u),
    "checkin":     lambda s, u: checkin_view.render(s, u),
    "meals":       lambda s, u: register_hub_view(s, u),
    "journey":     lambda s, u: journey_view(s, u),
    "habits":      lambda s, u: habits_view.render(s, u),
    "goals":       lambda s, u: goals_view.render(s, u),
    "analysis":    lambda s, u: achievements_view.render(s, u),
    "glp1":        lambda s, u: glp1_view.render(s, u),
    "bariatric":   lambda s, u: bariatric_view.render(s, u),
    "story":       lambda s, u: story_view.render(s, u),
    "profile":     lambda s, u: profile_view.render(s, u),
    "evolution":   lambda s, u: evolution_view(s, u),
    "share":       lambda s, u: share_view(s, u),
    # Redirecionamentos — mantidos para links legados
    "weight":      lambda s, u: register_hub_view(s, u),
    "supplements": lambda s, u: habits_view.render(s, u),
    "workout":     lambda s, u: habits_view.render(s, u),
    "dashboard":   lambda s, u: home_view.render(s, u),
}

# ── PÁGINAS SEM AUTENTICAÇÃO ──────────────────────────────────────────────────
_AUTH_PAGES: dict = {
    "landing":         lambda s: landing_view.render(s),
    "login":           lambda s: login_view.render(s),
    "register":        lambda s: register_view.render(s),
    "register_pro":    lambda s: register_view.render(s),
    "forgot_password": lambda s: forgot_password_view.render(s),
}


# ── INICIALIZAÇÃO ─────────────────────────────────────────────────────────────
def _init_session() -> None:
    for key, val in _SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _clear_session() -> None:
    """Limpa sessão no logout."""
    for key in list(_SESSION_DEFAULTS.keys()):
        st.session_state.pop(key, None)
    try:
        st.query_params.clear()
    except Exception:
        pass
    st.session_state.page = "landing"
    st.rerun()


def _load_css() -> None:
    try:
        with open("assets/style.css", encoding="utf-8") as f:
            css = f.read()
        user = st.session_state.get("user")
        if user and user.get("dark_mode"):
            st.markdown(
                '<script>document.documentElement'
                '.setAttribute("data-theme","dark")</script>',
                unsafe_allow_html=True,
            )
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        logger.warning("assets/style.css não encontrado.")


@st.cache_resource(show_spinner=False)
def _init_services() -> dict:
    logger.info("🚀 Inicializando serviços Melshape v2.0...")
    db = Database()
    supabase_client = db.client if db.is_real else None

    services = {
        "db":           db,
        "nutrition":    NutritionService(db),
        "gamification": GamificationService(db),
        "foods":        FoodService(supabase_client),
        "plan":         PlanService(db),
        "professional": ProfessionalService(db),
        "journey":      JourneyService(db),
        "orchestrator": Orchestrator(db),
        "notification": NotificationService(db),
    }

    try:
        schedule_daily_reminders(db)
        logger.info("✅ Agendador de notificações iniciado")
    except Exception as e:
        logger.warning(f"Agendador não iniciado: {e}")

    return services


def _load_demo_data(services: dict) -> None:
    """Popula dados demo para o usuário demo@melshape.com.br."""
    if st.session_state.get("demo_loaded"):
        return
    u = st.session_state.get("user", {})
    if u.get("email") != config.DEMO_EMAIL:
        return
    db = services["db"]
    try:
        if len(db.get_meals(30)) > 0:
            st.session_state.demo_loaded = True
            return
        from datetime import date as _d, timedelta as _td
        from core.models import Meal, WeightLog
        meals = [
            ("Peito de Frango Grelhado", 318, 64,   0,   7,   0,   "12:30", 0, "almoco"),
            ("Arroz Integral Cozido",    248,  5.6, 52,   1.6, 3.4, "12:35", 0, "almoco"),
            ("Café com Leite",           120,  6,   12,   4,   0,   "07:30", 0, "cafe_manha"),
            ("Proteína Whey",            120, 24,    3,   2,   0,   "18:00", 0, "pre_pos_treino"),
            ("Banana Prata",              98,  1.3, 26,   0.1, 2,   "15:30", 1, "lanche"),
            ("Tilápia Assada",           256, 52,    0,   5.4, 0,   "12:30", 1, "almoco"),
            ("Aveia em Flocos",          360, 13,   64,   6.9, 9.4, "08:00", 2, "cafe_manha"),
            ("PF: Arroz+Feijão+Frango",  520, 38,   64,   8,   6,   "12:30", 3, "almoco"),
            ("Iogurte Grego",            115,  8.5,  4,   6.5, 0,   "10:00", 4, "lanche"),
            ("Atum em Lata (água)",      116, 26,    0,   1,   0,   "12:00", 4, "almoco"),
        ]
        for food, cal, p, c, f, fi, t, d, tipo in meals:
            db.save_meal(Meal(
                food=food, calories=cal, protein=p, carbs=c,
                fat=f, fiber=fi, meal_time=t, meal_type=tipo,
                meal_date=(_d.today() - _td(days=d)).isoformat(),
            ))
        for i in range(30):
            db.save_weight(WeightLog(
                weight=round(82.0 - i * 0.14, 1),
                log_date=(_d.today() - _td(days=29 - i)).isoformat(),
            ))
        st.session_state.demo_loaded = True
        logger.info("✅ Demo data carregado")
    except Exception as e:
        logger.warning(f"_load_demo_data: {e}")


def _check_url_reset_token() -> bool:
    params = st.query_params
    return "reset_token" in params and "email" in params


def _trial_banner(services: dict, user: dict) -> None:
    """Exibe banner de trial em toda tela autenticada."""
    plan_svc = services.get("plan")
    if plan_svc:
        try:
            plan_svc.trial_banner(user)
        except Exception:
            pass


# ── ROTEADOR PROFISSIONAL ─────────────────────────────────────────────────────
def _route_professional(services: dict, pro: dict, page: str) -> None:
    sidebar_view.render(services)
    if page == "pro_patient_detail":
        patient_detail_view.render(services, pro)
    elif page == "pro_triagem":
        triage_view(services)
    elif page == "pro_executive":
        executive_view(services)
    else:
        pro_dashboard_view.render(services, pro)


# ── ROTEADOR PACIENTE ─────────────────────────────────────────────────────────
def _route_patient(services: dict, user: dict, page: str) -> None:
    sidebar_view.render(services)
    _trial_banner(services, user)

    view_fn = _PATIENT_ROUTES.get(page)
    if view_fn:
        view_fn(services, user)
    else:
        logger.warning(f"Página desconhecida: '{page}' — redirecionando para home")
        st.session_state.page = "home"
        st.rerun()


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main() -> None:
    try:
        _init_session()
        _load_css()
        services = _init_services()

        # ── 1. RESET DE SENHA VIA URL ─────────────────────────────────────────
        if _check_url_reset_token():
            forgot_password_view.render(services)
            return

        # ── 2. PROFISSIONAL AUTENTICADO ───────────────────────────────────────
        pro = st.session_state.professional
        if pro:
            page = st.session_state.page
            _route_professional(services, pro, page)
            return

        # ── 3. NÃO AUTENTICADO ────────────────────────────────────────────────
        user = st.session_state.user
        if not user:
            page = st.session_state.page
            auth_fn = _AUTH_PAGES.get(page, _AUTH_PAGES["landing"])
            auth_fn(services)
            return

        # ── 4. PACIENTE AUTENTICADO ───────────────────────────────────────────
        # Carregar demo data se necessário
        if user.get("email") == config.DEMO_EMAIL:
            _load_demo_data(services)

        page = st.session_state.page

        # Onboarding obrigatório
        if not user.get("onboarding_done") or page == "onboarding":
            onboarding_view.render(services, user)
            # Após onboarding, configurar lembretes
            if st.session_state.get("user", {}).get("onboarding_done"):
                try:
                    services["notification"].configurar_lembretes_iniciais(user)
                except Exception:
                    pass
            return

        # Redirecionar páginas de auth para home (usuário voltou via botão)
        if page in _AUTH_PAGES:
            st.session_state.page = "home"
            st.rerun()
            return

        # Roteamento normal
        _route_patient(services, user, page)

    except Exception as e:
        logger.error(f"Erro crítico em main(): {e}", exc_info=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                '<div style="text-align:center;padding:3rem 0;">'
                '<div style="font-size:2rem;">⚠️</div>'
                '<h3>Algo deu errado</h3>'
                '<p style="color:#6B7280;">Recarregue a página. '
                'Se persistir: suporte@melshape.com.br</p>'
                '</div>',
                unsafe_allow_html=True,
            )
            if st.button("🔄 Recarregar", type="primary",
                         use_container_width=True):
                st.rerun()


if __name__ == "__main__":
    main()
