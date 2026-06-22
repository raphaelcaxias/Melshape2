"""Melshape — Evolução: aba legal (consentimentos LGPD)."""
import streamlit as st
from services.evolution_service import EvolutionService
from views.components.cards import alert

# ── ABA 4: LEGAL ─────────────────────────────────────────────────────────────
def _tab_legal(svc: EvolutionService, user: dict) -> None:
    st.markdown("##### ⚖️ Consentimentos LGPD")
    consentimentos = svc.get_consentimentos()
    ativos  = [c for c in consentimentos if not c.get("revogado")]
    revog   = [c for c in consentimentos if c.get("revogado")]

    if ativos:
        ultimo = ativos[0]
        st.markdown(
            f'<div class="alert-success">'
            f'✅ Você assinou os termos em '
            f'{ultimo.get("assinado_em","")[:10]}<br>'
            f'<small>Versão: {ultimo.get("versao","—")} · '
            f'Tipo: {ultimo.get("tipo","—")}</small>'
            f'</div>',
            unsafe_allow_html=True,
        )
        # Revogação
        with st.expander("🔒 Gerenciar consentimentos"):
            for c in ativos[:3]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(
                        f'<div style="font-size:0.80rem;">'
                        f'{c.get("assinado_em","")[:10]} — '
                        f'{c.get("tipo","")} v{c.get("versao","")}</div>',
                        unsafe_allow_html=True,
                    )
                with col2:
                    cid = c.get("id", "")
                    if cid and st.button(
                        "Revogar", key=f"rev_{cid}",
                        help="Revogar este consentimento",
                    ):
                        ok = svc.revogar_consentimento(cid)
                        if ok:
                            st.toast("Consentimento revogado.", icon="🔒")
                            st.rerun()
    else:
        alert(
            "⚠️ Você ainda não assinou os termos de consentimento LGPD. "
            "Leia e assine abaixo para continuar usando o MelShape.",
            "warning",
        )

    if revog:
        st.markdown(
            f'<div style="font-size:0.76rem;color:var(--text-muted);'
            f'margin-top:0.4rem;">'
            f'{len(revog)} consentimento(s) revogado(s) anteriormente.</div>',
            unsafe_allow_html=True,
        )

    # Termos
    st.markdown("---")
    with st.expander("📄 Ler Termos de Consentimento LGPD"):
        st.markdown("""
**Declaração de Consentimento — MelShape v2.0**

Ao assinar, você autoriza o MelShape a coletar, armazenar e processar
seus dados pessoais de saúde para fins de acompanhamento da sua
jornada de transformação, conforme a Lei Geral de Proteção de Dados
(Lei 13.709/2018).

**Dados coletados:** peso, medidas, refeições, check-ins,
humor, energia, sono, exames clínicos e fotos de evolução.

**Seus direitos (Art. 18 LGPD):**
- Acessar seus dados a qualquer momento
- Solicitar correção ou exclusão
- Revogar este consentimento (dados serão anonimizados em 30 dias)
- Portabilidade dos dados

**Responsável:** MelShape · suporte@melshape.com.br
**Versão:** 2.0 · Vigência: 01/01/2025
        """)

    if not ativos:
        if st.button("✍️ Assinar consentimento", type="primary",
                     use_container_width=True, key="ev_assinar"):
            ok = svc.assinar_consentimento("lgpd", "2.0")
            if ok:
                st.toast("⚖️ Consentimento assinado!", icon="✅")
                st.rerun()
            else:
                st.toast("Erro ao assinar.", icon="❌")
    else:
        st.markdown(
            '<div style="font-size:0.78rem;color:var(--text-muted);'
            'margin-top:0.4rem;">✅ Termos vigentes assinados.</div>',
            unsafe_allow_html=True,
        )
