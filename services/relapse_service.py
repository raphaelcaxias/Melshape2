"""
Melshape — Protocolo de Recaída.

Recaída não é falha — é parte da jornada.

Detecta quando o streak zerou após uma sequência significativa.
Oferece fluxo ativo de recomeço:
  1. Reconhece a recaída (sem punição)
  2. Lembra o porquê da jornada
  3. Registra recomeço como evento positivo
  4. Dá XP de recomeço (começa do zero não significa perder tudo)
  5. Cria notificação motivacional

Chamado pela home quando streak == 0 e último streak > 0.
"""
import logging
from datetime import date
from typing import Optional, Dict, Any

logger = logging.getLogger("Melshape.Relapse")


class RelapseService:

    def __init__(self, db):
        self.db = db

    # ── DETECÇÃO ──────────────────────────────────────────────────────────────
    def detectar(self, user: dict) -> Optional[Dict[str, Any]]:
        """
        Detecta se o usuário está em situação de recaída.
        Retorna dados da recaída ou None se tudo bem.
        """
        streak_atual = self.db.get_checkin_streak()
        if streak_atual > 0:
            return None  # Não está em recaída

        melhor_streak = self._melhor_streak_historico()
        if melhor_streak < 3:
            return None  # Nunca chegou a 3 dias — não é recaída

        dias_ausente  = self._dias_sem_checkin()
        if dias_ausente == 0:
            return None  # Zerou hoje mas ainda não registrou

        return {
            "melhor_streak":  melhor_streak,
            "dias_ausente":   dias_ausente,
            "em_recaida":     True,
            "xp_recomeço":    self._calcular_xp_recomeço(melhor_streak),
        }

    def _melhor_streak_historico(self) -> int:
        """Busca a maior sequência já registrada pelo usuário."""
        if not (self.db.is_real and self.db.client):
            return self.db._mock().get("melhor_streak", 0)
        try:
            uid = self.db.uid()
            r   = (self.db.client.table("checkins")
                   .select("data_checkin")
                   .eq("perfil_id", uid)
                   .order("data_checkin")
                   .execute())
            datas = [d["data_checkin"] for d in (r.data or [])]
            return self._calcular_maior_streak(datas)
        except Exception as e:
            logger.warning(f"_melhor_streak_historico: {e}")
        return 0

    def _calcular_maior_streak(self, datas: list) -> int:
        if not datas:
            return 0
        from datetime import datetime, timedelta
        maior   = 0
        atual   = 1
        for i in range(1, len(datas)):
            d1 = datetime.fromisoformat(datas[i-1]).date()
            d2 = datetime.fromisoformat(datas[i]).date()
            if (d2 - d1).days == 1:
                atual += 1
                maior  = max(maior, atual)
            else:
                atual = 1
        return max(maior, atual)

    def _dias_sem_checkin(self) -> int:
        if not (self.db.is_real and self.db.client):
            return 0
        try:
            uid = self.db.uid()
            r   = (self.db.client.table("checkins")
                   .select("data_checkin")
                   .eq("perfil_id", uid)
                   .order("data_checkin", desc=True)
                   .limit(1)
                   .execute())
            if not r.data:
                return 0
            from datetime import datetime
            ultimo = datetime.fromisoformat(
                r.data[0]["data_checkin"]
            ).date()
            return (date.today() - ultimo).days
        except Exception as e:
            logger.warning(f"_dias_sem_checkin: {e}")
        return 0

    def _calcular_xp_recomeço(self, melhor_streak: int) -> int:
        """XP de recomeço: proporcional ao histórico — reconhece o esforço."""
        if melhor_streak >= 30:
            return 100
        if melhor_streak >= 14:
            return 75
        if melhor_streak >= 7:
            return 50
        return 25

    # ── AÇÃO DE RECOMEÇO ──────────────────────────────────────────────────────
    def registrar_recomeço(self, user: dict,
                            dados_recaida: Dict[str, Any]) -> bool:
        """
        Registra o recomeço como evento positivo.
        Dá XP, cria evento na jornada e notificação motivacional.
        """
        xp = dados_recaida.get("xp_recomeço", 25)
        ok1 = self._dar_xp_recomeço(xp)
        ok2 = self._registrar_evento_recomeço(user, dados_recaida)
        ok3 = self._criar_notificacao_recomeço(user, dados_recaida)

        logger.info(
            f"Recomeço registrado: xp={xp} "
            f"evento={ok2} notif={ok3}"
        )
        return ok1

    def _dar_xp_recomeço(self, xp: int) -> bool:
        try:
            self.db.add_xp(xp, motivo="recomeço")
            return True
        except Exception as e:
            logger.warning(f"_dar_xp_recomeço: {e}")
        return False

    def _registrar_evento_recomeço(self, user: dict,
                                    dados: Dict[str, Any]) -> bool:
        """Registra em eventos_vida e eventos_jornada."""
        try:
            self.db.registrar_evento_vida(
                titulo=f"Recomeço após {dados['melhor_streak']} dias",
                descricao=(
                    f"Voltei depois de {dados['dias_ausente']} dias. "
                    f"Meu melhor streak foi de {dados['melhor_streak']} dias "
                    f"e isso prova que consigo."
                ),
                tipo="inicio",
            )
            return True
        except Exception as e:
            logger.warning(f"_registrar_evento_recomeço: {e}")
        return False

    def _criar_notificacao_recomeço(self, user: dict,
                                     dados: Dict[str, Any]) -> bool:
        nome = user.get("name", "").split()[0] or "Você"
        msg  = (
            f"🌱 {nome}, bem-vindo de volta! "
            f"Sua sequência anterior de {dados['melhor_streak']} dias "
            f"prova que você consegue. Hoje é dia 1 de algo ainda maior."
        )
        try:
            self.db.criar_notificacao(msg, tipo="recomeço")
            return True
        except Exception as e:
            logger.warning(f"_criar_notificacao_recomeço: {e}")
        return False

    # ── MOTIVO DA JORNADA ─────────────────────────────────────────────────────
    def get_motivo_para_lembrar(self, user: dict) -> Optional[str]:
        """Retorna o porquê do usuário para exibir no momento de recaída."""
        try:
            jornada = self.db.get_jornada_ativa()
            if not jornada:
                return None
            motivos = self.db.get_motivos(jornada["id"])
            if motivos:
                return motivos[0].get("motivo", "")
        except Exception as e:
            logger.warning(f"get_motivo_para_lembrar: {e}")
        return None
