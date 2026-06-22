"""
Melshape — Loop Clínico Fechado.

Problema resolvido:
  Profissional registra conduta → paciente não sabia.
  Loop aberto = profissional age, paciente não sente.

Solução:
  Após cada conduta, observação ou prescrição:
  1. Cria notificação in-app para o paciente
  2. Envia email se paciente tiver notificações ativas
  3. Registra evento em eventos_jornada

Chamado por patient_actions.py após cada ação do profissional.
"""
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger("Melshape.ClinicalLoop")

_TIPO_MSG = {
    "orientacao":    ("📋", "Seu profissional registrou uma orientação para você"),
    "ajuste_dieta":  ("🥗", "Seu profissional ajustou seu plano alimentar"),
    "alerta":        ("⚠️", "Seu profissional deixou um alerta importante"),
    "encaminhamento":("🏥", "Seu profissional fez um encaminhamento"),
    "elogio":        ("🌟", "Seu profissional te elogiou — você está no caminho certo!"),
    "revisao":       ("🔄", "Seu profissional revisou seu protocolo"),
}


class ClinicalLoopService:

    def __init__(self, db):
        self.db = db

    # ── CONDUTA ───────────────────────────────────────────────────────────────
    def apos_conduta(self, perfil_id: str, titulo: str,
                     descricao: str, tipo: str,
                     pro_nome: str = "") -> bool:
        """
        Chamado imediatamente após registrar_conduta().
        Fecha o loop: profissional agiu → paciente sabe.
        """
        icon, msg_base = _TIPO_MSG.get(tipo, ("📋", "Seu profissional agiu"))
        quem = f" — {pro_nome}" if pro_nome else ""
        msg  = f"{icon} {msg_base}{quem}: {titulo}"

        ok1 = self._notificar_paciente(perfil_id, msg, tipo="conduta_clinica")
        ok2 = self._registrar_evento_jornada(perfil_id, titulo, tipo)
        ok3 = self._enviar_email_paciente(perfil_id, titulo, msg)

        logger.info(
            f"Loop clínico fechado: perfil={perfil_id} tipo={tipo} "
            f"notif={ok1} evento={ok2} email={ok3}"
        )
        return ok1

    # ── PRESCRIÇÃO ────────────────────────────────────────────────────────────
    def apos_prescricao(self, perfil_id: str,
                         objetivo: str,
                         pro_nome: str = "") -> bool:
        """Notifica paciente quando prescrição é criada."""
        quem = f" — {pro_nome}" if pro_nome else ""
        msg  = (
            f"🥗 Seu profissional{quem} criou uma nova prescrição alimentar: "
            f"{objetivo}"
        )
        ok1 = self._notificar_paciente(perfil_id, msg, tipo="prescricao")
        ok2 = self._registrar_evento_jornada(
            perfil_id, f"Prescrição: {objetivo}", "prescricao"
        )
        self._enviar_email_paciente(perfil_id, f"Nova prescrição: {objetivo}", msg)
        return ok1

    # ── OBSERVAÇÃO (pública) ──────────────────────────────────────────────────
    def apos_observacao_publica(self, perfil_id: str,
                                 observacao: str,
                                 pro_nome: str = "") -> bool:
        """Notifica paciente apenas se observação for pública."""
        quem = f" — {pro_nome}" if pro_nome else ""
        msg  = (
            f"📝 Seu profissional{quem} deixou uma anotação para você. "
            f"Acesse o app para ver."
        )
        return self._notificar_paciente(perfil_id, msg, tipo="observacao")

    # ── HELPERS INTERNOS ──────────────────────────────────────────────────────
    def _notificar_paciente(self, perfil_id: str,
                             mensagem: str,
                             tipo: str = "conduta_clinica") -> bool:
        """Cria notificação in-app na fila_notificacoes."""
        if not (self.db.is_real and self.db.client):
            logger.info(f"[MOCK] Notificação in-app: {mensagem[:60]}")
            return True
        try:
            self.db.client.table("fila_notificacoes").insert({
                "perfil_id": perfil_id,
                "mensagem":  mensagem,
                "tipo":      tipo,
                "lida":      False,
                "criado_em": date.today().isoformat(),
            }).execute()
            return True
        except Exception as e:
            logger.warning(f"_notificar_paciente: {e}")
            # Tenta via fn_criar_notificacao como fallback
            try:
                self.db.client.rpc("fn_criar_notificacao", {
                    "p_perfil_id": perfil_id,
                    "p_mensagem":  mensagem,
                    "p_tipo":      tipo,
                }).execute()
                return True
            except Exception as e2:
                logger.warning(f"fn_criar_notificacao fallback: {e2}")
        return False

    def _registrar_evento_jornada(self, perfil_id: str,
                                   titulo: str,
                                   tipo: str) -> bool:
        """Registra evento em eventos_jornada para a linha do tempo."""
        if not (self.db.is_real and self.db.client):
            return True
        try:
            jornada = self.db.get_jornada_ativa()
            if not jornada:
                return False
            self.db.client.table("eventos_jornada").insert({
                "jornada_id":  jornada["id"],
                "perfil_id":   perfil_id,
                "tipo":        f"conduta_{tipo}",
                "titulo":      titulo,
                "data_evento": date.today().isoformat(),
                "origem":      "profissional",
            }).execute()
            return True
        except Exception as e:
            logger.warning(f"_registrar_evento_jornada: {e}")
        return False

    def _enviar_email_paciente(self, perfil_id: str,
                                titulo: str,
                                mensagem: str) -> bool:
        """Envia email ao paciente se tiver notificações ativas."""
        if not (self.db.is_real and self.db.client):
            return True
        try:
            r = (self.db.client.table("perfis")
                 .select("email, nome_completo, disable_reminders")
                 .eq("id", perfil_id)
                 .limit(1)
                 .execute())
            if not r.data:
                return False
            perfil = r.data[0]
            if perfil.get("disable_reminders"):
                return False

            email = perfil.get("email", "")
            nome  = perfil.get("nome_completo", "").split()[0]
            if not email:
                return False

            from services.email_service import _send, _wrap
            content = f"""
            <h2 style="font-family:Sora,sans-serif;color:#1C1C1E;margin:0 0 .75rem;">
              Olá, {nome}! 👋</h2>
            <p style="color:#4a4a4a;line-height:1.6;">{mensagem}</p>
            <div style="text-align:center;margin:1.5rem 0;">
              <a href="https://melshape.com.br"
              style="background:linear-gradient(135deg,#C9A84C,#a8862e);
              color:#1C1C1E;padding:0.75rem 2rem;border-radius:8px;
              text-decoration:none;font-weight:600;">
                Ver no Melshape →
              </a>
            </div>"""
            return _send(email, f"📋 {titulo} — Melshape", _wrap(content))
        except Exception as e:
            logger.warning(f"_enviar_email_paciente: {e}")
        return False
