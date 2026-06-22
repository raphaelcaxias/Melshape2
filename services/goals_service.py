"""
Melshape — Serviço de Metas.

Tipos de meta suportados:
  peso       → usa pesagens (redução ou ganho)
  habito     → usa registros_habitos (dias cumpridos)
  consistencia → usa checkins (dias seguidos)
  agua       → usa registros_agua (média diária)
  proteina   → usa vw_consumo_diario (média de proteína)
  livre      → progresso manual

Cada tipo sabe calcular seu próprio progresso
com dados reais do banco — sem inputs manuais.
"""
import logging
from services.goals_calculators import calc_peso, calc_habito, calc_consistencia, calc_agua, calc_proteina
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger("Melshape.Goals")

_XP_META = 200    # XP ao concluir meta
_XP_75   = 50     # XP ao atingir 75% da meta

# Templates por tipo — usados na criação guiada
_TEMPLATES = {
    "peso": [
        {"titulo": "Perder 5 kg",         "valor_alvo": 5.0,  "unidade": "kg"},
        {"titulo": "Perder 10 kg",        "valor_alvo": 10.0, "unidade": "kg"},
        {"titulo": "Atingir peso ideal",  "valor_alvo": None, "unidade": "kg"},
    ],
    "habito": [
        {"titulo": "30 dias de hábito",   "valor_alvo": 30.0, "unidade": "dias"},
        {"titulo": "Aderência de 90%",    "valor_alvo": 90.0, "unidade": "%"},
    ],
    "consistencia": [
        {"titulo": "7 dias seguidos",     "valor_alvo": 7.0,  "unidade": "dias"},
        {"titulo": "30 dias seguidos",    "valor_alvo": 30.0, "unidade": "dias"},
        {"titulo": "90 dias seguidos",    "valor_alvo": 90.0, "unidade": "dias"},
    ],
    "agua": [
        {"titulo": "Beber 2L por 7 dias", "valor_alvo": 7.0,  "unidade": "dias"},
        {"titulo": "Meta diária 30 dias", "valor_alvo": 30.0, "unidade": "dias"},
    ],
    "livre": [
        {"titulo": "Meta personalizada",  "valor_alvo": 100.0,"unidade": "%"},
    ],
}

_TIPO_LABELS = {
    "peso":         ("⚖️", "Peso"),
    "habito":       ("📋", "Hábito"),
    "consistencia": ("🔥", "Consistência"),
    "agua":         ("💧", "Hidratação"),
    "proteina":     ("🥩", "Proteína"),
    "livre":        ("🎯", "Livre"),
}


class GoalsService:

    def __init__(self, db):
        self.db = db

    # ── PROGRESSO REAL ────────────────────────────────────────────────────────
    def calcular_progresso(self, meta: dict) -> dict:
        """
        Calcula progresso atual da meta com dados reais do banco.
        Retorna: {valor_atual, pct, concluida, delta_label}
        """
        tipo       = meta.get("tipo", "livre")
        valor_alvo = float(meta.get("valor_alvo") or 0)

        try:
            if tipo == "peso":
                return calc_peso(self.db, meta, valor_alvo)
            if tipo == "habito":
                return calc_habito(self.db, meta, valor_alvo)
            if tipo == "consistencia":
                return calc_consistencia(self.db, valor_alvo)
            if tipo == "agua":
                return calc_agua(self.db, valor_alvo)
            if tipo == "proteina":
                return calc_proteina(self.db, meta, valor_alvo)
        except Exception as e:
            logger.warning(f"calcular_progresso ({tipo}): {e}")

        # livre / fallback
        atual = float(meta.get("valor_atual") or 0)
        pct   = min(100, int(atual / valor_alvo * 100)) if valor_alvo else 0
        return {
            "valor_atual":  atual,
            "pct":          pct,
            "concluida":    pct >= 100,
            "delta_label":  f"{atual:.0f} / {valor_alvo:.0f} {meta.get('unidade','')}",
        }

        }

    def _zero(self, meta: dict, alvo: float) -> dict:
        return {
            "valor_atual": 0.0,
            "pct": 0,
            "concluida": False,
            "delta_label": f"0 de {alvo:.0f} {meta.get('unidade', '')}",
        }

    # ── CONCLUIR META ────────────────────────────────────────────────────────
    def concluir_meta(self, meta_id: str) -> bool:
        if self.db.is_real and self.db.client:
            try:
                self.db.client.table("metas").update({
                    "concluida":    True,
                    "concluida_em": date.today().isoformat(),
                }).eq("id", meta_id).execute()
                self.db.add_xp(_XP_META, motivo="meta_concluida")
                return True
            except Exception as e:
                logger.warning(f"concluir_meta: {e}")
        self.db.add_xp(_XP_META, motivo="meta_concluida")
        return True

    # ── UTILITÁRIOS ──────────────────────────────────────────────────────────
    def templates(self) -> dict:
        return _TEMPLATES

    def tipo_labels(self) -> dict:
        return _TIPO_LABELS

    def prazo_restante(self, prazo: Optional[str]) -> Optional[int]:
        if not prazo:
            return None
        try:
            alvo = date.fromisoformat(prazo[:10])
            return (alvo - date.today()).days
        except Exception:
            return None
