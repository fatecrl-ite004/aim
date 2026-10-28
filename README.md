# AIM — Active Intelligent Monitoring

> Documento-base do projeto acadêmico e da prova de conceito (PoC). Atualizado em 28 de outubro de 2026.
>
> **Direção vigente:** analisar anomalias temporais multivariadas em métricas de infraestrutura e APIs, apresentar evidências em uma aplicação web e apoiar a investigação operacional. Modelos, limiares, cenários e resultados ainda dependem de definição e avaliação experimental.

## Identidade do projeto

- **Nome:** AIM — Active Intelligent Monitoring.
- **Título do TCC:** *AIM: Uma análise multivariada de anomalias temporais em infraestruturas computacionais*.
- **Equipe:** Pedro Augusto de Melo Borges, Thiago Guerra Soares e João Paulo Cruz de Almeida Lima.
- **Natureza:** pesquisa aplicada e PoC acadêmica.
- **Telemetria prevista:** métricas de infraestrutura e de aplicação/API transportadas por OTLP.
- **Usuários de referência:** equipes de confiabilidade e desenvolvimento, liderança de suporte de produtos, arquitetura e gestão de produto.

## Problema e objetivo

Em sistemas computacionais, sinais de infraestrutura e sintomas percebidos pela aplicação são frequentemente examinados em painéis separados. A análise manual pode tornar difícil entender quando uma alteração começou, quais sinais mudaram em conjunto e se o comportamento observado coincide com uma degradação de API. Limites estáticos podem ser úteis em alguns contextos, mas também podem gerar ruído quando a variação normal depende de carga, sazonalidade ou cenário.

O AIM investiga como coletar e analisar séries temporais multivariadas para identificar anomalias, relacionar padrões de infraestrutura a efeitos observados em APIs e apresentar evidências que ajudem uma pessoa a investigar. Também será avaliado se certos métodos permitem sinalizar risco antes do início de eventos rotulados. Antecipação é uma hipótese experimental, não uma capacidade garantida.

**Pergunta de pesquisa de trabalho:** como a análise conjunta e temporal de métricas de infraestrutura e API pode contribuir para identificar degradações e apoiar sua investigação, quando comparada a baselines definidos para os mesmos cenários?

## Escopo e fronteiras

A PoC considera ingestão de métricas OTLP, organização temporal dos dados, análise estatística e/ou modelos em investigação, apresentação web com visualizações e indicadores, e controle de acesso por perfil (RBAC). O escopo de análise se concentra em métricas de infraestrutura — por exemplo CPU, memória, I/O e rede — e de aplicação/API — por exemplo latência, throughput e erros. A lista efetiva depende dos cenários e da disponibilidade de instrumentação.

A aplicação deve apoiar a investigação mostrando séries, intervalos, scores e sinais associados a um evento. A correlação temporal pode revelar associação útil, mas não demonstra por si só que uma métrica causou outra. Logs, traces e topologia podem ser complementos se forem disponíveis e se sua inclusão for justificada; não são pré-requisitos assumidos para o núcleo da PoC.

O AIM não executa correções automáticas em código ou infraestrutura, não cria commits ou pull requests, não faz deploy e não substitui a decisão de operadores. Notificação, canal de entrega e funcionalidades detalhadas ainda precisam ser definidos. Um LLM, caso investigado, é componente complementar para apresentar ou organizar evidências já produzidas, sujeito a validação; não é motor decisor nem funcionalidade garantida.

## Arquitetura conceitual proposta

```text
Infraestrutura e APIs
        │ métricas via OTLP
        ▼
Ingestão, validação e alinhamento temporal
        ▼
Armazenamento e preparação das séries
        ▼
Baselines estatísticos e métodos em avaliação
        ▼
Scores, eventos e associações temporais
        ▼
Aplicação web: visualização, contexto e RBAC
        ▼
Investigação e decisão por pessoas
```

Este fluxo representa uma arquitetura de pesquisa, não uma stack fechada ou implementação concluída. Persistência, frequência, retenção, normalização, componentes de software e método de detecção permanecem decisões em aberto. OTLP padroniza transporte e representação da telemetria; não define detector, interpretação nem qualidade dos dados.

## Objetivos analíticos que não devem ser confundidos

- **Detecção de anomalia:** identificar observações, janelas ou eventos que diferem do comportamento de referência. É preciso definir unidade, score e regra de decisão.
- **Forecasting:** estimar valores futuros de uma série. Erro de previsão não equivale automaticamente a risco de incidente.
- **Antecipação ou risco:** estimar se um evento definido ocorrerá dentro de um horizonte. Exige rótulos, horizonte, comparação e medida de antecedência; ainda é uma hipótese a avaliar.
- **Change point:** localizar uma alteração de regime. Uma mudança pode ser uma nova condição normal, não necessariamente uma anomalia ou falha.
- **Correlação e associação temporal:** descrever sinais que variam juntos ou em sequência. Isso não prova direção causal.
- **RCA e causalidade:** ordenar ou explicar causas candidatas sob dados e hipóteses específicos. RCA é uma linha de investigação complementar; o AIM não deve afirmar diagnóstico causal sem desenho e evidência que o sustentem.

## Plano de avaliação a definir

A avaliação deve começar com cenários experimentais explícitos e um *ground truth* auditável, por exemplo degradações controladas com início, duração, componente e impacto conhecidos. A divisão de dados precisa respeitar cronologia: ajustar transformações e modelos apenas no período de treino, escolher parâmetros e limiares na validação e reservar um período futuro para teste. Janelas ou rótulos que compartilhem observações entre partições, normalização ajustada com dados futuros, escolha de limiar com rótulos do teste e seleção repetida do melhor resultado no teste podem causar vazamento e devem ser evitadas.

Comparações devem usar a mesma telemetria, cenário, split e regra de avaliação. Baselines candidatos incluem limites estáticos configurados por cenário e métodos estatísticos simples; a seleção final depende do desenho experimental. Métodos mais complexos só devem ser mantidos se apresentarem contribuição mensurável. Repetições/sementes são relevantes quando houver aleatoriedade. Ablações podem retirar, por vez, métricas de infraestrutura, métricas de API, dependências multivariadas, contexto temporal ou componentes opcionais, para estimar o que cada grupo acrescenta.

Reportar métricas pontuais e por evento: precisão, recall e F1 conforme definição explícita; PR-AUC quando apropriada ao desbalanceamento; eventos detectados, eventos perdidos, falsos alertas por unidade de tempo/serviço, atraso de detecção e antecedência somente para um alvo de risco definido. Métricas event-wise devem declarar tolerância temporal e regra de correspondência. Evitar depender exclusivamente de point-adjust ou do melhor limiar retrospectivo, pois podem inflar a avaliação e não representam necessariamente uso prospectivo. Também medir custo computacional, atraso e, se viável, overhead da instrumentação.

Para associações com APIs, analisar alinhamento, defasagens e consistência entre cenários. Uma alteração de infraestrutura que precede um sintoma é evidência temporal, não prova de causa. Se houver avaliação de ranking de sinais, usar falhas controladas ou avaliação especializada e relatar estabilidade e limitações. Não comparar números de artigos com números da PoC como se fossem diretamente equivalentes.

## Evidências da literatura local e limites

As sínteses em `docs/pesquisa/estado-da-arte/` orientam perguntas e protocolos, não uma alegação de que o AIM já implementa esses métodos ou supera alternativas:

- **Observabilidade:** Sakinala (2025) organiza práticas cloud-native; Bissig (2024) combina entrevistas, protótipos e benchmark sintético e mostra que overhead depende da configuração; Vani (2025) relata resultados operacionais promissores, mas os detalhes disponíveis não permitem atribuição ou reprodução independentes. Use-os para requisitos de instrumentação e mensuração, não como garantia de ganho.
- **Detecção:** Chandola, Banerjee e Kumar (2009) oferecem taxonomia; Garg et al. (2021) mostram dependência do ranking em relação ao scoring e propõem avaliação por evento; Islam et al. (2021) descrevem sistema industrial; Huang et al. (2017) e Wagner et al. (2023) oferecem métodos e protocolos/benchmark. Datasets, rótulos, limiares e métricas variam, sem vencedor universal.
- **Séries e mudanças:** Aminikhanghahi e Cook (2017) distinguem métodos de change point; Sivaraman (2022) motiva limiares adaptativos, mas o resumo consultado não descreve detalhe suficiente para reproduzir seu percentual reportado; TopoMAD (He et al., 2020/2021) e InterFusion (Su et al., 2021) são candidatos de pesquisa para dependências temporais e entre métricas, não escolhas finais do AIM. Resultados com limiar ótimo ou point-adjust exigem cautela prospectiva.
- **Correlação e RCA:** Soldani e Brogi (2021) organizam técnicas e requisitos; Wu et al. (2021) observam que desempenho causal varia por falha e seleção de sinais; Sleuth (Gan et al.) e TraceDiag (Ding et al., 2023) exploram traces/topologia e dados específicos. Esses métodos requerem entradas e ground truth mais ricos, e seus resultados não autorizam atribuir causalidade a correlações de métricas agregadas.

Para a leitura detalhada, limites de evidência e referências completas, consulte as [quatro sínteses ampliadas](docs/pesquisa/estado-da-arte/) ([observabilidade](docs/pesquisa/estado-da-arte/Sintese%20ampliada%20para%20AIM%20-%20Secao%201%20Observabilidade.md), [detecção](docs/pesquisa/estado-da-arte/Sintese%20ampliada%20para%20AIM%20-%20Secao%202%20Deteccao%20de%20anomalias.md), [séries temporais](docs/pesquisa/estado-da-arte/Sintese%20ampliada%20para%20AIM%20-%20Secao%203%20Series%20temporais.md) e [correlação e RCA](docs/pesquisa/estado-da-arte/Sintese%20ampliada%20para%20AIM%20-%20Secao%204%20Correlacao%20e%20RCA.md)) e os respectivos resumos reutilizáveis. As referências bibliográficas aqui seguem os títulos e atribuições dessas sínteses locais; este documento não afirma constituir revisão global atualizada.

## Decisões em aberto

- Cenários, carga, eventos e rótulos (*ground truth*).
- Métricas, granularidade, frequência, alinhamento, retenção e tratamento de lacunas.
- Baselines e famílias de modelos a comparar.
- Definição de limiar fixo ou variável por cenário e método de calibração sem vazamento.
- Distinção operacional entre detecção, previsão de valores, risco, change point e diagnóstico.
- Métricas pontuais, event-wise e operacionais, tolerâncias e horizonte de avaliação.
- Contribuição incremental de infraestrutura além das métricas de API.
- Requisitos da aplicação, perfis RBAC, visualizações e fluxo de investigação.
- Custo de coleta, processamento, armazenamento e modelos.
- Se LLM será avaliado como apoio de apresentação, com limites e validação adequados.

## Mapa da documentação

- `docs/projeto/estado-atual.md`: direção vigente, escopo e pendências.
- `docs/projeto/historico.md`: evolução entre concepção inicial e pesquisa atual.
- `docs/requisitos/personas.md`, `docs/requisitos/mapas-de-empatia.md` e `docs/requisitos/cenarios-de-uso.md`: hipóteses de usuários e situações de uso; expectativas não equivalem a funcionalidades já implementadas.
- `docs/apresentacoes/pitch-ia.md`: narrativa concisa do problema e da proposta, alinhada ao escopo experimental.
- `archive/aim_old/`: documentos da concepção anterior, mantidos como histórico e ignorados pelo Git.

## Como navegar na estrutura reorganizada

- [Visão e escopo](docs/projeto/visao-e-escopo.md), [estado atual](docs/projeto/estado-atual.md), [histórico](docs/projeto/historico.md) e [glossário](docs/projeto/glossario.md).
- [Requisitos](docs/requisitos/requisitos.md), [personas](docs/requisitos/personas.md), [mapas de empatia](docs/requisitos/mapas-de-empatia.md) e [cenários de uso](docs/requisitos/cenarios-de-uso.md).
- [Arquitetura conceitual](docs/arquitetura/visao-geral.md), [pipeline analítico](docs/arquitetura/pipeline-analitico.md) e [modelo/dicionário de dados](docs/arquitetura/dados/modelo-de-dados.md).
- [Pesquisa documentada](docs/pesquisa/README.md), [sínteses locais](docs/pesquisa/estado-da-arte/) e [protocolo experimental](docs/pesquisa/protocolo-experimental.md).
- [Pesquisa executável](research/README.md), [sistema PoC](system/README.md), [convenções de dados](data/README.md) e [infraestrutura](infra/README.md).
- [Pitch](docs/apresentacoes/pitch-ia.md), [decisões](docs/decisoes/README.md), [desenvolvimento](docs/desenvolvimento/README.md) e [arquivo histórico](archive/README.md).

A estrutura diferencia documentação de pesquisa (`docs/pesquisa/`), artefatos experimentais executáveis (`research/`) e componentes de sistema (`system/`). Pastas vazias representam destinos organizacionais, não implementação ou decisão de tecnologia.

