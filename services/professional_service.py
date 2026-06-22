"""
Melshape — Serviço do Profissional de Saúde.

Gerencia pacientes vinculados, resumos clínicos
e autenticação do profissional.
"""
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger("Melshape.Professional")


class ProfessionalService:

    def __init__(self, db):
        self.db = db

    # ── PACIENTES ─────────────────────────────────────────────────────────────
    def get_patients(self, pro_email: str,
                     limit: int = 50) -> List[Dict[str, Any]]:
        """Retorna pacientes vinculados ao profissional."""
        if self.db.is_real and self.db.client:
            try:
                r = (self.db.client.table("perfis")
                     .select(
                         "id, nome_completo, email, tipo_jornada, "
                         "peso_atual, criado_em"
                     )
                     .eq("profissional_id", pro_email)
                     .order("nome_completo")
                     .limit(limit)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_patients: {e}")
        return self.db._mock().get(f"patients_of_{pro_email}", [])

    def get_patient_summary(self, perfil_id: str) -> Dict[str, Any]:
        """Resumo rápido do paciente para o profissional."""
        if self.db.is_real and self.db.client:
            try:
                r = (self.db.client.table("vw_dashboard_paciente")
                     .select("*")
                     .eq("perfil_id", perfil_id)
                     .limit(1)
                     .execute())
                return r.data[0] if r.data else {}
            except Exception as e:
                logger.warning(f"get_patient_summary: {e}")
        return {}

    def get_patients_at_risk(self,
                              limit: int = 20) -> List[Dict[str, Any]]:
        """Pacientes em risco via vw_prioridade_intervencao."""
        if self.db.is_real and self.db.client:
            try:
                r = (self.db.client.table("vw_prioridade_intervencao")
                     .select(
                         "id, nome_completo, score_prioridade, "
                         "risco_abandono, score_engajamento"
                     )
                     .order("score_prioridade", desc=True)
                     .limit(limit)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_patients_at_risk: {e}")
        return []

    # ── RESUMO EXECUTIVO ──────────────────────────────────────────────────────
    def get_executive_summary(self) -> Dict[str, Any]:
        """Dados de vw_resumo_executivo para dashboard de clínica."""
        if self.db.is_real and self.db.client:
            try:
                r = (self.db.client.table("vw_resumo_executivo")
                     .select("*")
                     .limit(1)
                     .execute())
                return r.data[0] if r.data else {}
            except Exception as e:
                logger.warning(f"get_executive_summary: {e}")
        return {
            "total_pacientes":     0,
            "aderencia_media":     0,
            "consistencia_media":  0,
            "risco_abandono_medio": 0,
        }

    # ── AUTENTICAÇÃO ──────────────────────────────────────────────────────────
    def authenticate(self, email: str,
                     password: str) -> Optional[Dict[str, Any]]:
        """Autentica profissional. Retorna dict ou None."""
        return self.db.get_professional(email, password)

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Busca profissional por email."""
        if self.db.is_real and self.db.client:
            try:
                r = (self.db.client.table("profissionais")
                     .select("*")
                     .eq("email", email)
                     .limit(1)
                     .execute())
                return r.data[0] if r.data else None
            except Exception as e:
                logger.warning(f"get_by_email: {e}")
        pros = self.db._mock().get("professionals", {})
        return pros.get(email.lower())

    # ── VÍNCULO PACIENTE ──────────────────────────────────────────────────────
    def vincular_paciente(self, pro_email: str,
                           paciente_email: str) -> bool:
        """Vincula paciente ao profissional."""
        if self.db.is_real and self.db.client:
            try:
                self.db.client.table("perfis").update({
                    "profissional_id": pro_email,
                }).eq("email", paciente_email).execute()
                return True
            except Exception as e:
                logger.warning(f"vincular_paciente: {e}")
        return False
