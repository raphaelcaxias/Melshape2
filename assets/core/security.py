"""
Melshape — Segurança: hash de senha e validações.
Usa hashlib PBKDF2 — sem dependência externa.
"""
import hashlib
import hmac
import os
import re
from datetime import datetime
from typing import Tuple


_SALT_SIZE   = 32
_ITERATIONS  = 260_000
_HASH_ALGO   = "sha256"


def hash_password(password: str) -> str:
    """
    Gera hash seguro da senha com PBKDF2-HMAC-SHA256.
    Retorna string no formato: salt_hex:hash_hex
    """
    salt   = os.urandom(_SALT_SIZE)
    digest = hashlib.pbkdf2_hmac(
        _HASH_ALGO,
        password.encode("utf-8"),
        salt,
        _ITERATIONS,
    )
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifica se a senha confere com o hash armazenado.
    Usa comparação em tempo constante (hmac.compare_digest).
    """
    if not stored_hash or ":" not in stored_hash:
        return False
    try:
        salt_hex, hash_hex = stored_hash.split(":", 1)
        salt   = bytes.fromhex(salt_hex)
        digest = hashlib.pbkdf2_hmac(
            _HASH_ALGO,
            password.encode("utf-8"),
            salt,
            _ITERATIONS,
        )
        return hmac.compare_digest(digest.hex(), hash_hex)
    except Exception:
        return False


def validate_email(email: str) -> Tuple[bool, str]:
    """Valida formato de email."""
    if not email or not email.strip():
        return False, "Email é obrigatório."
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email.strip()):
        return False, "Email inválido."
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Valida força mínima da senha."""
    if not password:
        return False, "Senha é obrigatória."
    if len(password) < 6:
        return False, "Senha deve ter no mínimo 6 caracteres."
    return True, ""


def lgpd_consent_text() -> str:
    """Retorna texto padrão de consentimento LGPD."""
    return (
        "_Ao criar sua conta, você concorda com os "
        "[Termos de Uso](https://melshape.com.br/termos) e a "
        "[Política de Privacidade](https://melshape.com.br/privacidade) "
        "do Melshape, incluindo o tratamento dos seus dados de saúde "
        "conforme a Lei Geral de Proteção de Dados (LGPD — Lei 13.709/2018)._"
    )


def record_lgpd_consent(email: str) -> str:
    """
    Registra timestamp do consentimento LGPD.
    Retorna ISO timestamp para armazenar no perfil.
    """
    return datetime.utcnow().isoformat()
