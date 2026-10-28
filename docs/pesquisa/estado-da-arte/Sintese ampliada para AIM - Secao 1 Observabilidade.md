# Seção 1 — Observabilidade de infraestrutura e aplicações

## Contexto da seção

Observabilidade é a capacidade de compreender o estado interno de um sistema a partir de sinais que ele produz. Em aplicações distribuídas, um problema raramente fica restrito a um único processo: uma mudança em CPU, memória, disco ou rede pode coincidir com alterações de latência, throughput ou erros em uma API; chamadas entre componentes podem propagar efeitos e tornar difícil localizar onde o comportamento começou. A seção fundamenta a camada de coleta e análise do AIM, que precisa reunir telemetria de infraestrutura e aplicação em séries comparáveis ao longo do tempo.

Métricas, logs e traces cumprem papéis diferentes. Métricas descrevem séries agregadas e permitem acompanhar tendências e comportamento de recursos; logs registram eventos discretos e mensagens; traces conectam spans de uma solicitação ao longo de serviços. Integrá-los permite contextualizar uma degradação. OpenTelemetry e OTLP ajudam a padronizar instrumentação e transporte, mas não resolvem por si só a seleção dos sinais, a qualidade dos dados, sua persistência, a interpretação dos scores ou a validade do modelo. Portanto, OTLP é base de interoperabilidade do AIM, não método de detecção.

## O que a literatura já faz

Os trabalhos desta seção se complementam em três frentes. Sakinala (2025) discute práticas para instrumentar aplicações cloud-native e organizar a observabilidade em métricas, logs e traces. É uma fonte de orientação técnica: ajuda a justificar coleta padronizada, dashboards, alertas e integração entre sinais, mas não testa uma solução em condições experimentais próprias.

Bissig (2024) torna mais concreta a questão da arquitetura unificada e, sobretudo, do custo da instrumentação. O trabalho combina revisão, entrevistas semiestruturadas, protótipos e benchmark sintético. A arquitetura descrita usa OpenTelemetry/OTLP Collector para ingestão e ClickHouse/Grafana para consulta e visualização. Seu benchmark compara serviços instrumentados e não instrumentados e mede latências em diferentes percentis, além de CPU e memória. Os valores apresentados mostram que o overhead pode ser considerável e variar conforme linguagem, instrumentação e carga: no cenário Java, o texto reporta aumento de 10,7% em p50 e 77,5% em p99; na configuração mista Java/TypeScript, informa aumento de p95 de até 411%. Esses números não devem ser generalizados como custo esperado de toda instalação OpenTelemetry: são resultados do ambiente sintético e da configuração testada.

Vani (2025) descreve uma arquitetura de observação de sistemas distribuídos que integra telemetria, modelos de detecção/previsão, alertas e apoio operacional. O artigo relata um caso de produção e declara TPR de 93,8%, FPR de 3,7%, previsão de 89,4% dos eventos antes do impacto, redução de MTTR de 89 para 29 minutos e de incidentes mensais de 37 para 17. Esses números apontam métricas operacionais relevantes para um projeto como o AIM, mas o material consultado não oferece dados brutos, configuração completa, protocolo de rotulagem e desenho comparativo necessários para reproduzir os resultados ou atribuir as mudanças exclusivamente ao sistema proposto.

Em conjunto, os trabalhos descrevem um percurso: coletar sinais coerentes, correlacioná-los, analisá-los e apresentá-los de modo acionável. Eles também indicam que a própria coleta deve entrar na avaliação, porque instrumentação pode afetar a aplicação observada.

## Comparação entre os trabalhos

Sakinala é principalmente conceitual e prático; sua contribuição está em organizar componentes e práticas de observabilidade. Bissig combina investigação qualitativa com uma avaliação de overhead; oferece um procedimento mais concreto para testar a instrumentação, embora o ambiente seja sintético. Vani aproxima arquitetura e operação de produção, trazendo indicadores de detecção e resposta, mas os detalhes disponíveis são insuficientes para auditoria externa dos números.

Essa diferença importa para a fundamentação: uma recomendação técnica não tem o mesmo peso que um benchmark controlado, e nenhum dos três materiais deve ser apresentado como prova definitiva de que uma determinada arquitetura reduz incidentes em qualquer ambiente. Para AIM, a combinação mais sólida é usar Sakinala para explicar os conceitos, Bissig para justificar a medição do custo e Vani para discutir a relevância operacional de medir antecedência, ruído e tempo de resposta, com ressalva explícita sobre a reprodutibilidade.

## Limitações e pontos em aberto

Os trabalhos não oferecem um protocolo comum para selecionar métricas, alinhar frequências de coleta, tratar valores ausentes, controlar cardinalidade ou garantir sincronização temporal. Também não definem uma lista universal de sinais: métricas úteis variam conforme a arquitetura e o serviço. O benchmark de overhead não equivale a uma implantação de produção; o relato de Vani não expõe detalhes suficientes para repetição independente; e o survey técnico não produz estimativas quantitativas próprias.

Para uma avaliação experimental do AIM, ainda é necessário definir taxa de coleta e retenção, tratamento de atrasos e lacunas, estratégia de normalização, custo do collector e do armazenamento e forma de relacionar uma série de infraestrutura a uma série da API. As medições de overhead devem comparar instrumentação ligada e desligada sob a mesma carga e reportar não apenas médias, mas percentis de cauda, uso de recursos e volume de telemetria.

## Conexão com o AIM

A contribuição desta seção ao AIM é estabelecer a camada de dados e os requisitos para que a análise posterior seja válida. O sistema deve receber métricas OTLP de infraestrutura (por exemplo, CPU, memória, I/O e rede) e de aplicação/API (latência, throughput e taxa de erros), preservar timestamps e atributos que permitam associá-las a serviço, instância ou cenário, e armazenar histórico suficiente para comparação temporal. Logs e traces podem complementar a interpretação quando estiverem disponíveis, mas o foco experimental pode permanecer nas métricas para manter o escopo controlado.

AIM não deve confundir coleta padronizada com compreensão automática: OTLP entrega uma representação interoperável; a análise multivariada e temporal é que deverá testar se padrões conjuntos de infraestrutura se relacionam com degradação da aplicação. O resultado deve ser apresentado como evidência e apoio à decisão, e o custo da telemetria precisa ser medido para verificar se a observação altera significativamente o sistema avaliado.

## Critérios de projeto e avaliação derivados da seção

A literatura também permite derivar questões práticas que precisam ser tratadas antes de comparar modelos. Primeiro, as séries devem ser associáveis: cada medição precisa carregar um timestamp coerente e atributos suficientes para identificar origem e contexto, sem produzir cardinalidade que torne armazenamento e consulta inviáveis. Segundo, os sinais precisam ter qualidade conhecida. Lacunas, atrasos, duplicações e diferentes frequências de coleta podem criar correlações artificiais ou deslocar a relação temporal que se deseja investigar. Terceiro, as métricas de infraestrutura e de aplicação devem ser comparadas em janelas compatíveis. Uma média de um minuto não deve ser associada sem cuidado a uma latência agregada em outro período.

Uma experiência de overhead pode ser organizada com execução pareada: rodar o mesmo workload com instrumentação desativada e ativada, alternando ordem ou repetindo para controlar variação, e manter máquina, versões, carga e duração constantes. Além de p50, p95 e p99, convém registrar throughput, CPU, memória, rede e volume enviado ao collector. O objetivo não é apenas provar que os dados chegam, mas determinar se a coleta afeta a aplicação e se a resolução temporal escolhida é suficiente para identificar degradação.

Por fim, os indicadores operacionais citados em relatos de campo — como tempo para detectar, falsos alertas e MTTR — precisam de definições operacionais. MTTD deve especificar o início real do evento, o momento do primeiro alerta correto e se atrasos de ingestão estão incluídos. Contagem de incidentes deve usar o mesmo critério e período antes/depois. Sem essas definições, números aparentemente comparáveis podem refletir processos de rotulagem e operação diferentes.
## Texto acadêmico aproveitável

A observabilidade de aplicações distribuídas depende da coleta de sinais complementares que permitam acompanhar tanto o estado dos recursos computacionais quanto o comportamento percebido pela aplicação. Métricas oferecem uma representação temporal agregada, logs registram eventos e traces descrevem o percurso de solicitações entre componentes. A integração desses sinais favorece a contextualização de degradações, enquanto padrões de instrumentação e transporte, como OpenTelemetry e OTLP, contribuem para a interoperabilidade da coleta. Entretanto, a padronização do transporte não determina quais variáveis devem ser analisadas nem garante que a instrumentação seja isenta de custo.

Os trabalhos examinados apresentam evidências de naturezas distintas. Revisões técnicas organizam práticas para ambientes cloud-native; estudos de arquitetura unificada avaliam protótipos e mostram que a instrumentação pode afetar latências e recursos; relatos de produção apresentam indicadores operacionais promissores, mas nem sempre disponibilizam dados e procedimentos suficientes para reprodução independente. Assim, o uso desses resultados requer distinguir recomendações conceituais, medições controladas e alegações de campo. Para o AIM, essa literatura fundamenta uma ingestão padronizada de métricas de infraestrutura e de APIs, acompanhada de avaliação explícita do overhead, da qualidade temporal dos dados e da utilidade dos sinais para identificar padrões associados à degradação.

## Fontes consideradas

Sakinala (2025), *Monitoring and Observability for Cloud-Native Applications*; Bissig (2024), *Unified Application Observability in Cloud-Native Systems*; Vani (2025), *AI-Based Distributed Systems Observation System for Performance Optimization and Reliability Enhancement*. Livro *Site Reliability Engineering* excluído do conjunto analisado conforme escopo anterior.

