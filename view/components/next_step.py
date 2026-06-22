"""
Melshape — Componente "Próximo Passo".

Responde em todas as telas:
1. O que faço agora? (ação principal)
2. O que ganho se continuar? (próxima conquista)
3. Quem me acompanha? (profissional)

Prioridade: check-in > hábito pendente > contexto pilar > jornada > água
Injetado no topo de qualquer tela do paciente via render_next_step(services, user).
"""
import streamlit as st
from typing import Optional, Dict, Any

from services.gamification_service import GamificationService, ACHIEVEMENTS


def render_next_step(services: dict, user: dict) -> None:
    """
    Renderiza o card de próximo passo.
    Chamado no início do render() de cada tela do paciente.
    """
    db   = services["db"]
    gami = services.get("gamification") or GamificationService(db)

    checkin    = db.get_checkin_today()
    streak     = db.get_checkin_streak()
    hydration  = db.get_hydration_today()
    hm         = user.get("health_mode", "general")
    profissional = user.get("professional_name") or user.get("professional_id")

    acao  = _decidir_acao(db, user, checkin, streak, hydration, hm)
    marco = _proximo_marco(db, gami, user)

    _render_card(acao, marco, profissional)


# ── DECISÃO DA AÇÃO ───────────────────────────────────────────────────────────
def _decidir_acao(db, user: dict, checkin, streak: int,
                  hydration: int, hm: str) -> Dict[str, Any]:

    # 1. Check-in pendente — prioridade máxima
    if not checkin:
        return {
            "texto":    "Faça seu check-in de hoje (30 segundos)",
            "icone":    "✅",
            "pagina":   "checkin",
            "hub_tipo": None,
            "urgencia": "alta",
        }

    # 2. Hábito pendente
    habitos  = db.get_habitos()
    feitos   = db.get_registros_hoje()
    pendentes = [h for h in habitos if h.get("id") not in feitos]
    if pendentes:
        h = pendentes[0]
        return {
            "texto":    f"Complete seu hábito: {h.get('nome','')}",
            "icone":    h.get("icone", "📋"),
            "pagina":   "habits",
            "hub_tipo": None,
            "urgencia": "media",
        }

    # 3. Contexto por pilar
    if hm == "glp1":
        acao = _acao_glp1(db, user)
        if acao:
            return acao

    if hm == "bariatric":
        acao = _acao_bariatric(user)
        if acao:
            return acao

    if hm == "fitness":
        treino = db.get_workout_today()
        if not treino:
            return {
                "texto":    "Registre seu treino de hoje",
                "icone":    "🏋️",
                "pagina":   "habits",
                "hub_tipo": None,
                "urgencia": "media",
            }

    # 4. Água abaixo de 1,5L
    if hydration < 1500:
        return {
            "texto":    f"Beba mais {2000 - hydration:.0f}ml de água para atingir a meta",
            "icone":    "💧",
            "pagina":   "meals",
            "hub_tipo": "hydration",
            "urgencia": "baixa",
        }

    # 5. Streak abaixo de 7
    if streak < 7:
        faltam = 7 - streak
        return {
            "texto":    f"Mais {faltam} dia(s) para completar 7 dias seguidos!",
            "icone":    "🔥",
            "pagina":   None,
            "hub_tipo": None,
            "urgencia": "ok",
        }

    # 6. Tudo em dia
    return {
        "texto":    f"🔥 {streak} dias seguidos! Continue assim.",
        "icone":    "⭐",
        "pagina":   None,
        "hub_tipo": None,
        "urgencia": "ok",
    }


def _acao_glp1(db, user: dict) -> Optional[Dict[str, Any]]:
    try:
        from services.glp1_service import GLP1Service
        prox = GLP1Service(db).proxima_dose(
            user.get("glp1_medication", "")
        )
        if prox and prox.lower() in ("hoje", "amanhã"):
            return {
                "texto":    f"Próxima dose GLP-1: {prox}",
                "icone":    "💉",
                "pagina":   "glp1",
                "hub_tipo": None,
                "urgencia": "media",
            }
    except Exception:
        pass
    return None


def _acao_bariatric(user: dict) -> Optional[Dict[str, Any]]:
    try:
        from config import BARIATRIC_PHASES
        fase_key = user.get("bariatric_phase", "liquid")
        fd = BARIATRIC_PHASES.get(fase_key, {})
        if fd:
            return {
                "texto": (
                    f"Fase {fd.get('name','')} — "
                    f"máx {fd.get('max_ml','')}ml por refeição"
                ),
                "icone":    "🔪",
                "pagina":   "bariatric",
                "hub_tipo": None,
                "urgencia": "baixa",
            }
    except Exception:
        pass
    return None


# ── PRÓXIMO MARCO ─────────────────────────────────────────────────────────────
def _proximo_marco(db, gami, user: dict) -> Optional[Dict[str, str]]:
    # 1. Próxima conquista de gamificação
    try:
        conquistadas = {
            a.get("achievement_name") for a in db.get_achievements()
        }
        for a in ACHIEVEMENTS:
            if a["name"] not in conquistadas:
                return {"titulo": a["title"], "descricao": a["desc"]}
    except Exception:
        pass

    # 2. Próxima etapa da jornada
    try:
        jornada = db.get_jornada_ativa()
        if jornada:
            from services.journey_service import JourneyService
            hm   = user.get("health_mode", "general")
            prog = JourneyService(db).progresso_jornada(jornada["id"], hm)
            prox = prog.get("etapa_seguinte")
            if prox:
                return {
                    "titulo":   prox.get("nome", ""),
                    "descricao": prox.get("descricao", ""),
                }
    except Exception:
        pass

    return {"titulo": "Continue consistente", "descricao": "Cada dia conta"}



def _render_card(acao: dict, marco, profissional) -> None:
    """Renderiza o card de próximo passo."""
    import streamlit as st
    _COR = {
        "alta":  "var(--error)",
        "media": "var(--warning)",
        "baixa": "var(--info)",
        "ok":    "var(--success)",
    }
    cor = _COR.get(acao.get("urgencia", "ok"), "var(--border)")

    marco_html = ""
    if marco:
        marco_html = (
            f'<span style="font-size:0.74rem;color:var(--primary);'
            f'background:var(--primary-light);padding:0.15rem 0.6rem;'
            f'border-radius:9999px;border:1px solid var(--primary-border);'
            f'white-space:nowrap;">→ {marco["titulo"]}</span>'
        )

    pro_html = ""
    if profissional:
        pro_html = (
            f'<span style="font-size:0.76rem;color:var(--text-muted);">'
            f'👤 {profissional}</span>'
        )

    st.markdown(
        f'<div class="fade-in" style="background:var(--surface-2);'
        f'border-radius:var(--radius-lg);padding:0.75rem 1rem;'
        f'margin-bottom:1rem;border:1px solid var(--border);'
        f'border-left:4px solid {cor};">'
        f'<div style="display:flex;align-items:center;'
        f'justify-content:space-between;flex-wrap:wrap;gap:0.5rem;">'
        f'<div style="display:flex;align-items:center;gap:0.6rem;">'
        f'<span style="font-size:1.4rem;">{acao["icone"]}</span>'
        f'<div>'
        f'<div style="font-size:0.70rem;color:var(--text-faint);'
        f'font-weight:700;text-transform:uppercase;letter-spacing:0.06em;">'
        f'Próximo passo</div>'
        f'<div style="font-weight:700;font-size:0.92rem;color:var(--text);">'
        f'{acao["texto"]}</div>'
        f'</div></div>'
        f'<div style="display:flex;align-items:center;gap:0.6rem;'
        f'flex-wrap:wrap;">{pro_html}{marco_html}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    if acao.get("pagina"):
        if st.button(
            f'{acao["icone"]} Fazer agora',
            type="primary",
            use_container_width=True,
            key="next_step_cta",
        ):
            st.session_state.page = acao["pagina"]
            if acao.get("hub_tipo"):
                st.session_state.hub_tipo = acao["hub_tipo"]
            st.rerun()
