# AIM - PoC

- **Equipe:** Pedro Augusto de Melo Borges, Thiago Guerra Soares e João Paulo Cruz de Almeida Lima
- **Público-alvo:** Times de engenharia, DevOps e SRE que precisam agir antes que falhas afetem o usuário final
- **Tipo de aplicação:** Serviço backend de observabilidade ativa
- **Plataforma(s):** .NET Aspire, ambiente servidor
- **Domínio:** Observabilidade, confiabilidade e engenharia de software
- **Previsão de entrega:** A definir

## Visão geral

O AIM é uma proposta de observabilidade ativa para aplicações distribuídas em .NET.

Em vez de apenas registrar e exibir métricas para análise posterior, o sistema passa a atuar de forma preventiva: ele coleta métricas via OTLP, correlaciona sinais de diferentes serviços, aplica modelos matemáticos estáticos ou dinâmicos para previsão de casos de desastre e dispara notificações em tempo real quando identifica risco de degradação.

A ideia central do PoC é transformar a observabilidade em um mecanismo atuante, capaz de antecipar falhas e orientar a resposta dos envolvidos antes que o problema se torne perceptível para o usuário final.

## Problema

Em sistemas distribuídos, métricas normalmente são usadas de forma reativa. Primeiro a falha acontece, depois os dados são analisados para descobrir a causa.

Esse modelo é limitado porque:

- a detecção costuma chegar tarde demais;
- a correlação entre sinais de diferentes serviços nem sempre é simples;
- equipes dependem de interpretação humana para perceber padrões de risco;
- problemas recorrentes podem ser detectados apenas após impacto em produção.

Para o TCC, o problema de pesquisa passa a ser: como transformar a observabilidade em uma camada ativa, capaz de prever cenários de desastre com base em séries temporais e apoiar a resposta em tempo real?

## Solução proposta

O AIM será um serviço que consome métricas OTLP de aplicações executadas no Aspire, organiza os dados por serviço e aplica análise temporal para identificar padrões de degradação.

A solução proposta no PoC inclui:

- extração contínua de métricas via OTLP;
- correlação entre métricas de múltiplos serviços;
- definição de thresholds específicos por serviço;
- aplicação de modelos matemáticos para previsão de desastres;
- notificação em tempo real para os responsáveis quando um risco for identificado.

O sistema não tenta resolver tudo de forma automática neste estágio. O foco é provar que a observabilidade pode sair do papel passivo de monitoramento e passar a operar como um componente de previsão e alerta antecipado.

## Funcionalidades

- Coletar métricas OTLP das aplicações executadas no Aspire
- Orquestrar 3 aplicações em um ambiente controlado
- Correlacionar sinais entre serviços diferentes
- Manter thresholds por serviço para reduzir ruído e melhorar direção da análise
- Trabalhar com séries temporais para identificar tendência, persistência e variação anormal
- Prever casos de desastre com base em modelos matemáticos estáticos ou dinâmicos
- Notificar em tempo real os envolvidos quando houver risco relevante
- Registrar eventos para validação experimental do comportamento do sistema

## Diferencial / Concorrência

Ferramentas tradicionais de observabilidade, como painéis e alertas, normalmente se concentram em exibir o que já está acontecendo.

O diferencial do AIM neste PoC é o deslocamento de foco:

- de observação para previsão;
- de métrica isolada para correlação temporal;
- de alerta genérico para direcionamento por serviço;
- de análise posterior para resposta antecipada.

Exemplos de ferramentas concorrentes ou complementares:

- Datadog
- Grafana

## Inovação / Criatividade

O ponto mais interessante do projeto é tratar observabilidade como um mecanismo ativo de decisão.

Os elementos de inovação do PoC são:

- uso de séries temporais para correlacionar métricas;
- previsão de casos de desastre com modelos matemáticos;
- thresholds por serviço para adaptar a detecção ao contexto;
- operação em tempo real sobre um ambiente orquestrado com Aspire.

## Escopo do projeto

### Essencial (MVP - obrigatório)

- Orquestrar 3 aplicações rodando em cima do Aspire
- Extrair métricas via OTLP
- Correlacionar os dados coletados entre os serviços
- Aplicar análise por séries temporais
- Definir thresholds por serviço
- Prever situações de desastre com base nos dados observados
- Notificar em tempo real os envolvidos quando um risco for detectado

### Importante (se houver tempo)

- Ajustar thresholds por serviço de forma configurável
- Melhorar a correlação entre métricas com múltiplos cenários
- Comparar modelos matemáticos estáticos e dinâmicos
- Registrar histórico das previsões e alertas para análise posterior

### Opcional (baixa prioridade)

- Painel visual simples para acompanhamento
- Simulações de cenários de desastre
- Sugestão de ação preventiva baseada no padrão identificado

## Planejamento (simplificado)

| Etapa | Descrição | Prazo |
| ----- | --------- | ----- |
| 1 | Definição do recorte do PoC e dos cenários de teste | A definir |
| 2 | Orquestração das 3 aplicações no Aspire | A definir |
| 3 | Coleta de métricas OTLP e organização temporal | A definir |
| 4 | Correlação, thresholds por serviço e previsão | A definir |
| 5 | Notificação em tempo real e validação do fluxo | A definir |
| 6 | Testes finais e consolidação do TCC | A definir |

## Tecnologias (inicialmente previstas)

- .NET
- .NET Aspire
- OTLP / OpenTelemetry
- Modelos matemáticos para análise temporal
- Canal de notificação em tempo real
