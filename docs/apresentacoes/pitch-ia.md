# AIM — Active Intelligent Monitoring

**Pitch revisado em:** 28 de outubro de 2026

## O problema

Quando uma API apresenta lentidão ou erros, as equipes precisam relacionar esse comportamento a métricas de infraestrutura e ao histórico do sistema. Os sinais costumam ser vistos separadamente, e a investigação pode exigir comparação manual de várias séries. Limites fixos continuam sendo uma referência possível, mas podem não representar o comportamento esperado em todos os cenários. A literatura também alerta que séries multivariadas, eventos longos, limiares e protocolos de avaliação tornam os resultados difíceis de comparar.

## A proposta

O AIM é uma pesquisa aplicada e PoC de monitoramento inteligente. A proposta é receber métricas de infraestrutura e de APIs por OTLP, organizá-las temporalmente, investigar métodos estatísticos e de aprendizado de máquina e apresentar séries, eventos e relações observadas em uma aplicação web com perfis de acesso. O objetivo é apoiar a investigação humana e avaliar experimentalmente se a análise conjunta acrescenta valor sobre baselines definidos para os mesmos cenários.

## O que será avaliado

A pesquisa deverá definir cenários rotulados, manter a ordem temporal entre treino, validação e teste, evitar o uso de informação futura na preparação e calibração, e comparar métodos simples com alternativas multivariadas. Serão consideradas medidas por ponto e por evento, falsos alertas, eventos perdidos, atraso de detecção e custo. Uma alegação de risco antecipado exige alvo e horizonte explícitos e teste cronológico reservado.

Thresholds estáticos e variáveis são opções condicionadas ao cenário. A previsão de valores, a detecção de anomalias, a detecção de mudanças de regime e a estimativa de risco respondem a perguntas diferentes. Correlação temporal pode apoiar uma hipótese de investigação, mas não comprova causa. RCA com traces, topologia ou inferência causal depende de dados e validação específicos e não é promessa do núcleo da PoC.

## Limites atuais

A escolha do modelo, dos dados, dos cenários, dos limiares e da arquitetura de software permanece em aberto. Ainda não há resultados que permitam afirmar redução de MTTD/MTTR, superioridade sobre outros métodos ou ganhos universais. O AIM não executa remediação automática. Um LLM pode ser investigado futuramente como apoio complementar para apresentar evidências, sem papel de decisão e sem garantia de inclusão.

## Princípio

O AIM deve tornar observáveis os sinais e critérios usados para sinalizar um evento, para que equipes técnicas possam examinar o contexto e decidir os próximos passos. A PoC avaliará em que condições essa análise ajuda; não presume que um score isolado explique ou antecipe toda falha.

