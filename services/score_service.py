"""
Melshape — Serviço de Score de Transformação.

Traduz vw_score_transformacao em:
- Narrativa humana para o paciente (nunca número cru)
- Recomendação de ação para o profissional

USO:
    from services.score_service import ScoreService
    svc = ScoreService(db)
    narrativa = svc.narrativa_paciente(user)
    recomendacao = svc.recomendacao_profissional(perfil_id)
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("Melshape.Score")


class ScoreService:

    def __init__(self, db):
        self.db = db

    # ── DADOS ─────────────────────────────────────────────────────────────────
    def get_score(self, perfil_id: Optional[str] = None) -> Optional[Dict]:
        uid = perfil_id or self.db.uid()
        if not (self.db.is_real and self.db.client):
            return None
        try:
            r = (self.db.client.table("vw_score_transformacao")
                 .select(
                     "score_global, aderencia, engajamento, "
                     "nutricao, comportamento"
                 )
                 .eq("perfil_id", uid)
                 .limit(1)
                 .execute())
            return r.data[0] if r.data else None
        except Exception as e:
            logger.warning(f"get_score: {e}")
        return None

    # ── NARRATIVA PARA O PACIENTE ─────────────────────────────────────────────
    def narrativa_paciente(self, user: dict) -> Dict[str, str]:
        """
        Retorna narrativa do score para o paciente.
        Nunca exibe número cru — sempre contexto emocional.
        """
        data  = self.get_score()
        if not data:
            return {
                "titulo":   "🗺️ Comece sua jornada",
                "mensagem": "Registre seus dados para ver seu score de transformação.",
                "cor":      "var(--text-muted)",
                "icone":    "🗺️",
            }

        score = float(data.get("score_global", 0))

        if score >= 80:
            return {
                "titulo":   "🏆 Transformação Avançada",
                "mensagem": (
                    "Sua consistência está gerando resultados excepcionais. "
                    "Você está entre os mais engajados da plataforma."
                ),
                "cor":   "var(--success)",
                "icone": "🏆",
            }
        if score >= 60:
            return {
                "titulo":   "📈 Progresso Consistente",
                "mensagem": (
                    "Você está evoluindo de forma sólida. "
                    "Continue com a consistência — os resultados estão chegando."
                ),
                "cor":   "var(--primary)",
                "icone": "📈",
            }
        if score >= 40:
            return {
                "titulo":   "⚡ Caminho Certo",
                "mensagem": (
                    "Você está no caminho certo. "
                    "Pequenos ajustes vão acelerar sua transformação."
                ),
                "cor":   "var(--warning)",
                "icone": "⚡",
            }
        if score >= 20:
            return {
                "titulo":   "🌱 Primeiros Passos",
                "mensagem": (
                    "Cada dia que você registra é um passo real. "
                    "Continue — a consistência se constrói aos poucos."
                ),
                "cor":   "var(--info)",
                "icone": "🌱",
            }
        return {
            "titulo":   "🌱 Comece Hoje",
            "mensagem": (
                "Seu score está se formando. "
                "Faça seu check-in agora para dar o primeiro passo."
            ),
            "cor":   "var(--text-muted)",
            "icone": "🌱",
        }

    # ── RECOMENDAÇÃO PARA O PROFISSIONAL ──────────────────────────────────────
    def recomendacao_profissional(self, perfil_id: str) -> Dict[str, Any]:
        """
        Traduz score em ação concreta para o profissional.
        Responde: "O que devo fazer com este paciente agora?"
        """
        data = self.get_score(perfil_id)
        if not data:
            return {
                "acao":     "Aguardar dados",
                "urgencia": "baixa",
                "mensagem": "Paciente ainda sem dados suficientes.",
            }

        score      = float(data.get("score_global", 0))
        aderencia  = float(data.get("aderencia", 0))
        engajamento = float(data.get("engajamento", 0))

        problemas = []
        if aderencia < 40:
            problemas.append("baixa aderência alimentar")
        if engajamento < 40:
            problemas.append("baixo engajamento")

        if score >= 70:
            return {
                "acao":     "Manter estratégia",
                "urgencia": "baixa",
                "mensagem": "Paciente evoluindo bem. Reforçar hábitos positivos.",
            }
        if score >= 50:
            msg = (
                f"Score moderado. Foco em: {', '.join(problemas)}."
                if problemas
                else "Score moderado. Agende consulta de reforço."
            )
            return {
                "acao":     f"Revisar: {', '.join(problemas) or 'protocolo'}",
                "urgencia": "media",
                "mensagem": msg,
            }
        return {
            "acao":     "Intervenção urgente",
            "urgencia": "alta",
            "mensagem": (
                f"Score baixo. "
                f"Motivo: {', '.join(problemas) or 'baixo engajamento geral'}. "
                f"Entre em contato."
            ),
        }
