# Introdução

O AIM é um projeto voltado para observabilidade ativa em aplicações distribuídas, com foco em antecipar situações de risco antes que elas se transformem em falhas percebidas pelo usuário final. A proposta nasce da necessidade de ir além do monitoramento tradicional, no qual as métricas são apenas registradas e analisadas após a ocorrência de um incidente.

Neste projeto, a ideia central é transformar métricas dos serviços onde as operações acontecem em informação útil para o monitoramento e detecção. O AIM busca interpretar padrões, identificar variações relevantes e associar esses sinais a possíveis cenários de desastre.

O mapeamento de metricas irá consideradar elementos como:

- identificação do serviço de origem;
- tipo de métrica coletada;
- variação ao longo do tempo;
- limiares definidos para cada serviço;
- correlação entre sinais de diferentes aplicações;
- persistência de comportamento anormal.

Com essa estrutura, o AIM poderá aplicar modelos matemáticos estáticos ou dinâmicos para reconhecer tendências e antecipar possíveis problemas. 

O necessário de infraestrutura será composto por:

- um banco de dados para persistência de métricas, eventos e histórico de previsões;
- instalação on-premises;
- um ambiente com as aplicações orquestradas.