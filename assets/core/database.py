"""
Melshape — Camada de dados principal.
Supabase (tabelas reais) com fallback MockDB para demo/offline.

Tabelas reais: perfis, refeicoes, itens_refeicao, alimentos_base,
               pesagens, registros_agua, checkins,
               experiencia_usuario, badges_usuario, badges, jornadas
"""
import logging
import copy
import streamlit as st
from datetime import date, datetime, timedelta
from typing import Optional

from core.models import User, Professional
from core.security import hash_password, verify_password
from core.database_records import RecordsMixin
from core.database_pro_auth import ProfessionalAuthMixin
from core.journey_repository import JourneyRepository
from core.habit_repository import HabitRepository
from core.glp1_repository import GLP1Repository
from core.bariatric_repository import BariatricRepository
from core.notification_repository import NotificationRepository
from core.clinical_repository import ClinicalRepository
from core.journey_story_repository import JourneyStoryRepository

logger = logging.getLogger("Melshape.Database")

_MOCK_DEFAULTS = {
    "users": {}, "professionals": {},
    "meals": [], "weights": [], "supplements": [],
    "workouts": [], "achievements": [],
    "hydration": [], "symptoms": [], "sleep": [], "cycles": [], "checkins": [],
}

class Database(RecordsMixin, JourneyRepository, HabitRepository, ProfessionalAuthMixin,
               GLP1Repository, BariatricRepository, NotificationRepository,
               ClinicalRepository, JourneyStoryRepository):
    """Abstração de banco: Supabase → MockDB automático."""

    def __init__(self):
        self.is_real = False
        self.client  = None
        try:
            if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
                from supabase import create_client
                self.client = create_client(
                    st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
                )
                self.is_real = True
                logger.info("✅ Supabase conectado")
        except Exception as e:
            logger.warning(f"⚠️ Modo offline: {e}")
        self._init_mock()

    # ── MOCK ──────────────────────────────────────────────────────────────────
    def _init_mock(self):
        if "mock_db" not in st.session_state:
            st.session_state.mock_db = copy.deepcopy(_MOCK_DEFAULTS)

    def _mock(self) -> dict:
        return st.session_state.mock_db

    # ── UID = perfil_id ───────────────────────────────────────────────────────
    def uid(self) -> str:
        if self.is_real and self.client:
            try:
                pid = st.session_state.get("perfil_id")
                if pid:
                    return pid
                u = self.client.auth.get_user()
                if u and u.user:
                    r = (self.client.table("perfis")
                         .select("id")
                         .eq("usuario_id", u.user.id)
                         .single().execute())
                    if r.data:
                        st.session_state["perfil_id"] = r.data["id"]
                        return r.data["id"]
            except Exception:
                pass
        u = st.session_state.get("user")
        return u.get("email", "anon") if u else "anon"

    # ── HELPERS ───────────────────────────────────────────────────────────────
    def _filter_user(self, lst: list, uid: str) -> list:
        return [x for x in lst if x.get("user_id") == uid]

    def _filter_days(self, lst: list, days: Optional[int],
                     date_field: str = "log_date") -> list:
        if not days:
            return lst
        cutoff = date.today() - timedelta(days=days)
        result = []
        for x in lst:
            try:
                d = datetime.strptime(
                    x.get(date_field, "2000-01-01"), "%Y-%m-%d"
                ).date()
                if d >= cutoff:
                    result.append(x)
            except Exception:
                pass
        return result

    def _make_model(self, cls, row: dict):
        valid = {k: v for k, v in row.items() if k in cls.__dataclass_fields__}
        return cls(**valid)

    # ── AUTH ──────────────────────────────────────────────────────────────────
    def get_user(self, email: str, password: str) -> Optional[User]:
        if self.is_real and self.client:
            try:
                r = self.client.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
                if r.user:
                    perfil = (self.client.table("perfis")
                              .select("*")
                              .eq("usuario_id", r.user.id)
                              .single().execute())
                    p = perfil.data or {}
                    st.session_state["perfil_id"] = p.get("id", "")
                    return User.from_dict({
                        **p,
                        "email": email,
                        "name":         p.get("nome_completo", email.split("@")[0]),
                        "health_mode":  p.get("tipo_jornada", "general"),
                        "onboarding_done": p.get("onboarding_concluido", False),
                        "dark_mode":    p.get("dark_mode", False),
                        "current_weight": p.get("peso_atual"),
                        "goal_weight":  p.get("peso_desejado"),
                        "height":       p.get("altura"),
                        "age":          p.get("idade"),
                        "gender":       p.get("genero", "female"),
                        "activity_level": p.get("nivel_atividade", "moderate"),
                    })
            except Exception as e:
                logger.error(f"Login Supabase: {e}")
        d = self._mock()["users"].get(email.lower())
        if d and verify_password(password, d.get("password_hash", "")):
            return User.from_dict(d)
        return None

    def create_user(self, email: str, password: str, name: str,
                    lgpd_ts: str = "", gender: str = "female") -> bool:
        import config
        if self.is_real and self.client:
            try:
                r = self.client.auth.sign_up({
                    "email": email, "password": password,
                    "options": {"data": {"name": name}},
                })
                if r.user:
                    self.client.table("perfis").insert({
                        "usuario_id": r.user.id,
                        "nome_completo": name,
                        "genero": gender,
                        "onboarding_concluido": False,
                        "tipo_jornada": "general",
                    }).execute()
                    return True
            except Exception as e:
                logger.error(f"Cadastro Supabase: {e}")
        users = self._mock()["users"]
        if email.lower() in users:
            return False
        trial_end = (
            datetime.utcnow() + timedelta(days=config.TRIAL_DAYS)
        ).isoformat()
        users[email.lower()] = {
            "email": email.lower(), "name": name,
            "password_hash": hash_password(password),
            "user_type": "patient", "plan": "trial",
            "trial_started_at": datetime.utcnow().isoformat(),
            "trial_expires_at": trial_end,
            "lgpd_accepted_at": lgpd_ts, "gender": gender,
            "onboarding_done": False, "health_mode": "general",
        }
        return True

    def update_user(self, data: dict) -> bool:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                campo_map = {
                    "name": "nome_completo", "health_mode": "tipo_jornada",
                    "current_weight": "peso_atual", "goal_weight": "peso_desejado",
                    "height": "altura", "age": "idade", "gender": "genero",
                    "activity_level": "nivel_atividade", "goal": "objetivo",
                    "dark_mode": "dark_mode", "onboarding_done": "onboarding_concluido",
                    "professional_id": "profissional_id",
                }
                payload = {campo_map.get(k, k): v for k, v in data.items()}
                self.client.table("perfis").update(payload).eq("id", uid).execute()
                return True
            except Exception as e:
                logger.error(f"update_user: {e}")
        u = st.session_state.get("user", {})
        if u:
            u.update(data)
            st.session_state.user = u
        return True

    def delete_user(self, email: str) -> bool:
        """Remove conta do paciente (LGPD — direito de exclusão)."""
        if self.is_real and self.client:
            try:
                self.client.table("perfis").delete().eq(
                    "email", email
                ).execute()
                return True
            except Exception as e:
                logger.error(f"delete_user: {e}")
        mock = self._mock()
        mock.get("users", {}).pop(email.lower(), None)
        return True

