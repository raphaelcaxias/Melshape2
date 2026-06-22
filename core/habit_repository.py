"""
Melshape — Repositório de Hábitos.

Tabelas: habitos, registros_habitos

habitos:
  id, perfil_id, nome, descricao, frequencia (daily/weekly),
  categoria, icone, ativo, criado_em

registros_habitos:
  id, habito_id, perfil_id, data_registro, concluido, observacao
"""
import logging
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger("Melshape.HabitRepo")


class HabitRepository:
    """
    Mixin de hábitos. Requer self.client, self.is_real,
    self.uid(), self._mock() da classe Database.
    """

    # ── HÁBITOS ──────────────────────────────────────────────────────────────
    def get_habitos(self) -> list:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = (self.client.table("habitos")
                     .select("*")
                     .eq("perfil_id", uid)
                     .eq("ativo", True)
                     .order("criado_em")
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_habitos: {e}")
        return [
            h for h in self._mock().get("habitos", [])
            if h.get("user_id") == uid and h.get("ativo", True)
        ]

    def criar_habito(self, nome: str, categoria: str = "geral",
                     icone: str = "⭐", frequencia: str = "daily",
                     descricao: str = "") -> Optional[dict]:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = self.client.table("habitos").insert({
                    "perfil_id":  uid,
                    "nome":       nome,
                    "descricao":  descricao or None,
                    "categoria":  categoria,
                    "icone":      icone,
                    "frequencia": frequencia,
                    "ativo":      True,
                }).execute()
                return r.data[0] if r.data else None
            except Exception as e:
                logger.warning(f"criar_habito: {e}")
        habito = {
            "id": f"h_{uid}_{nome[:10]}",
            "user_id": uid, "nome": nome,
            "categoria": categoria, "icone": icone,
            "frequencia": frequencia, "ativo": True,
        }
        self._mock().setdefault("habitos", []).append(habito)
        return habito

    def arquivar_habito(self, habito_id: str) -> bool:
        if self.is_real and self.client:
            try:
                self.client.table("habitos").update(
                    {"ativo": False}
                ).eq("id", habito_id).execute()
                return True
            except Exception as e:
                logger.warning(f"arquivar_habito: {e}")
        habitos = self._mock().get("habitos", [])
        for h in habitos:
            if h.get("id") == habito_id:
                h["ativo"] = False
        return True

    # ── REGISTROS ────────────────────────────────────────────────────────────
    def registrar_habito(self, habito_id: str,
                          data_str: Optional[str] = None,
                          observacao: str = "") -> bool:
        uid       = self.uid()
        data_str  = data_str or date.today().isoformat()
        if self.is_real and self.client:
            try:
                # upsert — só 1 registro por hábito por dia
                self.client.table("registros_habitos").upsert({
                    "habito_id":      habito_id,
                    "perfil_id":      uid,
                    "data_registro":  data_str,
                    "concluido":      True,
                    "observacao":     observacao or None,
                }, on_conflict="habito_id,data_registro").execute()
                return True
            except Exception as e:
                logger.warning(f"registrar_habito: {e}")
        key = f"reg_{habito_id}"
        self._mock().setdefault(key, []).append({
            "habito_id": habito_id, "user_id": uid,
            "data_registro": data_str, "concluido": True,
        })
        return True

    def get_registros_habito(self, habito_id: str,
                              days: int = 30) -> list:
        """Retorna lista de datas concluídas nos últimos N dias."""
        uid    = self.uid()
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        if self.is_real and self.client:
            try:
                r = (self.client.table("registros_habitos")
                     .select("data_registro, concluido")
                     .eq("habito_id", habito_id)
                     .eq("perfil_id", uid)
                     .eq("concluido", True)
                     .gte("data_registro", cutoff)
                     .order("data_registro", desc=True)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_registros_habito: {e}")
        return [
            r for r in self._mock().get(f"reg_{habito_id}", [])
            if r.get("data_registro", "") >= cutoff
        ]

    def get_registros_hoje(self) -> set:
        """IDs dos hábitos concluídos hoje."""
        uid   = self.uid()
        today = date.today().isoformat()
        if self.is_real and self.client:
            try:
                r = (self.client.table("registros_habitos")
                     .select("habito_id")
                     .eq("perfil_id", uid)
                     .eq("data_registro", today)
                     .eq("concluido", True)
                     .execute())
                return {x["habito_id"] for x in (r.data or [])}
            except Exception as e:
                logger.warning(f"get_registros_hoje: {e}")
        feitos = set()
        for h in self.get_habitos():
            regs = self._mock().get(f"reg_{h['id']}", [])
            if any(r.get("data_registro") == today for r in regs):
                feitos.add(h["id"])
        return feitos
