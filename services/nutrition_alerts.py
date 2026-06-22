"""
Melshape — Alertas clínicos nutricionais.
Importado por NutritionService.

Alertas disponíveis:
  calorie_alert          → calorias vs meta diária
  protein_alert          → proteína vs meta
  glp1_low_calorie_alert → <900kcal por 3+ dias (GLP-1)
  bariatric_volume_alert → volume excede fase bariátrica
  protein_two_day_alert  → proteína <50% por 2 dias seguidos
  nutrient_score         → score 0-100 de um alimento
"""
from datetime import date, timedelta
from typing import Optional
import config


def calorie_alert(current: int, goal: int) -> Optional[str]:
    if goal <= 0:
        return None
    if 0 < current < config.MIN_CALORIES_SAFE:
        return (f"🚨 Consumo muito baixo ({current} kcal). "
                "Déficits severos prejudicam o metabolismo e a massa muscular.")
    pct = current / goal
    if pct >= 1.0:
        return f"⚠️ Meta calórica atingida! {current} kcal consumidas."
    if pct >= config.ALERT_PCT_WARNING:
        return f"⚡ Restam {goal - current} kcal para a meta de hoje."
    return None


def protein_alert(current: float, goal: float) -> Optional[str]:
    if goal <= 0 or current <= 0:
        return None
    if current / goal < 0.5:
        return (f"🥩 Proteína baixa: {current:.0f}g de {goal:.0f}g. "
                "Fundamental para preservar massa muscular.")
    return None


def glp1_low_calorie_alert(daily_summary_fn) -> Optional[str]:
    """
    Alerta GLP-1: <900 kcal por 3+ dias consecutivos.
    daily_summary_fn: callable(date_str) → dict com chave 'calories'
    """
    consecutive = 0
    for i in range(config.GLP1_LOW_KCAL_DAYS):
        d   = (date.today() - timedelta(days=i)).isoformat()
        cal = daily_summary_fn(d).get("calories", 0)
        if 0 < cal < config.GLP1_LOW_KCAL_THRESHOLD:
            consecutive += 1
        else:
            break
    if consecutive >= config.GLP1_LOW_KCAL_DAYS:
        return (
            f"💉 Consumo abaixo de {config.GLP1_LOW_KCAL_THRESHOLD} kcal "
            f"por {consecutive} dias consecutivos. Com GLP-1 é essencial "
            f"manter ingestão adequada. Consulte seu médico."
        )
    return None


def bariatric_volume_alert(volume_ml: float, phase: str) -> Optional[str]:
    phase_data = config.BARIATRIC_PHASES.get(phase)
    if not phase_data or not volume_ml:
        return None
    max_ml = phase_data.get("max_ml", 999)
    if volume_ml > max_ml:
        return (
            f"🔪 Volume {volume_ml:.0f}ml excede o limite da fase "
            f"{phase_data['name']} ({max_ml}ml). Fracione as refeições."
        )
    return None


def protein_two_day_alert(daily_summary_fn, prot_goal: float) -> Optional[str]:
    """
    Alerta se proteína <50% da meta por 2 dias consecutivos.
    daily_summary_fn: callable(date_str) → dict com chave 'protein'
    """
    low_days = 0
    for i in range(2):
        d = (date.today() - timedelta(days=i)).isoformat()
        if daily_summary_fn(d)["protein"] < prot_goal * 0.5:
            low_days += 1
    if low_days >= 2:
        return ("🥩 Proteína abaixo de 50% da meta por 2 dias. "
                "Priorize fontes proteicas nas próximas refeições.")
    return None


def nutrient_score(food: dict) -> int:
    """Score nutricional simples 0-100 para um alimento."""
    score = 50
    prot  = food.get("protein",  food.get("proteina",  0))
    fiber = food.get("fiber",    food.get("fibra",      0))
    cal   = food.get("calories", food.get("calorias",  0))
    if prot > 20:   score += 20
    elif prot > 10: score += 10
    if fiber > 5:   score += 15
    elif fiber > 2: score += 7
    if cal > 300 and prot < 5 and fiber < 1:
        score -= 20
    return max(0, min(100, score))
