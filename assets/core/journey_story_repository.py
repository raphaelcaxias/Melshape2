"""
Melshape — Repositório da Narrativa da Jornada.

Tabelas:
  motivos_jornada    → o "porquê" do paciente (capturado no onboarding)
  fotos_evolucao     → registro fotográfico do progresso
  conquistas_jornada → conquistas específicas da jornada (≠ badges globais)
  eventos_vida       → momentos marcantes registrados pelo paciente

O "porquê" capturado e relembrado é o principal antídoto contra abandono.
"""
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger("Melshape.JourneyStory")


class JourneyStoryRepository:
    """
    Mixin de narrativa da jornada. Requer self.client, self.is_real,
    self.uid(), self._mock() do Database.
    """

    # ── MOTIVOS DA JORNADA ────────────────────────────────────────────────────
    def get_motivos(self, jornada_id: str) -> list:
        if self.is_real and self.client:
            try:
                r = (self.client.table("motivos_jornada")
                     .select("*")
                     .eq("jornada_id", jornada_id)
                     .order("criado_em")
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_motivos: {e}")
        return self._mock().get(f"motivos_{jornada_id}", [])

    def salvar_motivo(self, jornada_id: str,
                      motivo: str, emocional: bool = True) -> bool:
        """Salva o 'porquê' do paciente ao iniciar a jornada."""
        uid = self.uid()
        if self.is_real and self.client:
            try:
                self.client.table("motivos_jornada").insert({
                    "jornada_id": jornada_id,
                    "perfil_id":  uid,
                    "motivo":     motivo,
                    "emocional":  emocional,
                    "criado_em":  date.today().isoformat(),
                }).execute()
                return True
            except Exception as e:
                logger.warning(f"salvar_motivo: {e}")
        key = f"motivos_{jornada_id}"
        self._mock().setdefault(key, []).append({
            "jornada_id": jornada_id, "motivo": motivo,
            "emocional": emocional,
            "criado_em": date.today().isoformat(),
        })
        return True

    # ── FOTOS DE EVOLUÇÃO ─────────────────────────────────────────────────────
    def salvar_foto(self, perfil_id: str, url: str,
                    legenda: str = "", peso_na_data: float = 0.0) -> bool:
        if self.is_real and self.client:
            try:
                self.client.table("fotos_evolucao").insert({
                    "perfil_id":   perfil_id,
                    "url_foto":    url,
                    "legenda":     legenda or None,
                    "peso_na_data": peso_na_data or None,
                    "data_foto":   date.today().isoformat(),
                }).execute()
                return True
            except Exception as e:
                logger.warning(f"salvar_foto: {e}")
        self._mock().setdefault(f"fotos_{perfil_id}", []).append({
            "url_foto": url, "legenda": legenda,
            "peso_na_data": peso_na_data,
            "data_foto": date.today().isoformat(),
        })
        return True

    def get_fotos(self, perfil_id: str) -> list:
        if self.is_real and self.client:
            try:
                r = (self.client.table("fotos_evolucao")
                     .select("url_foto, legenda, peso_na_data, data_foto")
                     .eq("perfil_id", perfil_id)
                     .order("data_foto", desc=True)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_fotos: {e}")
        return self._mock().get(f"fotos_{perfil_id}", [])

    # ── CONQUISTAS DA JORNADA ─────────────────────────────────────────────────
    def get_conquistas_jornada(self, jornada_id: str) -> list:
        """Conquistas específicas desta jornada (≠ badges globais)."""
        if self.is_real and self.client:
            try:
                r = (self.client.table("conquistas_jornada")
                     .select("*")
                     .eq("jornada_id", jornada_id)
                     .order("conquistado_em", desc=True)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_conquistas_jornada: {e}")
        return self._mock().get(f"conq_j_{jornada_id}", [])

    def registrar_conquista_jornada(self, jornada_id: str,
                                     titulo: str,
                                     descricao: str = "") -> bool:
        if self.is_real and self.client:
            try:
                self.client.table("conquistas_jornada").insert({
                    "jornada_id":    jornada_id,
                    "titulo":        titulo,
                    "descricao":     descricao or None,
                    "conquistado_em": date.today().isoformat(),
                }).execute()
                return True
            except Exception as e:
                logger.warning(f"registrar_conquista_jornada: {e}")
        key = f"conq_j_{jornada_id}"
        self._mock().setdefault(key, []).append({
            "titulo": titulo, "descricao": descricao,
            "conquistado_em": date.today().isoformat(),
        })
        return True

    # ── EVENTOS DE VIDA ───────────────────────────────────────────────────────
    def get_eventos_vida(self) -> list:
        uid = self.uid()
        if self.is_real and self.client:
            try:
                r = (self.client.table("eventos_vida")
                     .select("*")
                     .eq("perfil_id", uid)
                     .order("data_evento", desc=True)
                     .limit(20)
                     .execute())
                return r.data or []
            except Exception as e:
                logger.warning(f"get_eventos_vida: {e}")
        return self._mock().get(f"ev_vida_{uid}", [])

    def registrar_evento_vida(self, titulo: str, descricao: str = "",
                               tipo: str = "marco",
                               data_evento: str = "") -> bool:
        uid = self.uid()
        data = data_evento or date.today().isoformat()
        if self.is_real and self.client:
            try:
                self.client.table("eventos_vida").insert({
                    "perfil_id":   uid,
                    "titulo":      titulo,
                    "descricao":   descricao or None,
                    "tipo":        tipo,
                    "data_evento": data,
                }).execute()
                return True
            except Exception as e:
                logger.warning(f"registrar_evento_vida: {e}")
        self._mock().setdefault(f"ev_vida_{uid}", []).append({
            "titulo": titulo, "descricao": descricao,
            "tipo": tipo, "data_evento": data,
        })
        return True
