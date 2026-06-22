"""
Melshape — Modelos de dados e constantes.
Dataclasses Python para os objetos de negócio.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List
import config


# ── USUÁRIO ───────────────────────────────────────────────────────────────────
@dataclass
class User:
    email:          str
    name:           str
    password_hash:  str         = ""
    current_weight: float       = 0.0
    height:         float       = 0.0
    age:            int         = 0
    gender:         str         = "female"
    goal:           str         = "lose"
    goal_weight:    float       = 0.0
    health_mode:    str         = "general"
    activity_level: str         = "moderate"
    plan:           str         = config.PLAN_TRIAL
    created_at:     str         = ""
    onboarding_done: bool       = False
    dark_mode:      bool        = False
    disable_reminders: bool     = False
    professional_id: str        = ""
    professional_name: str      = ""
    uses_glp1:      bool        = False
    glp1_medication: str        = ""
    glp1_dose:      str         = ""
    glp1_phase:     str         = ""
    is_bariatric:   bool        = False
    bariatric_phase: str        = "liquid"

    @classmethod
    def from_dict(cls, d: dict) -> "User":
        fields = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in fields})

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    def trial_days_remaining(self) -> int:
        if self.plan != config.PLAN_TRIAL:
            return 0
        if not self.created_at:
            return config.TRIAL_DAYS
        try:
            start = datetime.fromisoformat(self.created_at[:10]).date()
            return max(0, config.TRIAL_DAYS - (date.today() - start).days)
        except Exception:
            return 0

    def effective_plan(self) -> str:
        """Retorna plano efetivo considerando trial expirado."""
        if self.plan == config.PLAN_TRIAL and self.trial_days_remaining() <= 0:
            return config.PLAN_FREE
        return self.plan


# ── PROFISSIONAL ──────────────────────────────────────────────────────────────
@dataclass
class Professional:
    email:       str
    name:        str
    password_hash: str    = ""
    specialty:   str      = "nutritionist"
    crn:         str      = ""
    plan:        str      = config.PLAN_PRO
    created_at:  str      = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Professional":
        fields = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in fields})

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


# ── REFEIÇÃO ──────────────────────────────────────────────────────────────────
@dataclass
class Meal:
    food:       str
    calories:   float
    protein:    float   = 0.0
    carbs:      float   = 0.0
    fat:        float   = 0.0
    fiber:      float   = 0.0
    meal_time:  str     = "12:00"
    meal_type:  str     = "almoco"
    meal_date:  str     = field(default_factory=lambda: date.today().isoformat())
    notes:      str     = ""


# ── PESO ──────────────────────────────────────────────────────────────────────
@dataclass
class WeightLog:
    weight:    float
    log_date:  str   = field(default_factory=lambda: date.today().isoformat())
    notes:     str   = ""


# ── HIDRATAÇÃO ────────────────────────────────────────────────────────────────
@dataclass
class HydrationLog:
    amount_ml: int
    log_time:  str  = "12:00"
    log_date:  str  = field(default_factory=lambda: date.today().isoformat())


# ── SUPLEMENTO ────────────────────────────────────────────────────────────────
@dataclass
class Supplement:
    name:     str
    dose:     str
    unit:     str    = "mg"
    notes:    str    = ""
    category: str    = "general"
    time_taken: str  = "08:00"
    log_date: str    = field(default_factory=lambda: date.today().isoformat())


# ── TREINO ────────────────────────────────────────────────────────────────────
@dataclass
class WorkoutLog:
    workout_type:  str
    duration:      int   = 30
    intensity:     int   = 5
    notes:         str   = ""
    muscle_group:  str   = ""
    log_date:      str   = field(default_factory=lambda: date.today().isoformat())


# ── SINTOMA ───────────────────────────────────────────────────────────────────
@dataclass
class SymptomLog:
    symptom:    str
    severity:   int   = 1   # 1-3
    notes:      str   = ""
    log_date:   str   = field(default_factory=lambda: date.today().isoformat())


# ── SONO ──────────────────────────────────────────────────────────────────────
@dataclass
class SleepLog:
    hours:    float
    quality:  int   = 3   # 1-5
    notes:    str   = ""
    log_date: str   = field(default_factory=lambda: date.today().isoformat())


# ── CONSTANTES DE NEGÓCIO ─────────────────────────────────────────────────────
WORKOUT_TYPES = config.WORKOUT_TYPES

BARIATRIC_ESSENTIALS = config.BARIATRIC_ESSENTIALS

SEVERE_SYMPTOMS = config.SEVERE_SYMPTOMS

SYMPTOM_LIST = config.SYMPTOM_LIST

QUICK_ADD_ML = config.QUICK_ADD_ML
