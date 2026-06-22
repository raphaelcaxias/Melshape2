"""
Melshape — Serviço de Jornada.
Lógica de progresso, próximos passos e marcos automáticos.
"""
import logging
from datetime import date
from typing import Optional

from services.journey_data import _ETAPAS, _NOMES_JORNADA

logger = logging.getLogger("Melshape.Journey")


class JourneyService:

    def __init__(self, db):
        self.db = db

    # ── INICIALIZAÇÃO ─────────────────────────────────────────────────────────
    def garantir_jornada(self, user: dict) -> dict:
        """
        Garante que o paciente tem uma jornada ativa.
        Se não tiver, cria automaticamente com as etapas do pilar.
        """
        jornada = self.db.get_jornada_ativa()
        if jornada:
            return jornada

        hm     = user.get("health_mode", "general")
        nome   = _NOMES_JORNADA.get(hm, "Minha Jornada")
        obj    = user.get("goal_weight", "")
        jornada = self.db.criar_jornada(hm, nome, str(obj))

        if jornada:
            self._criar_etapas_iniciais(jornada["id"], hm)

        return jornada or {}

    def _criar_etapas_iniciais(self, jornada_id: str, hm: str) -> None:
        """Insere etapas padrão do pilar na tabela etapas_jornada."""
        etapas = _ETAPAS.get(hm, _ETAPAS["general"])
        if not (self.db.is_real and self.db.client):
            return
        try:
            for etapa in etapas:
                self.db.client.table("etapas_jornada").insert({
                    "jornada_id": jornada_id,
                    "ordem":      etapa["ordem"],
                    "nome":       etapa["nome"],
                    "descricao":  etapa["descricao"],
                    "icone":      etapa["icone"],
                    "concluida":  False,
                }).execute()
        except Exception as e:
            logger.warning(f"_criar_etapas_iniciais: {e}")

    # ── PROGRESSO ─────────────────────────────────────────────────────────────
    def progresso_jornada(self, jornada_id: str, hm: str) -> dict:
        """
        Calcula progresso com base em dados reais do paciente.
        Retorna: etapa_atual, pct_etapa, etapa_seguinte, total_etapas.
        """
        etapas_db  = self.db.get_etapas(jornada_id)
        etapas_ref = _ETAPAS.get(hm, _ETAPAS["general"])

        # Se não há etapas no banco, usa referência in-memory
        if not etapas_db:
            etapas_db = [
                {**e, "concluida": False, "id": f"mock_{e['ordem']}"}
                for e in etapas_ref
            ]

        concluidas  = [e for e in etapas_db if e.get("concluida")]
        pendentes   = [e for e in etapas_db if not e.get("concluida")]
        etapa_atual = pendentes[0] if pendentes else etapas_db[-1]
        proxima     = pendentes[1] if len(pendentes) > 1 else None

        pct_geral   = (
            int(len(concluidas) / len(etapas_db) * 100)
            if etapas_db else 0
        )

        # Progresso interno da etapa atual baseado em dados reais
        pct_etapa = self._calcular_progresso_etapa(
            etapa_atual, jornada_id
        )

        return {
            "etapa_atual":   etapa_atual,
            "etapa_seguinte": proxima,
            "concluidas":    concluidas,
            "pendentes":     pendentes,
            "total":         len(etapas_db),
            "pct_geral":     pct_geral,
            "pct_etapa":     pct_etapa,
        }

    def _calcular_progresso_etapa(self, etapa: dict,
                                   jornada_id: str) -> int:
        """Estima % de conclusão da etapa atual com dados reais."""
        try:
            streak  = self.db.get_checkin_streak()
            meals   = self.db.get_meals(30)
            weights = self.db.get_weights(30)
            xp      = self.db.get_xp()
            ordem   = etapa.get("ordem", 1)

            if ordem == 1:
                pontos = 0
                if streak >= 1:          pontos += 33
                if not weights.empty:    pontos += 33
                if len(meals) >= 1:      pontos += 34
                return min(100, pontos)

            if ordem == 2:
                return min(100, int(streak / 7 * 100))

            if ordem == 3:
                return min(100, int(streak / 30 * 100))

            if ordem == 4:
                return min(100, int(xp / 1000 * 100))

            if ordem == 5:
                return min(100, int(streak / 90 * 100))

        except Exception:
            pass
        return 0

    # ── PRÓXIMO PASSO ─────────────────────────────────────────────────────────
    def proximo_passo(self, etapa: dict, user: dict) -> dict:
        """
        Retorna uma ação concreta e acionável para o paciente.
        Prioriza o que está mais próximo de ser concluído.
        """
        streak = self.db.get_checkin_streak()
        meals  = self.db.get_meals(7)
        water  = self.db.get_hydration_today()
        ci     = self.db.get_checkin_today()
        ordem  = etapa.get("ordem", 1)

        # Check-in é sempre o primeiro a sugerir se não foi feito
        if not ci:
            return {
                "acao": "Fazer o check-in de hoje",
                "icone": "✅",
                "pagina": "meals",
                "hub_tipo": "checkin",
                "urgencia": "alta",
            }

        if ordem <= 2 and streak < 7:
            faltam = 7 - streak
            return {
                "acao": f"Manter sequência por mais {faltam} dia(s)",
                "icone": "🔥",
                "pagina": "meals",
                "hub_tipo": "checkin",
                "urgencia": "media",
            }

        if water < 1500:
            return {
                "acao": "Registrar mais água — meta: 2L",
                "icone": "💧",
                "pagina": "meals",
                "hub_tipo": "hydration",
                "urgencia": "media",
            }

        if len(meals) < 3:
            return {
                "acao": "Registrar as refeições de hoje",
                "icone": "🍽️",
                "pagina": "meals",
                "hub_tipo": "meal",
                "urgencia": "baixa",
            }

        return {
            "acao": "Continue assim! Você está no caminho certo.",
            "icone": "⭐",
            "pagina": None,
            "hub_tipo": None,
            "urgencia": "ok",
        }

    # ── MARCOS ───────────────────────────────────────────────────────────────
    def verificar_marcos_automaticos(self,
                                      jornada_id: str,
                                      user: dict) -> list:
        """Registra marcos automaticamente quando critérios são atingidos."""
        streak  = self.db.get_checkin_streak()
        weights = self.db.get_weights(365)
        marcos_existentes = {
            m.get("titulo", "") for m in self.db.get_marcos(jornada_id)
        }
        novos = []

        candidatos = [
            (streak >= 7,   "🔥 7 Dias Seguidos",   "Uma semana sem falhar!"),
            (streak >= 30,  "🏆 30 Dias Seguidos",   "Um mês de consistência!"),
            (streak >= 90,  "👑 90 Dias Seguidos",   "Três meses. Lendário."),
        ]

        if not weights.empty and len(weights) >= 2:
            try:
                diff = float(weights.iloc[0]["weight"]) - float(weights.iloc[-1]["weight"])
                candidatos += [
                    (diff >= 1,  "📉 1 kg eliminado",   "O primeiro quilo foi o mais difícil."),
                    (diff >= 5,  "💪 5 kg eliminados",  "5 quilos a menos. Isso é real."),
                    (diff >= 10, "🔥 10 kg eliminados", "10 quilos. Transformação total."),
                ]
            except Exception:
                pass

        for condicao, titulo, descricao in candidatos:
            if condicao and titulo not in marcos_existentes:
                self.db.registrar_marco(jornada_id, titulo, descricao)
                novos.append(titulo)

        return novos
