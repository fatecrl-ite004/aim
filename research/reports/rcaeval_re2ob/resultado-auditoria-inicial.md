# RCAEval RE2-OB: auditoria de origem e Wave v3

**Estado:** origem dos campos revisada no código do RCAEval; pipeline e preflight v3 executados. Nenhuma janela tem P/Q/D válido porque os spans da operação API de entrada não contêm status de erro.

## Dados locais

O checkout `C:\Users\00001\Downloads\RCAEval-main\RCAEval-main` contém framework e utilitários. Os 30 casos selecionados (CPU e delay; 5 serviços × 2 falhas × 3 repetições) foram baixados para `research/data/rcaeval/re2ob_cpu_delay/`, ignorado pelo Git. Cada caso tem 1.441 pontos de métricas a cada segundo e Parquet de traces.

## O que o código-fonte confirma

No [toolkit do RCAEval](https://github.com/phamquiluan/RCAEval/blob/main/RCAEval/agent/toolkit.py), o leitor converte timestamps do span por magnitude e declara que `duration` Jaeger está em microssegundos. O `trace_summary` agrupa por `serviceName` e `operationName`, chama as linhas do grupo de requests, calcula p50/p90 e classifica status gRPC `0` e HTTP `200–399` como sucesso; outros status explícitos viram erros. Quando não há status, o próprio toolkit informa que os traces não carregam status e direciona para a série `tracets_err`.

O conjunto tem muitas operações associadas a `frontendservice`. Agregar todas contaria também chamadas RPC internas. Inspeção em todos os 30 casos mostrou `operationName=frontend` como span raiz da entrada externa. Seus 549.502 spans têm timestamp e duração, mas **zero têm `statusCode`**. Portanto não é correto preencher falhas como zero. A média da duração pode ser convertida para segundos usando a unidade documentada; o valor de erro continua ausente.

O código do RCAEval também espera arquivos auxiliares `tracets_err.csv` e `tracets_lat.csv` nos datasets multi-source, e seu exportador os copia quando existem. Eles não vieram no subset Parquet baixado, que contém apenas metrics, traces, logs e tempo de injeção. O projeto publica também uma cópia Figshare com séries pré-processadas adicionais; verificar essa distribuição é o próximo passo para obter erros por operação.

## Execução v3

Rodei `s-fixed-reference-quality-v3` inalterado, com referências `S=1`, `Tref=40 req/s` e `Lref=0,1s`, em 741 janelas de um minuto da operação `frontendservice/frontend`:

- 710 janelas retornaram `missing / missing_counts`, pois não há status para derivar `failed`.
- 31 janelas retornaram `partial / no_traffic`, sem spans observados.
- 0 janelas válidas; P/Q/D não foram calculados.
- CPU ficou preservada como média bruta da coluna candidata do serviço injetado; 0 valores foram postos em `cpu_cores`, pois a unidade não está confirmada como cores.

O resultado detalhado por janela e hashes SHA-256 das 90 entradas estão em `research/reports/rcaeval_re2ob/generated/wave_v3_source_aligned_windows.csv` e `wave_v3_source_aligned_summary.json` (pasta ignorada pelo Git).

Um primeiro ensaio que agregava todas as spans `frontendservice` mostrou throughput acima da referência e P saturado em 1. Esse ensaio foi rejeitado para a API externa porque misturava múltiplas operações RPC internas; não é uma entrada válida de request do frontend.

## AD-microservice-app

O repositório indicado contém README, dois pares de CSV e licença, sem scripts de produção das métricas. Seu [README upstream](https://github.com/Mohamed164/AD-microservice-app) descreve categorias de métrica e labels, mas não define as fórmulas/unidades para os campos service `req_rate`, `req_ok`, `req_ko`, `avg_rt` e `avg_ok_rt`. O [artigo dos autores](https://doras.dcu.ie/30104/1/LOD_Paper.pdf) confirma CloudWatch para CPU de node/pod, Prometheus/Istio para métricas de serviço e FIS como fonte das intervenções/labels; não fornece o contrato de export desses nomes.

Nos arquivos locais, para dez serviços e todos os timestamps, `req_rate == req_ok` e `avg_rt == avg_ok_rt`, embora `req_ko` seja não-zero extensivamente. Wave v3 continua bloqueado nesse conjunto até os autores fornecerem a semântica/export original. A auditoria e os testes estão em `research/experiments/ad_microservice_app/` e `research/reports/ad_microservice_app/`.

## Conclusão e próximo passo

RCAEval oferece uma rota clara para a unidade de duração e a identidade de requests/erros por operação. O subset atual ainda não fornece erros para os spans da API externa; procure as séries `tracets_err.csv` pré-processadas na distribuição Figshare/Zenodo ou outra fonte de status do frontend. Depois disso, refazer a execução v3 sem alterar as fórmulas. Para AD-microservice-app, solicitar aos autores consulta/export original e esclarecer as igualdades observadas. Os resultados atuais são de auditoria e prontidão, não resultados matemáticos Wave nos dois datasets.
