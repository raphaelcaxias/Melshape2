"""
Melshape — Serviço Bariátrico.

Responsável por:
- Calcular fase automática por dias pós-cirurgia
- Retornar limites de volume e calorias da fase
- Listar suplementos obrigatórios da fase
- Calcular progresso pós-cirurgia
- Gerar alertas nutricionais bariátricos
"""
import logging
from datetime import date, datetime
from typing import Optional

import config
from core.models import BARIATRIC_ESSENTIALS

logger = logging.getLogger("Melshape.BariatricService")

# Dias de início de cada fase
_FASE_DIAS = {
    "liquid":      (0,   14),
    "pasty":       (15,  30),
    "soft":        (31,  60),
    "solid":       (61,  180),
    "maintenance": (181, 99999),
}

# Suplementos por fase (essenciais desde o início)
_SUPL_POR_FASE = {
    "liquid":      ["Vitamina B1 (Tiamina)", "Vitamina D3", "Proteína Whey"],
    "pasty":       ["Vitamina B12", "Vitamina D3", "Ferro", "Proteína Whey"],
    "soft":        ["Vitamina B12", "Vitamina D3", "Ferro",
                    "Cálcio Citrato", "Zinco", "Proteína Whey"],
    "solid":       [e["name"] for e in BARIATRIC_ESSENTIALS],
    "maintenance": [e["name"] for e in BARIATRIC_ESSENTIALS],
}


class BariatricService:

    def __init__(self, db):
        self.db = db

    # ── DIAS PÓS-CIRURGIA ─────────────────────────────────────────────────────
    def dias_pos_cirurgia(self, user: dict) -> Optional[int]:
        surgery = user.get("surgery_date")
        if not surgery:
            cirurgia = self.db.get_cirurgia()
            surgery  = cirurgia.get("data_cirurgia") if cirurgia else None
        if not surgery:
            return None
        try:
            d = datetime.strptime(surgery[:10], "%Y-%m-%d").date()
            return (date.today() - d).days
        except Exception:
            return None

    # ── FASE AUTOMÁTICA ───────────────────────────────────────────────────────
    def fase_automatica(self, dias: Optional[int]) -> str:
        """Determina fase pela quantidade de dias pós-cirurgia."""
        if dias is None:
            return "liquid"
        for fase, (ini, fim) in _FASE_DIAS.items():
            if ini <= dias <= fim:
                return fase
        return "maintenance"

    def fase_data(self, fase_key: str) -> dict:
        """Retorna todos os dados da fase do config."""
        data = config.BARIATRIC_PHASES.get(fase_key, {})
        return {
            "key":     fase_key,
            "nome":    data.get("name", "—"),
            "dias":    data.get("days", "—"),
            "max_ml":  data.get("max_ml", 999),
            "max_cal": data.get("max_cal", 9999),
        }

    # ── PROGRESSO ─────────────────────────────────────────────────────────────
    def progresso_jornada(self, dias: Optional[int]) -> dict:
        """
        Calcula % de progresso até 1 ano pós-cirurgia (meta de 365 dias).
        """
        if dias is None:
            return {"pct": 0, "dias": 0, "meta": 365}
        meta = 365
        pct  = min(100, int(dias / meta * 100))
        return {"pct": pct, "dias": dias, "meta": meta}

    # ── SUPLEMENTOS ───────────────────────────────────────────────────────────
    def suplementos_fase(self, fase_key: str) -> list:
        """Retorna lista de suplementos obrigatórios para a fase."""
        nomes    = _SUPL_POR_FASE.get(fase_key, [])
        todos    = {e["name"]: e for e in BARIATRIC_ESSENTIALS}
        resultado = []
        for nome in nomes:
            if nome in todos:
                resultado.append(todos[nome])
            else:
                resultado.append({"name": nome, "dose": "—", "unit": ""})
        return resultado

    # ── ALERTAS ───────────────────────────────────────────────────────────────
    def alertas(self, fase_key: str, user: dict) -> list:
        """
        Gera alertas nutricionais para o paciente bariátrico.
        """
        alertas    = []
        fase_info  = self.fase_data(fase_key)
        from services.nutrition_service import NutritionService
        nutr  = NutritionService(self.db)
        sm    = nutr.daily_summary()

        # Volume
        vol = sm.get("volume_ml", 0)
        if vol > 0 and vol > fase_info["max_ml"]:
            alertas.append((
                "error",
                f"🔪 Volume excedido: {vol:.0f}ml "
                f"(máx {fase_info['max_ml']}ml na fase {fase_info['nome']}). "
                f"Fracione as refeições.",
            ))

        # Calorias acima do limite
        cal = sm.get("calories", 0)
        if cal > 0 and cal > fase_info["max_cal"]:
            alertas.append((
                "warning",
                f"⚡ Calorias acima do limite da fase {fase_info['nome']}: "
                f"{cal:.0f} kcal (máx {fase_info['max_cal']} kcal).",
            ))

        # Proteína baixa
        prot     = sm.get("protein", 0)
        peso     = user.get("current_weight", 70) or 70
        meta_p   = peso * 1.5  # 1.5g/kg para bariátrico
        if prot > 0 and prot < meta_p * 0.6:
            alertas.append((
                "warning",
                f"🥩 Proteína baixa: {prot:.0f}g de {meta_p:.0f}g. "
                f"Priorize fontes proteicas em cada refeição.",
            ))

        return alertas

    # ── RESUMO ────────────────────────────────────────────────────────────────
    def resumo(self, user: dict) -> dict:
        dias         = self.dias_pos_cirurgia(user)
        fase_key     = (
            user.get("bariatric_phase")
            or self.fase_automatica(dias)
        )
        cirurgia     = self.db.get_cirurgia()
        tipo_key     = user.get("bariatric_type", "")
        tipo_label   = config.BARIATRIC_TYPES.get(tipo_key, tipo_key or "—")
        return {
            "dias":        dias,
            "fase":        self.fase_data(fase_key),
            "fase_key":    fase_key,
            "tipo":        tipo_label,
            "progresso":   self.progresso_jornada(dias),
            "suplementos": self.suplementos_fase(fase_key),
            "cirurgia":    cirurgia,
        }
