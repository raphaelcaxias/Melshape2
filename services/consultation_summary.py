"""
Melshape — Resumo Pré-Consulta.

Gera um resumo completo dos últimos 30 dias do paciente
para o profissional usar antes da consulta.

Formato: texto estruturado (exibido na tela) + PDF opcional.
Elimina 30 minutos de trabalho do profissional por consulta.
"""
import logging
from datetime import date, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger("Melshape.ConsultationSummary")


class ConsultationSummaryService:

    def __init__(self, db):
        self.db = db

    def gerar(self, perfil_id: str,
              dias: int = 30) -> Dict[str, Any]:
        """
        Gera resumo completo dos últimos N dias do paciente.
        Retorna dicionário estruturado pronto para exibição ou PDF.
        """
        cutoff = (date.today() - timedelta(days=dias)).isoformat()

        perfil       = self._get_perfil(perfil_id)
        peso         = self._get_evolucao_peso(perfil_id, cutoff)
        nutricao     = self._get_media_nutricao(perfil_id, cutoff)
        habitos      = self._get_aderencia_habitos(perfil_id, cutoff)
        checkins     = self._get_checkins(perfil_id, cutoff)
        condutas     = self._get_condutas(perfil_id)
        metas        = self._get_metas(perfil_id)
        alertas      = self._get_alertas(perfil_id)
        xp           = self._get_xp_periodo(perfil_id, cutoff)

        return {
            "perfil":       perfil,
            "periodo":      {"dias": dias, "de": cutoff,
                             "ate": date.today().isoformat()},
            "peso":         peso,
            "nutricao":     nutricao,
            "habitos":      habitos,
            "checkins":     checkins,
            "condutas":     condutas,
            "metas":        metas,
            "alertas":      alertas,
            "xp":           xp,
            "gerado_em":    date.today().isoformat(),
        }

    # ── DADOS DO PACIENTE ─────────────────────────────────────────────────────
    def _get_perfil(self, perfil_id: str) -> Dict[str, Any]:
        if not (self.db.is_real and self.db.client):
            return {}
        try:
            r = (self.db.client.table("perfis")
                 .select(
                     "nome_completo, email, tipo_jornada, "
                     "peso_atual, peso_meta, altura, idade, genero"
                 )
                 .eq("id", perfil_id)
                 .limit(1)
                 .execute())
            return r.data[0] if r.data else {}
        except Exception as e:
            logger.warning(f"_get_perfil: {e}")
        return {}

    # ── EVOLUÇÃO DE PESO ──────────────────────────────────────────────────────
    def _get_evolucao_peso(self, perfil_id: str,
                            cutoff: str) -> Dict[str, Any]:
        if not (self.db.is_real and self.db.client):
            return {}
        try:
            r = (self.db.client.table("pesagens")
                 .select("peso, data_pesagem")
                 .eq("perfil_id", perfil_id)
                 .gte("data_pesagem", cutoff)
                 .order("data_pesagem")
                 .execute())
            dados = r.data or []
            if not dados:
                return {"registros": 0}
            pesos   = [float(d["peso"]) for d in dados]
            inicial = pesos[0]
            atual   = pesos[-1]
            return {
                "registros":  len(dados),
                "inicial":    inicial,
                "atual":      atual,
                "variacao":   round(atual - inicial, 1),
                "minimo":     min(pesos),
                "maximo":     max(pesos),
                "historico":  dados[-5:],
            }
        except Exception as e:
            logger.warning(f"_get_evolucao_peso: {e}")
        return {"registros": 0}

    # ── MÉDIA NUTRICIONAL ─────────────────────────────────────────────────────
    def _get_media_nutricao(self, perfil_id: str,
                             cutoff: str) -> Dict[str, Any]:
        if not (self.db.is_real and self.db.client):
            return {}
        try:
            r = (self.db.client.table("registros_alimentares")
                 .select("calorias, proteina, carboidrato, gordura")
                 .eq("perfil_id", perfil_id)
                 .gte("data_registro", cutoff)
                 .execute())
            dados = r.data or []
            if not dados:
                return {"dias_registrados": 0}
            cal   = [float(d.get("calorias",  0)) for d in dados]
            prot  = [float(d.get("proteina",  0)) for d in dados]
            carb  = [float(d.get("carboidrato", 0)) for d in dados]
            fat   = [float(d.get("gordura",   0)) for d in dados]
            n     = len(dados)
            return {
                "dias_registrados": n,
                "media_calorias":   round(sum(cal)  / n, 0),
                "media_proteina":   round(sum(prot) / n, 1),
                "media_carbs":      round(sum(carb) / n, 1),
                "media_gordura":    round(sum(fat)  / n, 1),
            }
        except Exception as e:
            logger.warning(f"_get_media_nutricao: {e}")
        return {"dias_registrados": 0}

    # ── ADERÊNCIA AOS HÁBITOS ─────────────────────────────────────────────────
    def _get_aderencia_habitos(self, perfil_id: str,
                                cutoff: str) -> Dict[str, Any]:
        if not (self.db.is_real and self.db.client):
            return {}
        try:
            r_hab = (self.db.client.table("habitos")
                     .select("id, nome, icone")
                     .eq("perfil_id", perfil_id)
                     .eq("ativo", True)
                     .execute())
            habitos = r_hab.data or []
            if not habitos:
                return {"total": 0}

            import datetime as dt
            dias_periodo = (
                date.today() - dt.date.fromisoformat(cutoff)
            ).days or 1

            resultado = []
            for h in habitos:
                r_reg = (self.db.client.table("registros_habitos")
                         .select("id")
                         .eq("habito_id", h["id"])
                         .gte("data_registro", cutoff)
                         .execute())
                feitos = len(r_reg.data or [])
                resultado.append({
                    "nome":      h["nome"],
                    "icone":     h.get("icone", "⭐"),
                    "feitos":    feitos,
                    "possivel":  dias_periodo,
                    "aderencia": round(feitos / dias_periodo * 100, 0),
                })
            media = sum(h["aderencia"] for h in resultado) / len(resultado)
            return {"total": len(resultado), "habitos": resultado,
                    "media_aderencia": round(media, 0)}
        except Exception as e:
            logger.warning(f"_get_aderencia_habitos: {e}")
        return {"total": 0}

    # ── CHECK-INS ─────────────────────────────────────────────────────────────
    def _get_checkins(self, perfil_id: str,
                      cutoff: str) -> Dict[str, Any]:
        if not (self.db.is_real and self.db.client):
            return {}
        try:
            r = (self.db.client.table("checkins")
                 .select("data_checkin, humor, energia, qualidade_sono")
                 .eq("perfil_id", perfil_id)
                 .gte("data_checkin", cutoff)
                 .order("data_checkin", desc=True)
                 .execute())
            dados = r.data or []
            if not dados:
                return {"total": 0}
            humores  = [d["humor"]          for d in dados if d.get("humor")]
            energias = [d["energia"]         for d in dados if d.get("energia")]
            sonos    = [d["qualidade_sono"]  for d in dados if d.get("qualidade_sono")]
            return {
                "total":        len(dados),
                "humor_medio":  round(sum(humores)  / len(humores),  1) if humores  else 0,
                "energia_media":round(sum(energias) / len(energias), 1) if energias else 0,
                "sono_medio":   round(sum(sonos)    / len(sonos),    1) if sonos    else 0,
                "ultimo":       dados[0].get("data_checkin", "")[:10],
            }

    def _get_metas(self, perfil_id, cutoff=None):
        return _get_metas_impl(self, perfil_id)

    def _get_alertas(self, perfil_id, cutoff=None):
        return _get_alertas_impl(self, perfil_id)

    def _get_xp_periodo(self, perfil_id, cutoff):
        return _get_xp_impl(self, perfil_id, cutoff)

    def formatar_texto(self, resumo):
        return formatar_texto_impl(resumo)


# ── (consolidado de consultation_summary_b.py) ──
        p     = resumo.get("perfil", {})
        per   = resumo.get("periodo", {})
        peso  = resumo.get("peso", {})
        nutr  = resumo.get("nutricao", {})
        hab   = resumo.get("habitos", {})
        ci    = resumo.get("checkins", {})
        metas = resumo.get("metas", [])
        cond  = resumo.get("condutas", [])
        alert = resumo.get("alertas", [])
        xp    = resumo.get("xp", {})

        nome  = p.get("nome_completo", "Paciente")
        pilar = p.get("tipo_jornada", "—")

        linhas = [
            f"MELSHAPE — RESUMO PRÉ-CONSULTA",
            f"Paciente: {nome}  |  Pilar: {pilar}",
            f"Período: {per.get('de','')} a {per.get('ate','')}",
            f"Gerado em: {resumo.get('gerado_em','')}",
            "",
            "── PESO ──",
            f"Registros: {peso.get('registros', 0)}",
        ]
        if peso.get("variacao") is not None:
            sinal = "▲" if peso["variacao"] > 0 else "▼"
            linhas += [
                f"Inicial: {peso.get('inicial', '—')} kg  "
                f"→  Atual: {peso.get('atual', '—')} kg  "
                f"({sinal} {abs(peso['variacao'])} kg)",
            ]

        linhas += [
            "",
            "── NUTRIÇÃO (MÉDIA DO PERÍODO) ──",
            f"Dias com registro: {nutr.get('dias_registrados', 0)}",
            f"Calorias:  {nutr.get('media_calorias', '—')} kcal/dia",
            f"Proteína:  {nutr.get('media_proteina', '—')} g/dia",
            f"Carbs:     {nutr.get('media_carbs', '—')} g/dia",
            "",
            "── HÁBITOS ──",
            f"Aderência média: {hab.get('media_aderencia', '—')}%",
        ]
        for h in hab.get("habitos", []):
            linhas.append(
                f"  {h['icone']} {h['nome']}: {h['aderencia']:.0f}%"
            )

        linhas += [
            "",
            "── CHECK-INS ──",
            f"Total: {ci.get('total', 0)} check-ins",
            f"Humor médio: {ci.get('humor_medio', '—')}/5",
            f"Energia média: {ci.get('energia_media', '—')}/5",
            f"Sono médio: {ci.get('sono_medio', '—')}/5",
        ]

        if metas:
            linhas += ["", "── METAS ──"]
            for m in metas:
                status = "✅" if m.get("concluida") else "⏳"
                linhas.append(
                    f"  {status} {m.get('titulo','—')} "
                    f"({m.get('valor_atual','?')}/{m.get('valor_alvo','?')})"
                )

        if cond:
            linhas += ["", "── CONDUTAS ANTERIORES ──"]
            for c in cond:
                linhas.append(
                    f"  [{c.get('data_conduta','')[:10]}] "
                    f"{c.get('titulo','—')}"
                )

        if alert:
            linhas += ["", "── ALERTAS EM ABERTO ──"]
            for a in alert:
                linhas.append(
                    f"  ⚠️ [{a.get('gravidade','?')}] {a.get('titulo','—')}"
                )

        linhas += [
            "",
            f"── ENGAJAMENTO ──",
            f"XP ganho no período: {xp.get('total', 0)} pts",
            "",
            "─" * 40,
            "Melshape · melshape.com.br",
        ]
        return "\n".join(linhas)
