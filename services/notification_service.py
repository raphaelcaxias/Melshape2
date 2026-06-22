"""
Melshape — Serviço de notificações.

Modo 1 — In-app: notificações via fila_notificacoes (Supabase)
Modo 2 — Agendado: APScheduler em background (20h lembretes, 9h trial)
Modo 3 — Manual: send_manual_reminder()

Compatível com anti-abandono via vw_pacientes_para_notificar.
"""
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger("Melshape.Notifications")


class NotificationService:
    """Notificações in-app e anti-abandono."""

    def __init__(self, db):
        self.db = db

    # ── IN-APP ────────────────────────────────────────────────────────────────
    def verificar_risco_abandono(self, user: dict) -> Optional[str]:
        """
        Verifica vw_pacientes_para_notificar para o usuário logado.
        Cria notificação in-app se em risco.
        Retorna mensagem gerada ou None.
        """
        if not (self.db.is_real and self.db.client):
            return None
        try:
            uid = self.db.uid()
            r   = (self.db.client.table("vw_pacientes_para_notificar")
                   .select("motivo, dias_sem_checkin")
                   .eq("perfil_id", uid)
                   .limit(1)
                   .execute())
            if not r.data:
                return None
            row    = r.data[0]
            motivo = row.get("motivo", "")
            dias   = int(row.get("dias_sem_checkin") or 0)
            nome   = user.get("name", "").split()[0] or "Você"
            msg    = self._msg(motivo, dias, nome)
            if msg:
                self.db.criar_notificacao(msg, tipo="risco_abandono")
            return msg
        except Exception as e:
            logger.warning(f"verificar_risco_abandono: {e}")
        return None

    def _msg(self, motivo: str, dias: int, nome: str) -> Optional[str]:
        if motivo == "RISCO_ABANDONO":
            if dias >= 7:
                return (
                    f"😔 {nome}, sentimos sua falta! {dias} dias sem check-in. "
                    f"Cada recomeço conta — estamos aqui."
                )
            return (
                f"⚡ {nome}, sua sequência anterior provou que você consegue. "
                f"Vamos retomar juntos?"
            )
        if motivo == "SEM_CHECKIN":
            return (
                f"✅ {nome}, seu check-in de hoje está esperando. "
                f"30 segundos mantêm sua sequência ativa."
            )
        return None

    def configurar_lembretes_iniciais(self, user: dict) -> None:
        """Cria lembretes recorrentes padrão após onboarding."""
        if not (self.db.is_real and self.db.client):
            return
        try:
            self.db.client.table("lembretes_recorrentes").insert({
                "perfil_id":  self.db.uid(),
                "tipo":       "lembrete_diario",
                "horario":    "20:00",
                "ativo":      True,
                "mensagem":   "Registre suas refeições do dia!",
            }).execute()
        except Exception as e:
            logger.warning(f"configurar_lembretes_iniciais: {e}")

    def get_inbox(self, limit: int = 10) -> list:
        """Retorna notificações in-app não lidas."""
        if not (self.db.is_real and self.db.client):
            return []
        try:
            uid = self.db.uid()
            r   = (self.db.client.table("fila_notificacoes")
                   .select("*")
                   .eq("perfil_id", uid)
                   .eq("lida", False)
                   .order("criado_em", desc=True)
                   .limit(limit)
                   .execute())
            return r.data or []
        except Exception as e:
            logger.warning(f"get_inbox: {e}")
        return []

    def marcar_lida(self, notif_id: str) -> None:
        if not (self.db.is_real and self.db.client):
            return
        try:
            self.db.client.table("fila_notificacoes").update(
                {"lida": True}
            ).eq("id", notif_id).execute()
        except Exception as e:
            logger.warning(f"marcar_lida: {e}")


# ── AGENDADOR (chamado uma vez na inicialização) ───────────────────────────────
def schedule_daily_reminders(db) -> Optional[object]:
    """
    Inicia APScheduler em background.
    20h → lembretes de refeição
    09h → avisos de trial expirando
    Retorna scheduler ou None se APScheduler não instalado.
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = BackgroundScheduler()

        scheduler.add_job(
            lambda: _run_daily(db),
            CronTrigger(hour=20, minute=0),
            id="daily_reminders", replace_existing=True,
        )
        scheduler.add_job(
            lambda: _run_trial(db),
            CronTrigger(hour=9, minute=0),
            id="trial_check", replace_existing=True,
        )
        scheduler.start()
        logger.info("✅ Agendador iniciado (20h lembretes · 9h trial)")
        return scheduler

    except ImportError:
        logger.warning(
            "APScheduler não instalado — notificações agendadas inativas. "
            "pip install apscheduler"
        )
    except Exception as e:
        logger.error(f"Agendador: {e}")
    return None


def _run_daily(db) -> None:
    from services.email_service import send_meal_reminder, send_streak_at_risk
    users = db._mock().get("users", {})
    sent  = 0
    for email, user in users.items():
        try:
            if user.get("disable_reminders"):
                continue
            today = date.today().isoformat()
            meals = [m for m in db._mock().get("meals", [])
                     if m.get("user_id") == email
                     and m.get("meal_date") == today]
            if meals:
                continue
            streak = _calc_streak(db, email)
            if streak >= 3:
                send_streak_at_risk(email, user.get("name", ""), streak)
            else:
                send_meal_reminder(email, user.get("name", ""), streak)
            sent += 1
        except Exception as e:
            logger.error(f"Lembrete {email}: {e}")
    logger.info(f"Lembretes enviados: {sent}")


def _run_trial(db) -> None:
    from services.email_service import send_trial_expiring
    users = db._mock().get("users", {})
    for email, user in users.items():
        try:
            if user.get("plan") != "trial":
                continue
            from core.models import User
            u    = User.from_dict(user)
            days = u.trial_days_remaining()
            if days in (3, 1):
                send_trial_expiring(email, u.name, days)
        except Exception as e:
            logger.error(f"Trial {email}: {e}")


def _calc_streak(db, email: str) -> int:
    from datetime import timedelta
    today = date.today()
    streak = 0
    for i in range(1, 31):
        d = (today - timedelta(days=i)).isoformat()
        meals = [m for m in db._mock().get("meals", [])
                 if m.get("user_id") == email and m.get("meal_date") == d]
        if meals:
            streak += 1
        else:
            break
    return streak


def send_manual_reminder(email: str, name: str, db) -> bool:
    from services.email_service import send_meal_reminder
    try:
        streak = _calc_streak(db, email)
        return send_meal_reminder(email, name, streak)
    except Exception as e:
        logger.error(f"Lembrete manual {email}: {e}")
        return False
