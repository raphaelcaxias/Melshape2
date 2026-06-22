"""
Melshape — Metas: formulário de criação guiada.
Templates por tipo, vincula automaticamente à jornada ativa.
"""
import streamlit as st
from services.goals_service import GoalsService


def render_form_meta(db, svc: GoalsService,
                     jornada_id: str, hm: str) -> None:
    st.markdown("##### ➕ Nova Meta")

    if not jornada_id:
        st.warning("Você precisa ter uma jornada ativa para criar metas.")
        return

    tipo_labels = svc.tipo_labels()
    tipos       = list(tipo_labels.keys())

    col1, col2 = st.columns(2)
    with col1:
        tipo_sel = st.selectbox(
            "Tipo de meta",
            tipos,
            format_func=lambda k: f"{tipo_labels[k][0]} {tipo_labels[k][1]}",
            key="goal_tipo",
        )
    with col2:
        templates = svc.templates().get(tipo_sel, [])
        nomes_tmpl = (
            [t["titulo"] for t in templates] + ["Personalizado"]
        )
        tmpl_idx = st.selectbox(
            "Template",
            range(len(nomes_tmpl)),
            format_func=lambda i: nomes_tmpl[i],
            key="goal_tmpl",
        )

    # Preenche campos com template selecionado
    is_custom = tmpl_idx >= len(templates)
    tmpl      = templates[tmpl_idx] if not is_custom else {}

    titulo_default = tmpl.get("titulo", "")
    alvo_default   = float(tmpl.get("valor_alvo") or 10.0)
    unid_default   = tmpl.get("unidade", "unidades")

    col3, col4 = st.columns([3, 1])
    with col3:
        titulo = st.text_input(
            "Título da meta",
            value=titulo_default,
            key="goal_titulo",
        )
    with col4:
        prazo = st.date_input(
            "Prazo (opcional)",
            value=None,
            key="goal_prazo",
        )

    col5, col6 = st.columns(2)
    with col5:
        valor_alvo = st.number_input(
            "Valor alvo",
            min_value=0.1,
            value=alvo_default,
            step=0.5,
            key="goal_alvo",
        )
    with col6:
        unidade = st.text_input(
            "Unidade",
            value=unid_default,
            key="goal_unidade",
        )

    # Explicação do tipo selecionado
    _explicar_tipo(tipo_sel)

    if st.button(
        "✅ Criar meta",
        type="primary",
        use_container_width=True,
        key="goal_criar",
    ):
        if not titulo.strip():
            st.toast("Digite um título para a meta.", icon="⚠️")
            return

        prazo_str = prazo.isoformat() if prazo else ""
        ok = db.criar_meta(
            jornada_id=jornada_id,
            titulo=titulo.strip(),
            valor_alvo=valor_alvo,
            unidade=unidade.strip(),
            prazo=prazo_str,
        )

        # Salva o tipo na meta (update após inserção)
        if ok and db.is_real and db.client:
            try:
                # Pega o ID da meta recém-criada
                uid = db.uid()
                r   = (db.client.table("metas")
                       .select("id")
                       .eq("jornada_id", jornada_id)
                       .eq("titulo", titulo.strip())
                       .order("criado_em", desc=True)
                       .limit(1)
                       .execute())
                if r.data:
                    db.client.table("metas").update(
                        {"tipo": tipo_sel}
                    ).eq("id", r.data[0]["id"]).execute()
            except Exception:
                pass

        if ok:
            st.toast(f"🎯 Meta '{titulo}' criada!", icon="✅")
            st.rerun()
        else:
            st.toast("Erro ao criar meta.", icon="❌")


def _explicar_tipo(tipo: str) -> None:
    explicacoes = {
        "peso": (
            "📊 Progresso calculado automaticamente "
            "comparando seu peso inicial com o atual."
        ),
        "habito": (
            "📋 Progresso baseado nos dias que você "
            "registrou pelo menos 1 hábito."
        ),
        "consistencia": (
            "🔥 Progresso = sua sequência atual de check-ins."
        ),
        "agua": (
            "💧 Conta os dias em que você atingiu 2L de água."
        ),
        "proteina": (
            "🥩 Compara sua média de proteína (7d) com o alvo."
        ),
        "livre": (
            "🎯 Você controla o progresso manualmente."
        ),
    }
    msg = explicacoes.get(tipo, "")
    if msg:
        st.markdown(
            f'<div style="font-size:0.80rem;color:var(--text-muted);'
            f'background:var(--surface-2);padding:0.5rem 0.8rem;'
            f'border-radius:var(--radius-sm);margin:0.4rem 0;">'
            f'{msg}</div>',
            unsafe_allow_html=True,
        )
