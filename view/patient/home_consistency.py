"""
Melshape — Home: bloco de consistência (streak + calendário).
Usa contextualizer — streak zero nunca é punição, sempre recomeço.
"""
import streamlit as st
from datetime import date, timedelta
from views.components.cards import alert
from services.contextualizer import ctx


def _bloco_consistencia(streak: int, checkin, db, gami, user: dict) -> None:
    st.markdown(
        '<p style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;'
        'color:var(--text-faint);text-transform:uppercase;margin-bottom:0.6rem;">'
        'Consistência</p>',
        unsafe_allow_html=True,
    )

    ci_hoje  = checkin is not None
    ci_emoji = "✅" if ci_hoje else "⬜"
    ci_label = "Check-in feito!" if ci_hoje else "Sem check-in hoje"
    cor_streak = (
        "success" if streak >= 7
        else "warning" if streak >= 3
        else ""
    )
    # Contextualizer transforma o número em narrativa
    msg_streak = ctx.streak(streak)

    hist = _historico_checkins(db, 7)
    # ⬜ em vez de ⚫ — neutro, não punitivo
    dots = "".join("🟢" if d else "⬜" for d in hist)

    c1, c2, c3 = st.columns([2, 1, 1])

    with c1:
        st.markdown(
            f'<div class="metric-card fade-in">'
            f'<div class="metric-value {cor_streak}" style="font-size:3rem;">'
            f'{streak}</div>'
            f'<div style="font-size:0.78rem;color:var(--text-muted);'
            f'margin-top:0.2rem;">{msg_streak}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card fade-in" style="text-align:center;">'
            f'<div style="font-size:2rem;">{ci_emoji}</div>'
            f'<div class="metric-label">{ci_label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="metric-card fade-in" style="text-align:center;">'
            f'<div style="font-size:1.1rem;letter-spacing:2px;">{dots}</div>'
            f'<div class="metric-label">Últimos 7 dias</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Mensagens — sempre encorajadores, nunca punitivos
    if streak >= 30:
        alert("🏆 30 dias seguidos! Você é lendário.", "success")
    elif streak >= 7:
        alert(f"🔥 {streak} dias seguidos! Continue assim.", "success")
    elif streak == 0 and not ci_hoje:
        # Protocolo de recaída — detectar e oferecer recomeço ativo
        try:
            from services.relapse_service import RelapseService
            svc_relapse = RelapseService(db)
            dados_recaida = svc_relapse.detectar(user)

            if dados_recaida:
                _bloco_recomeço(svc_relapse, dados_recaida, user)
            else:
                alert(
                    "Comece sua sequência hoje. Um check-in muda tudo.",
                    "info",
                )
        except Exception:
            alert(
                "Comece sua sequência hoje. Um check-in muda tudo.",
                "info",
            )


def _historico_checkins(db, days: int = 7) -> list:
    """Retorna lista bool dos últimos N dias (True = fez check-in)."""
    today = date.today()
    datas = [
        (today - timedelta(days=i)).isoformat()
        for i in range(days - 1, -1, -1)
    ]
    feitos: set = set()

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
            if c.get("user_id") == db.uid()
            and c.get("log_date") in datas
        }
    return [d in feitos for d in datas]


def _bloco_recomeço(svc_relapse, dados: dict, user: dict) -> None:
    """Bloco de recomeço ativo — nunca punitivo."""
    melhor = dados.get("melhor_streak", 0)
    dias   = dados.get("dias_ausente",  0)
    xp     = dados.get("xp_recomeço",  25)

    st.markdown(
        f'<div class="metric-card fade-in" style="'
        f'border-left:4px solid var(--primary);">'
        f'<div style="font-size:1.5rem;margin-bottom:0.4rem;">🌱</div>'
        f'<div style="font-weight:700;font-size:0.95rem;color:var(--text);">'
        f'Sua sequência anterior de {melhor} dias prova que você consegue.'
        f'</div>'
        f'<div style="font-size:0.82rem;color:var(--text-muted);'
        f'margin-top:0.3rem;">'
        f'Hoje é dia 1 de algo ainda maior. '
        f'Recomeçar também vale +{xp} XP.</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Mostrar motivo da jornada se existir
    motivo = svc_relapse.get_motivo_para_lembrar(user)
    if motivo:
        st.markdown(
            f'<div style="background:var(--primary-light);'
            f'border:1px solid var(--primary-border);'
            f'border-radius:var(--radius-md);padding:0.8rem 1rem;'
            f'margin:0.5rem 0;font-size:0.86rem;color:var(--text);">'
            f'💛 Lembre-se: "{motivo}"'
            f'</div>',
            unsafe_allow_html=True,
        )

    if st.button(
        "🌱 Recomeçar minha jornada — +{} XP".format(xp),
        type="primary",
        use_container_width=True,
        key="recomeço_cta",
    ):
        svc_relapse.registrar_recomeço(user, dados)
        st.toast(
            f"🌱 Bem-vindo de volta! +{xp} XP pelo recomeço.",
            icon="🔥",
        )
        st.session_state.page = "checkin"
        st.rerun()
