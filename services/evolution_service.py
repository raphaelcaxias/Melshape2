"""
Melshape — Serviço de Evolução Completa.

Agrupa dados de:
  medidas_corporais, fotos_evolucao, indicadores_clinicos,
  vw_estagnacao_clinica, vw_campeoes_transformacao,
  carteira_gamificacao, historico_xp, consentimentos

Correções aplicadas vs versão original:
  - self.uid() é método, não property
  - Nomes de colunas alinhados com o banco real
  - Guard clauses em todas as queries
  - Fallback completo para tabelas/views ausentes
"""
import logging
from datetime import date, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger("Melshape.Evolution")


class EvolutionService:

    def __init__(self, db):
        self.db = db

    def _uid(self) -> str:
        """uid() é método no Database — nunca property."""
        return self.db.uid()

    def _query(self, table: str, select: str,
               filters: dict = None, order: str = None,
               desc: bool = True, limit: int = 100) -> list:
        """Helper genérico de query com fallback silencioso."""
        if not (self.db.is_real and self.db.client):
            return []
        try:
            q = self.db.client.table(table).select(select)
            for col, val in (filters or {}).items():
                if col.startswith("gte:"):
                    q = q.gte(col[4:], val)
                else:
                    q = q.eq(col, val)
            if order:
                q = q.order(order, desc=desc)
            return q.limit(limit).execute().data or []
        except Exception as e:
            logger.warning(f"_query({table}): {e}")
        return []

    # ── MEDIDAS CORPORAIS ─────────────────────────────────────────────────────
    def get_medidas(self, days: int = 90) -> List[Dict[str, Any]]:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        return self._query(
            "medidas_corporais", "*",
            filters={"perfil_id": self._uid(), "gte:data_medicao": cutoff},
            order="data_medicao", desc=True,
        )

    def salvar_medida(self, data: dict) -> bool:
        if not (self.db.is_real and self.db.client):
            return False
        try:
            # Nomes exatos das colunas da tabela medidas_corporais
            payload = {
                "perfil_id":               self._uid(),
                "data_medicao":            data.get("data_medicao",
                                                    date.today().isoformat()),
                "peso":                    data.get("peso") or None,
                "circunferencia_cintura":  data.get("cintura") or None,
                "circunferencia_quadril":  data.get("quadril") or None,
                "circunferencia_braco":    data.get("braco") or None,
                "circunferencia_coxa":     data.get("coxa") or None,
                "percentual_gordura":      data.get("gordura") or None,
            }
            self.db.client.table("medidas_corporais").insert(payload).execute()
            return True
        except Exception as e:
            logger.warning(f"salvar_medida: {e}")
        return False

    # ── INDICADORES CLÍNICOS ──────────────────────────────────────────────────
    def get_indicadores(self, days: int = 365) -> List[Dict[str, Any]]:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        return self._query(
            "indicadores_clinicos", "*",
            filters={"perfil_id": self._uid(), "gte:data_coleta": cutoff},
            order="data_coleta", desc=True,
        )

    def salvar_indicador(self, data: dict) -> bool:
        if not (self.db.is_real and self.db.client):
            return False
        try:
            payload = {
                "perfil_id":        self._uid(),
                "data_coleta":      data.get("data_coleta",
                                             date.today().isoformat()),
                "glicemia_jejum":   data.get("glicemia") or None,
                "colesterol_total": data.get("colesterol_total") or None,
                "colesterol_hdl":   data.get("hdl") or None,
                "colesterol_ldl":   data.get("ldl") or None,
                "triglicerideos":   data.get("triglicerideos") or None,
                "vitamina_d":       data.get("vitamina_d") or None,
                "vitamina_b12":     data.get("b12") or None,
                "ferritina":        data.get("ferritina") or None,
                "tsh":              data.get("tsh") or None,
            }
            self.db.client.table("indicadores_clinicos").insert(payload).execute()
            return True
        except Exception as e:
            logger.warning(f"salvar_indicador: {e}")
        return False

    def get_estagnacao(self) -> Optional[Dict[str, Any]]:
        """
        Consulta vw_estagnacao_clinica com fallback para nomes de campo
        alternativos (dias_estagnado vs dias_sem_evolucao).
        """
        if not (self.db.is_real and self.db.client):
            return None
        try:
            r = (self.db.client.table("vw_estagnacao_clinica")
                 .select("*")
                 .eq("perfil_id", self._uid())
                 .limit(1)
                 .execute())
            if not r.data:
                return None
            row  = r.data[0]
            dias = (
                row.get("dias_estagnado")
                or row.get("dias_sem_evolucao")
                or row.get("dias")
                or 0
            )
            return {"dias_estagnado": int(dias)}
        except Exception as e:
            logger.warning(f"get_estagnacao: {e}")
        return None

    # ── FOTOS ─────────────────────────────────────────────────────────────────
    def get_fotos(self) -> List[Dict[str, Any]]:
        return self._query(
            "fotos_evolucao", "url_foto,legenda,peso_na_data,data_foto",
            filters={"perfil_id": self._uid()},
            order="data_foto", desc=True,
        )

    def salvar_foto(self, url: str, legenda: str = "",
                    peso: float = 0.0) -> bool:
        if not url.strip():
            return False
        if not (self.db.is_real and self.db.client):
            return False
        try:
            self.db.client.table("fotos_evolucao").insert({
                "perfil_id":   self._uid(),
                "url_foto":    url.strip(),
                "legenda":     legenda.strip() or None,
                "peso_na_data": peso or None,
                "data_foto":   date.today().isoformat(),
            }).execute()
            return True
        except Exception as e:
            logger.warning(f"salvar_foto: {e}")
        return False


    def get_campeoes(self, limit: int = 10) -> list:
        if not (self.db.is_real and self.db.client):
            return []
        try:
            r = (self.db.client.table("vw_campeoes_transformacao")
                 .select("*").limit(limit).execute())
            result = []
            for row in (r.data or []):
                score = (row.get("score") or row.get("score_global")
                         or row.get("pontos") or 0)
                result.append({
                    "nome_completo": (row.get("nome_completo")
                                     or row.get("nome") or "—"),
                    "score": float(score),
                })
            return sorted(result, key=lambda x: x["score"], reverse=True)
        except Exception as e:
            logger.warning(f"get_campeoes: {e}")
        return []

    # ── CARTEIRA ──────────────────────────────────────────────────────────────
    def get_carteira(self) -> dict:
        uid = self._uid()
        if not (self.db.is_real and self.db.client):
            return {"moedas": 0, "recompensas_resgatadas": []}
        try:
            r = (self.db.client.table("carteira_gamificacao")
                 .select("moedas, recompensas_resgatadas")
                 .eq("perfil_id", uid).limit(1).execute())
            if r.data:
                row = r.data[0]
                resgatadas = row.get("recompensas_resgatadas") or []
                if isinstance(resgatadas, str):
                    import json
                    try:
                        resgatadas = json.loads(resgatadas)
                    except Exception:
                        resgatadas = []
                return {"moedas": int(row.get("moedas") or 0),
                        "recompensas_resgatadas": resgatadas}
            self.db.client.table("carteira_gamificacao").insert({
                "perfil_id": uid, "moedas": 0,
            }).execute()
            return {"moedas": 0, "recompensas_resgatadas": []}
        except Exception as e:
            logger.warning(f"get_carteira: {e}")
        return {"moedas": 0, "recompensas_resgatadas": []}

    # ── HISTÓRICO XP ──────────────────────────────────────────────────────────
    def get_historico_xp(self, days: int = 30) -> list:
        from datetime import date, timedelta
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        if not (self.db.is_real and self.db.client):
            return []
        try:
            r = (self.db.client.table("historico_xp")
                 .select("*").eq("perfil_id", self._uid())
                 .limit(200).execute())
            result = []
            for row in (r.data or []):
                data_val = (row.get("data") or row.get("criado_em")
                            or row.get("created_at") or "")
                if data_val[:10] >= cutoff:
                    result.append({
                        "data":     data_val[:10],
                        "xp_ganho": int(row.get("xp_ganho") or row.get("xp") or 0),
                        "motivo":   row.get("motivo") or "",
                    })
            return sorted(result, key=lambda x: x["data"])
        except Exception as e:
            logger.warning(f"get_historico_xp: {e}")
        return []

    # ── CONSENTIMENTOS ────────────────────────────────────────────────────────
    def get_consentimentos(self) -> list:
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
                "assinado_em": __import__("datetime").date.today().isoformat(),
                "revogado":    False,
            }).execute()
            return True
        except Exception as e:
            logger.warning(f"assinar_consentimento: {e}")
        return False

    def revogar_consentimento(self, cid: str) -> bool:
        if not (self.db.is_real and self.db.client):
            return False
        try:
            self.db.client.table("consentimentos").update({
                "revogado":    True,
                "revogado_em": __import__("datetime").date.today().isoformat(),
            }).eq("id", cid).execute()
            return True
        except Exception as e:
            logger.warning(f"revogar_consentimento: {e}")
        return False
