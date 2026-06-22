"""
Melshape — Inbox de Notificações In-App.

Exibido no topo da home após login.
Também usado no dashboard profissional para ver pacientes em risco.
"""
import streamlit as st
from services.notification_service import NotificationService


_TIPO_ICON = {
    "streak_risco":   "🔥",
    "meta_proxima":   "🎯",
    "habito_pendente":"📋",
    "jornada_avanco": "🗺️",
    "risco_abandono": "😔",
    "sem_checkin":    "⚡",
    "engajamento":    "✅",
}

_TIPO_KIND = {
    "streak_risco":   "warning",
    "meta_proxima":   "info",
    "habito_pendente":"info",
    "jornada_avanco": "success",
    "risco_abandono": "error",
    "sem_checkin":    "warning",
    "engajamento":    "success",
}


def exibir_notificacoes(services: dict, user: dict) -> None:
    """
    Lê fila_notificacoes, exibe via st.toast() e marca como entregues.
    Também verifica risco de abandono em tempo real.
    Chamado na home a cada acesso.
    """
    db   = services["db"]
    svc  = NotificationService(db)

    # Verifica risco de abandono
    svc.verificar_risco_abandono(user)

    # Verifica condições para novas notificações contextuais
    svc.notificar_streak_em_risco(user)
    svc.notificar_meta_proxima(user)
    svc.notificar_habito_pendente(user)

    # Entrega pendentes via toast
    pendentes = svc.entregar_pendentes(user)
    for n in pendentes:
        tipo = n.get("tipo", "engajamento")
        icon = _TIPO_ICON.get(tipo, "💬")
        msg  = n.get("mensagem", "")
        if msg:
            st.toast(msg, icon=icon)


def render_inbox_panel(services: dict, user: dict) -> None:
    """
    Painel visual de notificações recentes (para a tela de perfil ou notificações).
    """
    db        = services["db"]
    historico = db.get_historico_notificacoes(days=7)
    pendentes = db.get_notificacoes_pendentes(limit=5)
    todas     = pendentes + historico

    if not todas:
        st.markdown(
            '<div style="font-size:0.84rem;color:var(--text-muted);">'
            '📭 Nenhuma notificação recente.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<div style="font-size:0.80rem;color:var(--text-muted);'
        f'margin-bottom:0.6rem;">'
        f'<b>{len(todas)}</b> notificação(ões) recentes</div>',
        unsafe_allow_html=True,
    )

    for n in todas[:8]:
        tipo     = n.get("tipo", "engajamento")
        icon     = _TIPO_ICON.get(tipo, "💬")
        kind_css = _KIND_CSS.get(_TIPO_KIND.get(tipo, "info"), "")
        msg      = n.get("mensagem", "")
        data     = n.get("criado_em", "")[:10] if n.get("criado_em") else ""

        st.markdown(
            f'<div style="display:flex;gap:0.6rem;align-items:flex-start;'
            f'padding:0.5rem 0;border-bottom:1px solid var(--border-subtle);">'
            f'<span style="font-size:1.1rem;flex-shrink:0;">{icon}</span>'
            f'<div style="flex:1;">'
            f'<div style="font-size:0.84rem;color:var(--text);">{msg}</div>'
            f'<div style="font-size:0.72rem;color:var(--text-faint);">{data}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )


_KIND_CSS = {
    "warning": "color:var(--warning);",
    "error":   "color:var(--error);",
    "success": "color:var(--success);",
    "info":    "color:var(--info);",
}


def render_pacientes_risco_pro(services: dict) -> None:
    """
    Painel de pacientes em risco para o profissional.
    Usa vw_pacientes_para_notificar.
    """
    db  = services["db"]
    svc = NotificationService(db)
    lst = svc.pacientes_para_notificar()

    if not lst:
        st.markdown(
            '<div style="font-size:0.84rem;color:var(--success);">'
            '✅ Nenhum paciente em risco de abandono no momento.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<div style="font-size:0.82rem;color:var(--text-muted);'
        f'margin-bottom:0.6rem;">'
        f'⚠️ <b>{len(lst)}</b> paciente(s) precisam de atenção</div>',
        unsafe_allow_html=True,
    )

    _MOTIVO_LABEL = {
        "RISCO_ABANDONO": ("🚨", "error",   "Risco de abandono"),
        "SEM_CHECKIN":    ("⚡", "warning", "Sem check-in"),
        "ACOMPANHAMENTO": ("📋", "info",    "Acompanhamento"),
    }

    for p in lst:
        nome    = p.get("nome_completo", "—")
        motivo  = p.get("motivo", "ACOMPANHAMENTO")
        dias_ci = p.get("dias_sem_checkin", 0)
        dias_ac = p.get("dias_sem_acesso", 0)
        icon, kind, label = _MOTIVO_LABEL.get(
            motivo, ("📋", "info", motivo)
        )
        cor = {
            "error":   "var(--error)",
            "warning": "var(--warning)",
            "info":    "var(--info)",
        }.get(kind, "var(--text-muted)")

        st.markdown(
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;padding:0.55rem 0.8rem;'
            f'border:1px solid var(--border);border-radius:var(--radius-md);'
            f'margin-bottom:0.4rem;background:var(--surface);">'
            f'<div>'
            f'<div style="font-weight:600;font-size:0.90rem;'
            f'color:var(--text);">{icon} {nome}</div>'
            f'<div style="font-size:0.74rem;color:var(--text-muted);">'
            f'{dias_ci}d sem check-in · {dias_ac}d sem acesso</div>'
            f'</div>'
            f'<span style="font-size:0.76rem;font-weight:700;'
            f'color:{cor};">{label}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
