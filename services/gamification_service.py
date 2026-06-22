"""
Melshape — Gamificação: streaks, conquistas, XP, níveis.

TABELAS/VIEWS USADAS:
  experiencia_usuario  → xp_total, nivel_atual_id
  badges_usuario       → badges conquistadas
  vw_conquistas_usuario → view com nome do badge + data
  fn_ganhar_xp (RPC)   → function que credita XP com segurança
"""
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

from core.database import Database

logger = logging.getLogger("Melshape.Gamification")

ACHIEVEMENTS = [
    {"name": "first_meal",       "title": "🍽️ Primeira Refeição",  "desc": "Registrou a primeira refeição!",           "xp": 50},
    {"name": "ten_meals",        "title": "🍴 10 Refeições",        "desc": "10 refeições registradas!",                "xp": 100},
    {"name": "fifty_meals",      "title": "🎖️ 50 Refeições",       "desc": "Mestre do registro!",                      "xp": 500},
    {"name": "week_streak",      "title": "📅 7 Dias Seguidos",     "desc": "Uma semana de consistência!",              "xp": 200},
    {"name": "month_streak",     "title": "🏆 30 Dias!",            "desc": "30 dias consecutivos. Incrível!",          "xp": 1000},
    {"name": "first_weight",     "title": "⚖️ Primeira Pesagem",    "desc": "Começou a monitorar o peso!",              "xp": 50},
    {"name": "lost_1kg",         "title": "📉 Perdeu 1 kg",         "desc": "1 kg eliminado!",                          "xp": 300},
    {"name": "lost_5kg",         "title": "💪 Perdeu 5 kg",         "desc": "5 kg eliminados!",                         "xp": 1000},
    {"name": "first_workout",    "title": "🏋️ Primeiro Treino",     "desc": "Registrou o primeiro treino!",             "xp": 50},
    {"name": "first_supplement", "title": "💊 Suplementação",        "desc": "Registrou suplementos pela primeira vez!", "xp": 50},
    {"name": "hydration_goal",   "title": "💧 Hidratação em Dia",    "desc": "Atingiu a meta de água hoje!",             "xp": 30},
    {"name": "glp1_week",        "title": "💉 1 Semana GLP-1",      "desc": "Uma semana de tratamento monitorado!",     "xp": 150},
    {"name": "bariatric_month",  "title": "🔪 1 Mês Pós-Cirurgia",  "desc": "Um mês de acompanhamento bariátrico!",    "xp": 500},
    {"name": "first_sleep",      "title": "😴 Sono Registrado",     "desc": "Começou a monitorar o sono!",              "xp": 30},
    {"name": "first_checkin",    "title": "✅ Primeiro Check-in",   "desc": "Fez o primeiro check-in diário!",          "xp": 30},
    {"name": "streak_checkin_7", "title": "🔥 7 Check-ins Seguidos","desc": "7 dias de check-in consecutivos!",         "xp": 150},
]

LEVELS = [
    {"level": 1, "name": "Iniciante",   "min_xp": 0,    "icon": "🌱"},
    {"level": 2, "name": "Determinado", "min_xp": 200,  "icon": "🌿"},
    {"level": 3, "name": "Consistente", "min_xp": 500,  "icon": "🌳"},
    {"level": 4, "name": "Dedicado",    "min_xp": 1000, "icon": "⭐"},
    {"level": 5, "name": "Campeão",     "min_xp": 2000, "icon": "🏆"},
    {"level": 6, "name": "Lendário",    "min_xp": 5000, "icon": "👑"},
]

WEEKLY_CHALLENGES = [
    {"title": "Registrar 14 refeições esta semana", "xp": 50,  "emoji": "🍴"},
    {"title": "Atingir meta proteica por 3 dias",   "xp": 120, "emoji": "🥩"},
    {"title": "Beber 2L de água por 5 dias",        "xp": 80,  "emoji": "💧"},
    {"title": "Pesar-se 2 vezes esta semana",       "xp": 80,  "emoji": "⚖️"},
    {"title": "Registrar treino por 3 dias",        "xp": 100, "emoji": "🏋️"},
    {"title": "Fazer check-in por 5 dias",          "xp": 90,  "emoji": "✅"},
    {"title": "Registrar sono por 5 dias seguidos", "xp": 70,  "emoji": "😴"},
]


class GamificationService:

    def __init__(self, db: Database):
        self.db = db

    # ── STREAK ────────────────────────────────────────────────────────────────
    def streak(self) -> int:
        """
        Usa checkins para calcular streak — mais preciso que refeições.
        Fallback para refeições se não houver check-ins.
        """
        streak_val = self.db.get_checkin_streak()
        if streak_val > 0:
            return streak_val

        # fallback: streak por refeições
        meals = self.db.get_meals(60)
        if not meals:
            return 0
        dates = sorted(set(
            datetime.strptime(m.meal_date, "%Y-%m-%d").date()
            for m in meals
        ))
        today = date.today()
        if not dates or dates[-1] not in [today, today - timedelta(days=1)]:
            return 0
        count = 1
        for i in range(len(dates) - 1, 0, -1):
            if (dates[i] - dates[i - 1]).days == 1:
                count += 1
            else:
                break
        return count

    # ── XP E NÍVEL ────────────────────────────────────────────────────────────
    def total_xp(self) -> int:
        """
        Lê XP diretamente de experiencia_usuario (Supabase).
        Fallback: soma das conquistas desbloqueadas.
        """
        xp_banco = self.db.get_xp()
        if xp_banco > 0:
            return xp_banco
        # fallback: calcula pelo histórico de conquistas
        earned = {a.get("achievement_name") for a in self.db.get_achievements()}
        return sum(a["xp"] for a in ACHIEVEMENTS if a["name"] in earned)

    def level(self) -> Dict[str, Any]:
        xp      = self.total_xp()
        current = LEVELS[0]
        for lvl in LEVELS:
            if xp >= lvl["min_xp"]:
                current = lvl
        idx = LEVELS.index(current)
        nxt = LEVELS[idx + 1] if idx + 1 < len(LEVELS) else None
        pct = (
            int((xp - current["min_xp"]) /
                (nxt["min_xp"] - current["min_xp"]) * 100)
            if nxt else 100
        )
        return {
            "xp": xp, "current": current,
            "next": nxt, "progress_pct": pct,
        }

    # ── CONQUISTAS ────────────────────────────────────────────────────────────
    def check_achievements(self, user: dict = None) -> List[str]:
        """
        Verifica condições e desbloqueia conquistas novas.
        Credita XP via fn_ganhar_xp para cada conquista nova.
        Retorna lista de títulos desbloqueados nesta verificação.
        """
        unlocked    = []
        meals       = self.db.get_meals(365)
        weights     = self.db.get_weights(365)
        workouts    = self.db.get_workouts(365)
        supplements = self.db.get_supplements(365)
        sleep_logs  = self.db.get_sleep_logs(365)
        streak_val  = self.streak()
        checkins    = self.db.get_checkin_today()
        streak_ci   = self.db.get_checkin_streak()

        checks = [
            ("first_meal",       "🍽️ Primeira Refeição",   len(meals) >= 1),
            ("ten_meals",        "🍴 10 Refeições",         len(meals) >= 10),
            ("fifty_meals",      "🎖️ 50 Refeições",        len(meals) >= 50),
            ("week_streak",      "📅 7 Dias Seguidos",      streak_val >= 7),
            ("month_streak",     "🏆 30 Dias!",             streak_val >= 30),
            ("first_workout",    "🏋️ Primeiro Treino",      len(workouts) >= 1),
            ("first_supplement", "💊 Suplementação",        len(supplements) >= 1),
            ("first_sleep",      "😴 Sono Registrado",      len(sleep_logs) >= 1),
            ("first_checkin",    "✅ Primeiro Check-in",    checkins is not None),
            ("streak_checkin_7", "🔥 7 Check-ins Seguidos", streak_ci >= 7),
        ]

        if not weights.empty:
            checks.append(("first_weight", "⚖️ Primeira Pesagem", True))
            if len(weights) >= 2:
                try:
                    diff = (
                        float(weights.iloc[0]["weight"]) -
                        float(weights.iloc[-1]["weight"])
                    )
                    checks.append(("lost_1kg", "📉 Perdeu 1 kg", diff >= 1.0))
                    checks.append(("lost_5kg", "💪 Perdeu 5 kg", diff >= 5.0))
                except Exception:
                    pass

        if user:
            if user.get("uses_glp1") and user.get("glp1_start_date"):
                try:
                    start = datetime.strptime(
                        user["glp1_start_date"], "%Y-%m-%d"
                    ).date()
                    days  = (date.today() - start).days
                    checks.append(("glp1_week", "💉 1 Semana GLP-1", days >= 7))
                except Exception:
                    pass
            if user.get("is_bariatric") and user.get("surgery_date"):
                try:
                    start = datetime.strptime(
                        user["surgery_date"], "%Y-%m-%d"
                    ).date()
                    days  = (date.today() - start).days
                    checks.append((
                        "bariatric_month", "🔪 1 Mês Pós-Cirurgia", days >= 30
                    ))
                except Exception:
                    pass

        for name, title, condition in checks:
            if not condition:
                continue
            desbloqueou = self.db.unlock_achievement(name, title)
            if desbloqueou:
                unlocked.append(title)
                # credita XP no banco real
                xp_val = next(
                    (a["xp"] for a in ACHIEVEMENTS if a["name"] == name), 0
                )
                if xp_val:
                    self.db.add_xp(xp_val, motivo=name)

        return unlocked

    # ── DESAFIOS SEMANAIS ─────────────────────────────────────────────────────
    def weekly_challenges(self) -> List[Dict[str, Any]]:
        week  = date.today().isocalendar()[1]
        start = week % len(WEEKLY_CHALLENGES)
        return (WEEKLY_CHALLENGES[start:] + WEEKLY_CHALLENGES[:start])[:3]

    # ── DASHBOARD RÁPIDO ──────────────────────────────────────────────────────
    def quick_stats(self) -> Dict[str, Any]:
        """Stats consolidadas para o card de gamificação na home."""
        lvl_data    = self.level()
        streak_val  = self.streak()
        achievements = self.db.get_achievements()
        return {
            "xp":           lvl_data["xp"],
            "level_name":   lvl_data["current"]["name"],
            "level_icon":   lvl_data["current"]["icon"],
            "level_number": lvl_data["current"]["level"],
            "progress_pct": lvl_data["progress_pct"],
            "next_level":   lvl_data["next"]["name"] if lvl_data["next"] else None,
            "xp_to_next":   (
                lvl_data["next"]["min_xp"] - lvl_data["xp"]
                if lvl_data["next"] else 0
            ),
            "streak":       streak_val,
            "total_badges": len(achievements),
        }
