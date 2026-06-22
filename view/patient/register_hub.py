"""
Melshape — Hub de Registro.
Regra dos 3 cliques: toda ação de registro em no máximo 3 interações.

Fluxo:
  1. Usuário clica em "Registrar" na sidebar → esta tela
  2. Escolhe o tipo (refeição / peso / água / check-in)
  3. Preenche e confirma → toast de feedback + XP

Botão flutuante "+" também navega para cá.
"""
import streamlit as st
from datetime import date

from views.patient.register_hub_quick import _form_agua, _form_checkin
from views.components.cards import (
    section_header, empty_state, metric_card,
    show_new_achievements, xp_toast, alert,
)
import config

_TIPOS = {
    "🍽️ Refeição":  "meal",
    "⚖️ Peso":      "weight",
    "💧 Água":      "hydration",
    "✅ Check-in":  "checkin",
}


def render(services: dict, user: dict) -> None:
    db    = services["db"]
    nutr  = services["nutrition"]
    gami  = services["gamification"]
    foods = services["foods"]

    section_header("➕ Registrar", "Escolha o que quer registrar hoje")

    # ── SELEÇÃO DO TIPO (clique 1) ────────────────────────────────────────────
    cols = st.columns(4)
    tipo_labels = list(_TIPOS.keys())
    for i, label in enumerate(tipo_labels):
        with cols[i]:
            if st.button(label, use_container_width=True, key=f"hub_{i}"):
                st.session_state["hub_tipo"] = _TIPOS[label]

    tipo = st.session_state.get("hub_tipo", "meal")

    st.markdown(
        '<div style="border-top:1px solid var(--border);margin:0.8rem 0;"></div>',
        unsafe_allow_html=True,
    )

    # ── FORMULÁRIOS (cliques 2 e 3) ───────────────────────────────────────────
    if tipo == "meal":
        _form_refeicao(db, nutr, gami, foods, user)
    elif tipo == "weight":
        _form_peso(db, gami, user)
    elif tipo == "hydration":
        _form_agua(db, gami)
    elif tipo == "checkin":
        _form_checkin(db, gami)


# ── REFEIÇÃO ──────────────────────────────────────────────────────────────────
def _form_refeicao(db, nutr, gami, foods, user: dict) -> None:
    st.markdown("#### 🍽️ Registrar Refeição")

    health_mode = user.get("health_mode", "general")
    is_bariatric = user.get("is_bariatric", False)

    # Busca de alimento (clique 2)
    col1, col2 = st.columns([3, 1])
    with col1:
        termo = st.text_input(
            "Buscar alimento",
            placeholder="Ex: frango, arroz, ovo...",
            key="hub_food_search",
            label_visibility="collapsed",
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)

    # Sugestões rápidas
    frequentes = nutr.suggest_foods()
    if frequentes and not termo:
        st.markdown(
            '<div style="font-size:0.80rem;color:var(--text-muted);'
            'margin-bottom:0.3rem;">⚡ Recentes:</div>',
            unsafe_allow_html=True,
        )
        cols_freq = st.columns(min(5, len(frequentes)))
        for i, nome in enumerate(frequentes[:5]):
            with cols_freq[i]:
                if st.button(nome[:18], key=f"freq_{i}", use_container_width=True):
                    st.session_state["hub_food_search"] = nome
                    st.session_state["hub_food_selected"] = nome
                    st.rerun()

    # Resultados da busca
    resultados = foods.search_foods(termo, limit=8, frequent_foods=frequentes)
    alimento_sel = st.session_state.get("hub_food_selected_obj")

    if resultados and not alimento_sel:
        nomes = [f"{r.get('nome', r.get('name',''))} "
                 f"({r.get('calorias', r.get('calories', 0)):.0f} kcal/100g)"
                 for r in resultados]
        idx = st.selectbox(
            "Selecione o alimento",
            range(len(nomes)),
            format_func=lambda i: nomes[i],
            key="hub_food_idx",
            label_visibility="collapsed",
        )
        if st.button("Selecionar →", key="hub_food_confirm"):
            st.session_state["hub_food_selected_obj"] = resultados[idx]
            st.rerun()
        return

    if not alimento_sel:
        empty_state("🔍", "Busque um alimento acima",
                    "Digite pelo menos 2 letras para buscar nos 695 alimentos")
        return

    # Alimento selecionado — formulário final (clique 3)
    nome_al = alimento_sel.get("nome", alimento_sel.get("name", ""))
    cal100  = float(alimento_sel.get("calorias", alimento_sel.get("calories", 0)))
    prot100 = float(alimento_sel.get("proteina", alimento_sel.get("protein", 0)))
    carb100 = float(alimento_sel.get("carboidratos", alimento_sel.get("carbs", 0)))
    fat100  = float(alimento_sel.get("gorduras", alimento_sel.get("fat", 0)))
    porcao  = float(alimento_sel.get("porcao_padrao", 100))

    st.markdown(
        f'<div class="metric-card fade-in" style="margin-bottom:0.8rem;">'
        f'<div style="font-weight:700;color:var(--text);">{nome_al}</div>'
        f'<div style="font-size:0.80rem;color:var(--text-muted);margin-top:0.3rem;">'
        f'Por 100g: {cal100:.0f} kcal · {prot100:.1f}g prot · '
        f'{carb100:.1f}g carb · {fat100:.1f}g gord</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_q, col_t, col_tipo = st.columns([2, 1, 2])
    with col_q:
        qtd = st.number_input(
            "Quantidade (g)", min_value=1.0, max_value=2000.0,
            value=porcao, step=10.0, key="hub_qtd",
        )
    with col_t:
        horario = st.text_input("Horário", value="", placeholder="12:30",
                                key="hub_horario")
    with col_tipo:
        tipo_ref = st.selectbox(
            "Tipo",
            ["cafe_manha", "almoco", "jantar", "lanche", "pre_pos_treino", "outro"],
            format_func=lambda x: {
                "cafe_manha": "☀️ Café", "almoco": "🍽️ Almoço",
                "jantar": "🌙 Jantar", "lanche": "🍎 Lanche",
                "pre_pos_treino": "💪 Pré/Pós Treino", "outro": "📋 Outro",
            }.get(x, x),
            key="hub_tipo_ref",
        )

    # Volume para bariátrico
    vol_ml = 0.0
    if is_bariatric or health_mode == "bariatric":
        vol_ml = st.number_input(
            "Volume (ml) — controle bariátrico",
            min_value=0.0, max_value=800.0, value=0.0, step=10.0,
            key="hub_vol",
        )

    # Preview de macros
    fator = qtd / 100
    cal_calc = cal100 * fator
    prot_calc = prot100 * fator
    carb_calc = carb100 * fator
    fat_calc  = fat100  * fator

    alerta_cross = nutr.cross_validate(cal_calc, prot_calc, carb_calc, fat_calc)

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card(f"{cal_calc:.0f}", "kcal", "🔥")
    with c2: metric_card(f"{prot_calc:.1f}g", "proteína", "🥩")
    with c3: metric_card(f"{carb_calc:.1f}g", "carbos", "🌾")
    with c4: metric_card(f"{fat_calc:.1f}g", "gordura", "🫙")

    if alerta_cross:
        alert(alerta_cross, "warning")

    col_reg, col_vol = st.columns([2, 1])
    with col_reg:
        if st.button("✅ Registrar refeição", type="primary",
                     use_container_width=True, key="hub_save_meal"):
            ok, alerta = nutr.register_meal(
                food=alimento_sel, quantity=fator,
                meal_time=horario, meal_type=tipo_ref, volume_ml=vol_ml,
            )
            if ok:
                st.toast("🍽️ Refeição registrada!", icon="✅")
                if alerta:
                    st.toast(alerta, icon="⚠️")
                orch   = services.get("orchestrator")
                if orch:
                    result = orch.processar("refeicao", user, {})
                    if result.xp_ganho:
                        xp_toast(result.xp_ganho, "refeição")
                    show_new_achievements(result.badges_novos)
                else:
                    novos = gami.check_achievements(user)
                    show_new_achievements(novos)
                st.session_state.pop("hub_food_selected_obj", None)
                st.session_state.pop("hub_food_search", None)
                st.rerun()
            else:
                st.toast("Erro ao registrar. Tente novamente.", icon="❌")
    with col_vol:
        if st.button("🔄 Trocar alimento", use_container_width=True,
                     key="hub_change_food"):
            st.session_state.pop("hub_food_selected_obj", None)
            st.rerun()


# ── PESO ──────────────────────────────────────────────────────────────────────
def _form_peso(db, gami, user: dict) -> None:
    st.markdown("#### ⚖️ Registrar Peso")

    peso_atual = float(user.get("current_weight") or 70.0)

    col1, col2 = st.columns([2, 1])
    with col1:
        peso = st.number_input(
            "Peso (kg)", min_value=20.0, max_value=300.0,
            value=peso_atual, step=0.1, key="hub_peso",
        )
    with col2:
        gordura = st.number_input(
            "% Gordura (opcional)", min_value=0.0, max_value=80.0,
            value=0.0, step=0.1, key="hub_gordura",
        )

    massa = st.number_input(
        "Massa muscular kg (opcional)", min_value=0.0, max_value=150.0,
        value=0.0, step=0.1, key="hub_massa",
    )
    obs = st.text_input("Observação", placeholder="Ex: Após treino",
                        key="hub_peso_obs")

    # Diferença vs peso anterior
    if peso != peso_atual and peso_atual > 0:
        diff  = peso - peso_atual
        emoji = "📉" if diff < 0 else "📈"
        cor   = "success" if diff < 0 else "warning"
        alert(
            f"{emoji} Diferença: {diff:+.1f} kg em relação ao último registro",
            cor,
        )

    if st.button("✅ Registrar peso", type="primary",
                 use_container_width=True, key="hub_save_peso"):
        from core.models import WeightLog
        w = WeightLog(
            weight=peso, body_fat=gordura, muscle_mass=massa,
            log_date=date.today().isoformat(), notes=obs,
        )
        ok = db.save_weight(w)
        if ok:
            st.session_state.user["current_weight"] = peso
            st.toast(f"⚖️ {peso:.1f} kg registrado!", icon="✅")
            orch = services.get("orchestrator")
            if orch:
                result = orch.processar("peso", user, {"peso": peso})
                if result.xp_ganho:
                    xp_toast(result.xp_ganho, "pesagem")
                from views.components.cards import show_new_achievements
                show_new_achievements(result.badges_novos)
            else:
                db.xp_pesagem()
                xp_toast(30, "pesagem")
            novos = gami.check_achievements(user)
            show_new_achievements(novos)
            st.rerun()
        else:
            st.toast("Erro ao registrar peso.", icon="❌")

