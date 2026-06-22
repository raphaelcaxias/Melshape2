"""Melshape — Dashboard Profissional: tabs de alertas e inativos."""
import streamlit as st
from views.components.cards import empty_state



# ── ALERTAS CLÍNICOS ──────────────────────────────────────────────────────────
def _tab_alertas(db) -> None:
    alertas = _query(db, "vw_alertas_abertos",
                     "nome_completo,titulo,descricao,gravidade,criado_em")

    if not alertas:
        st.markdown(
            '<div class="alert-success">✅ Nenhum alerta clínico aberto</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<div class="alert-warning">'
        f'⚠️ <b>{len(alertas)}</b> alerta(s) clínico(s) aberto(s)</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="margin-top:0.6rem;"></div>', unsafe_allow_html=True
    )

    for a in alertas:
        gravidade = str(a.get("gravidade", 1))
        cor = "error" if gravidade == "3" else "warning" if gravidade == "2" else "info"
        criado = a.get("criado_em", "")
        data_str = criado[:10] if criado else "—"
        st.markdown(
            f'<div class="metric-card fade-in" style="margin-bottom:0.5rem;">'
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:flex-start;">'
            f'<div>'
            f'<div style="font-weight:700;font-size:0.92rem;color:var(--text);">'
            f'{a.get("nome_completo","—")}</div>'
            f'<div style="font-size:0.85rem;color:var(--text-muted);'
            f'margin-top:0.2rem;">{a.get("titulo","")}</div>'
            f'<div style="font-size:0.80rem;color:var(--text-faint);'
            f'margin-top:0.15rem;">{a.get("descricao","")}</div>'
            f'</div>'
            f'<div style="text-align:right;font-size:0.75rem;'
            f'color:var(--text-faint);">{data_str}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )


# ── INATIVOS ──────────────────────────────────────────────────────────────────
def _tab_inativos(db) -> None:
    inativos = _query(db, "vw_pacientes_inativos",
                      "nome_completo,dias_sem_acesso,dias_sem_checkin,risco_abandono")
    sem_ci   = _query(db, "vw_sem_checkin_recente",
                      "nome_completo,dias_sem_checkin,ultimo_checkin")

    if not inativos and not sem_ci:
        st.markdown(
            '<div class="alert-success">✅ Todos os pacientes estão ativos</div>',
            unsafe_allow_html=True,
        )
        return

    if inativos:
        st.markdown("##### 📵 Risco de Abandono")
        for p in inativos:
            risco = float(p.get("risco_abandono") or 0)
            cor   = "error" if risco >= 70 else "warning"
            dias  = p.get("dias_sem_acesso", 0)
            st.markdown(
                f'<div class="metric-card fade-in" style="margin-bottom:0.4rem;">'
                f'<div style="display:flex;justify-content:space-between;">'
                f'<div>'
                f'<div style="font-weight:600;color:var(--text);">'
                f'{p.get("nome_completo","—")}</div>'
                f'<div style="font-size:0.78rem;color:var(--text-muted);">'
                f'Sem acesso há {dias} dias</div>'
                f'</div>'
                f'<span class="xp-badge" style="'
                f'background:var(--{"error" if cor == "error" else "warning"}-bg);'
                f'color:var(--{cor});border-color:transparent;">'
                f'Risco: {risco:.0f}%</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    if sem_ci:
        st.markdown("##### 🔕 Sem Check-in Recente")
        for p in sem_ci:
            dias = p.get("dias_sem_checkin", 0)
            st.markdown(
                f'<div style="font-size:0.88rem;padding:0.5rem 0;'
                f'border-bottom:1px solid var(--border);">'
                f'<b>{p.get("nome_completo","—")}</b> — '
                f'{dias} dia(s) sem check-in</div>',
                unsafe_allow_html=True,
            )


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _pro_email() -> str:
    pro = st.session_state.get("professional")
    if pro:
        return getattr(pro, "email", "") or pro.get("email", "")
    return ""


def _query(db, tabela: str, colunas: str,
           filtro_pro: bool = False) -> list:
    """Executa SELECT no Supabase. Fallback silencioso → lista vazia."""
    if db.is_real and db.client:
        try:
            q = db.client.table(tabela).select(colunas)
            if filtro_pro and tabela == "perfis":
                q = q.eq("profissional_id", _pro_email())
            return q.limit(100).execute().data or []
        except Exception as e:
            import logging
            logging.getLogger("Melshape.ProDash").warning(f"{tabela}: {e}")
    return []

    # Botão de logout profissional
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        st.session_state.pop("professional", None)
        st.session_state.page = "landing"
        st.rerun()


# ── VISÃO GERAL ───────────────────────────────────────────────────────────────
def _tab_geral(db) -> None:
    dados = _query(db, "vw_dashboard_profissional",
                   "total_pacientes,aderencia_media,consistencia_media,risco_abandono_medio")

    if dados:
        row = dados[0]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card(str(row.get("total_pacientes", 0)),
                        "Total de Pacientes", "👥")
        with c2:
            ader = row.get("aderencia_media") or 0
            metric_card(f"{float(ader):.0f}%",
                        "Aderência Média", "📋",
                        "success" if float(ader) >= 70 else "warning")
        with c3:
            cons = row.get("consistencia_media") or 0
            metric_card(f"{float(cons):.0f}%",
                        "Consistência Média", "🔥",
                        "success" if float(cons) >= 70 else "warning")
        with c4:
            risco = row.get("risco_abandono_medio") or 0
            metric_card(f"{float(risco):.0f}%",
                        "Risco de Abandono", "⚠️",
                        "error" if float(risco) >= 50 else "warning")
    else:
        # fallback mock
        resumo = db.get_patients_of_professional(
            _pro_email()
        )
        c1, c2 = st.columns(2)
        with c1:
            metric_card(str(len(resumo)), "Pacientes", "👥")
        with c2:
            metric_card("—", "Sem dados suficientes", "📊")

    st.markdown("---")

    # Gráfico: distribuição por jornada
    pacientes = _query(db, "perfis",
                       "tipo_jornada", filtro_pro=True)
    if pacientes:
        from collections import Counter
        contagem = Counter(p.get("tipo_jornada", "general") for p in pacientes)
        labels = {
            "general": "⚖️ Emagrecimento",
            "fitness":   "💪 Fitness",
            "bariatric": "🔪 Pós-Bariátrica",
            "glp1":      "💉 GLP-1",
        }
        df_data = {
            "Jornada": [labels.get(k, k) for k in contagem],
            "Total":   list(contagem.values()),
        }
        fig = px.pie(
            df_data, names="Jornada", values="Total",
            title="Distribuição por Jornada",
            color_discrete_sequence=["#C9A84C", "#6366F1", "#8B5CF6", "#10B981"],
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#6B6B6B",
            margin=dict(t=40, b=10, l=10, r=10),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        empty_state("📊", "Nenhum paciente cadastrado ainda",
                    "Adicione pacientes para ver os dados aqui")


# ── FILA DE ATENDIMENTO ───────────────────────────────────────────────────────
def _tab_fila(db) -> None:
    fila = _query(db, "vw_fila_atendimento",
                  "nome_completo,score_prioridade,prioridade")

    if not fila:
        empty_state("🏥", "Fila vazia", "Nenhum paciente requer atenção agora")
        return

    st.markdown(
        '<div style="font-size:0.82rem;color:var(--text-muted);'
        'margin-bottom:0.8rem;">'
        f'<b>{len(fila)}</b> pacientes na fila de atendimento</div>',
        unsafe_allow_html=True,
    )

    # Agrupa por prioridade
    grupos = {"URGENTE": [], "ALTA": [], "MODERADA": [], "BAIXA": []}
    for p in fila:
        prior = p.get("prioridade", "BAIXA")
        grupos.get(prior, grupos["BAIXA"]).append(p)

    for nivel in ["URGENTE", "ALTA", "MODERADA", "BAIXA"]:
        pacientes = grupos[nivel]
        if not pacientes:
            continue
        emoji = _PRIORIDADE_EMOJI[nivel]
        cor   = _PRIORIDADE_COR[nivel]
        st.markdown(
            f'<div class="alert-{cor}" style="margin-bottom:0.4rem;">'
            f'{emoji} <b>{nivel}</b> — {len(pacientes)} paciente(s)</div>',
            unsafe_allow_html=True,
        )
        for p in pacientes:
            nome  = p.get("nome_completo", "—")
            score = p.get("score_prioridade", 0)
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(
                    f'<div style="font-weight:600;font-size:0.92rem;'
                    f'color:var(--text);">{nome}</div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f'<div style="font-size:0.80rem;color:var(--text-muted);">'
                    f'Score: {float(score):.0f}</div>',
                    unsafe_allow_html=True,
                )
            with c3:
                if st.button("Ver →", key=f"fila_{nome}",
                             use_container_width=True):
                    st.session_state["pro_selected_patient"] = nome
                    st.session_state.page = "pro_patient_detail"
                    st.rerun()

        st.markdown(
            '<div style="border-bottom:1px solid var(--border);'
            'margin:0.5rem 0;"></div>',
            unsafe_allow_html=True,
        )
