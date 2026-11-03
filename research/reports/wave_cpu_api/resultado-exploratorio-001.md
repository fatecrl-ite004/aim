# Execução exploratória 001 — Wave CPU/API no AIOpsArena

**Data:** 2 de novembro de 2026. **Status:** execução concluída; interpretação exploratória.  
**Código:** `research/src/aim_wave/` e `research/experiments/wave_cpu_api/run_aiopsarena.py`.  
**Saídas completas locais (ignoradas pelo Git):** `research/reports/wave_cpu_api/generated/`.

## Pergunta e procedimento

A rodada leu `container_cpu_usage_seconds_total`, `istio_requests_total`, `istio_request_duration_milliseconds_sum` e ground truth em Case-1/Case-2. Deltas foram calculados dentro de cada série; contagem e duração foram pareadas pelo mesmo cmdb_id, sufixo/status e intervalo antes da agregação por prefixo de instância. CPU foi normalizada pela referência experimental de 1 core; P usou as referências Wave de 100 req/s e 0,1 s. A variante calculada é `wave-cpu-api-harmonic-v0.1`, com A, P, R e phi; não é a variante v3 de S=1.

A saída inclui 300.831 intervalos CPU candidatos. Em 73.481 (24,4%) houve uma janela API válida/pareada para calcular todos os índices; 227.350 ficaram parciais por falta de uma série API correspondente ao prefixo/intervalo. As métricas selecionadas têm deltas majoritariamente de 15 s; o estudo não reamostrou os dados para 5 s.

O emparelhamento identificou 784.926 séries-edge/status/intervalos em Case-1 e 250.056 em Case-2. Restaram 3 contagens sem duração e 16 durações sem contagem em Case-1; em Case-2, 0 e 1, respectivamente. Foram observados resets em CPU/request/duration: Case-1 53/151/138; Case-2 0/7/6. Foram registrados pontos duplicados nos três arquivos. O resumo JSON guarda as contagens e hashes SHA-256 por arquivo de entrada.

## Leitura dos eventos CPU anotados

O ground truth contém dois episódios CPU em Case-1 e um episódio CPU em Case-2 (três réplicas anotadas simultaneamente). Entre as janelas com CPU e API válidas, houve 9 para `paymentservice-1`, 13 para `recommendationservice-1` e 10 por réplica `currencyservice-0/1/2`.

| Caso/instância | CPU % da referência, evento / controle | Latência média, evento / controle | Throughput req/s, evento / controle | Erro gRPC, evento / controle |
|---|---:|---:|---:|---:|
| Case-1 paymentservice-1 | 25,02 / 0,88 | 27,47 / 2,32 ms | 0,304 / 0,256 | 0 / 0% |
| Case-1 recommendationservice-1 | 0 / 1,32 | 19,43 / 2,64 ms | 9,877 / 10,057 | 0 / 0% |
| Case-2 currencyservice-0 | 27,77 / 5,18 | 118,93 / 2,04 ms | 19,460 / 20,681 | 0 / 0% |
| Case-2 currencyservice-1 | 0 / 0 | 125,35 / 1,97 ms | 19,567 / 20,669 | 0 / 0% |
| Case-2 currencyservice-2 | 0 / 0 | 113,69 / 1,97 ms | 20,087 / 20,802 | 0 / 0% |

Os valores do quadro são médias descritivas somente das janelas com API pareada. Em duas réplicas do episódio Case-2 e em `recommendationservice-1`, o contador de CPU não cresce no período CPU anotado, embora a duração média da API aumente. Isso exige auditar semântica/identidade/cobertura dos contadores antes de interpretar a coordenada CPU como resposta completa à injeção.

## Associações no tempo

Foram calculadas correlações de Spearman por caso e instância, sem p-valores, usando janelas possivelmente autocorrelacionadas. Das 54 combinações caso/instância, 23 tiveram variância suficiente em CPU para uma correlação numérica com latência e throughput; 6 tiveram variância suficiente para erro gRPC.

Nas três instâncias com mudança de CPU visível durante o episódio anotado, as correlações globais CPU–latência foram pequenas: `paymentservice-1` ρ=0,044; `recommendationservice-1` ρ=−0,003; `currencyservice-0` ρ=0,058. CPU–throughput: ρ=0,044; 0,119; 0,172, respectivamente. Os resultados são heterogêneos e não demonstram uma associação estável generalizável. CPU×P também é uma relação composta porque P inclui throughput, latência e erro; por isso o relatório mantém as relações CPU×desfechos originais separadas.

Nos intervalos CPU do ground truth dessas instâncias, o erro gRPC derivado foi zero; isso **não** significa “sem erro crítico” em geral. O dataset não fornece uma classe independente de severidade crítica para esses registros. O código considera sucesso apenas o sufixo gRPC `grpc.200.0`; a interpretação dos demais status precisa de validação de domínio. A duração disponível permite média, não p95.

## Conclusão limitada

O teste demonstra que o AIM consegue ler as séries de CPU acumulada, derivar deltas, aplicar o port das fórmulas documentadas e emitir A/P/R/phi e associações descritivas. **Não demonstra** que Wave ou CPU prevêem impacto, que a CPU causou latência, que os índices são uma classificação de saúde/eficiência, nem que a junção de arestas mede o tráfego percebido pelo usuário.

A cobertura de apenas 24,4% das janelas candidatas e as réplicas com CPU constante tornam esta rodada um diagnóstico de viabilidade do caminho e dos dados. Antes de usar a saída como feature de detector AIM, é necessário confirmar a topologia/orientação dos cmdb IDs, revisar contadores e status, obter a implementação/fixtures C++ original ausente no snapshot Wave e repetir avaliação por episódio/caso com comparações contra CPU e API brutas.

## Reprodução

Comandos, interpretação dos campos e roteiro de evolução: [guia passo a passo](../../experiments/wave_cpu_api/README.md). Resultados completos e dados derivados desta execução permanecem locais em `generated/` e não foram adicionados ao Git.

## Verificação executada

Em 2/11/2026, com Python 3.14.0, a suíte foi executada duas vezes (pelo agente de execução e revisão independente) com:

```powershell
$env:PYTHONPATH = "$PWD\research\src"
python -m unittest discover -s research\tests -p 'test_*.py' -v
```

Resultado da revisão independente: **9 testes aprovados, 0 falhas**. Os casos cobrem fórmula e reconstrução polar, valores acima da referência sem corte, valores fracionários, ausência, vetor nulo, janela inválida, portadora, reset e pareamento por aresta/status/intervalo. Isso valida o port e o adaptador nas fixtures testadas; não é teste de paridade contra o código C++ original ausente nem validação do significado operacional do modelo.
