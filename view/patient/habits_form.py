"""Melshape — Hábitos: formulário de criação e sugestões por pilar."""
import streamlit as st

_CATEGORIAS = {
    "hidratacao":   ("💧", "Hidratação"),
    "nutricao":     ("🥩", "Nutrição"),
    "movimento":    ("🚶", "Movimento"),
    "treino":       ("🏋️", "Treino"),
    "sono":         ("😴", "Sono"),
    "registro":     ("✅", "Registro"),
    "suplementos":  ("💊", "Suplementos"),
    "saude":        ("🩺", "Saúde"),
    "medicamento":  ("💉", "Medicamento"),
    "alimentacao":  ("🍽️", "Alimentação"),
    "monitoramento":("📊", "Monitoramento"),
    "geral":        ("⭐", "Geral"),
}

# ── TAB NOVO ──────────────────────────────────────────────────────────────────
def _tab_novo(db, svc: HabitService, hm: str) -> None:
    st.markdown("##### ➕ Criar Novo Hábito")

    # Sugestões do pilar
    sugs = svc.sugestoes(hm)
    st.markdown(
        '<div style="font-size:0.80rem;color:var(--text-muted);'
        'margin-bottom:0.5rem;">💡 Sugestões para seu pilar:</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(min(3, len(sugs)))
    for i, (icone, nome, cat, freq) in enumerate(sugs[:3]):
        with cols[i % 3]:
            if st.button(
                f"{icone} {nome[:22]}",
                key=f"sug_{i}",
                use_container_width=True,
            ):
                ok = db.criar_habito(nome, cat, icone, freq)
                if ok:
                    st.toast(f"{icone} Hábito criado!", icon="✅")
                    st.rerun()

    st.markdown("---")
    st.markdown("**Ou crie um personalizado:**")

    col1, col2 = st.columns([3, 1])
    with col1:
        nome_custom = st.text_input(
            "Nome do hábito",
            placeholder="Ex: Meditar 10 minutos",
            key="hab_nome",
        )
    with col2:
        icone_custom = st.text_input(
            "Ícone", value="⭐", max_chars=2, key="hab_icone"
        )

    col3, col4 = st.columns(2)
    with col3:
        cat_custom = st.selectbox(
            "Categoria",
            list(_CATEGORIAS.keys()),
            format_func=lambda k: f"{_CATEGORIAS[k][0]} {_CATEGORIAS[k][1]}",
            key="hab_cat",
        )
    with col4:
        freq_custom = st.selectbox(
            "Frequência",
            ["daily", "weekly"],
            format_func=lambda x: "Diário" if x == "daily" else "Semanal",
            key="hab_freq",
        )

    if st.button(
        "✅ Criar hábito",
        type="primary",
        use_container_width=True,
        key="hab_criar",
    ):
        if not nome_custom.strip():
            st.toast("Digite um nome para o hábito.", icon="⚠️")
        else:
            ok = db.criar_habito(
                nome_custom.strip(), cat_custom,
                icone_custom, freq_custom,
            )
            if ok:
                st.toast(
                    f"{icone_custom} Hábito '{nome_custom}' criado!",
                    icon="✅",
                )
                st.rerun()
            else:
                st.toast("Erro ao criar hábito.", icon="❌")


