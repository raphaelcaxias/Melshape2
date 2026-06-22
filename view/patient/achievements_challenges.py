"""
Melshape — Desafios com progresso real.

Tabelas: desafios, desafios_usuario
Fallback: lista semanal do GamificationService quando banco vazio.
"""
import streamlit as st
from datetime import date, timedelta

from services.gamification_service import GamificationService
from views.components.cards import empty_state, xp_toast, show_new_achievements


def render_desafios(db, gami: GamificationService) -> None:
    desafios_db = _buscar_desafios(db)
    if desafios_db:
        _render_desafios_banco(db, gami, desafios_db)
    else:
        _render_desafios_fallback(db, gami)


# ── DESAFIOS DO BANCO ─────────────────────────────────────────────────────────
def _render_desafios_banco(db, gami, desafios: list) -> None:
    uid            = db.uid()
    concluidos_db  = _buscar_progresso_usuario(db, uid)
    concluidos_ids = {d.get("desafio_id") for d in concluidos_db
                      if d.get("concluido")}
    ativos         = [d for d in desafios if not d.get("encerrado")]

    st.markdown(
        f'<div style="font-size:0.82rem;color:var(--text-muted);'
        f'margin-bottom:0.8rem;">'
        f'<b>{len(ativos)}</b> desafio(s) ativo(s) · '
        f'<b>{len(concluidos_ids)}</b> concluído(s)</div>',
        unsafe_allow_html=True,
    )

    if not ativos:
        empty_state("🎯", "Nenhum desafio ativo", "Novos desafios em breve!")
        return

    for d in ativos:
        did       = d.get("id", "")
        titulo    = d.get("titulo", "Desafio")
        descricao = d.get("descricao", "")
        xp_val    = int(d.get("xp_recompensa") or 0)
        concluido = did in concluidos_ids
        dias_rest = _dias_restantes(d.get("data_fim", ""))
        cor       = "var(--success)" if concluido else "var(--border)"
        icon      = "✅" if concluido else "🎯"
        xp_html   = f'<span class="xp-badge">+{xp_val} XP</span>' if xp_val else ""
        prazo_html = (
            f'<div style="font-size:0.72rem;color:var(--text-faint);">'
            f'{dias_rest}d restantes</div>'
            if dias_rest is not None else ""
        )

        st.markdown(
            f'<div class="metric-card fade-in" style="margin-bottom:0.6rem;'
            f'border-color:{cor};">'
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:flex-start;">'
            f'<div style="display:flex;gap:0.6rem;">'
            f'<span style="font-size:1.3rem;">{icon}</span>'
            f'<div><div style="font-weight:700;font-size:0.92rem;'
            f'color:var(--text);">{titulo}</div>'
            f'{"<div style=font-size:0.78rem;color:var(--text-muted);>" + descricao + "</div>" if descricao else ""}'
            f'</div></div>'
            f'<div style="text-align:right;">{xp_html}{prazo_html}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        if not concluido:
            if st.button("✅ Marcar concluído", key=f"ch_{did}",
                         use_container_width=True):
                _concluir_desafio(db, gami, did, xp_val, uid)


def _concluir_desafio(db, gami, did: str, xp_val: int, uid: str) -> None:
    ok = False
    if db.is_real and db.client:
        try:
            db.client.table("desafios_usuario").upsert({
                "desafio_id": did, "perfil_id": uid,
                "concluido": True,
                "concluido_em": date.today().isoformat(),
            }, on_conflict="desafio_id,perfil_id").execute()
            ok = True
        except Exception as e:
            import logging
            logging.getLogger("Melshape").warning(f"desafio: {e}")
    else:
        ok = True
    if ok:
        db.add_xp(xp_val, motivo=f"desafio_{did[:8]}")
        st.toast(f"🎯 +{xp_val} XP!", icon="🎉")
        xp_toast(xp_val, "desafio concluído")
        st.rerun()


# ── FALLBACK SEMANAL ──────────────────────────────────────────────────────────
def _render_desafios_fallback(db, gami: GamificationService) -> None:
    st.markdown(
        '<div style="font-size:0.80rem;color:var(--text-muted);'
        'margin-bottom:0.8rem;">🎯 Desafios desta semana</div>',
        unsafe_allow_html=True,
    )
    desafios   = gami.weekly_challenges()
    concluidos = st.session_state.get("desafios_concluidos_local", set())

    if not desafios:
        empty_state("🎯", "Sem desafios esta semana")
        return

    for i, d in enumerate(desafios):
        emoji     = d.get("emoji", "🎯")
        titulo    = d.get("title", "")
        xp_val    = d.get("xp", 0)
        key       = f"ch_local_{i}"
        concluido = key in concluidos
        cor       = "var(--success)" if concluido else "var(--border)"

        st.markdown(
            f'<div class="metric-card fade-in" style="margin-bottom:0.5rem;'
            f'border-color:{cor};">'
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;">'
            f'<span style="font-size:0.90rem;font-weight:600;'
            f'color:var(--text);">{emoji} {titulo}</span>'
            f'<span class="xp-badge">+{xp_val} XP</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        if not concluido:
            if st.button("✅ Concluído", key=f"ch_fb_{i}",
                         use_container_width=True):
                concluidos.add(key)
                st.session_state["desafios_concluidos_local"] = concluidos
                db.add_xp(xp_val, motivo="desafio_semanal")
                st.toast(f"{emoji} +{xp_val} XP!", icon="🎉")
                xp_toast(xp_val, "desafio")
                novos = gami.check_achievements()
                show_new_achievements(novos)
                st.rerun()
        else:
            st.markdown(
                '<div style="font-size:0.76rem;color:var(--success);">✅ Concluído</div>',
                unsafe_allow_html=True,
            )

    hoje      = date.today()
    prox_seg  = hoje + timedelta(days=(7 - hoje.weekday()))
    st.markdown(
        f'<div style="font-size:0.74rem;color:var(--text-faint);'
        f'margin-top:0.5rem;text-align:center;">'
        f'🔄 Reset em {(prox_seg - hoje).days} dia(s)</div>',
        unsafe_allow_html=True,
    )


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _buscar_desafios(db) -> list:
    if db.is_real and db.client:
        try:
            r = (db.client.table("desafios")
                 .select("id,titulo,descricao,xp_recompensa,data_fim,encerrado")
                 .eq("encerrado", False).limit(20).execute())
            return r.data or []
        except Exception:
            pass
    return []


def _buscar_progresso_usuario(db, uid: str) -> list:
    if db.is_real and db.client:
        try:
            r = (db.client.table("desafios_usuario")
                 .select("desafio_id,concluido")
                 .eq("perfil_id", uid).execute())
            return r.data or []
        except Exception:
            pass
    return []


def _dias_restantes(prazo: str) -> int | None:
    if not prazo:
        return None
    try:
        return max(0, (date.fromisoformat(prazo[:10]) - date.today()).days)
    except Exception:
        return None
