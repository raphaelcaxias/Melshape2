"""Melshape — Dados de referência das jornadas por pilar."""
"""
Melshape — Serviço de Jornada.

Responsável por:
- Criar jornada inicial ao concluir onboarding
- Definir etapas por pilar (geral, fitness, bariatric, glp1)
- Calcular progresso da etapa atual
- Sugerir próximo passo com base nos dados reais do paciente
"""
import logging
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger("Melshape.Journey")

# Etapas por pilar — ordem e critérios de progresso
_ETAPAS = {
    "general": [
        {"ordem": 1, "nome": "Primeiros Passos",
         "descricao": "Configure seu perfil e registre os primeiros dados.",
         "icone": "🌱",
         "criterios": ["Perfil completo", "1ª pesagem", "1º check-in"]},
        {"ordem": 2, "nome": "Construindo o Hábito",
         "descricao": "7 dias consecutivos de check-in.",
         "icone": "🔥",
         "criterios": ["7 check-ins seguidos", "7 refeições registradas"]},
        {"ordem": 3, "nome": "Consistência Real",
         "descricao": "30 dias de acompanhamento ativo.",
         "icone": "📈",
         "criterios": ["30 dias de check-in", "Meta de água 5x"]},
        {"ordem": 4, "nome": "Transformação Visível",
         "descricao": "Resultado mensurável e consistência sólida.",
         "icone": "⭐",
         "criterios": ["Perda de 3kg", "Nível 4 alcançado"]},
        {"ordem": 5, "nome": "Novo Padrão de Vida",
         "descricao": "90 dias. Os hábitos já são parte de você.",
         "icone": "🏆",
         "criterios": ["90 dias ativos", "Badge Lendário"]},
    ],
    "fitness": [
        {"ordem": 1, "nome": "Linha de Base",
         "descricao": "Avalie sua composição corporal inicial.",
         "icone": "📊",
         "criterios": ["Medidas iniciais", "1º treino registrado"]},
        {"ordem": 2, "nome": "Rotina Estabelecida",
         "descricao": "3 treinos por semana por 2 semanas.",
         "icone": "🏋️",
         "criterios": ["6 treinos em 14 dias", "Meta proteica 5x"]},
        {"ordem": 3, "nome": "Progressão de Carga",
         "descricao": "Evolução mensurável de força ou volume.",
         "icone": "💪",
         "criterios": ["30 dias de treino", "Aumento de carga"]},
        {"ordem": 4, "nome": "Composição em Foco",
         "descricao": "Redução de gordura com manutenção de massa.",
         "icone": "📉",
         "criterios": ["Gordura reduzida 2%", "Massa mantida"]},
        {"ordem": 5, "nome": "Alta Performance",
         "descricao": "90 dias de evolução contínua.",
         "icone": "🥇",
         "criterios": ["90 dias ativos", "Nível 5 alcançado"]},
    ],
    "bariatric": [
        {"ordem": 1, "nome": "Adaptação Alimentar",
         "descricao": "Fase líquida — foco em hidratação e volume.",
         "icone": "💧",
         "criterios": ["Volume diário controlado", "Suplementos registrados"]},
        {"ordem": 2, "nome": "Evolução da Textura",
         "descricao": "Progressão para alimentos pastosos e brandos.",
         "icone": "🥄",
         "criterios": ["14 dias na fase", "Proteína meta 5x"]},
        {"ordem": 3, "nome": "Reintrodução Sólida",
         "descricao": "Alimentação sólida fracionada.",
         "icone": "🍽️",
         "criterios": ["30 dias pós-cirurgia", "Sem intolerâncias"]},
        {"ordem": 4, "nome": "Hábitos Permanentes",
         "descricao": "6 meses de acompanhamento e novos hábitos.",
         "icone": "🌿",
         "criterios": ["6 meses de registro", "Peso estabilizado"]},
        {"ordem": 5, "nome": "Nova Vida",
         "descricao": "1 ano pós-cirurgia com saúde e autonomia.",
         "icone": "🌟",
         "criterios": ["1 ano de acompanhamento", "Exames em dia"]},
    ],
    "glp1": [
        {"ordem": 1, "nome": "Início do Tratamento",
         "descricao": "Primeira dose registrada e protocolo ativo.",
         "icone": "💉",
         "criterios": ["Dose registrada", "Perfil GLP-1 completo"]},
        {"ordem": 2, "nome": "Adaptação",
         "descricao": "Primeiras semanas — monitorar sintomas e adesão.",
         "icone": "🔬",
         "criterios": ["7 dias de adesão", "Sintomas monitorados"]},
        {"ordem": 3, "nome": "Ajuste de Dose",
         "descricao": "Dose estabilizada e alimentação adaptada.",
         "icone": "⚖️",
         "criterios": ["30 dias de tratamento", "Proteína meta 10x"]},
        {"ordem": 4, "nome": "Resultados Visíveis",
         "descricao": "Perda de peso consistente com tratamento ativo.",
         "icone": "📉",
         "criterios": ["Perda de 5%", "60 dias de adesão"]},
        {"ordem": 5, "nome": "Manutenção Comportamental",
         "descricao": "Hábitos sólidos que sustentam o tratamento.",
         "icone": "🏆",
         "criterios": ["90 dias", "Hábitos estabelecidos"]},
    ],
}

_NOMES_JORNADA = {
    "general":   "Jornada de Emagrecimento",
    "fitness":   "Jornada Fitness",
    "bariatric": "Jornada Pós-Bariátrica",
    "glp1":      "Jornada GLP-1",
}


