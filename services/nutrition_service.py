"""
Melshape — Serviço de nutrição.
TMB/TDEE, metas, resumos, validação cruzada e registro de refeições.

Alertas clínicos: nutrition_alerts.py
Views usadas: vw_consumo_diario, vw_consumo_semanal, vw_aderencia_nutricional
"""
import logging
import pandas as pd
from datetime import date, timedelta
from typing import Dict, Any, Optional, List

from core.database import Database
from core.models import Meal
import config
from services.nutrition_alerts import (
    calorie_alert, protein_alert,
    glp1_low_calorie_alert, bariatric_volume_alert,
    protein_two_day_alert, nutrient_score,
)

logger = logging.getLogger("Melshape.Nutrition")
_CROSS_THRESHOLD = 0.15


class NutritionService:

    def __init__(self, db: Database):
        self.db = db

    # ── VALIDAÇÃO CRUZADA ─────────────────────────────────────────────────────
    def cross_validate(self, calories: float, protein: float,
                       carbs: float, fat: float) -> Optional[str]:
        """Alerta se diferença entre kcal declaradas e calculadas > 15%."""
        if calories <= 0:
            return None
        calc = (protein * 4) + (carbs * 4) + (fat * 9)
        pct  = abs(calories - calc) / calories
        if pct > _CROSS_THRESHOLD:
            return (
                f"⚠️ Divergência nutricional: declarado {calories:.0f} kcal, "
                f"calculado pelos macros {calc:.0f} kcal "
                f"({pct * 100:.0f}% de diferença). "
                f"Verifique as quantidades registradas."
            )
        return None

    def validate_meal(self, food: dict, quantity: float) -> Optional[str]:
        """Valida alimento antes de registrar. Retorna alerta ou None."""
        return self.cross_validate(
            food.get("calories", 0) * quantity,
            food.get("protein",  0) * quantity,
            food.get("carbs",    0) * quantity,
            food.get("fat",      0) * quantity,
        )

    # ── TMB / TDEE / METAS ───────────────────────────────────────────────────
    def calc_tmb(self, weight: Optional[float], height: Optional[int],
                 age: Optional[int], gender: str = "female") -> int:
        if not all([weight, height, age]):
            return 1500
        base = 10 * weight + 6.25 * height - 5 * age
        return int(base + 5) if gender == "male" else int(base - 161)

    def calc_tdee(self, tmb: int, activity_level: str = "moderate") -> int:
        return int(tmb * config.ACTIVITY_FACTORS.get(activity_level, 1.55))

    def calc_goal_calories(self, tmb: int, activity_level: str = "moderate",
                            goal: str = "lose", health_mode: str = "general",
                            workout_adjustment: int = 0) -> int:
        tdee = self.calc_tdee(tmb, activity_level)
        if health_mode == "bariatric":
            base = max(config.MIN_CALORIES_SAFE, tdee - 300)
        elif health_mode == "glp1":
            base = max(config.MIN_CALORIES_SAFE, tdee - 400)
        elif goal == "lose":
            base = max(config.SAFE_MIN_CALORIES, tdee - 500)
        elif goal == "gain":
            base = tdee + 300
        else:
            base = tdee
        return base + workout_adjustment

    def calc_protein_goal(self, weight: Optional[float],
                           health_mode: str = "general") -> float:
        if not weight:
            return 120.0
        per_kg = {
            "glp1": config.GLP1_PROTEIN_PER_KG,
            "bariatric": config.BARIATRIC_PROTEIN_PER_KG,
            "fitness": config.FITNESS_PROTEIN_PER_KG,
            "general": config.GENERAL_PROTEIN_PER_KG,
        }.get(health_mode, config.GENERAL_PROTEIN_PER_KG)
        return round(weight * per_kg, 1)

    def calc_macros_goal(self, goal_calories: int,
                          goal: str = "lose") -> Dict[str, int]:
        if goal == "lose":
            return {
                "protein": int(goal_calories * 0.30 / 4),
                "carbs":   int(goal_calories * 0.35 / 4),
                "fat":     int(goal_calories * 0.35 / 9),
            }
        if goal == "gain":
            return {
                "protein": int(goal_calories * 0.25 / 4),
                "carbs":   int(goal_calories * 0.50 / 4),
                "fat":     int(goal_calories * 0.25 / 9),
            }
        return {
            "protein": int(goal_calories * 0.25 / 4),
            "carbs":   int(goal_calories * 0.45 / 4),
            "fat":     int(goal_calories * 0.30 / 9),
        }

    def days_to_goal(self, current: Optional[float],
                     goal_w: Optional[float]) -> Optional[int]:
        if not current or not goal_w or current == goal_w:
            return None
        return int(abs(current - goal_w) / (3500 / 7700) * 7)

    # ── RESUMOS ───────────────────────────────────────────────────────────────
    def daily_summary(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """Tenta vw_consumo_diario; fallback soma local."""
        if not date_str:
            date_str = date.today().isoformat()
        if self.db.is_real and self.db.client:
            try:
                uid = self.db.uid()
                r   = (self.db.client.table("vw_consumo_diario")
                       .select("calorias,proteina,carboidratos,gorduras,total_refeicoes")
                       .eq("perfil_id", uid).eq("dia", date_str)
                       .limit(1).execute())
                if r.data:
                    row = r.data[0]
                    return {
                        "calories": int(row.get("calorias") or 0),
                        "protein":  float(row.get("proteina") or 0),
                        "carbs":    float(row.get("carboidratos") or 0),
                        "fat":      float(row.get("gorduras") or 0),
                        "fiber": 0.0, "volume_ml": 0.0,
                        "count":    int(row.get("total_refeicoes") or 0),
                        "meals":    [],
                    }
            except Exception as e:
                logger.warning(f"vw_consumo_diario: {e}")
        meals = self.db.get_meals_by_date(date_str)
        return {
            "calories": sum(m.calories for m in meals),
            "protein":  round(sum(m.protein   for m in meals), 1),
            "carbs":    round(sum(m.carbs     for m in meals), 1),
            "fat":      round(sum(m.fat       for m in meals), 1),
            "fiber":    round(sum(m.fiber     for m in meals), 1),
            "volume_ml":round(sum(m.volume_ml for m in meals), 0),
            "count":    len(meals),
            "meals":    sorted(meals, key=lambda x: x.meal_time),
        }

    def weekly_summary(self) -> pd.DataFrame:
        """Tenta vw_consumo_semanal; fallback local."""
        if self.db.is_real and self.db.client:
            try:
                uid = self.db.uid()
                r   = (self.db.client.table("vw_consumo_semanal")
                       .select("ano,semana,calorias,proteina,carboidratos,gorduras")
                       .eq("perfil_id", uid)
                       .order("ano", desc=True).order("semana", desc=True)
                       .limit(8).execute())
                if r.data:
                    return pd.DataFrame(r.data)
            except Exception as e:
                logger.warning(f"vw_consumo_semanal: {e}")
        meals = self.db.get_meals(7)
        if not meals:
            return pd.DataFrame()
        df = pd.DataFrame([{
            "date": m.meal_date, "calories": m.calories, "protein": m.protein,
        } for m in meals])
        df["date"] = pd.to_datetime(df["date"])
        return (df.groupby(df["date"].dt.date)
                  .agg(calories=("calories", "sum"), protein=("protein", "sum"))
                  .reset_index())

    def consistency_score(self) -> float:
        """% de dias com registro (usa vw_aderencia_nutricional)."""
        if self.db.is_real and self.db.client:
            try:
                uid = self.db.uid()
                r   = (self.db.client.table("vw_aderencia_nutricional")
                       .select("percentual_aderencia")
                       .eq("perfil_id", uid).limit(1).execute())
                if r.data:
                    return float(r.data[0].get("percentual_aderencia") or 0)
            except Exception as e:
                logger.warning(f"vw_aderencia_nutricional: {e}")
        meals = self.db.get_meals(30)
        return round(len(set(m.meal_date for m in meals)) / 30 * 100, 1) if meals else 0.0

    def period_analysis(self) -> Dict[str, Any]:
        meals   = self.db.get_meals(30)
        periods = {"Manhã": 0, "Tarde": 0, "Noite": 0}
        counts  = {"Manhã": 0, "Tarde": 0, "Noite": 0}
        for m in meals:
            if not m.meal_time:
                continue
            try:
                h = int(m.meal_time.split(":")[0])
            except Exception:
                continue
            p = "Manhã" if h < 12 else "Tarde" if h < 18 else "Noite"
            periods[p] += m.calories
            counts[p]  += 1
        return {"calories_by_period": periods, "count_by_period": counts}

    # ── ALERTAS (delegados para nutrition_alerts.py) ──────────────────────────
    def calorie_alert(self, current: int, goal: int) -> Optional[str]:
        return calorie_alert(current, goal)

    def protein_alert(self, current: float, goal: float) -> Optional[str]:
        return protein_alert(current, goal)

    def glp1_low_calorie_alert(self) -> Optional[str]:
        return glp1_low_calorie_alert(self.daily_summary)

    def bariatric_volume_alert(self, volume_ml: float, phase: str) -> Optional[str]:
        return bariatric_volume_alert(volume_ml, phase)

    def protein_two_day_alert(self, prot_goal: float) -> Optional[str]:
        return protein_two_day_alert(self.daily_summary, prot_goal)

    def nutrient_score(self, food: dict) -> int:
        return nutrient_score(food)

    # ── REGISTRO ──────────────────────────────────────────────────────────────
    def register_meal(self, food: dict, quantity: float,
                      meal_time: str, meal_type: str = "",
                      mood: str = "", volume_ml: float = 0.0) -> tuple:
        """Registra refeição. Retorna (sucesso: bool, alerta_divergência: str|None)."""
        try:
            cal  = food.get("calories", food.get("calorias", 0))
            prot = food.get("protein",  food.get("proteina", 0))
            carb = food.get("carbs",    food.get("carboidratos", 0))
            fat  = food.get("fat",      food.get("gorduras", 0))
            fib  = food.get("fiber",    food.get("fibra", 0))
            nome = food.get("name",     food.get("nome", ""))
            alerta = self.cross_validate(
                cal * quantity, prot * quantity,
                carb * quantity, fat * quantity
            )
            meal = Meal(
                food=nome,
                calories=int(cal  * quantity),
                protein= round(prot * quantity, 1),
                carbs=   round(carb * quantity, 1),
                fat=     round(fat  * quantity, 1),
                fiber=   round(fib  * quantity, 1),
                quantity=quantity, volume_ml=volume_ml,
                meal_time=meal_time, meal_type=meal_type,
                mood=mood, nutrient_score=self.nutrient_score(food),
            )
            ok = self.db.save_meal(meal)
            return ok, alerta
        except Exception as e:
            logger.error(f"register_meal: {e}")
            return False, None

    def suggest_foods(self) -> List[str]:
        meals = self.db.get_meals(14)
        if not meals:
            return []
        from collections import Counter
        return [f for f, _ in Counter(m.food for m in meals).most_common(5)]
