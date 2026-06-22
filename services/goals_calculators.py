"""
Melshape — Calculadores de progresso de metas.
Funções puras, recebem db como parâmetro.
Importadas por GoalsService.
"""
from datetime import date, timedelta
from typing import Optional


def _zero(meta: dict, alvo: float) -> dict:
    return {
        "valor_atual": 0.0, "pct": 0,
        "concluida": False,
        "delta_label": f"0 de {alvo:.0f} {meta.get('unidade', '')}",
    }


def calc_peso(db, meta: dict, alvo: float) -> dict:
    df = db.get_weights(365)
    if df.empty:
        return _zero(meta, alvo)
    peso_inicial = float(meta.get("valor_inicial") or df.iloc[0]["weight"])
    peso_atual   = float(df.iloc[-1]["weight"])
    delta        = abs(peso_inicial - peso_atual)
    pct          = min(100, int(delta / alvo * 100)) if alvo else 0
    return {
        "valor_atual":  delta,
        "pct":          pct,
        "concluida":    pct >= 100,
        "delta_label":  f"{delta:.1f} de {alvo:.1f} kg ({pct}%)",
    }


def calc_habito(db, meta: dict, alvo: float) -> dict:
    habitos = db.get_habitos()
    if not habitos:
        return _zero(meta, alvo)
    unidade = meta.get("unidade", "dias")
    if unidade == "%":
        from services.habit_service import HabitService
        atual = HabitService(db).aderencia_geral(days=30)
    else:
        dias_set: set = set()
        for h in habitos:
            regs = db.get_registros_habito(h["id"], days=365)
            dias_set |= {r["data_registro"] for r in regs}
        atual = float(len(dias_set))
    pct = min(100, int(atual / alvo * 100)) if alvo else 0
    return {
        "valor_atual": atual, "pct": pct,
        "concluida":   pct >= 100,
        "delta_label": f"{atual:.0f} de {alvo:.0f} {unidade}",
    }


def calc_consistencia(db, alvo: float) -> dict:
    streak = db.get_checkin_streak()
    pct    = min(100, int(streak / alvo * 100)) if alvo else 0
    return {
        "valor_atual":  float(streak),
        "pct":          pct,
        "concluida":    pct >= 100,
        "delta_label":  f"{streak} de {alvo:.0f} dias seguidos",
    }


def calc_agua(db, alvo: float) -> dict:
    meta_ml  = 2000
    dias_ok  = 0
    uid      = db.uid()
    for i in range(30):
        d = (date.today() - timedelta(days=i)).isoformat()
        try:
            if db.is_real and db.client:
                r     = (db.client.table("registros_agua")
                         .select("quantidade_ml")
                         .eq("perfil_id", uid)
                         .eq("data_registro", d).execute())
                total = sum(x.get("quantidade_ml", 0) for x in (r.data or []))
            else:
                total = sum(
                    x.get("amount_ml", 0)
                    for x in db._mock().get("hydration", [])
                    if x.get("user_id") == uid and x.get("log_date") == d
                )
            if total >= meta_ml:
                dias_ok += 1
        except Exception:
            pass
    pct = min(100, int(dias_ok / alvo * 100)) if alvo else 0
    return {
        "valor_atual":  float(dias_ok),
        "pct":          pct,
        "concluida":    pct >= 100,
        "delta_label":  f"{dias_ok} de {alvo:.0f} dias com 2L",
    }


def calc_proteina(db, meta: dict, alvo: float) -> dict:
    meals = db.get_meals(7)
    if not meals:
        return _zero(meta, alvo)
    from collections import defaultdict
    por_dia: dict = defaultdict(float)
    for m in meals:
        por_dia[m.meal_date] += m.protein
    atual = sum(por_dia.values()) / max(len(por_dia), 1)
    pct   = min(100, int(atual / alvo * 100)) if alvo else 0
    return {
        "valor_atual":  round(atual, 1),
        "pct":          pct,
        "concluida":    pct >= 100,
        "delta_label":  f"{atual:.0f}g de {alvo:.0f}g/dia (média 7d)",
    }
