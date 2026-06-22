"""
Melshape — Serviço de email via Resend (3k/mês grátis).
Mock automático quando RESEND_API_KEY não configurado.

USO:
    from services.email_service import send_welcome, request_password_reset
"""
import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

import streamlit as st

logger = logging.getLogger("Melshape.Email")

# Tokens em memória (produção: tabela password_resets no Supabase)
_RESET_TOKENS: dict = {}


# ── CLIENTE ───────────────────────────────────────────────────────────────────
def _get_client():
    try:
        import resend
        key = st.secrets.get("RESEND_API_KEY", "")
        if not key:
            return None
        resend.api_key = key
        return resend
    except ImportError:
        return None


def _send(to: str, subject: str, html: str) -> bool:
    client = _get_client()
    if not client:
        logger.info(f"[MOCK EMAIL] Para: {to} | Assunto: {subject}")
        return True
    try:
        from_addr = st.secrets.get(
            "RESEND_FROM", "Melshape <noreply@melshape.com.br>"
        )
        client.Emails.send({"from": from_addr, "to": [to],
                             "subject": subject, "html": html})
        logger.info(f"Email enviado → {to}")
        return True
    except Exception as e:
        logger.error(f"Resend error ({to}): {e}")
        return False


# ── TEMPLATE BASE ─────────────────────────────────────────────────────────────
_BASE = """
<div style="font-family:'DM Sans',Arial,sans-serif;max-width:560px;margin:0 auto;
background:#fafaf8;border-radius:16px;overflow:hidden;border:1px solid #e8e0d0;">
  <div style="background:linear-gradient(135deg,#C9A84C,#a8862e,#3D5A73);
  padding:2rem;text-align:center;">
    <div style="font-size:2rem;">🔥</div>
    <div style="font-family:Sora,Arial,sans-serif;font-weight:800;
    font-size:1.4rem;color:white;">Melshape</div>
    <div style="font-size:0.8rem;color:rgba(255,255,255,0.85);">
    Para quem está mudando de verdade.</div>
  </div>
  <div style="padding:1.75rem 2rem;">{content}</div>
  <div style="background:#f1ebe0;padding:1rem 2rem;text-align:center;
  font-size:0.72rem;color:#94a3b8;">
    © 2025 Melshape ·
    <a href="https://melshape.com.br/privacidade"
    style="color:#C9A84C;">Privacidade</a> ·
    <a href="https://melshape.com.br/termos"
    style="color:#C9A84C;">Termos</a>
  </div>
</div>"""

_BTN = ('<a href="{url}" style="background:linear-gradient(135deg,#C9A84C,'
        '#a8862e);color:#1C1C1E;padding:0.75rem 2rem;border-radius:8px;'
        'text-decoration:none;font-weight:600;font-family:Sora,sans-serif;">'
        '{label}</a>')


def _wrap(content: str) -> str:
    return _BASE.format(content=content)


# ── EMAILS ────────────────────────────────────────────────────────────────────
def send_welcome(to: str, name: str, trial_days: int = 10) -> bool:
    content = f"""
    <h2 style="font-family:Sora,sans-serif;color:#1C1C1E;margin:0 0 .75rem;">
      Olá, {name}! 🎉</h2>
    <p style="color:#4a4a4a;line-height:1.6;">Bem-vindo ao <b>Melshape</b>!
    Você tem <b>{trial_days} dias de acesso Pro</b> — sem cartão.</p>
    <div style="background:#fffbeb;border:1px solid #fcd34d;border-left:4px
    solid #C9A84C;border-radius:8px;padding:1rem;margin:1rem 0;">
      <b style="color:#78350f;">⏳ Trial expira em {trial_days} dias.</b><br>
      <span style="font-size:.88rem;color:#92400e;">
      Registre refeições, monitore peso e configure seu perfil.</span>
    </div>
    <p style="color:#4a4a4a;line-height:1.6;"><b>3 coisas para fazer agora:</b><br>
    1️⃣ Complete o onboarding (2 min)<br>
    2️⃣ Registre sua primeira refeição<br>
    3️⃣ Configure seu modo de saúde</p>
    <div style="text-align:center;margin:1.5rem 0;">
      {_BTN.format(url="https://melshape.com.br",
                   label="Acessar o Melshape →")}
    </div>"""
    return _send(to, "🔥 Bem-vindo ao Melshape!", _wrap(content))


def send_password_reset(to: str, name: str, reset_url: str) -> bool:
    content = f"""
    <h2 style="font-family:Sora,sans-serif;color:#1C1C1E;margin:0 0 .75rem;">
      Redefinir senha</h2>
    <p style="color:#4a4a4a;line-height:1.6;">
      Olá, <b>{name}</b>! Recebemos uma solicitação de redefinição de senha.</p>
    <div style="text-align:center;margin:1.5rem 0;">
      {_BTN.format(url=reset_url, label="Redefinir minha senha →")}
    </div>
    <p style="color:#64748b;font-size:.85rem;text-align:center;">
      ⏰ Link expira em <b>15 minutos</b>.</p>
    <div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:8px;
    padding:.75rem;margin-top:1rem;">
      <span style="font-size:.82rem;color:#7f1d1d;">
      🔒 Se não foi você, ignore este email.</span>
    </div>"""
    return _send(to, "🔒 Redefinição de senha — Melshape", _wrap(content))


def send_meal_reminder(to: str, name: str, streak: int = 0) -> bool:
    streak_html = ""
    if streak >= 3:
        streak_html = (
            f'<div style="background:#fffbeb;border:1px solid #fcd34d;'
            f'border-radius:8px;padding:.65rem 1rem;margin:.75rem 0;'
            f'color:#92400e;font-size:.88rem;">'
            f'🔥 Sequência de <b>{streak} dias</b>! Não perca agora.</div>'
        )
    content = f"""
    <h2 style="font-family:Sora,sans-serif;color:#1C1C1E;margin:0 0 .75rem;">
      Oi, {name}! 👋</h2>
    <p style="color:#4a4a4a;line-height:1.6;">
      Você ainda não registrou refeições hoje.</p>
    {streak_html}
    <div style="text-align:center;margin:1.25rem 0;">
      {_BTN.format(url="https://melshape.com.br",
                   label="Registrar agora →")}
    </div>
    <p style="font-size:.78rem;color:#94a3b8;text-align:center;">
      Para cancelar: Perfil → Preferências.</p>"""
    return _send(to, "🍽️ Registre suas refeições hoje", _wrap(content))


def send_streak_at_risk(to: str, name: str, streak: int) -> bool:
    content = f"""
    <h2 style="font-family:Sora,sans-serif;color:#dc2626;margin:0 0 .75rem;">
      🔥 Sequência de {streak} dias em risco!</h2>
    <p style="color:#4a4a4a;line-height:1.6;">
      Olá, <b>{name}</b>! Registre hoje para manter sua sequência.</p>
    <div style="text-align:center;margin:1.5rem 0;">
      {_BTN.format(url="https://melshape.com.br",
                   label="Salvar minha sequência →")}
    </div>"""
    return _send(to, f"🔥 Sequência de {streak} dias em risco!", _wrap(content))


def send_trial_expiring(to: str, name: str, days_remaining: int) -> bool:
    cor = "#dc2626" if days_remaining <= 1 else "#f59e0b"
    content = f"""
    <h2 style="font-family:Sora,sans-serif;color:#1C1C1E;margin:0 0 .75rem;">
      Trial expira em {days_remaining} dia(s) ⏳</h2>
    <div style="background:{cor}10;border:2px solid {cor}40;border-radius:10px;
    padding:1rem;text-align:center;margin:1rem 0;">
      <span style="font-size:1.5rem;font-weight:700;color:{cor};">
      {days_remaining} dia(s) restante(s)</span>
    </div>
    <p style="color:#4a4a4a;line-height:1.6;">Olá, <b>{name}</b>!
    Assine o Pro por <b>R$19,90/mês</b> para continuar.</p>
    <div style="text-align:center;margin:1.5rem 0;">
      {_BTN.format(url="https://melshape.com.br",
                   label="Assinar o Melshape Pro →")}
    </div>"""
    return _send(to, f"⏰ Trial expira em {days_remaining} dia(s)", _wrap(content))


# ── TOKENS DE RESET ───────────────────────────────────────────────────────────
def _gen_token(length: int = 32) -> str:
    return "".join(
        secrets.choice(string.ascii_letters + string.digits)
        for _ in range(length)
    )


def request_password_reset(email: str, name: str,
                            base_url: str = "https://melshape.com.br") -> bool:
    token   = _gen_token()
    expires = datetime.utcnow() + timedelta(minutes=15)
    _RESET_TOKENS[email.lower()] = {
        "token": token, "expires_at": expires, "name": name
    }
    url = f"{base_url}/?reset_token={token}&email={email}"
    return send_password_reset(email, name, url)


def validate_reset_token(email: str, token: str) -> bool:
    rec = _RESET_TOKENS.get(email.lower())
    if not rec or rec["token"] != token:
        return False
    if datetime.utcnow() > rec["expires_at"]:
        _RESET_TOKENS.pop(email.lower(), None)
        return False
    return True


def consume_reset_token(email: str, token: str) -> bool:
    if validate_reset_token(email, token):
        _RESET_TOKENS.pop(email.lower(), None)
        return True
    return False
