# Histórico de evolução do AIM

**Revisado em:** 28 de outubro de 2026

Este documento registra as principais mudanças de direção do AIM. Ele diferencia a concepção inicial do escopo que passou a orientar o TCC.

## Concepção inicial — orquestração e intervenção automática

Nos primeiros materiais do projeto, o AIM era apresentado como **Active Orchestration Service**. A proposta incluía monitorar aplicações distribuídas via OpenTelemetry, detectar cenários definidos em YAML e executar intervenções automáticas nos repositórios dos serviços, com apoio do GitHub Copilot SDK, guardrails e notificações.

Essa concepção aparece nos documentos legados `archive/aim_old/BRIEF.docx`, `archive/aim_old/MVP-SCOPE.docx` e `archive/aim_old/PRD.docx`. Esses arquivos são mantidos como histórico da ideia, não como definição do escopo vigente.

## Foco acadêmico — observabilidade e análise de anomalias

O foco do TCC passou a ser a análise multivariada de anomalias temporais em infraestruturas computacionais e a relação desses padrões com o comportamento de APIs e aplicações web. O projeto passou a priorizar coleta padronizada de telemetria via OTLP, análise estatística e aprendizado de máquina, correlação entre camadas e apresentação de resultados para apoiar equipes técnicas.

O capítulo 1 do TCC, `AIM capítulo 1 (1 bimestre) (3).docx`, registra o título **“AIM: Uma análise multivariada de anomalias temporais em infraestruturas computacionais”** e expande a proposta para uma aplicação web com visualização de anomalias, séries temporais, indicadores de saúde e controle de acesso por perfil (RBAC).

## Mudança de escopo — sem remediação automática

O escopo atual não inclui correção automática de código, commits, pull requests, deploys de correção nem remediação autônoma da infraestrutura. O AIM busca investigar sinais de anomalia, relacioná-los temporalmente ao comportamento das aplicações e avaliar se a identificação pode apoiar a investigação e a antecipação em cenários definidos. Essa utilidade ainda requer validação.

Assim, a prevenção ou mitigação descrita no TCC corresponde ao apoio fornecido por detecção, análise, correlação e visualização das evidências. Não significa que o AIM execute reparos automaticamente.

## Evolução do tratamento de limites

Os materiais anteriores descreviam thresholds estáticos e configuráveis. O entendimento atual reconhece que limites estáticos podem não acompanhar variações normais de carga e comportamento dos sistemas, contribuindo para sobrecarga de alertas e falsos positivos. Por isso, o projeto considera **limites variáveis em alguns cenários**.

Essa mudança não define que todos os limites serão variáveis. A escolha entre limites estáticos e variáveis deverá considerar o cenário, as métricas, a evidência disponível e os resultados experimentais. Resultados de scoring dinâmico em benchmarks não demonstram superioridade universal de limiares variáveis. Os métodos específicos e os critérios para selecionar cada abordagem ainda precisam ser definidos e avaliados.

## Referências de direção

- Estado do TCC: `AIM capítulo 1 (1 bimestre) (3).docx`.
- Documento-base atualizado em 28 de outubro de 2026: `README.md`.
- Materiais da concepção inicial de intervenção automática: `archive/aim_old/`.

## Revisão documental — 28 de outubro de 2026

A direção vigente foi alinhada ao estado da arte sintetizado localmente em quatro frentes: observabilidade, detecção de anomalias, séries temporais e mudanças, e correlação/RCA. A revisão reforça a separação entre detecção, forecasting, risco, change points e diagnóstico; explicita validação temporal, baselines e avaliação por evento; e mantém os métodos e ganhos como questões a avaliar, sem tratá-los como funcionalidades ou resultados do AIM.



