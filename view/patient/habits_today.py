"""Melshape — Hábitos: tab de hoje e detalhe."""
import streamlit as st
from services.habit_service import HabitService
from views.components.cards import empty_state, show_new_achievements
from views.patient.habits_detail import render_detalhe_habito

# ── TAB HOJE ──────────────────────────────────────────────────────────────────
def _tab_hoje(habitos: list, feitos_hoje: set,
              svc: HabitService, gami, user: dict) -> None:
    if not habitos:
        empty_state(
            "📋", "Nenhum hábito criado",
            "Vá em 'Novo Hábito' para começar"
        )
        return

    for h in habitos:
        hid     = h.get("id", "")
        nome    = h.get("nome", "")
        icone   = h.get("icone", "⭐")
        cat_key = h.get("categoria", "geral")
        _, cat_label = _CATEGORIAS.get(cat_key, ("⭐", "Geral"))
        feito   = hid in feitos_hoje
        streak  = svc.streak_habito(hid)
        ader    = svc.aderencia(hid, days=7)

        # Calendário compacto (7 dias)
        cal     = svc.calendario(hid, days=7)
        dots    = "".join(
            "🟢" if d["concluido"] else "⚫" for d in cal
        )

        cor_card = (
            "border-color:var(--success);"
            if feito else ""
        )

        st.markdown(
            f'<div class="metric-card fade-in" '
            f'style="margin-bottom:0.6rem;{cor_card}">'
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:flex-start;">'
            f'<div style="display:flex;align-items:center;gap:0.6rem;">'
            f'<span style="font-size:1.5rem;">{icone}</span>'
            f'<div>'
            f'<div style="font-weight:700;font-size:0.95rem;color:var(--text);">'
            f'{nome}</div>'
            f'<div style="font-size:0.74rem;color:var(--text-muted);">'
            f'{cat_label} · {streak}d seguidos · {ader:.0f}% (7d)</div>'
            f'</div></div>'
            f'<div style="font-size:0.85rem;letter-spacing:1px;">{dots}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        col_btn, col_arch = st.columns([4, 1])
        with col_btn:
            if feito:
                st.button(
                    "✅ Concluído",
                    key=f"h_done_{hid}",
                    disabled=True,
                    use_container_width=True,
                )
            else:
                if st.button(
                    f"Marcar {nome[:20]}",
                    key=f"h_reg_{hid}",
                    type="primary",
                    use_container_width=True,
                ):
                    resultado = svc.registrar(hid)
                    if resultado["ok"]:
                        st.toast(
                            f"{icone} {nome} concluído! "
                            f"+{resultado['xp_ganho']} XP",
                            icon="✅",
                        )
                        if resultado["bonus_msg"]:
                            st.toast(resultado["bonus_msg"], icon="🎉")
                        novos = gami.check_achievements(user)
                        show_new_achievements(novos)
                        st.rerun()
                    else:
                        st.toast("Erro ao registrar.", icon="❌")
        with col_arch:
            if st.button("🗄️", key=f"h_arch_{hid}",
                         help="Arquivar hábito"):
                db_ref = svc.db
                db_ref.arquivar_habito(hid)
                st.toast(f"Hábito arquivado.", icon="🗄️")
                st.rerun()


# ── TAB DETALHE ───────────────────────────────────────────────────────────────
def _tab_detalhe(habitos: list, svc: HabitService) -> None:
    if not habitos:
        empty_state("📈", "Sem hábitos para analisar")
        return
    nomes = [f"{h.get('icone','')} {h.get('nome','')}" for h in habitos]
    idx   = st.selectbox(
        "Selecione o hábito",
        range(len(nomes)),
        format_func=lambda i: nomes[i],
        key="habit_detail_sel",
        label_visibility="collapsed",
    )
    render_detalhe_habito(habitos[idx], svc)


def _melhor_streak_geral(svc: HabitService, habitos: list) -> int:
    if not habitos:
        return 0
    return max((svc.streak_habito(h["id"]) for h in habitos), default=0)
