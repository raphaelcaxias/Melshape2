"""
Melshape — TransformationOrchestrator.

O cérebro do MelShape. Uma ação do paciente dispara
consequências em cascata em todos os domínios.

USO:
  from services.orchestrator import Orchestrator
  result = Orchestrator(db).processar("checkin", user, payload)

Eventos: checkin | peso | habito | refeicao | agua | dose_glp1 | meta_concluida
"""
import logging
from dataclasses import dataclass, field
from typing import List


logger = logging.getLogger("Melshape.Orchestrator")


@dataclass
class OrchestratorResult:
    """Resultado consolidado retornado para a view após um evento."""
    xp_ganho:        int        = 0
    badges_novos:    List[str]  = field(default_factory=list)
    marcos_novos:    List[str]  = field(default_factory=list)
    alertas:         List[tuple]= field(default_factory=list)
    proximo_passo:   str        = ""
    proximo_hub:     str        = ""
    proximo_tipo:    str        = ""
    streak:          int        = 0
    jornada_avancou: bool       = False
    notificacao_msg: str        = ""


class Orchestrator(CascadeMixin):
    """
    Ponto de entrada do Orchestrator.
    Herda CascadeMixin para a cascata de consequências.
    """

    def __init__(self, db):
        self.db = db

    def processar(self, evento: str, user: dict,
                  payload: dict = None) -> OrchestratorResult:
        payload = payload or {}
        result  = OrchestratorResult()
        try:
            # 1. Processar o evento específico
            handlers = {
                "checkin":       self._proc_checkin,
                "peso":          self._proc_peso,
                "habito":        self._proc_habito,
                "refeicao":      self._proc_refeicao,
                "agua":          self._proc_agua,
                "dose_glp1":     self._proc_glp1,
                "meta_concluida":self._proc_meta,
            }
            handler = handlers.get(evento)
            if handler:
                handler(user, payload, result)

            # 2. Cascata comum a todos os eventos
            self._atualizar_jornada(user, result)
            self._verificar_badges(user, result)
            self._verificar_alertas(user, result)
            self._gerar_proximo_passo(user, evento, result)
            self._programar_notificacao(user, result)

        except Exception as e:
            logger.error(f"Orchestrator ({evento}): {e}", exc_info=True)
        return result

    # ── PROCESSADORES DE EVENTO ───────────────────────────────────────────────
    def _proc_checkin(self, user: dict, p: dict,
                      r: OrchestratorResult) -> None:
        r.streak = self.db.get_checkin_streak()
        self.db.xp_checkin()
        r.xp_ganho += 20
        bonus = _streak_bonus(r.streak)
        if bonus:
            self.db.add_xp(bonus["xp"], motivo=bonus["motivo"])
            r.xp_ganho += bonus["xp"]
            r.badges_novos.append(bonus["badge"])
        habito_id = p.get("habito_id")
        if habito_id:
            self._proc_habito(user, {"habito_id": habito_id}, r)
        self._impactar_metas("consistencia", r)
        r.notificacao_msg = _msg_checkin(r.streak)

    def _proc_peso(self, user: dict, p: dict,
                   r: OrchestratorResult) -> None:
        self.db.xp_pesagem()
        r.xp_ganho += 30
        self._impactar_metas("peso", r)

    def _proc_habito(self, user: dict, p: dict,
                     r: OrchestratorResult) -> None:
        from services.habit_service import HabitService
        habito_id = p.get("habito_id", "")
        if not habito_id:
            return
        res = HabitService(self.db).registrar(habito_id)
        r.xp_ganho += res.get("xp_ganho", 0)
        if res.get("bonus_msg"):
            r.badges_novos.append(res["bonus_msg"])
        self._impactar_metas("habito", r)

    def _proc_refeicao(self, user: dict, p: dict,
                       r: OrchestratorResult) -> None:
        self.db.add_xp(5, motivo="refeicao")
        r.xp_ganho += 5
        self._impactar_metas("proteina", r)

    def _proc_agua(self, user: dict, p: dict,
                   r: OrchestratorResult) -> None:
        import config
        if self.db.get_hydration_today() >= config.HYDRATION_GOAL_ML:
            self.db.add_xp(30, motivo="meta_agua")
            r.xp_ganho += 30
        self._impactar_metas("agua", r)

    def _proc_glp1(self, user: dict, p: dict,
                   r: OrchestratorResult) -> None:
        self.db.add_xp(25, motivo="dose_glp1")
        r.xp_ganho       += 25
        r.notificacao_msg  = "💉 Dose registrada. Próxima em 7 dias."

    def _proc_meta(self, user: dict, p: dict,
                   r: OrchestratorResult) -> None:
        self.db.add_xp(200, motivo="meta_concluida")
        r.xp_ganho += 200
        r.badges_novos.append(
            f'🎯 Meta concluída: {p.get("titulo","")}'
        )


# ── HELPERS PUROS ────────────────────────────────────────────────────────────
def _streak_bonus(streak: int) -> dict:
    return {
        7:  {"xp": 50,   "motivo": "streak_7",  "badge": "📅 7 dias seguidos!"},
        14: {"xp": 100,  "motivo": "streak_14", "badge": "🔥 14 dias!"},
        30: {"xp": 300,  "motivo": "streak_30", "badge": "🏆 30 dias!"},
        60: {"xp": 600,  "motivo": "streak_60", "badge": "💪 60 dias!"},
        90: {"xp": 1000, "motivo": "streak_90", "badge": "👑 90 dias!"},
    }.get(streak, {})


def _msg_checkin(streak: int) -> str:
    msgs = {
        6:  "🔥 Amanhã você completa 7 dias seguidos. Não quebre agora!",
        13: "⭐ Mais 1 dia para 14 dias consecutivos!",
        29: "🏆 Amanhã são 30 dias. Você está quase lá!",
    }
    return msgs.get(streak,
        f"✅ {streak} dia(s) seguidos. Volte amanhã!" if streak > 0
        else "✅ Check-in feito! Comece sua sequência amanhã."
    )


# ── (consolidado de orchestrator_cascade.py) ──
logger = logging.getLogger("Melshape.Cascade")

if TYPE_CHECKING:
    from services.orchestrator import OrchestratorResult


class CascadeMixin:
    """
    Mixin com a cascata de consequências compartilhadas.
    Requer self.db do Orchestrator.
    """

    # ── METAS ────────────────────────────────────────────────────────────────
    def _impactar_metas(self, tipo: str,
                         r: "OrchestratorResult") -> None:
        """Recalcula e conclui automaticamente metas do tipo."""
        try:
            jornada = self.db.get_jornada_ativa()
            if not jornada:
                return
            from services.goals_service import GoalsService
            svc   = GoalsService(self.db)
            metas = self.db.get_metas(jornada["id"])
            for m in metas:
                if m.get("tipo") == tipo and not m.get("concluida"):
                    prog = svc.calcular_progresso(m)
                    if prog["pct"] >= 100:
                        svc.concluir_meta(m["id"])
                        titulo = m.get("titulo", "Meta")
                        r.badges_novos.append(f"🎯 {titulo} concluída!")
                        r.xp_ganho += 200
        except Exception as e:
            logger.warning(f"_impactar_metas ({tipo}): {e}")

    # ── JORNADA ──────────────────────────────────────────────────────────────
    def _atualizar_jornada(self, user: dict,
                            r: "OrchestratorResult") -> None:
        """Avança etapa da jornada se critérios forem atingidos."""
        try:
            from services.journey_service import JourneyService
            svc     = JourneyService(self.db)
            jornada = self.db.get_jornada_ativa()
            if not jornada:
                return
            hm   = user.get("health_mode", "general")
            prog = svc.progresso_jornada(jornada["id"], hm)

            if prog["pct_etapa"] >= 100 and prog["pendentes"]:
                etapa_id = prog["etapa_atual"].get("id", "")
                if etapa_id:
                    self.db.concluir_etapa(etapa_id)
                    r.jornada_avancou = True
                    proxima = prog.get("etapa_seguinte")
                    if proxima:
                        nome_prox = proxima.get("nome","")
                        r.badges_novos.append(f'🗺️ Nova etapa: {nome_prox}')
                        # Registra conquista específica da jornada
                        self.db.registrar_conquista_jornada(
                            jornada["id"],
                            f'Etapa concluída: {prog["etapa_atual"].get("nome","")}',
                            f'Avançou para {nome_prox}',
                        )

            novos_marcos = svc.verificar_marcos_automaticos(
                jornada["id"], user
            )
            r.marcos_novos.extend(novos_marcos)
        except Exception as e:
            logger.warning(f"_atualizar_jornada: {e}")

    # ── BADGES ───────────────────────────────────────────────────────────────
    def _verificar_badges(self, user: dict,
                           r: "OrchestratorResult") -> None:
        """Desbloqueia conquistas novas centralmente."""
        try:
            from services.gamification_service import GamificationService
            novos = GamificationService(self.db).check_achievements(user)
            r.badges_novos.extend(novos)
        except Exception as e:
            logger.warning(f"_verificar_badges: {e}")

    # ── ALERTAS ──────────────────────────────────────────────────────────────
    def _verificar_alertas(self, user: dict,
                            r: "OrchestratorResult") -> None:
        """Chama fn_alerta_risco e alertas por pilar."""
        try:
            if self.db.is_real and self.db.client:
                self.db.client.rpc("fn_alerta_risco", {
                    "p_perfil_id": self.db.uid()
                }).execute()
        except Exception as e:
            logger.warning(f"fn_alerta_risco: {e}")

        hm = user.get("health_mode", "general")
        try:
            if hm == "glp1":
                from services.nutrition_alerts import glp1_low_calorie_alert
                from services.nutrition_service import NutritionService
                al = glp1_low_calorie_alert(
                    NutritionService(self.db).daily_summary
                )
                if al:
                    r.alertas.append(("warning", al))

            if hm == "bariatric":
                from services.bariatric_service import BariatricService
                svc      = BariatricService(self.db)
                fase_key = user.get("bariatric_phase", "liquid")
                for kind, msg in svc.alertas(fase_key, user):
                    r.alertas.append((kind, msg))
        except Exception as e:
            logger.warning(f"_verificar_alertas ({hm}): {e}")

    # ── PRÓXIMO PASSO ────────────────────────────────────────────────────────
    def _gerar_proximo_passo(self, user: dict, evento: str,
                              r: "OrchestratorResult") -> None:
        """Define próximo passo contextual e acionável."""
        streak = r.streak or self.db.get_checkin_streak()
        agua   = self.db.get_hydration_today()
        ci     = self.db.get_checkin_today()
        hm     = user.get("health_mode", "general")

        # Check-in pendente tem prioridade máxima
        if not ci and evento != "checkin":
            r.proximo_passo = "Fazer o check-in de hoje"
            r.proximo_hub   = "meals"
            r.proximo_tipo  = "checkin"
            return

        # Contexto por pilar
        if hm == "glp1":
            from services.glp1_service import GLP1Service
            prox = GLP1Service(self.db).proxima_dose(
                user.get("glp1_medication", "")
            )
            if prox and prox not in ("Hoje", "Amanhã"):
                r.proximo_passo = f"Próxima dose: {prox}"
                return

        if hm == "bariatric":
            fase = user.get("bariatric_phase", "liquid")
            from config import BARIATRIC_PHASES
            fd = BARIATRIC_PHASES.get(fase, {})
            if fd:
                r.proximo_passo = (
                    f"Fase {fd.get('name','')} — "
                    f"máx {fd.get('max_ml','')}ml por refeição"
                )
                return

        # Genérico por dado faltante
        if agua < 1500:
            faltam = 2000 - agua
            r.proximo_passo = f"Registrar mais {faltam}ml de água"
            r.proximo_hub   = "meals"
            r.proximo_tipo  = "hydration"
        elif streak < 7:
            r.proximo_passo = (
                f"Continue! Faltam {7 - streak} dia(s) para 7 dias seguidos"
            )
        else:
            r.proximo_passo = "Você está no caminho certo. Continue assim!"

    # ── NOTIFICAÇÃO ───────────────────────────────────────────────────────────
    def _programar_notificacao(self, user: dict,
                                r: "OrchestratorResult") -> None:
        """Grava notificação contextual em fila_notificacoes."""
        if not r.notificacao_msg:
            return
        try:
            uid = self.db.uid()
            if self.db.is_real and self.db.client:
                try:
                    self.db.client.rpc("fn_criar_notificacao", {
                        "p_perfil_id": uid,
                        "p_mensagem":  r.notificacao_msg,
                        "p_tipo":      "engajamento",
                    }).execute()
                    return
                except Exception:
                    pass
                # fallback: insert direto na fila
                self.db.client.table("fila_notificacoes").insert({
                    "perfil_id": uid,
                    "mensagem":  r.notificacao_msg,
                    "tipo":      "engajamento",
                    "enviada":   False,
                }).execute()
        except Exception as e:
            logger.warning(f"_programar_notificacao: {e}")
