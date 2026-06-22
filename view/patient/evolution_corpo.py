"""Melshape — Evolução: aba corpo (medidas + fotos)."""
import streamlit as st
import pandas as pd
from services.evolution_service import EvolutionService
from views.components.cards import empty_state

# ── ABA 1: CORPO ─────────────────────────────────────────────────────────────
def _tab_corpo(svc: EvolutionService, user: dict) -> None:
    st.markdown("##### 📏 Medidas Corporais")

    col1, col2, col3 = st.columns(3)
    with col1:
        peso = st.number_input(
            "Peso (kg)", min_value=20.0, max_value=300.0,
            value=float(user.get("current_weight") or 70),
            step=0.1, key="ev_peso",
        )
    with col2:
        cintura = st.number_input(
            "Cintura (cm)", min_value=40.0, max_value=200.0,
            value=90.0, step=0.5, key="ev_cintura",
        )
    with col3:
        quadril = st.number_input(
            "Quadril (cm)", min_value=50.0, max_value=200.0,
            value=100.0, step=0.5, key="ev_quadril",
        )

    col4, col5 = st.columns(2)
    with col4:
        braco = st.number_input(
            "Braço (cm)", min_value=10.0, max_value=80.0,
            value=30.0, step=0.5, key="ev_braco",
        )
    with col5:
        gordura = st.number_input(
            "% Gordura", min_value=0.0, max_value=70.0,
            value=25.0, step=0.5, key="ev_gordura",
        )

    if st.button("📏 Salvar medidas", type="primary",
                 use_container_width=True, key="ev_save_medidas"):
        ok = svc.salvar_medida({
            "peso": peso, "cintura": cintura,
            "quadril": quadril, "braco": braco, "gordura": gordura,
        })
        if ok:
            st.toast("📏 Medidas salvas!", icon="✅")
            svc.db.add_xp(10, motivo="medidas_corporais")
            st.rerun()
        else:
            st.toast("Erro ao salvar.", icon="❌")

    # ── Histórico ────────────────────────────────────────────────────────────
    st.markdown("---")
    medidas = svc.get_medidas(days=90)
    if medidas:
        st.markdown(
            f'<div style="font-size:0.82rem;color:var(--text-muted);'
            f'margin-bottom:0.6rem;">'
            f'<b>{len(medidas)}</b> registro(s) nos últimos 90 dias</div>',
            unsafe_allow_html=True,
        )
        try:
            import plotly.express as px
            df = pd.DataFrame(medidas)
            df["data_medicao"] = pd.to_datetime(df["data_medicao"])
            df = df.sort_values("data_medicao")

            cols_plot = [
                c for c in
                ["circunferencia_cintura", "circunferencia_quadril"]
                if c in df.columns and df[c].notna().any()
            ]
            if cols_plot and len(df) >= 2:
                fig = px.line(
                    df, x="data_medicao", y=cols_plot,
                    title="Evolução das Medidas",
                    labels={"value": "cm", "data_medicao": "Data"},
                    color_discrete_sequence=["#C9A84C", "#6366F1"],
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="var(--text-muted)",
                    margin=dict(t=40, b=10, l=0, r=0),
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass

        # Tabela simplificada
        for m in medidas[:5]:
            data   = m.get("data_medicao", "")[:10]
            p      = m.get("peso") or "—"
            cin    = m.get("circunferencia_cintura") or "—"
            quad   = m.get("circunferencia_quadril") or "—"
            st.markdown(
                f'<div style="font-size:0.82rem;padding:0.35rem 0;'
                f'border-bottom:1px solid var(--border-subtle);">'
                f'{data} · Peso: {p}kg · Cintura: {cin}cm · Quadril: {quad}cm'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        empty_state("📏", "Nenhuma medida registrada",
                    "Registre suas primeiras medidas acima")

    # ── Fotos ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### 📸 Fotos de Evolução")
    fotos = svc.get_fotos()

    if fotos:
        # Antes x Depois se houver >= 2 fotos
        if len(fotos) >= 2:
            col_antes, col_depois = st.columns(2)
            with col_antes:
                f_antes = fotos[-1]
                url_a   = f_antes.get("url_foto", "")
                if url_a.startswith("http"):
                    st.image(url_a, caption=f'Antes — {f_antes.get("data_foto","")[:10]}',
                             use_container_width=True)
            with col_depois:
                f_dep = fotos[0]
                url_d = f_dep.get("url_foto", "")
                if url_d.startswith("http"):
                    st.image(url_d, caption=f'Agora — {f_dep.get("data_foto","")[:10]}',
                             use_container_width=True)
        else:
            f = fotos[0]
            url = f.get("url_foto", "")
            if url.startswith("http"):
                st.image(url, caption=f.get("legenda") or f.get("data_foto", "")[:10],
                         use_container_width=True)

        st.markdown(
            f'<div style="font-size:0.78rem;color:var(--text-muted);">'
            f'{len(fotos)} foto(s) registrada(s)</div>',
            unsafe_allow_html=True,
        )
    else:
        empty_state("📸", "Nenhuma foto ainda",
                    "Adicione fotos para visualizar seu antes e depois")

    col_url, col_leg = st.columns([3, 1])
    with col_url:
        url_nova = st.text_input(
            "URL da foto (Google Fotos, Imgur, Drive)",
            placeholder="https://...",
            key="ev_foto_url",
        )
    with col_leg:
        leg_nova = st.text_input("Legenda", key="ev_foto_leg")

    if st.button("📸 Adicionar foto", use_container_width=True,
                 key="ev_add_foto"):
        if not url_nova.strip():
            st.toast("Cole a URL da foto.", icon="⚠️")
        else:
            ok = svc.salvar_foto(url_nova.strip(), leg_nova.strip())
            if ok:
                st.toast("📸 Foto adicionada!", icon="✅")
                st.rerun()
            else:
                st.toast("Erro ao adicionar.", icon="❌")


