"""
Melshape — Extensão do Database: registros de dados.
Importar junto com database.py via mixin ou herança.

Tabelas: refeicoes, itens_refeicao, pesagens, registros_agua,
         checkins, experiencia_usuario, badges_usuario, badges
"""
import logging
import pandas as pd
import streamlit as st
from datetime import date, datetime, timedelta
from typing import Optional, List

from core.models import (
    Meal, WeightLog, HydrationLog, Supplement,
    WorkoutLog, SymptomLog, SleepLog, CycleLog,
)

logger = logging.getLogger("Melshape.Database")


class RecordsMixin:
    """
    Mixin com todos os métodos de leitura/escrita de registros.
    Requer que a classe base tenha: self.client, self.is_real,
    self.uid(), self._mock(), self._filter_user(), self._filter_days(),
    self._make_model()
    """

    # ── REFEIÇÕES ─────────────────────────────────────────────────────────────
    def save_meal(self, meal: Meal) -> bool:
        meal.user_id = self.uid()
        if self.is_real and self.client:
            try:
                ref = self.client.table("refeicoes").insert({
                    "perfil_id":     meal.user_id,
                    "tipo_refeicao": meal.meal_type or "outro",
                    "data_refeicao": meal.meal_date,
                    "horario":       meal.meal_time or None,
                    "humor":         meal.mood or None,
                    "observacoes":   meal.notes or None,
                }).execute()
                if not ref.data:
                    return False
                refeicao_id = ref.data[0]["id"]
                alimento_id = self._find_alimento_id(meal.food)
                self.client.table("itens_refeicao").insert({
                    "refeicao_id":    refeicao_id,
                    "alimento_id":    alimento_id,
                    "quantidade":     meal.quantity,
                    "calorias_calc":  meal.calories,
                    "proteina_calc":  meal.protein,
                    "carbo_calc":     meal.carbs,
                    "gordura_calc":   meal.fat,
                    "nome_livre":     meal.food if not alimento_id else None,
                }).execute()
                return True
            except Exception as e:
                logger.error(f"save_meal: {e}")
        self._mock()["meals"].append(meal.to_dict())
        return True

    def _find_alimento_id(self, nome: str) -> Optional[str]:
        try:
            r = (self.client.table("alimentos_base")
                 .select("id").eq("nome", nome).limit(1).execute())
            return r.data[0]["id"] if r.data else None
        except Exception:
            return None

    def get_meals(self, days: Optional[int] = 7) -> List[Meal]:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                q = (self.client.table("vw_refeicoes_nutricionais")
                     .select("*").eq("perfil_id", uid))
                if days:
                    cutoff = (date.today() - timedelta(days=days)).isoformat()
                    q = q.gte("criado_em", cutoff)
                rows = q.order("criado_em", desc=True).execute().data or []
                return [self._row_to_meal(r) for r in rows]
            except Exception as e:
                logger.error(f"get_meals: {e}")
                return []
        data = self._filter_user(self._mock()["meals"], uid)
        data = self._filter_days(data, days, "meal_date")
        return [self._make_model(Meal, r) for r in data]

    def _row_to_meal(self, r: dict) -> Meal:
        criado    = r.get("criado_em", "")
        meal_date = criado[:10] if criado else date.today().isoformat()
        meal_time = criado[11:16] if len(criado) > 15 else ""
        return Meal(
            food=r.get("tipo_refeicao", "Refeição"),
            calories=int(r.get("calorias") or 0),
            protein=float(r.get("proteina") or 0),
            carbs=float(r.get("carboidratos") or 0),
            fat=float(r.get("gorduras") or 0),
            meal_date=meal_date, meal_time=meal_time,
            meal_type=r.get("tipo_refeicao", ""),
            user_id=r.get("perfil_id", ""),
        )

    def get_meals_by_date(self, date_str: str) -> List[Meal]:
        return [m for m in self.get_meals(None) if m.meal_date == date_str]

    def count_meals_today(self) -> int:
        return len(self.get_meals_by_date(date.today().isoformat()))

    def get_last_meals(self, limit: int = 10) -> List[Meal]:
        meals = self.get_meals(14)
        seen, result = set(), []
        for m in sorted(meals, key=lambda x: (x.meal_date, x.meal_time), reverse=True):
            if m.food not in seen:
                seen.add(m.food)
                result.append(m)
            if len(result) >= limit:
                break
        return result

    # ── PESO ──────────────────────────────────────────────────────────────────
    def save_weight(self, w: WeightLog) -> bool:
        w.user_id = self.uid()
        if self.is_real and self.client:
            try:
                self.client.table("pesagens").insert({
                    "perfil_id":         w.user_id,
                    "peso":              w.weight,
                    "data_pesagem":      w.log_date,
                    "gordura_pct":       w.body_fat or None,
                    "massa_muscular_kg": w.muscle_mass or None,
                    "observacoes":       w.notes or None,
                    "origem":            "manual",
                }).execute()
                self.client.table("perfis").update(
                    {"peso_atual": w.weight}
                ).eq("id", w.user_id).execute()
                return True
            except Exception as e:
                logger.error(f"save_weight: {e}")
        self._mock()["weights"].append(w.to_dict())
        uid = w.user_id
        if uid in self._mock()["users"]:
            self._mock()["users"][uid]["current_weight"] = w.weight
        return True

    def get_weights(self, days: int = 30) -> pd.DataFrame:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                cutoff = (date.today() - timedelta(days=days)).isoformat()
                r = (self.client.table("pesagens")
                     .select("data_pesagem, peso, gordura_pct, massa_muscular_kg, observacoes")
                     .eq("perfil_id", uid).gte("data_pesagem", cutoff)
                     .order("data_pesagem").execute())
                if r.data:
                    df = pd.DataFrame(r.data).rename(columns={
                        "data_pesagem": "log_date", "peso": "weight",
                        "gordura_pct": "body_fat", "massa_muscular_kg": "muscle_mass",
                        "observacoes": "notes",
                    })
                    df["log_date"] = pd.to_datetime(df["log_date"])
                    return df.sort_values("log_date")
            except Exception as e:
                logger.error(f"get_weights: {e}")
        data = self._filter_user(self._mock()["weights"], uid)
        data = self._filter_days(data, days)
        if not data:
            return pd.DataFrame(
                columns=["log_date", "weight", "notes", "body_fat", "muscle_mass"]
            )
        df = pd.DataFrame(data)
        df["log_date"] = pd.to_datetime(df["log_date"])
        return df.sort_values("log_date")

    # ── HIDRATAÇÃO ────────────────────────────────────────────────────────────
    def save_hydration(self, h: HydrationLog) -> bool:
        h.user_id = self.uid()
        if self.is_real and self.client:
            try:
                self.client.table("registros_agua").insert({
                    "perfil_id":     h.user_id,
                    "quantidade_ml": h.amount_ml,
                    "data_registro": h.log_date,
                    "horario":       h.log_time or None,
                    "fonte":         h.source or "water",
                }).execute()
                return True
            except Exception as e:
                logger.error(f"save_hydration: {e}")
        self._mock()["hydration"].append(h.to_dict())
        return True

    def get_hydration_today(self) -> int:
        uid   = self.uid()
        today = date.today().isoformat()
        if self.is_real and self.client:
            try:
                r = (self.client.table("registros_agua")
                     .select("quantidade_ml").eq("perfil_id", uid)
                     .eq("data_registro", today).execute())
                return sum(x.get("quantidade_ml", 0) for x in (r.data or []))
            except Exception as e:
                logger.error(f"get_hydration_today: {e}")
        return sum(
            x.get("amount_ml", 0) for x in self._mock()["hydration"]
            if x.get("user_id") == uid and x.get("log_date") == today
        )

    def get_hydration_logs_today(self) -> List[HydrationLog]:
        uid   = self.uid()
        today = date.today().isoformat()
        if self.is_real and self.client:
            try:
                r = (self.client.table("registros_agua")
                     .select("*").eq("perfil_id", uid)
                     .eq("data_registro", today).execute())
                return [
                    HydrationLog(
                        amount_ml=x.get("quantidade_ml", 0),
                        log_date=x.get("data_registro", today),
                        log_time=x.get("horario", ""),
                        source=x.get("fonte", "water"), user_id=uid,
                    )
                    for x in (r.data or [])
                ]
            except Exception as e:
                logger.error(f"get_hydration_logs_today: {e}")
        data = [
            x for x in self._mock()["hydration"]
            if x.get("user_id") == uid and x.get("log_date") == today
        ]
        return [self._make_model(HydrationLog, r) for r in data]

    # ── CHECK-IN ──────────────────────────────────────────────────────────────
    def save_checkin(self, humor: int, energia: int, sono: float,
                     notes: str = "") -> bool:
        uid   = self.uid()
        today = date.today().isoformat()
        if self.is_real and self.client:
            try:
                self.client.table("checkins").upsert({
                    "perfil_id": uid, "data_checkin": today,
                    "humor": humor, "energia": energia,
                    "qualidade_sono": sono, "observacoes": notes or None,
                }, on_conflict="perfil_id,data_checkin").execute()
                return True
            except Exception as e:
                logger.error(f"save_checkin: {e}")
        self._mock()["checkins"].append({
            "user_id": uid, "log_date": today,
            "humor": humor, "energia": energia,
            "qualidade_sono": sono, "notes": notes,
        })
        return True

    def get_checkin_today(self) -> Optional[dict]:
        uid   = self.uid()
        today = date.today().isoformat()
        if self.is_real and self.client:
            try:
                r = (self.client.table("checkins").select("*")
                     .eq("perfil_id", uid).eq("data_checkin", today)
                     .limit(1).execute())
                return r.data[0] if r.data else None
            except Exception as e:
                logger.error(f"get_checkin_today: {e}")
        for c in reversed(self._mock()["checkins"]):
            if c.get("user_id") == uid and c.get("log_date") == today:
                return c
        return None

    def get_checkin_streak(self) -> int:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = (self.client.table("checkins").select("data_checkin")
                     .eq("perfil_id", uid).order("data_checkin", desc=True)
                     .limit(60).execute())
                dates = [x["data_checkin"] for x in (r.data or [])]
            except Exception:
                dates = []
        else:
            dates = sorted(
                set(c.get("log_date", "") for c in self._mock()["checkins"]
                    if c.get("user_id") == uid), reverse=True,
            )
        streak = 0
        check  = date.today()
        for ds in dates:
            try:
                d = datetime.strptime(ds, "%Y-%m-%d").date()
            except Exception:
                continue
            if d == check:
                streak += 1
                check  -= timedelta(days=1)
            elif d < check:
                break
        return streak

    # ── GAMIFICAÇÃO ───────────────────────────────────────────────────────────
    def get_xp(self) -> int:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = (self.client.table("experiencia_usuario")
                     .select("xp_total").eq("perfil_id", uid).limit(1).execute())
                return r.data[0]["xp_total"] if r.data else 0
            except Exception as e:
                logger.error(f"get_xp: {e}")
        return 0

    def add_xp(self, amount: int, motivo: str = "") -> bool:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                self.client.rpc("fn_ganhar_xp", {
                    "p_perfil_id": uid, "p_xp": amount, "p_motivo": motivo,
                }).execute()
                return True
            except Exception as e:
                logger.error(f"add_xp: {e}")
        return False

    def xp_checkin(self) -> bool:
        """Chama fn_xp_checkin — função específica do banco para check-in."""
        uid = self.uid()
        if self.is_real and self.client:
            try:
                self.client.rpc("fn_xp_checkin", {
                    "p_perfil_id": uid,
                }).execute()
                return True
            except Exception as e:
                logger.warning(f"fn_xp_checkin: {e}")
                # fallback para fn_ganhar_xp genérico
                return self.add_xp(20, "checkin_diario")
        return self.add_xp(20, "checkin_diario")

    def xp_pesagem(self) -> bool:
        """Chama fn_xp_pesagem — função específica do banco para pesagem."""
        uid = self.uid()
        if self.is_real and self.client:
            try:
                self.client.rpc("fn_xp_pesagem", {
                    "p_perfil_id": uid,
                }).execute()
                return True
            except Exception as e:
                logger.warning(f"fn_xp_pesagem: {e}")
                return self.add_xp(30, "pesagem")
        return self.add_xp(30, "pesagem")

    def unlock_achievement(self, name: str, title: str) -> bool:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                b = (self.client.table("badges").select("id")
                     .eq("nome", title).limit(1).execute())
                if b.data:
                    badge_id = b.data[0]["id"]
                    exists = (self.client.table("badges_usuario").select("id")
                              .eq("perfil_id", uid).eq("badge_id", badge_id)
                              .limit(1).execute())
                    if not exists.data:
                        self.client.table("badges_usuario").insert({
                            "perfil_id": uid, "badge_id": badge_id,
                        }).execute()
                        return True
                return False
            except Exception as e:
                logger.error(f"unlock_achievement: {e}")
        achs = self._mock()["achievements"]
        if any(a.get("achievement_name") == name and a.get("user_id") == uid
               for a in achs):
            return False
        achs.append({
            "user_id": uid, "achievement_name": name,
            "title": title, "unlocked_at": date.today().isoformat(),
        })
        return True

    def get_achievements(self) -> List[dict]:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = (self.client.table("vw_conquistas_usuario")
                     .select("badge, categoria, conquistado_em")
                     .eq("perfil_id", uid).execute())
                return [
                    {"achievement_name": x.get("badge", ""),
                     "title": x.get("badge", ""),
                     "unlocked_at": x.get("conquistado_em", "")}
                    for x in (r.data or [])
                ]
            except Exception as e:
                logger.error(f"get_achievements: {e}")
        return [a for a in self._mock()["achievements"] if a.get("user_id") == uid]

    # ── SUPLEMENTOS (mock na V1) ───────────────────────────────────────────────
    def save_supplement(self, s: Supplement) -> bool:
        s.user_id = self.uid()
        self._mock()["supplements"].append(s.to_dict())
        return True

    def get_supplements(self, days: int = 7) -> List[Supplement]:
        uid  = self.uid()
        data = self._filter_user(self._mock()["supplements"], uid)
        data = self._filter_days(data, days)
        return [self._make_model(Supplement, r) for r in data]

    def get_supplements_today(self) -> List[Supplement]:
        today = date.today().isoformat()
        return [s for s in self.get_supplements(1) if s.log_date == today]

    # ── TREINO (mock na V1) ───────────────────────────────────────────────────
    def save_workout(self, w: WorkoutLog) -> bool:
        w.user_id = self.uid()
        self._mock()["workouts"].append(w.to_dict())
        return True

    def get_workout_today(self) -> Optional[WorkoutLog]:
        uid   = self.uid()
        today = date.today().isoformat()
        for w in reversed(self._mock()["workouts"]):
            if w.get("user_id") == uid and w.get("log_date") == today:
                return self._make_model(WorkoutLog, w)
        return None

    def get_workouts(self, days: int = 30) -> List[WorkoutLog]:
        uid  = self.uid()
        data = self._filter_user(self._mock()["workouts"], uid)
        data = self._filter_days(data, days)
        return [self._make_model(WorkoutLog, r) for r in data]

    # ── SINTOMAS (mock na V1) ─────────────────────────────────────────────────
    def save_symptom(self, s: SymptomLog) -> bool:
        s.user_id = self.uid()
        self._mock()["symptoms"].append(s.to_dict())
        return True

    def get_symptoms(self, days: int = 7) -> List[SymptomLog]:
        uid  = self.uid()
        data = self._filter_user(self._mock()["symptoms"], uid)
        data = self._filter_days(data, days)
        return [self._make_model(SymptomLog, r) for r in data]

    def consecutive_severe_symptom_days(self) -> int:
        logs = self.get_symptoms(14)
        if not logs:
            return 0
        dates_severe = sorted(
            set(s.log_date for s in logs if s.has_severe()), reverse=True
        )
        if not dates_severe:
            return 0
        count = 1
        for i in range(1, len(dates_severe)):
            d1 = datetime.strptime(dates_severe[i - 1], "%Y-%m-%d").date()
            d2 = datetime.strptime(dates_severe[i],     "%Y-%m-%d").date()
            if (d1 - d2).days == 1:
                count += 1
            else:
                break
        return count

    # ── SONO + CICLO (mock na V1) ─────────────────────────────────────────────
    def save_sleep(self, s: SleepLog) -> bool:
        s.user_id = self.uid()
        self._mock()["sleep"].append(s.to_dict())
        return True

    def get_sleep_today(self) -> Optional[SleepLog]:
        uid   = self.uid()
        today = date.today().isoformat()
        for s in reversed(self._mock()["sleep"]):
            if s.get("user_id") == uid and s.get("log_date") == today:
                return self._make_model(SleepLog, s)
        return None

    def get_sleep_logs(self, days: int = 7) -> List[SleepLog]:
        uid  = self.uid()
        data = self._filter_user(self._mock()["sleep"], uid)
        data = self._filter_days(data, days)
        return [self._make_model(SleepLog, r) for r in data]

    def save_cycle(self, c: CycleLog) -> bool:
        c.user_id = self.uid()
        self._mock()["cycles"].append(c.to_dict())
        return True

    def get_cycle_today(self) -> Optional[CycleLog]:
        uid   = self.uid()
        today = date.today().isoformat()
        for c in reversed(self._mock()["cycles"]):
            if c.get("user_id") == uid and c.get("log_date") == today:
                return self._make_model(CycleLog, c)
        return None

    # ── PAINEL PROFISSIONAL ───────────────────────────────────────────────────
    def get_patients_of_professional(self, professional_email: str) -> List[dict]:
        if self.is_real and self.client:
            try:
                r = (self.client.table("perfis")
                     .select("id, nome_completo, tipo_jornada, peso_atual, criado_em")
                     .eq("profissional_id", professional_email).execute())
                return r.data or []
            except Exception as e:
                logger.error(f"get_patients: {e}")
        return [u for u in self._mock()["users"].values()
                if u.get("professional_id") == professional_email]

    def get_patient_summary(self, patient_email: str) -> dict:
        today   = date.today().isoformat()
        meals   = [m for m in self._mock()["meals"]
                   if m.get("user_id") == patient_email]
        weights = [w for w in self._mock()["weights"]
                   if w.get("user_id") == patient_email]
        m_today = [m for m in meals if m.get("meal_date") == today]
        last_w  = weights[-1]["weight"]  if weights else None
        first_w = weights[0]["weight"]   if weights else None
        w_diff  = round(last_w - first_w, 1) if (last_w and first_w) else None
        all_dates = sorted(
            set(m.get("meal_date", "") for m in meals), reverse=True
        )
        gap_days = 0
        if all_dates:
            try:
                last_date = datetime.strptime(all_dates[0], "%Y-%m-%d").date()
                gap_days  = (date.today() - last_date).days
            except Exception:
                pass
        return {
            "cal_today":  sum(m.get("calories", 0) for m in m_today),
            "prot_today": round(sum(m.get("protein", 0) for m in m_today), 1),
            "last_weight": last_w, "weight_diff": w_diff,
            "days_logged": len(set(m.get("meal_date") for m in meals)),
            "total_meals": len(meals), "gap_days": gap_days,
        }

    # ── EXPORTAÇÃO ────────────────────────────────────────────────────────────
    def export_meals_csv(self) -> str:
        meals = self.get_meals(365)
        if not meals:
            return "data,horario,alimento,calorias,proteinas,carbos,gorduras,fibras,humor\n"
        header = "data,horario,alimento,calorias,proteinas,carbos,gorduras,fibras,humor"
        rows = [
            f"{m.meal_date},{m.meal_time},{m.food},{m.calories},"
            f"{m.protein},{m.carbs},{m.fat},{m.fiber},{m.mood}"
            for m in meals
        ]
        return header + "\n" + "\n".join(rows)

    def export_weights_csv(self) -> str:
        df = self.get_weights(365)
        if df.empty:
            return "data,peso,gordura_pct,massa_muscular_kg,notas\n"
        cols = [c for c in ["log_date", "weight", "body_fat", "muscle_mass", "notes"]
                if c in df.columns]
        return df[cols].to_csv(index=False)
