"""Melshape — Auth de profissional (mock na V1)."""
import logging
from datetime import datetime, timedelta
from typing import Optional
from core.models import Professional
from core.security import hash_password, verify_password
logger = logging.getLogger("Melshape.Database")

class ProfessionalAuthMixin:

    def get_professional(self, email: str, password: str) -> Optional[Professional]:
        d = self._mock()["professionals"].get(email.lower())
        if d and verify_password(password, d.get("password_hash", "")):
            return Professional.from_dict(d)
        return None

    def create_professional(self, email: str, password: str, name: str,
                             specialty: str, crn: str, lgpd_ts: str = "") -> bool:
        import config
        pros = self._mock()["professionals"]
        if email.lower() in pros:
            return False
        trial_end = (
            datetime.utcnow() + timedelta(days=config.TRIAL_DAYS)
        ).isoformat()
        pros[email.lower()] = {
            "email": email.lower(), "name": name,
            "password_hash": hash_password(password),
            "user_type": "professional", "specialty": specialty,
            "crn_number": crn, "pro_plan": "starter",
            "patient_count": 0, "trial_expires_at": trial_end,
            "lgpd_accepted_at": lgpd_ts, "onboarding_done": False,
        }
        return True
