"""
Melshape — Repositório Clínico do Profissional.

Tabelas:
  condutas_clinicas         → decisões clínicas do profissional
  observacoes_profissionais → anotações livres sobre o paciente
  prescricoes_alimentares   → prescrição vinculada ao paciente
  modelos_refeicao          → modelos de refeição do profissional
  itens_modelo_refeicao     → itens de cada modelo

Todas as operações identificam o profissional pelo session_state.
"""
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger("Melshape.ClinicalRepo")


class ClinicalRepository:
    """
    Mixin clínico. Requer self.client, self.is_real,
    self.uid(), self._mock() do Database.
    """

    def _pro_uid(self) -> str:
        """Retorna ID do profissional logado."""
        pro = __import__("streamlit").session_state.get("professional")
        if pro:
            return getattr(pro, "email", "") or pro.get("email", "")
        return self.uid()

    # ── CONDUTAS CLÍNICAS ─────────────────────────────────────────────────────
    def registrar_conduta(self, perfil_id: str, titulo: str,
                           descricao: str, tipo: str = "orientacao") -> bool:
        pro_id = self._pro_uid()
        if self.is_real and self.client:
            try:
                self.client.table("condutas_clinicas").insert({
                    "perfil_id":      perfil_id,
                    "profissional_id": pro_id,
                    "titulo":         titulo,
                    "descricao":      descricao,
                    "tipo":           tipo,
                    "data_conduta":   date.today().isoformat(),
                    "resolvido":      False,
                }).execute()
                return True
            except Exception as e:
                logger.warning(f"registrar_conduta: {e}")
        key = f"condutas_{perfil_id}"
        self._mock().setdefault(key, []).append({
            "profissional_id": pro_id, "titulo": titulo,
            "descricao": descricao, "tipo": tipo,
            "data_conduta": date.today().isoformat(),
        })
        return True

    def get_condutas(self, perfil_id: str, limit: int = 20) -> list:
        if self.is_real and self.client:
            try:
                r = (self.client.table("condutas_clinicas")
                     .select("*")
                     .eq("perfil_id", perfil_id)
                     .order("data_conduta", desc=True)
                     .limit(limit)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_condutas: {e}")
        return self._mock().get(f"condutas_{perfil_id}", [])

    # ── OBSERVAÇÕES ───────────────────────────────────────────────────────────
    def registrar_observacao(self, perfil_id: str,
                              observacao: str,
                              privada: bool = True) -> bool:
        pro_id = self._pro_uid()
        if self.is_real and self.client:
            try:
                self.client.table("observacoes_profissionais").insert({
                    "perfil_id":       perfil_id,
                    "profissional_id": pro_id,
                    "observacao":      observacao,
                    "privada":         privada,
                    "criado_em":       date.today().isoformat(),
                }).execute()
                return True
            except Exception as e:
                logger.warning(f"registrar_observacao: {e}")
        self._mock().setdefault(f"obs_{perfil_id}", []).append({
            "profissional_id": pro_id, "observacao": observacao,
            "criado_em": date.today().isoformat(),
        })
        return True

    def get_observacoes(self, perfil_id: str) -> list:
        if self.is_real and self.client:
            try:
                r = (self.client.table("observacoes_profissionais")
                     .select("observacao, criado_em, privada")
                     .eq("perfil_id", perfil_id)
                     .order("criado_em", desc=True)
                     .limit(20)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_observacoes: {e}")
        return self._mock().get(f"obs_{perfil_id}", [])

    # ── PRESCRIÇÕES ───────────────────────────────────────────────────────────
    def criar_prescricao(self, perfil_id: str,
                          objetivo: str, validade_dias: int = 30) -> Optional[dict]:
        pro_id    = self._pro_uid()
        validade  = date.today().isoformat()
        if self.is_real and self.client:
            try:
                r = self.client.table("prescricoes_alimentares").insert({
                    "perfil_id":       perfil_id,
                    "profissional_id": pro_id,
                    "objetivo":        objetivo,
                    "data_inicio":     validade,
                    "ativa":           True,
                }).execute()
                return r.data[0] if r.data else None
            except Exception as e:
                logger.warning(f"criar_prescricao: {e}")
        presc = {
            "id": f"presc_{perfil_id}",
            "perfil_id": perfil_id, "objetivo": objetivo,
            "data_inicio": validade, "ativa": True,
        }
        self._mock()[f"prescricao_{perfil_id}"] = presc
        return presc

    def get_prescricao_ativa(self, perfil_id: str) -> Optional[dict]:
        if self.is_real and self.client:
            try:
                r = (self.client.table("prescricoes_alimentares")
                     .select("*")
                     .eq("perfil_id", perfil_id)
                     .eq("ativa", True)
                     .order("data_inicio", desc=True)
                     .limit(1)
                     .execute())
                return r.data[0] if r.data else None
            except Exception as e:
                logger.warning(f"get_prescricao_ativa: {e}")
        return self._mock().get(f"prescricao_{perfil_id}")

    # ── MODELOS DE REFEIÇÃO ────────────────────────────────────────────────────
    def get_modelos_profissional(self) -> list:
        pro_id = self._pro_uid()
        if self.is_real and self.client:
            try:
                r = (self.client.table("modelos_refeicao")
                     .select("id, nome, descricao")
                     .eq("profissional_id", pro_id)
                     .order("criado_em", desc=True)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_modelos_profissional: {e}")
        return self._mock().get(f"modelos_{pro_id}", [])
