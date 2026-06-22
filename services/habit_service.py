"""
Melshape — Serviço de Hábitos.

Responsável por:
- Calcular streak por hábito
- Calcular aderência (% de dias cumpridos)
- Sugerir hábitos iniciais por pilar
- Creditar XP ao registrar hábito
"""
import logging
from datetime import date, timedelta, datetime
from typing import Dict, List

logger = logging.getLogger("Melshape.HabitService")

# Hábitos sugeridos por pilar
_SUGESTOES = {
    "general": [
        ("💧", "Beber 2L de água",       "hidratacao", "daily"),
        ("🥩", "Atingir meta de proteína","nutricao",   "daily"),
        ("🚶", "Caminhar 30 minutos",     "movimento",  "daily"),
        ("😴", "Dormir 7-8 horas",        "sono",       "daily"),
        ("✅", "Registrar refeições",     "registro",   "daily"),
    ],
    "fitness": [
        ("🏋️", "Treinar hoje",            "treino",     "daily"),
        ("🥩", "Meta proteica (2g/kg)",   "nutricao",   "daily"),
        ("💧", "Beber 3L de água",        "hidratacao", "daily"),
        ("😴", "Dormir 8 horas",          "sono",       "daily"),
        ("📊", "Registrar treino",        "registro",   "daily"),
    ],
    "bariatric": [
        ("🥄", "Mastigar devagar",        "alimentacao","daily"),
        ("💊", "Tomar suplementos",       "suplementos","daily"),
        ("💧", "Beber 1,5L de água",      "hidratacao", "daily"),
        ("⚖️", "Pesar-se semanalmente",   "monitoramento","weekly"),
        ("✅", "Registro de volume",      "registro",   "daily"),
    ],
    "glp1": [
        ("💉", "Registrar dose",          "medicamento","weekly"),
        ("🥩", "Proteína primeiro",       "nutricao",   "daily"),
        ("💧", "Beber 2L de água",        "hidratacao", "daily"),
        ("📋", "Monitorar sintomas",      "saude",      "daily"),
        ("✅", "Check-in diário",         "registro",   "daily"),
    ],
}

_XP_HABITO = 15   # XP por hábito concluído
_XP_STREAK_7  = 50   # Bônus 7 dias
_XP_STREAK_30 = 200  # Bônus 30 dias


class HabitService:

    def __init__(self, db):
        self.db = db

    # ── STREAK ────────────────────────────────────────────────────────────────
    def streak_habito(self, habito_id: str) -> int:
        """Dias consecutivos cumpridos até hoje."""
        regs = self.db.get_registros_habito(habito_id, days=60)
        if not regs:
            return 0
        datas_feitas = {r["data_registro"] for r in regs}
        streak = 0
        dia    = date.today()
        while dia.isoformat() in datas_feitas:
            streak += 1
            dia    -= timedelta(days=1)
        return streak

    def melhor_streak(self, habito_id: str) -> int:
        """Maior sequência histórica."""
        regs = self.db.get_registros_habito(habito_id, days=365)
        if not regs:
            return 0
        datas = sorted({r["data_registro"] for r in regs})
        melhor = atual = 1
        for i in range(1, len(datas)):
            d1 = datetime.strptime(datas[i - 1], "%Y-%m-%d").date()
            d2 = datetime.strptime(datas[i],     "%Y-%m-%d").date()
            if (d2 - d1).days == 1:
                atual += 1
                melhor = max(melhor, atual)
            else:
                atual = 1
        return melhor

    # ── ADERÊNCIA ────────────────────────────────────────────────────────────
    def aderencia(self, habito_id: str, days: int = 30) -> float:
        """% de dias cumpridos nos últimos N dias."""
        regs = self.db.get_registros_habito(habito_id, days=days)
        return round(len(regs) / days * 100, 1)

    def aderencia_geral(self, days: int = 7) -> float:
        """% médio de aderência de todos os hábitos."""
        habitos = self.db.get_habitos()
        if not habitos:
            return 0.0
        scores = [self.aderencia(h["id"], days) for h in habitos]
        return round(sum(scores) / len(scores), 1)

    # ── CALENDÁRIO ───────────────────────────────────────────────────────────
    def calendario(self, habito_id: str, days: int = 21) -> List[dict]:
        """
        Retorna lista dos últimos N dias com status de cada um.
        Cada item: {data, concluido, dia_semana}
        """
        regs   = self.db.get_registros_habito(habito_id, days=days)
        feitas = {r["data_registro"] for r in regs}
        result = []
        for i in range(days - 1, -1, -1):
            d = date.today() - timedelta(days=i)
            result.append({
                "data":       d.isoformat(),
                "concluido":  d.isoformat() in feitas,
                "dia_semana": ["S", "T", "Q", "Q", "S", "S", "D"][d.weekday()],
                "futuro":     d > date.today(),
            })
        return result

    # ── REGISTRAR COM XP ────────────────────────────────────────────────────
    def registrar(self, habito_id: str,
                  observacao: str = "") -> Dict[str, object]:
        """
        Registra hábito e credita XP.
        Retorna {ok, xp_ganho, streak, bonus_msg}
        """
        ok = self.db.registrar_habito(habito_id, observacao=observacao)
        if not ok:
            return {"ok": False, "xp_ganho": 0, "streak": 0, "bonus_msg": ""}

        streak    = self.streak_habito(habito_id)
        xp_ganho  = _XP_HABITO
        bonus_msg = ""

        if streak == 7:
            xp_ganho  += _XP_STREAK_7
            bonus_msg  = f"🔥 7 dias seguidos! +{_XP_STREAK_7} XP bônus"
        elif streak == 30:
            xp_ganho  += _XP_STREAK_30
            bonus_msg  = f"🏆 30 dias! +{_XP_STREAK_30} XP bônus"
        elif streak > 0 and streak % 10 == 0:
            bonus = streak * 2
            xp_ganho  += bonus
            bonus_msg  = f"⭐ {streak} dias! +{bonus} XP bônus"

        self.db.add_xp(xp_ganho, motivo=f"habito_{habito_id[:8]}")
        return {
            "ok":        True,
            "xp_ganho":  xp_ganho,
            "streak":    streak,
            "bonus_msg": bonus_msg,
        }

    # ── SUGESTÕES ───────────────────────────────────────────────────────────
    def sugestoes(self, health_mode: str) -> list:
        return _SUGESTOES.get(health_mode, _SUGESTOES["general"])

    def inicializar_habitos_padrao(self, health_mode: str) -> int:
        """
        Cria hábitos padrão do pilar se o paciente não tiver nenhum.
        Retorna quantidade criada.
        """
        existentes = self.db.get_habitos()
        if existentes:
            return 0
        sug   = self.sugestoes(health_mode)
        count = 0
        for icone, nome, cat, freq in sug:
            if self.db.criar_habito(nome, cat, icone, freq):
                count += 1
        return count
