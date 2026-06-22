"""Melshape — Evolução: aba conquistas (hall da fama + carteira + XP)."""
import streamlit as st
import pandas as pd
from services.evolution_service import EvolutionService
from services.contextualizer import ctx
from views.components.cards import empty_state

# ── ABA 3: CONQUISTAS ─────────────────────────────────────────────────────────
def _tab_conquistas(svc: EvolutionService, user: dict) -> None:
    nome_atual = user.get("name", "")

    # ── Carteira ──────────────────────────────────────────────────────────────
    st.markdown("##### 💰 Carteira de Recompensas")
    carteira = svc.get_carteira()
    moedas   = carteira.get("moedas", 0)

    # Narrativa via contextualizer
    if moedas >= 500:
        moedas_msg = f"Você tem {moedas} moedas — saldo excelente para resgatar recompensas!"
    elif moedas >= 100:
        moedas_msg = f"{moedas} moedas acumuladas. Continue engajado para resgatar benefícios."
    else:
        moedas_msg = f"{moedas} moedas. Faça check-ins e complete hábitos para acumular mais."

    st.markdown(
        f'<div class="metric-card fade-in" style="margin-bottom:1rem;">'
        f'<div style="display:flex;align-items:center;gap:0.8rem;">'
        f'<span style="font-size:2rem;">🪙</span>'
        f'<div>'
        f'<div style="font-size:1.6rem;font-weight:800;color:var(--primary);">'
        f'{moedas}</div>'
        f'<div style="font-size:0.80rem;color:var(--text-muted);">'
        f'{moedas_msg}</div>'
        f'</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Hall da Fama ──────────────────────────────────────────────────────────
    st.markdown("##### 🏆 Hall da Fama — Top Transformação")
    campeoes = svc.get_campeoes(limit=10)

    if campeoes:
        _MEDALHAS = {0: "🥇", 1: "🥈", 2: "🥉"}
        minha_pos = next(
            (i + 1 for i, c in enumerate(campeoes)
             if c.get("nome_completo", "") == nome_atual),
            None,
        )
        if minha_pos:
            st.markdown(
                f'<div style="font-size:0.84rem;color:var(--primary);'
                f'font-weight:700;margin-bottom:0.5rem;">'
                f'🎯 Você está em #{minha_pos} no hall da fama!</div>',
                unsafe_allow_html=True,
            )

        for i, c in enumerate(campeoes[:5]):
            medalha = _MEDALHAS.get(i, f"#{i+1}")
            nome    = c.get("nome_completo", "—")
            score   = float(c.get("score", 0))
            eh_eu   = nome == nome_atual
            destaque = "font-weight:800;color:var(--primary);" if eh_eu else ""
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'padding:0.4rem 0;border-bottom:1px solid var(--border-subtle);">'
                f'<span style="{destaque}">{medalha} {nome}'
                f'{"  👈 você" if eh_eu else ""}</span>'
                f'<span style="font-weight:700;color:var(--primary);">'
                f'{score:.0f} pts</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        empty_state("🏆", "Hall da fama em construção",
                    "Seja consistente para aparecer aqui!")

    # ── Histórico XP ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### 📈 Histórico de XP (30 dias)")
    historico = svc.get_historico_xp(days=30)

    if historico and len(historico) >= 2:
        try:
            import plotly.express as px
            df = pd.DataFrame(historico)
            df["data"] = pd.to_datetime(df["data"])
            fig = px.bar(
                df, x="data", y="xp_ganho",
                title="XP ganho por dia",
                labels={"data": "Data", "xp_ganho": "XP"},
                color_discrete_sequence=["#C9A84C"],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#6B6B6B",
                margin=dict(t=40, b=10, l=0, r=0),
            )
            st.plotly_chart(fig, use_container_width=True)

            total_xp = sum(r["xp_ganho"] for r in historico)
            st.markdown(
                f'<div style="font-size:0.84rem;color:var(--text-muted);">'
                f'{ctx.score(min(100, total_xp / 10))}</div>',
                unsafe_allow_html=True,
            )
        except Exception:
            empty_state("📊", "Gráfico temporariamente indisponível")
    elif historico:
        st.markdown(
            f'<div style="font-size:0.84rem;color:var(--text-muted);">'
            f'XP total (30d): {sum(r["xp_ganho"] for r in historico)} XP</div>',
            unsafe_allow_html=True,
        )
    else:
        empty_state("📊", "Nenhum XP registrado",
                    "Faça check-ins e complete hábitos para acumular XP")


