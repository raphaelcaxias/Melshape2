"""Melshape — Sidebar: navegação contextual por pilar e logout."""
import streamlit as st


def render_pilar_perfil(u: dict, cur: str) -> None:
    """Renderiza link do pilar específico + perfil + sair."""
    hm        = u.get("health_mode", "general")
    pilar_map = {
        "glp1":      ("💉", "GLP-1",     "glp1"),
        "bariatric": ("🔪", "Bariátrica", "bariatric"),
        "fitness":   ("💪", "Fitness",    "dashboard"),
    }
    if hm in pilar_map:
        p_icon, p_label, p_route = pilar_map[hm]
        kind_p = "primary" if cur == p_route else "secondary"
        if st.button(f"{p_icon} {p_label}", use_container_width=True,
                     type=kind_p, key="nav_pilar"):
            st.session_state.page = p_route
            st.rerun()

    if st.button("👤 Perfil", use_container_width=True, key="nav_profile",
                 type="primary" if cur == "profile" else "secondary"):
        st.session_state.page = "profile"
        st.rerun()

    st.markdown(
        '<div style="border-top:1px solid var(--border);'
        'margin:0.4rem 0;"></div>',
        unsafe_allow_html=True,
    )


def _clear_session() -> None:
    for key in (
        "user", "professional", "perfil_id", "demo_loaded",
        "onboarding_step", "onboarding_mode",
        "pro_page", "pro_selected_patient", "ci_result",
    ):
        st.session_state.pop(key, None)
    st.session_state.page = "landing"
    st.rerun()
