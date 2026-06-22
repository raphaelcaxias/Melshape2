"""
Melshape — Repositório Bariátrico.

Tabelas:
  cirurgias        → dados da cirurgia do paciente
  fases_bariatricas → fase atual registrada pelo profissional ou paciente

Colunas cirurgias:
  perfil_id, tipo_cirurgia, data_cirurgia,
  peso_pre_cirurgia, altura, observacoes

Colunas fases_bariatricas:
  perfil_id, fase, iniciada_em, observacao
"""
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger("Melshape.BariatricRepo")


class BariatricRepository:
    """
    Mixin bariátrico. Requer self.client, self.is_real,
    self.uid(), self._mock() do Database.
    """

    # ── CIRURGIA ─────────────────────────────────────────────────────────────
    def get_cirurgia(self) -> Optional[dict]:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = (self.client.table("cirurgias")
                     .select("*")
                     .eq("perfil_id", uid)
                     .order("data_cirurgia", desc=True)
                     .limit(1)
                     .execute())
                return r.data[0] if r.data else None
            except Exception as e:
                logger.warning(f"get_cirurgia: {e}")
        return self._mock().get(f"cirurgia_{uid}")

    def registrar_cirurgia(self, tipo: str, data_cirurgia: str,
                            peso_pre: float, observacoes: str = "") -> bool:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                # Verifica se já existe
                existente = self.get_cirurgia()
                if existente:
                    self.client.table("cirurgias").update({
                        "tipo_cirurgia":    tipo,
                        "data_cirurgia":    data_cirurgia,
                        "peso_pre_cirurgia": peso_pre,
                        "observacoes":      observacoes or None,
                    }).eq("id", existente["id"]).execute()
                else:
                    self.client.table("cirurgias").insert({
                        "perfil_id":        uid,
                        "tipo_cirurgia":    tipo,
                        "data_cirurgia":    data_cirurgia,
                        "peso_pre_cirurgia": peso_pre,
                        "observacoes":      observacoes or None,
                    }).execute()
                # Atualiza perfil
                self.update_user({
                    "is_bariatric":  True,
                    "surgery_date":  data_cirurgia,
                    "bariatric_type": tipo,
                })
                return True
            except Exception as e:
                logger.warning(f"registrar_cirurgia: {e}")
        self._mock()[f"cirurgia_{uid}"] = {
            "tipo_cirurgia": tipo,
            "data_cirurgia": data_cirurgia,
            "peso_pre_cirurgia": peso_pre,
        }
        return True

    # ── FASE ─────────────────────────────────────────────────────────────────
    def get_fase_bariatrica(self) -> Optional[dict]:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = (self.client.table("fases_bariatricas")
                     .select("*")
                     .eq("perfil_id", uid)
                     .order("iniciada_em", desc=True)
                     .limit(1)
                     .execute())
                return r.data[0] if r.data else None
            except Exception as e:
                logger.warning(f"get_fase_bariatrica: {e}")
        return self._mock().get(f"fase_bar_{uid}")

    def registrar_fase_bariatrica(self, fase: str,
                                   observacao: str = "") -> bool:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                self.client.table("fases_bariatricas").insert({
                    "perfil_id":  uid,
                    "fase":       fase,
                    "iniciada_em": date.today().isoformat(),
                    "observacao": observacao or None,
                }).execute()
                self.update_user({"bariatric_phase": fase})
                return True
            except Exception as e:
                logger.warning(f"registrar_fase_bariatrica: {e}")
        self._mock()[f"fase_bar_{uid}"] = {
            "fase": fase, "iniciada_em": date.today().isoformat()
        }
        self.update_user({"bariatric_phase": fase})
        return True

    # ── HISTÓRICO DE FASES ────────────────────────────────────────────────────
    def get_historico_fases(self) -> list:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = (self.client.table("fases_bariatricas")
                     .select("fase,iniciada_em,observacao")
                     .eq("perfil_id", uid)
                     .order("iniciada_em", desc=True)
                     .limit(10)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_historico_fases: {e}")
        fase = self._mock().get(f"fase_bar_{uid}")
        return [fase] if fase else []
