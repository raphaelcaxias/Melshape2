"""
Melshape — Repositório de Notificações.

Tabelas:
  fila_notificacoes      → notificações pendentes de entrega
  historico_notificacoes → notificações já exibidas
  lembretes_recorrentes  → lembretes fixos (check-in diário, etc.)

Estratégia V1 (custo zero):
  Notificações in-app: lidas da fila a cada login e exibidas via st.toast()
  E-mail: via Supabase Auth (reset/magic link) quando disponível
"""
import logging
from datetime import date, datetime, timedelta
from typing import Optional

logger = logging.getLogger("Melshape.NotifRepo")


class NotificationRepository:
    """
    Mixin de notificações. Requer self.client, self.is_real,
    self.uid(), self._mock() do Database.
    """

    # ── FILA ─────────────────────────────────────────────────────────────────
    def get_notificacoes_pendentes(self, limit: int = 5) -> list:
        """Retorna notificações não enviadas do paciente."""
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = (self.client.table("fila_notificacoes")
                     .select("id, mensagem, tipo, criado_em")
                     .eq("perfil_id", uid)
                     .eq("enviada", False)
                     .order("criado_em", desc=True)
                     .limit(limit)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_notificacoes_pendentes: {e}")
        return self._mock().get(f"notif_fila_{uid}", [])

    def marcar_entregue(self, notif_id: str) -> bool:
        """Marca notificação como entregue e move para histórico."""
        uid = self.uid()
        if self.is_real and self.client:
            try:
                # Atualiza fila
                self.client.table("fila_notificacoes").update(
                    {"enviada": True, "enviada_em": datetime.utcnow().isoformat()}
                ).eq("id", notif_id).execute()
                return True
            except Exception as e:
                logger.warning(f"marcar_entregue: {e}")
        return False

    def criar_notificacao(self, mensagem: str, tipo: str = "engajamento",
                           agendada_para: Optional[str] = None) -> bool:
        """Cria notificação diretamente (fallback quando fn_criar_notificacao falha)."""
        uid = self.uid()
        if self.is_real and self.client:
            try:
                payload = {
                    "perfil_id": uid,
                    "mensagem":  mensagem,
                    "tipo":      tipo,
                    "enviada":   False,
                }
                if agendada_para:
                    payload["agendada_para"] = agendada_para
                self.client.table("fila_notificacoes").insert(payload).execute()
                return True
            except Exception as e:
                logger.warning(f"criar_notificacao: {e}")
        key = f"notif_fila_{uid}"
        self._mock().setdefault(key, []).append({
            "id": f"n_{uid}_{len(self._mock().get(key, []))}",
            "mensagem": mensagem, "tipo": tipo, "enviada": False,
            "criado_em": datetime.utcnow().isoformat(),
        })
        return True

    # ── LEMBRETES RECORRENTES ─────────────────────────────────────────────────
    def get_lembretes(self) -> list:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = (self.client.table("lembretes_recorrentes")
                     .select("*")
                     .eq("perfil_id", uid)
                     .eq("ativo", True)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_lembretes: {e}")
        return self._mock().get(f"lembretes_{uid}", [])

    def criar_lembrete_checkin(self) -> bool:
        """Cria lembrete recorrente de check-in diário se não existir."""
        uid       = self.uid()
        lembretes = self.get_lembretes()
        if any(l.get("tipo") == "checkin_diario" for l in lembretes):
            return False
        if self.is_real and self.client:
            try:
                self.client.table("lembretes_recorrentes").insert({
                    "perfil_id":  uid,
                    "tipo":       "checkin_diario",
                    "mensagem":   "✅ Seu check-in de hoje está esperando. 30 segundos.",
                    "horario":    "08:00",
                    "frequencia": "daily",
                    "ativo":      True,
                }).execute()
                return True
            except Exception as e:
                logger.warning(f"criar_lembrete_checkin: {e}")
        self._mock().setdefault(f"lembretes_{uid}", []).append({
            "tipo": "checkin_diario", "ativo": True,
        })
        return True

    # ── HISTÓRICO ─────────────────────────────────────────────────────────────
    def get_historico_notificacoes(self, days: int = 7) -> list:
        uid    = self.uid()
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        if self.is_real and self.client:
            try:
                r = (self.client.table("historico_notificacoes")
                     .select("mensagem, tipo, criado_em")
                     .eq("perfil_id", uid)
                     .gte("criado_em", cutoff)
                     .order("criado_em", desc=True)
                     .limit(20)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_historico_notificacoes: {e}")
        return []
