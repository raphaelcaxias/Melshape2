"""
Melshape — Repositório de Jornada.

Tabelas: jornadas, etapas_jornada, marcos, eventos_jornada,
         conquistas_jornada, metas

Usado por: views/patient/journey.py e journey_service.py
"""
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger("Melshape.JourneyRepo")


class JourneyRepository:
    """
    Mixin de jornada — requer self.client, self.is_real, self.uid(),
    self._mock() da classe Database base.
    """

    # ── JORNADA ATIVA ────────────────────────────────────────────────────────
    def get_jornada_ativa(self) -> Optional[dict]:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = (self.client.table("jornadas")
                     .select("*")
                     .eq("perfil_id", uid)
                     .eq("ativa", True)
                     .limit(1)
                     .execute())
                return r.data[0] if r.data else None
            except Exception as e:
                logger.warning(f"get_jornada_ativa: {e}")

        for j in self._mock().get("jornadas", []):
            if j.get("user_id") == uid and j.get("ativa"):
                return j
        return None

    def criar_jornada(self, tipo: str, nome: str,
                      objetivo: str = "") -> Optional[dict]:
        """Cria jornada ativa para o paciente se não existir."""
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = self.client.table("jornadas").insert({
                    "perfil_id":  uid,
                    "tipo":       tipo,
                    "nome":       nome,
                    "objetivo":   objetivo or None,
                    "ativa":      True,
                    "iniciada_em": date.today().isoformat(),
                }).execute()
                return r.data[0] if r.data else None
            except Exception as e:
                logger.warning(f"criar_jornada: {e}")

        jornada = {
            "id": f"j_{uid}_{tipo}",
            "user_id": uid, "tipo": tipo,
            "nome": nome, "ativa": True,
            "iniciada_em": date.today().isoformat(),
        }
        self._mock().setdefault("jornadas", []).append(jornada)
        return jornada

    # ── ETAPAS ───────────────────────────────────────────────────────────────
    def get_etapas(self, jornada_id: str) -> list:
        if self.is_real and self.client:
            try:
                r = (self.client.table("etapas_jornada")
                     .select("*")
                     .eq("jornada_id", jornada_id)
                     .order("ordem")
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_etapas: {e}")
        return []

    def get_etapa_atual(self, jornada_id: str) -> Optional[dict]:
        """Retorna a primeira etapa não concluída."""
        etapas = self.get_etapas(jornada_id)
        for e in etapas:
            if not e.get("concluida"):
                return e
        return etapas[-1] if etapas else None

    def concluir_etapa(self, etapa_id: str) -> bool:
        if self.is_real and self.client:
            try:
                self.client.table("etapas_jornada").update({
                    "concluida":    True,
                    "concluida_em": date.today().isoformat(),
                }).eq("id", etapa_id).execute()
                return True
            except Exception as e:
                logger.warning(f"concluir_etapa: {e}")
        return False

    # ── MARCOS ───────────────────────────────────────────────────────────────
    def get_marcos(self, jornada_id: str) -> list:
        if self.is_real and self.client:
            try:
                r = (self.client.table("marcos")
                     .select("*")
                     .eq("jornada_id", jornada_id)
                     .order("data_marco", desc=True)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_marcos: {e}")
        return self._mock().get(f"marcos_{jornada_id}", [])

    def registrar_marco(self, jornada_id: str,
                        titulo: str, descricao: str = "") -> bool:
        if self.is_real and self.client:
            try:
                self.client.table("marcos").insert({
                    "jornada_id":  jornada_id,
                    "titulo":      titulo,
                    "descricao":   descricao or None,
                    "data_marco":  date.today().isoformat(),
                }).execute()
                return True
            except Exception as e:
                logger.warning(f"registrar_marco: {e}")
        key = f"marcos_{jornada_id}"
        self._mock().setdefault(key, []).append({
            "titulo": titulo, "descricao": descricao,
            "data_marco": date.today().isoformat(),
        })
        return True

    # ── EVENTOS ───────────────────────────────────────────────────────────────
    def get_eventos(self, jornada_id: str, limit: int = 10) -> list:
        if self.is_real and self.client:
            try:
                r = (self.client.table("eventos_jornada")
                     .select("*")
                     .eq("jornada_id", jornada_id)
                     .order("criado_em", desc=True)
                     .limit(limit)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_eventos: {e}")
        return []

    def registrar_evento(self, jornada_id: str,
                         tipo: str, descricao: str) -> bool:
        if self.is_real and self.client:
            try:
                self.client.table("eventos_jornada").insert({
                    "jornada_id": jornada_id,
                    "tipo":       tipo,
                    "descricao":  descricao,
                }).execute()
                return True
            except Exception as e:
                logger.warning(f"registrar_evento: {e}")
        return False

    # ── METAS ────────────────────────────────────────────────────────────────
    def get_metas(self, jornada_id: str) -> list:
        if self.is_real and self.client:
            try:
                r = (self.client.table("metas")
                     .select("*")
                     .eq("jornada_id", jornada_id)
                     .order("criado_em", desc=True)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_metas: {e}")
        return self._mock().get(f"metas_{jornada_id}", [])

    def criar_meta(self, jornada_id: str, titulo: str,
                   valor_alvo: float, unidade: str,
                   prazo: str = "") -> bool:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                self.client.table("metas").insert({
                    "jornada_id":  jornada_id,
                    "perfil_id":   uid,
                    "titulo":      titulo,
                    "valor_alvo":  valor_alvo,
                    "unidade":     unidade,
                    "prazo":       prazo or None,
                    "concluida":   False,
                }).execute()
                return True
            except Exception as e:
                logger.warning(f"criar_meta: {e}")
        key = f"metas_{jornada_id}"
        self._mock().setdefault(key, []).append({
            "titulo": titulo, "valor_alvo": valor_alvo,
            "unidade": unidade, "prazo": prazo,
            "concluida": False,
            "criado_em": date.today().isoformat(),
        })
        return True
