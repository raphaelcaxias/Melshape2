"""
Melshape — Formulários da Narrativa da Jornada.
Importado por journey_story.py.
"""
import streamlit as st
from datetime import date


def render_form_motivo(db, jornada_id: str,
                        has_motivo: bool = False) -> None:
    """Captura o 'porquê' do paciente."""
    label = "Adicionar outro motivo" if has_motivo else "Registrar meu porquê"
    st.markdown(f"**{label}**")

    motivo_texto = st.text_area(
        "Motivo",
        height=90,
        placeholder=(
            "Ex: Quero ter energia para brincar com meus filhos. "
            "Quero me sentir bem ao me olhar no espelho. "
            "Quero controlar minha saúde antes que seja tarde."
        ),
        key="story_motivo",
        label_visibility="collapsed",
    )

    if st.button(
        "💛 Salvar meu porquê",
        type="primary",
        use_container_width=True,
        key="story_motivo_save",
    ):
        if not motivo_texto.strip():
            st.toast("Escreva seu motivo.", icon="⚠️")
            return
        ok = db.salvar_motivo(jornada_id, motivo_texto.strip())
        if ok:
            st.toast("💛 Motivo salvo!", icon="✅")
            st.rerun()
        else:
            st.toast("Erro ao salvar.", icon="❌")


def render_form_foto(db, perfil_id: str, user: dict) -> None:
    """Formulário de registro de foto de evolução."""
    st.markdown("**📸 Registrar nova foto**")

    col1, col2 = st.columns(2)
    with col1:
        url_foto = st.text_input(
            "URL da foto (Google Drive, Imgur, etc.)",
            placeholder="https://...",
            key="story_foto_url",
        )
    with col2:
        peso_foto = st.number_input(
            "Peso nesta data (kg)",
            min_value=0.0,
            max_value=300.0,
            value=float(user.get("current_weight") or 0),
            step=0.1,
            key="story_foto_peso",
        )

    legenda = st.text_input(
        "Legenda (opcional)",
        placeholder="Ex: Início da jornada, 3 meses depois...",
        key="story_foto_leg",
    )

    st.markdown(
        '<div style="font-size:0.76rem;color:var(--text-muted);">'
        '💡 Dica: hospede no Google Fotos, Imgur ou Drive e cole o link direto.'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "📸 Registrar foto",
        use_container_width=True,
        key="story_foto_save",
    ):
        if not url_foto.strip():
            st.toast("Cole a URL da foto.", icon="⚠️")
            return
        ok = db.salvar_foto(perfil_id, url_foto.strip(),
                             legenda, peso_foto)
        if ok:
            st.toast("📸 Foto registrada!", icon="✅")
            st.rerun()
        else:
            st.toast("Erro ao salvar.", icon="❌")


def render_form_evento(db) -> None:
    """Formulário para registrar evento de vida."""
    st.markdown("**📅 Registrar momento**")

    _TIPOS = {
        "marco":       "🏁 Marco alcançado",
        "celebracao":  "🎉 Celebração",
        "desafio":     "⚡ Superei um desafio",
        "dificuldade": "💪 Momento difícil superado",
        "inicio":      "🌱 Início de algo novo",
    }

    col1, col2 = st.columns([1, 2])
    with col1:
        tipo = st.selectbox(
            "Tipo",
            list(_TIPOS.keys()),
            format_func=lambda k: _TIPOS[k],
            key="ev_tipo",
            label_visibility="collapsed",
        )
    with col2:
        titulo = st.text_input(
            "Título",
            placeholder="Ex: Completei minha primeira semana",
            key="ev_titulo",
            label_visibility="collapsed",
        )

    descricao = st.text_area(
        "Como foi? (opcional)",
        height=70,
        key="ev_desc",
        placeholder="Descreva como se sentiu...",
        label_visibility="collapsed",
    )

    if st.button(
        "📅 Salvar momento",
        use_container_width=True,
        key="ev_save",
    ):
        if not titulo.strip():
            st.toast("Dê um título ao momento.", icon="⚠️")
            return
        ok = db.registrar_evento_vida(titulo.strip(), descricao, tipo)
        if ok:
            st.toast("📅 Momento registrado!", icon="✅")
            st.rerun()
        else:
            st.toast("Erro ao salvar.", icon="❌")
