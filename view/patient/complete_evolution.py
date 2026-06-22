"""
Melshape — Evolução Completa.

Reúne 8 funcionalidades ausentes em uma tela com 4 abas:
  📏 Corpo    → medidas corporais + fotos
  🧪 Clínico  → exames + estagnação
  🏆 Conquistas → hall da fama + carteira + histórico XP
  ⚖️ Legal    → consentimentos LGPD + revogação

Correções vs versão original:
  - self.uid → self._uid() (método, não property)
  - Guard clauses em todos os gráficos Plotly
  - Contextualizer aplicado (números→narrativa)
  - Revogação de consentimento implementada
  - Campos de medida alinhados com banco real
"""
import streamlit as st
import pandas as pd

from services.evolution_service import EvolutionService
from services.contextualizer import ctx
from views.components.cards import (
    section_header, empty_state, alert, metric_card,
)


def render(services: dict, user: dict) -> None:
    db  = services["db"]
    svc = EvolutionService(db)

    section_header(
        "📊 Evolução Completa",
        "Corpo, exames, conquistas e privacidade em um só lugar",
    )

    tab_corpo, tab_clinico, tab_conquistas, tab_legal = st.tabs([
        "📏 Corpo",
        "🧪 Clínico",
        "🏆 Conquistas",
        "⚖️ Legal",
    ])

    with tab_corpo:
        _tab_corpo(svc, user)

    with tab_clinico:
        _tab_clinico(svc, user)

    with tab_conquistas:
        _tab_conquistas(svc, user)

    with tab_legal:
        _tab_legal(svc, user)


from views.patient.evolution_corpo import _tab_corpo
from views.patient.evolution_clinico import _tab_clinico
from views.patient.evolution_gami import _tab_conquistas
from views.patient.evolution_legal import _tab_legal
