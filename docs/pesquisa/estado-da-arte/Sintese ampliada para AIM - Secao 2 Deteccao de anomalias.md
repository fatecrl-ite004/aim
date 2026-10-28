# Seção 2 — Detecção de anomalias em séries temporais

## Contexto da seção

A detecção de anomalias procura identificar comportamentos que diferem de uma referência de normalidade. Em séries temporais de infraestrutura, essa tarefa não se resume a verificar se uma métrica ultrapassou um limite: um valor pode ser normal em um horário de pico e anômalo em outro contexto; uma degradação pode aparecer como uma sequência prolongada de desvios; e uma falha pode se manifestar apenas na relação entre várias métricas. Para o AIM, essa literatura fundamenta como formular o problema, selecionar modelos, definir scores e avaliar os resultados sem confundir bom ajuste retrospectivo com utilidade operacional.

O primeiro cuidado é explicitar o que constitui uma anomalia. Chandola, Banerjee e Kumar (2009) distinguem anomalias pontuais, contextuais e coletivas. Uma anomalia pontual é um valor individual discrepante; uma contextual depende de atributos de contexto, como período do dia ou carga; uma coletiva é uma sequência ou conjunto que se torna anormal pela combinação, ainda que seus pontos isolados não pareçam extremos. Essa distinção é importante para infraestrutura: CPU alta pode ser esperada em uma execução de carga planejada, mas uma elevação simultânea de CPU, latência e erros HTTP pode constituir uma condição de degradação mais significativa.

## O que a literatura já faz

### Taxonomias e famílias de métodos

O survey de Chandola et al. organiza os métodos em seis grupos gerais: classificação, vizinhança mais próxima, clustering, métodos estatísticos, teoria da informação e métodos espectrais. A escolha depende da existência de exemplos rotulados, da hipótese sobre a normalidade, da dimensionalidade e da forma temporal dos dados. O survey não compara modelos por um experimento próprio; sua contribuição para o AIM está em mostrar que não existe detector adequado sem uma definição do contexto e da hipótese que o método assume.

Huang et al. (2017) apresentam RLPSVDD, uma adaptação de Support Vector Data Description para detecção de anomalias em séries. A representação usa atraso temporal e janelas deslizantes com saltos, e o método estima uma fronteira que descreve regiões consideradas normais. A avaliação usa séries do Yahoo A1 (67 séries) e coleções associadas a Twitter, Etsy e Numenta, com comparação a alternativas contemporâneas ao trabalho. O artigo relata resultados competitivos, mas a seleção dos parâmetros minimiza falsos positivos e falsos negativos com rótulos disponíveis na própria série. Esse detalhe muda a interpretação: o detector pode ser não supervisionado no ajuste da fronteira, mas a escolha retrospectiva de hiperparâmetros usa informação supervisionada. Uma reprodução atual deve reservar validação distinta do teste e evitar acesso aos rótulos finais para calibrar limiar.

### Avaliação de detectores e métricas

Garg et al. (2021) deslocam o foco para a forma de avaliar. O estudo compara dez modelos e quatro funções de score em sete datasets multivariados que cobrem 114 entidades, repetindo experimentos com cinco sementes e aplicando teste de Friedman e pós-teste de Hochberg para comparar rankings. Os autores propõem FC1, que combina precisão pontual e recall por evento para lidar melhor com eventos anômalos longos: métricas pontuais podem contar muitos acertos dentro de um único incidente e, assim, exagerar a qualidade operacional.

Um dos achados centrais é que o ranking dos detectores depende da função que converte a saída do modelo em score. Funções dinâmicas como Gauss-D e Gauss-D-K superam opções estáticas em parte dos cenários; um autoencoder channel-wise simples (UAE) também alcança posição média alta. Isso não estabelece um vencedor universal: mostra que comparação confiável exige avaliar modelo e scoring em conjunto e analisar a unidade de interesse (ponto, janela ou evento).

Wagner et al. (2023), com TimeSeAD, expandem essa preocupação para um benchmark de 28 métodos profundos em 21 conjuntos (15 subconjuntos SMD e seis Exathlon, segundo filtros descritos no estudo). Além de resultados comparativos, auditam problemas dos datasets: posição enviesada das anomalias, janelas anormais muito longas e distribuição de treino diferente da de teste. O artigo apresenta medidas temporais como TRec/TPrec e uma formulação de F1 sensível a evento, buscando aproximar a avaliação daquilo que interessa a um operador: detectar eventos completos, sem aceitar excesso de alertas. O resultado geral é que não há modelo profundo sempre melhor e que métodos mais antigos continuam competitivos sob protocolos consistentes.

### Sistemas em operação

Islam et al. (2021) descrevem a implantação de detecção em uma plataforma cloud de grande escala. O sistema usa um autoencoder GRU sobre telemetria HTTP agregada a cada cinco minutos. Os dados são organizados por endpoint, método e status e incluem estatísticas e padrões de sazonalidade. O erro de reconstrução de janelas é transformado em score/likelihood; há inicialização com cerca de 9000 pontos (aproximadamente um mês), atualizações online, retreino em lote a cada seis horas e um canal para feedback humano dos operadores.

Em um conjunto de uma VM com 265.200 linhas, os autores reportam F1=0,8489 e precisão=0,7374. Relatam também ausência de falsos negativos conforme o feedback dos operadores e uma detecção cerca de 20 minutos antes em um caso de produção. Esses resultados têm níveis distintos de evidência: as métricas numéricas vêm de um conjunto descrito; a antecedência e a validação humana são relatos operacionais, sem desenho experimental comparativo suficiente para concluir um ganho geral de 20 minutos. O artigo não disponibiliza no material consultado os dados multidimensionais brutos e todas as configurações necessárias para reprodução exata.

## Comparação entre os trabalhos

Os artigos cobrem perguntas complementares. Chandola et al. fornecem a taxonomia conceitual; Huang et al. detalham um método de fronteira para séries e levantam a questão de seleção de parâmetros com labels; Garg et al. demonstram que score e métrica afetam as conclusões sobre o modelo; TimeSeAD reúne uma avaliação ampla e expõe vieses dos benchmarks; Islam et al. mostra como um detector pode ser incorporado a um fluxo de produção com atualização e supervisão humana.

Não é correto comparar diretamente o F1 de um sistema industrial, o ranking agregado de um benchmark e resultados de datasets históricos: mudam a unidade de avaliação, rótulos, thresholds, distribuição de dados e regras de ajuste. Tampouco a maior sofisticação do modelo implica melhor resultado. UAE, um autoencoder simples, obtém bom ranking em parte da avaliação de Garg et al.; TimeSeAD também encontra métodos não recentes competitivos. O argumento aplicável ao AIM é que o modelo deve ser escolhido por desempenho sob o cenário experimental definido, robustez, custo e possibilidade de validação, e não por novidade arquitetural.

## Limitações e pontos em aberto

A literatura ainda enfrenta inconsistência entre datasets, rótulos, métricas, tratamento de eventos e seleção de thresholds. Métricas como AUROC podem parecer boas mesmo sob forte desbalanceamento, enquanto métricas pontuais podem inflar acertos em incidentes longos. O point-adjust, quando usado para marcar como corretos pontos de um evento após detectar apenas parte dele, pode favorecer modelos de forma pouco realista. “Best F1” obtido ao testar vários limiares nos dados rotulados também revela um limite superior retrospectivo, não necessariamente o desempenho que será obtido online.

Há ainda diferenças entre detectar anomalia, prever risco antes de uma falha, detectar mudança permanente de regime e diagnosticar a causa. Esses objetivos exigem rótulos, horizontes e métricas diferentes. Treino contaminado, mudança de carga, dados ausentes, dependência entre entidades e custo de atualizar modelos também podem alterar resultados. A validação deve separar períodos cronologicamente e reservar o conjunto final para avaliação única, especialmente quando há sazonalidade e drift.

## Conexão com o AIM

AIM precisa comparar sinais de infraestrutura e APIs no tempo e, por isso, não deve reduzir a tarefa a thresholds isolados. Esta seção orienta o projeto a definir uma unidade de evento (por exemplo, janela de degradação da API), identificar quais variáveis e períodos compõem a normalidade e comparar um baseline simples com detectores multivariados. Uma abordagem inicial pode calcular scores por modelo e por grupo de métricas, mantendo thresholds fixos e variáveis como alternativas experimentais, sem assumir de antemão que o threshold dinâmico sempre vence.

O protocolo do AIM deve usar divisão temporal entre treino, validação e teste; documentar normalização e seleção de limiar; repetir sementes quando o modelo for estocástico; medir precisão, recall, F1 e PR-AUC; incluir medidas por evento, atraso de detecção, falsos alertas por dia e custo computacional. Deve relatar os resultados por cenário e entidade, não apenas uma média agregada. Para alegar antecipação, o ground truth precisa definir o início do incidente e o horizonte de antecedência; para alegar correlação entre infraestrutura e aplicação, é necessário mostrar alinhamento temporal e associação observada, sem chamar isso de causalidade comprovada.

## Texto acadêmico aproveitável

A detecção de anomalias em séries temporais é um problema dependente do contexto, da unidade de análise e das hipóteses adotadas sobre o comportamento normal. A literatura distingue anomalias pontuais, contextuais e coletivas, e reúne métodos estatísticos, classificadores, técnicas baseadas em vizinhança, clustering, teoria da informação e modelos de representação. Em infraestrutura computacional, essa variedade é relevante porque uma métrica isolada pode apresentar oscilações legítimas, enquanto desvios conjuntos ao longo do tempo podem indicar uma condição de degradação.

Estudos comparativos mostram que a avaliação não é determinada apenas pela arquitetura do detector. A função de scoring, o threshold, o tratamento de eventos longos e a distribuição dos conjuntos influenciam o ranking dos métodos. Comparações multivariadas e benchmarks recentes indicam que não há um modelo universalmente superior e que alternativas simples podem competir com redes mais complexas. Estudos de implantação demonstram a possibilidade de usar autoencoders recorrentes em fluxos de telemetria com atualização e feedback operacional, mas a disponibilidade limitada de dados e configurações restringe a reprodução independente de alguns resultados de produção.

Dessa forma, a avaliação do AIM deve separar treino, validação e teste no tempo, comparar modelos com baselines, explicitar como os scores e limiares são calculados e reportar medidas tanto por ponto quanto por evento. Além das métricas de classificação, são relevantes a antecedência, a quantidade de alertas falsos, a estabilidade sob mudanças de comportamento e o custo de execução. Essa abordagem permite avaliar se a análise conjunta de métricas de infraestrutura e aplicação acrescenta informação em relação ao monitoramento pontual, sem atribuir ao detector capacidades de previsão ou diagnóstico causal que não tenham sido verificadas experimentalmente.

## Fontes consideradas

Chandola, Banerjee e Kumar (2009), *Anomaly Detection: A Survey*; Garg et al. (2021), *An Evaluation of Anomaly Detection and Diagnosis in Multivariate Time Series*; Islam et al. (2021), *Anomaly Detection in a Large-Scale Cloud Platform*; Huang et al. (2017), *Time Series Anomaly Detection for Trustworthy Services*; Wagner et al. (2023), *TimeSeAD: Benchmarking Deep Multivariate Time-Series Anomaly Detection*.
