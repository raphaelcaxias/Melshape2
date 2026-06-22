"""
Melshape — Constantes globais.
Centraliza todas as configurações do sistema.
"""
import logging

# ── IDENTIDADE ────────────────────────────────────────────────────────────────
APP_NAME     = "Melshape"
APP_VERSION  = "2.0.0"
APP_ICON     = "🔥"
APP_TAGLINE  = "Para quem está mudando de verdade."

# ── PLANOS ────────────────────────────────────────────────────────────────────
TRIAL_DAYS   = 10
PLAN_FREE    = "free"
PLAN_TRIAL   = "trial"
PLAN_PRO     = "pro"
PLAN_CLINIC  = "clinic"

PLAN_PRICE_PRO    = 19.90   # R$/mês
PLAN_PRICE_CLINIC = 99.00   # R$/mês por clínica

# ── DEMO ──────────────────────────────────────────────────────────────────────
DEMO_EMAIL    = "demo@melshape.com.br"
DEMO_PASSWORD = "demo123"

# ── NUTRIÇÃO ──────────────────────────────────────────────────────────────────
HYDRATION_GOAL_ML    = 2000
MIN_CALORIES_SAFE    = 1000   # Mínimo calórico seguro (kcal)
MAX_CALORIES_DISPLAY = 5000   # Máximo para gráficos

# ── GAMIFICAÇÃO ───────────────────────────────────────────────────────────────
XP_CHECKIN      = 50
XP_REFEICAO     = 25
XP_PESO         = 30
XP_HABITO       = 20
XP_SUPLEMENTO   = 10
XP_TREINO       = 40
XP_GLP1         = 25
XP_MEDIDA       = 15
XP_FOTO         = 10
XP_STREAK_7     = 100
XP_STREAK_14    = 200
XP_STREAK_30    = 500
XP_STREAK_90    = 1000

# ── GLP-1 ─────────────────────────────────────────────────────────────────────
GLP1_MEDICATIONS = [
    "semaglutida",
    "tirzepatida",
    "liraglutida",
    "dulaglutida",
    "exenatida",
    "outro",
]

GLP1_PHASES = {
    "inicio":     {"label": "Início",      "icon": "🌱", "semanas": "1-4"},
    "ajuste":     {"label": "Ajuste",      "icon": "⚡", "semanas": "5-12"},
    "manutencao": {"label": "Manutenção",  "icon": "🎯", "semanas": "13+"},
}

# ── FASES BARIÁTRICAS ─────────────────────────────────────────────────────────
BARIATRIC_PHASES = {
    "liquid":    {"name": "Líquida",        "dias": "1-15",  "max_ml": 50,  "max_cal": 400},
    "pastosa":   {"name": "Pastosa",        "dias": "16-30", "max_ml": 100, "max_cal": 600},
    "semi":      {"name": "Semi-sólida",    "dias": "31-60", "max_ml": 150, "max_cal": 800},
    "solida":    {"name": "Sólida",         "dias": "61-90", "max_ml": 200, "max_cal": 1000},
    "adaptacao": {"name": "Adaptação",      "dias": "91+",   "max_ml": 250, "max_cal": 1200},
}

BARIATRIC_ESSENTIALS = [
    "Proteína Whey", "Vitamina B12", "Vitamina D3",
    "Ferro", "Cálcio + Vitamina D", "Ácido Fólico",
]

# ── SINTOMAS ──────────────────────────────────────────────────────────────────
SYMPTOM_LIST = [
    "Náusea", "Vômito", "Diarreia", "Constipação",
    "Dor abdominal", "Refluxo", "Fadiga", "Tontura",
    "Perda de apetite", "Queda de cabelo",
]

SEVERE_SYMPTOMS = ["Vômito", "Dor abdominal", "Tontura"]

# ── HIDRATAÇÃO ────────────────────────────────────────────────────────────────
QUICK_ADD_ML = [150, 200, 300, 350, 500, 750, 1000]

# ── TREINO ────────────────────────────────────────────────────────────────────
WORKOUT_TYPES = {
    "strength":   "🏋️ Musculação",
    "cardio":     "🏃 Cardio",
    "hiit":       "⚡ HIIT",
    "yoga":       "🧘 Yoga/Pilates",
    "swimming":   "🏊 Natação",
    "cycling":    "🚴 Ciclismo",
    "walking":    "🚶 Caminhada",
    "functional": "💪 Funcional",
    "sports":     "⚽ Esporte",
    "other":      "🎯 Outro",
}

# ── MENSAGENS MOTIVACIONAIS POR PILAR ─────────────────────────────────────────
MENSAGENS_MOTIVACIONAIS = {
    "general": [
        "Consistência bate perfeição todos os dias.",
        "Um dia de cada vez. Isso é tudo que precisa.",
        "Você não precisa ser extremo. Só precisa ser constante.",
        "Cada escolha alimentar é um voto pela pessoa que você quer ser.",
        "O resultado é consequência. O hábito é a causa.",
    ],
    "fitness": [
        "O corpo muda devagar. A disciplina muda rápido.",
        "Cada treino é uma promessa cumprida com você mesmo.",
        "Força não é só física.",
        "Proteína primeiro. Sempre.",
        "Descanso é parte do treino, não ausência dele.",
    ],
    "bariatric": [
        "Cada refeição certa é uma vitória clínica real.",
        "Seu corpo está se reconstruindo. Respeite o processo.",
        "Pequenas porções, grandes resultados.",
        "A cirurgia foi o começo. O hábito é o trabalho real.",
        "Mastigue devagar. Seu novo estômago agradece.",
    ],
    "glp1": [
        "O medicamento abre a porta. Você decide o que entra.",
        "Proteína primeiro. Sempre.",
        "Adesão ao tratamento é parte da transformação.",
        "Cada dose registrada é um compromisso com sua saúde.",
        "O remédio controla a fome. Você controla as escolhas.",
    ],
}

# ── LOGGING ───────────────────────────────────────────────────────────────────
LOG_LEVEL  = logging.INFO
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
