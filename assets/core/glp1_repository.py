"""
Melshape — Repositório GLP-1.

Tabelas:
  doses_glp1     → registro de cada aplicação
  sintomas_glp1  → sintomas relatados pelo paciente
  protocolos_glp1 → protocolo ativo do paciente

Colunas doses_glp1:
  perfil_id, medicamento, dose, data_aplicacao,
  fase, observacao, protocolo_id

Colunas sintomas_glp1:
  perfil_id, data_registro, sintomas (jsonb/text),
  severidade, observacao
"""
import logging
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger("Melshape.GLP1Repo")


class GLP1Repository:
    """
    Mixin GLP-1. Requer self.client, self.is_real,
    self.uid(), self._mock() do Database.
    """

    # ── DOSES ────────────────────────────────────────────────────────────────
    def registrar_dose_glp1(self, medicamento: str, dose: str,
                             fase: str, observacao: str = "",
                             protocolo_id: str = "") -> bool:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                payload = {
                    "perfil_id":       uid,
                    "medicamento":     medicamento,
                    "dose":            dose,
                    "data_aplicacao":  date.today().isoformat(),
                    "fase":            fase,
                    "observacao":      observacao or None,
                }
                if protocolo_id:
                    payload["protocolo_id"] = protocolo_id
                self.client.table("doses_glp1").insert(payload).execute()
                return True
            except Exception as e:
                logger.warning(f"registrar_dose_glp1: {e}")
        self._mock().setdefault("doses_glp1", []).append({
            "user_id": uid, "medicamento": medicamento,
            "dose": dose, "fase": fase,
            "data_aplicacao": date.today().isoformat(),
        })
        return True

    def get_doses_glp1(self, days: int = 90) -> list:
        uid    = self.uid()
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        if self.is_real and self.client:
            try:
                r = (self.client.table("doses_glp1")
                     .select("*")
                     .eq("perfil_id", uid)
                     .gte("data_aplicacao", cutoff)
                     .order("data_aplicacao", desc=True)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_doses_glp1: {e}")
        return [
            d for d in self._mock().get("doses_glp1", [])
            if d.get("user_id") == uid
            and d.get("data_aplicacao", "") >= cutoff
        ]

    def get_ultima_dose(self) -> Optional[dict]:
        doses = self.get_doses_glp1(days=30)
        return doses[0] if doses else None

    # ── SINTOMAS ─────────────────────────────────────────────────────────────
    def registrar_sintomas_glp1(self, sintomas: list,
                                 severidade: int,
                                 observacao: str = "") -> bool:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                import json
                self.client.table("sintomas_glp1").insert({
                    "perfil_id":      uid,
                    "data_registro":  date.today().isoformat(),
                    "sintomas":       json.dumps(sintomas),
                    "severidade":     severidade,
                    "observacao":     observacao or None,
                }).execute()
                return True
            except Exception as e:
                logger.warning(f"registrar_sintomas_glp1: {e}")
        self._mock().setdefault("sintomas_glp1", []).append({
            "user_id": uid, "sintomas": sintomas,
            "severidade": severidade,
            "data_registro": date.today().isoformat(),
        })
        return True

    def get_sintomas_glp1(self, days: int = 30) -> list:
        uid    = self.uid()
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        if self.is_real and self.client:
            try:
                r = (self.client.table("sintomas_glp1")
                     .select("*")
                     .eq("perfil_id", uid)
                     .gte("data_registro", cutoff)
                     .order("data_registro", desc=True)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_sintomas_glp1: {e}")
        return [
            s for s in self._mock().get("sintomas_glp1", [])
            if s.get("user_id") == uid
            and s.get("data_registro", "") >= cutoff
        ]

    # ── PROTOCOLO ────────────────────────────────────────────────────────────
    def get_protocolo_ativo(self) -> Optional[dict]:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = (self.client.table("protocolos_glp1")
                     .select("*")
                     .eq("perfil_id", uid)
                     .eq("ativo", True)
                     .limit(1)
                     .execute())
                return r.data[0] if r.data else None
            except Exception as e:
                logger.warning(f"get_protocolo_ativo: {e}")
        return None

    def criar_protocolo(self, medicamento: str,
                         dose_inicial: str) -> Optional[dict]:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = self.client.table("protocolos_glp1").insert({
                    "perfil_id":    uid,
                    "medicamento":  medicamento,
                    "dose_inicial": dose_inicial,
                    "dose_atual":   dose_inicial,
                    "fase":         "adapting",
                    "ativo":        True,
                    "iniciado_em":  date.today().isoformat(),
                }).execute()
                return r.data[0] if r.data else None
            except Exception as e:
                logger.warning(f"criar_protocolo: {e}")
        proto = {
            "id": f"p_{uid}", "user_id": uid,
            "medicamento": medicamento,
            "dose_atual": dose_inicial, "fase": "adapting",
            "iniciado_em": date.today().isoformat(),
        }
        self._mock()["protocolo_glp1"] = proto
        return proto
