# Especificação experimental: Wave v3 com CPU como covariável

**Estado:** port e avaliação exploratória; não é uma nova fórmula nem integração de produção.  
**Modelo:** `s-fixed-reference-quality-v3`, conforme o snapshot `research/vendor/wave-source/`.  
**Dados:** AIOpsArena Case-1/Case-2, lidos localmente e sem banco.  
**Plano geral local:** `plans/adaptacao-wave-aim.md` (ignorado pelo Git).

## Pergunta e interpretação

A v3 pode processar por janela as métricas de API junto com CPU observada e gerar suas saídas geométricas, mantendo CPU disponível para correlação e investigação do AIM?

**Sim, como covariável. Não como coordenada geométrica.** O contrato original já transporta `cpu_cores` na observação e resultado, mas CPU não entra nas fórmulas. Este experimento preserva esse comportamento. Se a hipótese passar a exigir que CPU altere P, Q ou S, será necessário outro modelo e `model_id`, com nova definição formal, domínio, invariantes e testes. Não chamar essa alteração de v3.

## Fórmulas v3 preservadas

Para cada serviço/janela, duração Δ, requests concluídas N, falhas F, latência média L, referências `Tref=40 req/s`, `Lref=0,1 s` e `Sref=1`:

```text
goodput = (N - F) / Δ
quality = Lref / max(L, Lref)
alpha_raw = (goodput / Tref) * quality
S = Sref = 1
P_raw = S * alpha_raw
alpha = min(1, max(0, alpha_raw))
P = S * alpha
Q = sqrt(S - P) * sqrt(S + P)
D = hypot(P - 1, Q)
theta = atan2(Q, P)
```

O corte é explícito e preserva `P_raw`, diferença e flags. Para esta v3, `P²+Q²=S²` e, com S=1, `D²=2-2P`. `cpu_cores = delta(container_cpu_usage_seconds_total) / Δ` é preservado sem corte em unidade de cores. **CPU não muda nenhuma das expressões acima.** Referência de um core é unidade de normalização/covariável e não implica limite físico do contêiner.

`N=0` com contadores observados é `partial/no_traffic`, mantendo CPU e `Sref`; P/Q/D ficam ausentes. Uma série ausente é `missing`, não zero. Deltas fracionários incompatíveis com contagens inteiras são inválidos; não arredondar silenciosamente.

## Entrada AIOpsArena e preparação

O estudo usa contador de CPU por contêiner e contadores/duration sum Istio de requests por status gRPC. Somente os intervalos com CPU, requests e duração correspondentes podem produzir a v3 completa. O join por prefixo de `cmdb_id` e a agregação de arestas são provisórios; preservar IDs/arestas e auditoria. O estudo usa intervalos observados, predominantemente 15 s; não interpolar para 5 s.

- Deltas são derivados dentro da série de mesma identidade/status/aresta; resets, duplicatas e intervalos incompatíveis são contados no audit.
- A soma de duração é pareada com requests pelo mesmo `cmdb_id`, status e intervalo antes da agregação.
- Latência é média (delta de duration sum / delta requests), não p95.
- `grpc.200.0` é sucesso nesta leitura; demais status contam como falha observada, sem rótulo de criticidade independente.
- Ground truth `cpu` indica injeção, não impacto garantido na API.

## Implementação e saídas

`research/src/aim_wave/v3.py` é o port do `canonicalize`/`derive` do snapshot Wave. `research/experiments/wave_v3_cpu/run_aiopsarena_v3.py` aplica-o aos mesmos intervalos do adaptador local. O teste de paridade extrai as funções originais `canonicalize`/`derive` do snapshot via AST, sem importar a pipeline completa, pois o snapshot não precisa de `plots.py` nem NumPy para testar as fórmulas.

Por janela, o CSV local inclui CPU em cores, entrada de API, `S/P_raw/P/Q/D/theta`, alfa, corte, status/razão, intervalo, instância, arestas e sobreposição com falha CPU. `summary.json` inclui hashes dos CSVs, referências, auditoria do adaptador, estados e associações por caso/instância. Arquivos derivados grandes ficam em `research/reports/wave_v3_cpu/generated/`, ignorado pelo Git. Relatório interpretativo pequeno e guia são versionáveis.

## Testes e evidência

Os testes devem demonstrar:

1. Paridade exata do port com a função v3 do snapshot para fixtures representativas.
2. `P²+Q²=S²` e `D²=2-2P` dentro de tolerância numérica pré-fixada.
3. Cortes explicitamente sinalizados, sem apagar `P_raw`.
4. CPU preservada como covariável; alterar CPU mantendo API constante não altera S/P/Q/D.
5. Zero tráfego distinto de telemetria ausente; contagens fracionárias/reset não viram valores válidos por arredondamento.
6. Join e tratamento de duração/status por aresta, status e intervalo.

Cada rodada registra comando, versão Python, hashes SHA-256 das fontes locais, `model_id`, referências, resultados e limitações. A correlação CPU–P/D é secundária, porque P/D são construídos a partir de métricas API; sempre reportar também CPU versus throughput, latência e erro brutos. Spearman é descritivo por instância/caso em janelas dependentes; não usar p-values ingênuos nem alegar causalidade.

## Critério de avanço

Esta etapa responde se o AIM consegue carregar CPU junto à API, calcular v3 sem alterá-la e apresentar associações observadas. Não testa se CPU aumenta desempenho de detecção. Para avaliar valor como feature, comparar baselines e detector com API-only, CPU-only e combinação, usando split por execução/episódio. Para CPU alterar a geometria, formalizar variante separada antes de implementar.
