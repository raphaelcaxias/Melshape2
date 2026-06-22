"""Melshape — Home do Paciente: funções utilitárias."""
from datetime import date, datetime, timedelta

# ── HELPERS ───────────────────────────────────────────────────────────────────
def _get_last_weight(db) -> float | None:
    df = db.get_weights(30)
    if df.empty:
        return None
    try:
        return float(df.iloc[-1]["weight"])
    except Exception:
        return None


def _get_dashboard_paciente(db) -> dict:
    """Lê vw_dashboard_paciente do Supabase. Fallback → dict vazio."""
    if db.is_real and db.client:
        try:
            uid = db.uid()
            r   = (db.client.table("vw_dashboard_paciente")
                   .select("xp_total,nivel,total_badges,desafios_concluidos")
                   .eq("perfil_id", uid)
                   .limit(1)
                   .execute())
            return r.data[0] if r.data else {}
        except Exception:
            pass
    return {}


def _historico_checkins(db, days: int = 7) -> list:
    """Retorna lista bool dos últimos N dias (True = fez check-in)."""
    from datetime import timedelta
    today  = date.today()
    datas  = [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]
    feitos = set()

    if db.is_real and db.client:
        try:
            uid = db.uid()
            r   = (db.client.table("checkins")
                   .select("data_checkin")
                   .eq("perfil_id", uid)
                   .in_("data_checkin", datas)
                   .execute())
            feitos = {x["data_checkin"] for x in (r.data or [])}
        except Exception:
            pass
    else:
        feitos = {
            c.get("log_date", "")
            for c in db._mock().get("checkins", [])
            if c.get("user_id") == db.uid() and c.get("log_date") in datas
        }

    return [d in feitos for d in datas]


def _turno() -> str:
    from datetime import datetime
    h = datetime.now().hour
    if h < 12:
        return "Bom dia"
    if h < 18:
        return "Boa tarde"
    return "Boa noite"


def _data_br() -> str:
    from datetime import datetime
    meses = [
        "jan", "fev", "mar", "abr", "mai", "jun",
        "jul", "ago", "set", "out", "nov", "dez",
    ]
    dias  = ["Segunda", "Terça", "Quarta", "Quinta",
             "Sexta", "Sábado", "Domingo"]
    hoje  = date.today()
    return f"{dias[hoje.weekday()]}, {hoje.day} de {meses[hoje.month - 1]}"
