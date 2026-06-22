"""
Melshape — Serviço de Risco e Ações Proativas.

Consome vw_pacientes_para_notificar para:
1. Disparar notificações contextuais (nunca genéricas)
2. Gerar lista de ações para o profissional
3. Retornar resumo clínico para a clínica/gestor

Diferencial: o sistema age — não espera o usuário aparecer.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("Melshape.Risk")


class RiskService:

    def __init__(self, db):
        self.db = db

    # ── PACIENTES EM RISCO ────────────────────────────────────────────────────
    def pacientes_em_risco(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retorna pacientes em risco via vw_pacientes_para_notificar."""
        if not (self.db.is_real and self.db.client):
            return []
        try:
            r = (self.db.client.table("vw_pacientes_para_notificar")
                 .select(
                     "perfil_id, nome_completo, "
                     "dias_sem_acesso, dias_sem_checkin, motivo"
                 )
                 .order("dias_sem_acesso", desc=True)
                 .limit(limit)
                 .execute())
            return r.data or []
        except Exception as e:
            logger.warning(f"pacientes_em_risco: {e}")
        return []

    # ── PROCESSAR RISCO DO PACIENTE ATUAL ────────────────────────────────────
    def processar_risco_paciente(self, user: dict) -> Dict[str, Any]:
        """
        Verifica se o paciente logado está em risco.
        Se sim, cria notificação contextual e retorna status.
        """
        if not (self.db.is_real and self.db.client):
            return {"status": "mock"}
        try:
            uid = self.db.uid()
            r   = (self.db.client.table("vw_pacientes_para_notificar")
                   .select("motivo, dias_sem_checkin")
                   .eq("perfil_id", uid)
                   .limit(1)
                   .execute())
            if not r.data:
                return {"status": "ok"}

            row    = r.data[0]
            motivo = row.get("motivo", "")
            dias   = int(row.get("dias_sem_checkin") or 0)
            msg    = self._msg_risco(motivo, dias, user)
            if msg:
                self.db.criar_notificacao(msg, tipo="risco_abandono")
                return {"status": "notificado", "mensagem": msg}
        except Exception as e:
            logger.warning(f"processar_risco_paciente: {e}")
        return {"status": "ok"}

    def _msg_risco(self, motivo: str, dias: int,
                   user: dict) -> Optional[str]:
        """Gera mensagem personalizada — nunca genérica."""
        nome = user.get("name", "").split()[0] or "Você"
        if motivo == "RISCO_ABANDONO":
            if dias >= 7:
                return (
                    f"😔 {nome}, sentimos sua falta! "
                    f"Faz {dias} dias sem check-in. "
                    f"Sua jornada está te esperando — "
                    f"cada recomeço é uma nova oportunidade."
                )
            return (
                f"⚡ {nome}, sua sequência anterior provou "
                f"que você consegue. Vamos retomar juntos?"
            )
        if motivo == "SEM_CHECKIN":
            return (
                f"✅ {nome}, seu check-in de hoje está esperando. "
                f"Leva 30 segundos e mantém sua sequência ativa."
            )
        return None

    # ── AÇÕES PARA O PROFISSIONAL ─────────────────────────────────────────────
    def acoes_profissional(self) -> List[Dict[str, Any]]:
        """
        Retorna lista de ações recomendadas ao profissional.
        Cada item responde: "O que devo fazer com este paciente agora?"
        """
        pacientes = self.pacientes_em_risco(limit=10)
        acoes     = []

        for p in pacientes:
            motivo     = p.get("motivo", "")
            dias       = int(p.get("dias_sem_checkin") or 0)
            nome       = p.get("nome_completo", "—")
            perfil_id  = p.get("perfil_id", "")

            if motivo == "RISCO_ABANDONO" and dias >= 5:
                acoes.append({
                    "paciente":  nome,
                    "perfil_id": perfil_id,
                    "motivo":    f"🚨 {dias} dias sem check-in",
                    "acao":      "Entrar em contato imediatamente",
                    "urgencia":  "alta",
                    "icone":     "🚨",
                })
            elif motivo == "RISCO_ABANDONO":
                acoes.append({
                    "paciente":  nome,
                    "perfil_id": perfil_id,
                    "motivo":    f"⚠️ {dias} dias sem check-in",
                    "acao":      "Enviar mensagem de reforço",
                    "urgencia":  "media",
                    "icone":     "⚠️",
                })
            else:
                acoes.append({
                    "paciente":  nome,
                    "perfil_id": perfil_id,
                    "motivo":    "📋 Acompanhamento regular",
                    "acao":      "Monitorar",
                    "urgencia":  "baixa",
                    "icone":     "📋",
                })

        return acoes

    # ── RESUMO PARA A CLÍNICA ─────────────────────────────────────────────────
    def resumo_clinica(self) -> Dict[str, Any]:
        """Resumo clínico para gestores/administradores."""
        pacientes = self.pacientes_em_risco(limit=100)
        if not pacientes:
            return {
                "total": 0,
                "por_motivo": {},
                "recomendacao": "✅ Todos os pacientes estão engajados.",
            }

        por_motivo: Dict[str, int] = {}
        for p in pacientes:
            m = p.get("motivo", "ACOMPANHAMENTO")
            por_motivo[m] = por_motivo.get(m, 0) + 1

        total = len(pacientes)
        if total >= 10:
            rec = "🚨 Alto número de pacientes em risco. Reforçar retenção."
        elif total >= 5:
            rec = "⚠️ Número moderado em risco. Revisar protocolos."
        else:
            rec = "✅ Nível de risco controlado. Manter estratégia."

        return {
            "total":        total,
            "por_motivo":   por_motivo,
            "recomendacao": rec,
        }
