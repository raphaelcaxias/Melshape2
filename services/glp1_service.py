"""
Melshape — Serviço GLP-1.

Responsável por:
- Calcular fase atual (adaptação/manutenção/desmame/parado)
- Calcular adesão (doses por semana vs esperado)
- Detectar sintomas graves e gerar alertas
- Calcular dias de tratamento
- Identificar próxima dose esperada
"""
import logging
from datetime import date, datetime, timedelta
from typing import Optional

import config
from core.models import SEVERE_SYMPTOMS

logger = logging.getLogger("Melshape.GLP1Service")

# Frequência esperada por tipo (doses/semana)
_FREQ_SEMANAL = {
    "Ozempic (Semaglutida)":  1,
    "Wegovy (Semaglutida)":   1,
    "Mounjaro (Tirzepatida)": 1,
    "Zepbound (Tirzepatida)": 1,
    "Victoza (Liraglutida)":  7,  # diário
    "Saxenda (Liraglutida)":  7,
    "Outro":                  1,
}


class GLP1Service:

    def __init__(self, db):
        self.db = db

    # ── DIAS DE TRATAMENTO ────────────────────────────────────────────────────
    def dias_tratamento(self, user: dict) -> Optional[int]:
        inicio = user.get("glp1_start_date")
        if not inicio:
            proto = self.db.get_protocolo_ativo()
            inicio = proto.get("iniciado_em") if proto else None
        if not inicio:
            return None
        try:
            d = datetime.strptime(inicio[:10], "%Y-%m-%d").date()
            return (date.today() - d).days
        except Exception:
            return None

    # ── FASE ──────────────────────────────────────────────────────────────────
    def fase_atual(self, user: dict) -> dict:
        """Retorna dados da fase com label, descrição e cor."""
        fase_key  = user.get("glp1_phase", "adapting")
        proto     = self.db.get_protocolo_ativo()
        if proto:
            fase_key = proto.get("fase", fase_key)

        fases = {
            "adapting":    ("🔬", "Adaptação",    "var(--info)",    "Primeiras semanas — monitorar sintomas"),
            "maintenance": ("✅", "Manutenção",   "var(--success)", "Dose estabilizada — foco em hábitos"),
            "tapering":    ("📉", "Desmame",       "var(--warning)", "Redução gradual — manter hábitos"),
            "stopped":     ("⏹️", "Parado",        "var(--error)",   "Tratamento encerrado"),
        }
        icon, label, cor, desc = fases.get(
            fase_key, fases["adapting"]
        )
        return {
            "key":   fase_key,
            "icon":  icon,
            "label": label,
            "cor":   cor,
            "desc":  desc,
        }

    # ── ADESÃO ────────────────────────────────────────────────────────────────
    def adesao_semanal(self, medicamento: str) -> dict:
        """Calcula % de adesão nas últimas 4 semanas."""
        esperado_semana = _FREQ_SEMANAL.get(medicamento, 1)
        doses           = self.db.get_doses_glp1(days=28)
        registradas     = len(doses)
        esperado_total  = esperado_semana * 4
        pct = min(100, int(registradas / esperado_total * 100)) if esperado_total else 0
        return {
            "registradas":    registradas,
            "esperado":       esperado_total,
            "pct":            pct,
            "por_semana":     esperado_semana,
        }

    # ── PRÓXIMA DOSE ──────────────────────────────────────────────────────────
    def proxima_dose(self, medicamento: str) -> Optional[str]:
        """Estima data da próxima dose com base na última registrada."""
        ultima = self.db.get_ultima_dose()
        if not ultima:
            return "Hoje (primeira dose)"
        try:
            freq  = _FREQ_SEMANAL.get(medicamento, 1)
            inter = 7 // freq  # dias entre doses
            ultima_data = date.fromisoformat(ultima["data_aplicacao"][:10])
            prox        = ultima_data + timedelta(days=inter)
            delta       = (prox - date.today()).days
            if delta <= 0:
                return "Hoje"
            if delta == 1:
                return "Amanhã"
            return f"Em {delta} dias ({prox.strftime('%d/%m')})"
        except Exception:
            return None

    # ── ALERTAS DE SINTOMAS ───────────────────────────────────────────────────
    def alertas_sintomas(self) -> list:
        """
        Verifica sintomas graves nos últimos 3 dias.
        Retorna lista de alertas médicos.
        """
        alertas  = []
        sintomas = self.db.get_sintomas_glp1(days=3)
        if not sintomas:
            return alertas

        graves_recentes = set()
        for s in sintomas:
            lista = s.get("sintomas", [])
            if isinstance(lista, str):
                import json
                try:
                    lista = json.loads(lista)
                except Exception:
                    lista = []
            graves_recentes.update(
                cod for cod in lista if cod in SEVERE_SYMPTOMS
            )

        _LABELS = {
            "nausea":   "Náusea intensa",
            "dizziness":"Tontura",
            "pain":     "Dor abdominal",
        }
        for cod in graves_recentes:
            alertas.append(
                f"⚠️ {_LABELS.get(cod, cod)} reportada nos últimos 3 dias. "
                f"Considere consultar seu médico."
            )

        # Alerta calórico do nutrition_alerts
        from services.nutrition_alerts import glp1_low_calorie_alert
        from services.nutrition_service import NutritionService
        nutr  = NutritionService(self.db)
        al_cal = glp1_low_calorie_alert(nutr.daily_summary)
        if al_cal:
            alertas.append(al_cal)

        return alertas

    # ── RESUMO ────────────────────────────────────────────────────────────────
    def resumo(self, user: dict) -> dict:
        med   = user.get("glp1_medication", "")
        dose  = user.get("glp1_dose", "")
        proto = self.db.get_protocolo_ativo()
        if proto:
            med  = proto.get("medicamento", med)
            dose = proto.get("dose_atual", dose)
        return {
            "medicamento":  med,
            "dose_atual":   dose,
            "fase":         self.fase_atual(user),
            "dias":         self.dias_tratamento(user),
            "proxima_dose": self.proxima_dose(med),
            "adesao":       self.adesao_semanal(med),
        }
