"""Melshape — Evolution Service B: fotos, hall da fama, carteira, XP, consentimentos."""
import logging
import json
from datetime import date, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger("Melshape.EvolutionB")

class EvolutionServiceB:

    # ── HALL DA FAMA ──────────────────────────────────────────────────────────
    def get_campeoes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Consulta vw_campeoes_transformacao com normalização de nomes
        de campo (score vs score_global).
        """
        if not (self.db.is_real and self.db.client):
            return []
        try:
            r = (self.db.client.table("vw_campeoes_transformacao")
                 .select("*")
                 .limit(limit)
                 .execute())
            resultado = []
            for row in (r.data or []):
                score = (
                    row.get("score")
                    or row.get("score_global")
                    or row.get("pontos")
                    or 0
                )
                resultado.append({
                    "nome_completo": (
                        row.get("nome_completo")
                        or row.get("nome")
                        or "—"
                    ),
                    "score": float(score),
                })
            resultado.sort(key=lambda x: x["score"], reverse=True)
            return resultado
        except Exception as e:
            logger.warning(f"get_campeoes: {e}")
        return []

    # ── CARTEIRA ──────────────────────────────────────────────────────────────
    def get_carteira(self) -> Dict[str, Any]:
        uid = self._uid()
        if not (self.db.is_real and self.db.client):
            return {"moedas": 0, "recompensas_resgatadas": []}
        try:
            r = (self.db.client.table("carteira_gamificacao")
                 .select("moedas, recompensas_resgatadas")
                 .eq("perfil_id", uid)
                 .limit(1)
                 .execute())
            if r.data:
                row = r.data[0]
                resgatadas = row.get("recompensas_resgatadas") or []
                if isinstance(resgatadas, str):
                    import json
                    try:
                        resgatadas = json.loads(resgatadas)
                    except Exception:
                        resgatadas = []
                return {
                    "moedas":                int(row.get("moedas") or 0),
                    "recompensas_resgatadas": resgatadas,
                }
            # Criar carteira se não existir
            self.db.client.table("carteira_gamificacao").insert({
                "perfil_id": uid,
                "moedas":    0,
            }).execute()
            return {"moedas": 0, "recompensas_resgatadas": []}
        except Exception as e:
            logger.warning(f"get_carteira: {e}")
        return {"moedas": 0, "recompensas_resgatadas": []}

    # ── HISTÓRICO XP ──────────────────────────────────────────────────────────
    def get_historico_xp(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Tenta historico_xp com campo criado_em como fallback para data.
        """
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        if not (self.db.is_real and self.db.client):
            return []
        try:
            r = (self.db.client.table("historico_xp")
                 .select("*")
                 .eq("perfil_id", self._uid())
                 .limit(100)
                 .execute())
            resultado = []
            for row in (r.data or []):
                data_val = (
                    row.get("data")
                    or row.get("criado_em")
                    or row.get("created_at")
                    or ""
                )
                if data_val[:10] >= cutoff:
                    resultado.append({
                        "data":      data_val[:10],
                        "xp_ganho":  int(row.get("xp_ganho") or row.get("xp") or 0),
                        "motivo":    row.get("motivo") or row.get("descricao") or "",
                    })
            return sorted(resultado, key=lambda x: x["data"])
        except Exception as e:
            logger.warning(f"get_historico_xp: {e}")
        return []

    # ── CONSENTIMENTOS ────────────────────────────────────────────────────────
    def get_consentimentos(self) -> List[Dict[str, Any]]:
        return self._query(
            "consentimentos", "*",
            filters={"perfil_id": self._uid()},
            order="assinado_em", desc=True,
        )

    def assinar_consentimento(self, tipo: str = "lgpd",
                               versao: str = "2.0") -> bool:
        if not (self.db.is_real and self.db.client):
            return False
        try:
            self.db.client.table("consentimentos").insert({
                "perfil_id":   self._uid(),
                "tipo":        tipo,
                "versao":      versao,
                "assinado_em": date.today().isoformat(),
                "revogado":    False,
            }).execute()
            return True
        except Exception as e:
            logger.warning(f"assinar_consentimento: {e}")
        return False

    def revogar_consentimento(self, consentimento_id: str) -> bool:
        """LGPD exige suporte à revogação."""
        if not (self.db.is_real and self.db.client):
            return False
        try:
            self.db.client.table("consentimentos").update({
                "revogado":    True,
                "revogado_em": date.today().isoformat(),
            }).eq("id", consentimento_id).execute()
            return True
        except Exception as e:
            logger.warning(f"revogar_consentimento: {e}")
        return False
