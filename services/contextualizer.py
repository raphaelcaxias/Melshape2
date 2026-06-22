"""
Melshape — Motor de Contextualização.

Transforma dados brutos em narrativas humanas acolhedoras.
Garante que nenhum número chegue à tela sem contexto emocional.

REGRA: Nunca punir. Sempre acolher, motivar e orientar.

USO:
    from services.contextualizer import ctx

    msg = ctx.calories(800, 2000)
    # → "Você consumiu 800 kcal. Faltam 1200 kcal — continue no ritmo."
"""
import random
from typing import Optional


class Contextualizer:

    # ── CALORIAS ──────────────────────────────────────────────────────────────
    def calories(self, consumed: float, goal: float) -> str:
        if goal <= 0:
            return "Acompanhe sua alimentação com atenção."
        pct       = consumed / goal * 100
        remaining = max(0, goal - consumed)
        if pct >= 100:
            return (
                f"Você atingiu sua meta calórica! {consumed:.0f} kcal. "
                f"Foque na qualidade das próximas refeições."
            )
        if pct >= 80:
            return (
                f"Quase lá! {consumed:.0f} kcal — "
                f"faltam {remaining:.0f} kcal para sua meta."
            )
        if pct >= 50:
            return (
                f"{consumed:.0f} kcal de {goal:.0f}. "
                f"Continue no seu ritmo — qualidade importa."
            )
        if consumed > 0:
            return (
                f"{consumed:.0f} kcal registradas. "
                f"Lembre-se de se alimentar bem ao longo do dia."
            )
        return "Comece seu dia com uma refeição nutritiva."

    # ── PROTEÍNA ──────────────────────────────────────────────────────────────
    def protein(self, consumed: float, goal: float) -> str:
        if goal <= 0:
            return "A proteína é essencial para sua jornada."
        if consumed <= 0:
            return "Inclua uma fonte de proteína na próxima refeição."
        pct = consumed / goal * 100
        if pct >= 80:
            return (
                f"{consumed:.0f}g de {goal:.0f}g — "
                f"excelente! Isso preserva sua massa muscular."
            )
        if pct >= 50:
            return (
                f"{consumed:.0f}g de {goal:.0f}g. "
                f"Continue priorizando proteína."
            )
        return (
            f"{consumed:.0f}g de {goal:.0f}g. "
            f"Adicione uma fonte proteica na próxima refeição."
        )

    # ── HIDRATAÇÃO ────────────────────────────────────────────────────────────
    def hydration(self, consumed: float, goal: float) -> str:
        if goal <= 0:
            return "A hidratação é essencial para sua saúde."
        if consumed <= 0:
            return "💧 Comece a beber água agora. Seu corpo agradece."
        pct       = consumed / goal * 100
        remaining = max(0, goal - consumed)
        if pct >= 100:
            return f"💧 Meta de água atingida! {consumed:.0f}ml — muito bem."
        if pct >= 70:
            return f"💧 {consumed:.0f}ml — faltam {remaining:.0f}ml para a meta."
        if pct >= 40:
            return f"💧 {consumed:.0f}ml de {goal:.0f}ml. Continue bebendo."
        return f"💧 {consumed:.0f}ml registrados. Que tal um copo agora?"

    # ── STREAK ────────────────────────────────────────────────────────────────
    def streak(self, days: int) -> str:
        if days <= 0:
            return random.choice([
                "Sua sequência anterior provou que você consegue. "
                "Vamos recomeçar juntos?",
                "Todo recomeço é uma nova oportunidade. "
                "Você já foi mais longe antes.",
                "Recomeçar é parte da jornada. Estamos aqui com você.",
            ])
        if days < 3:
            return f"🌱 {days} dia(s). O hábito está começando a se formar."
        if days < 7:
            return f"⚡ {days} dias. Você está construindo consistência."
        if days < 30:
            return (
                f"🔥 {days} dias! Você é mais consistente "
                f"do que a maioria das pessoas."
            )
        if days < 90:
            return f"🏆 {days} dias! Você já provou que consegue."
        return f"👑 {days} dias! Isso é lendário."

    # ── PESO ──────────────────────────────────────────────────────────────────
    def weight(self, current: float,
               previous: Optional[float] = None,
               goal: Optional[float] = None) -> str:
        msg = f"Seu peso atual é {current:.1f} kg."
        if previous is not None:
            diff = current - previous
            if diff < -0.5:
                msg += (
                    f" Você progrediu! "
                    f"{abs(diff):.1f} kg desde o último registro."
                )
            elif diff > 0.5:
                msg += (
                    " Pequenas variações são normais. "
                    "Continue focado na consistência."
                )
            else:
                msg += " Peso estável — a consistência está funcionando."
        if goal is not None:
            diff_g = current - goal
            if diff_g > 0.5:
                msg += (
                    f" Faltam {diff_g:.1f} kg para sua meta — "
                    f"você está no caminho."
                )
            elif diff_g <= 0:
                msg += " 🎯 Meta atingida! Mantenha o foco."
        return msg

    # ── SCORE ─────────────────────────────────────────────────────────────────
    def score(self, value: float) -> str:
        if value >= 80:
            return (
                "Seu progresso está acima de 80% da média. "
                "Continue assim."
            )
        if value >= 60:
            return "Você está evoluindo de forma consistente. Continue focado."
        if value >= 40:
            return "Você está no caminho certo. Cada dia é um passo."
        if value >= 20:
            return (
                "Continue construindo sua consistência. "
                "Pequenos passos geram grandes mudanças."
            )
        return "Começar já é uma vitória. Estamos aqui para te apoiar."

    # ── HÁBITO ────────────────────────────────────────────────────────────────
    def habit(self, name: str, done: bool, streak: int = 0) -> str:
        if done:
            if streak >= 7:
                return (
                    f"✅ {name} — {streak} dias seguidos! "
                    f"Você está construindo algo sólido."
                )
            return f"✅ {name} concluído hoje. Ótimo trabalho!"
        if streak > 0:
            return (
                f"⏳ {name} ainda pendente. "
                f"Sua sequência de {streak} dias está te esperando."
            )
        return f"⏳ {name} — que tal completar hoje?"

    # ── ADESÃO ────────────────────────────────────────────────────────────────
    def adherence(self, pct: float, context: str = "paciente") -> str:
        if context == "profissional":
            if pct >= 70:
                return f"{pct:.0f}% — adesão boa. Mantenha o plano."
            if pct >= 50:
                return (
                    f"{pct:.0f}% — adesão moderada. "
                    f"Considere reforçar orientações."
                )
            return f"{pct:.0f}% — adesão baixa. Intervenção necessária."
        # paciente
        if pct >= 80:
            return f"{pct:.0f}% — você está no caminho certo!"
        if pct >= 50:
            return f"{pct:.0f}% — continue construindo consistência."
        return f"{pct:.0f}% — cada dia conta. Não desista."

    # ── RISCO ─────────────────────────────────────────────────────────────────
    def risk(self, pct: float) -> str:
        if pct >= 50:
            return f"{pct:.0f}% — risco alto. Ação urgente necessária."
        if pct >= 30:
            return f"{pct:.0f}% — risco moderado. Monitorar de perto."
        return f"{pct:.0f}% — risco baixo. Manter estratégia."


# ── INSTÂNCIA GLOBAL ─────────────────────────────────────────────────────────
ctx = Contextualizer()
