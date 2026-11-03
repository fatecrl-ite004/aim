# Resultado v3 com CPU como covariável — rodada 001

**Data:** 2 de novembro de 2026  
**Modelo:** `s-fixed-reference-quality-v3`  
**Dados:** AIOpsArena local, Case-1 e Case-2; dados brutos não foram copiados para o AIM.  
**Escopo:** executar a v3 original preservando CPU para análise paralela. CPU não entra em P/Q/S/D.

## Pergunta e método

Verificamos se o adaptador consegue derivar CPU por intervalo de `container_cpu_usage_seconds_total`, alinhar a observação com métricas Istio, executar a v3 e emitir um resumo por janela que possa ser avaliado futuramente no pipeline AIM. A CPU é `delta(container_cpu_usage_seconds_total) / segundos_do_intervalo`, em cores, sem clipping. O join por prefixo de instância de `cmdb_id` é provisório e foi auditado.

A matemática v3 foi comparada diretamente às funções `canonicalize` e `derive` no snapshot da fonte Wave. O teste carrega essas funções do arquivo original por AST, sem alterá-lo. Para entradas compatíveis, os estados e saídas batem exatamente. O teste também verifica invariantes e que variar CPU, mantendo API fixa, não altera S/P/Q/D.

## Execução e contagens

Comando reproduzível (PowerShell, raiz do AIM):

```powershell
$env:PYTHONPATH = "$PWD\research\src"
python -m unittest discover -s research\tests -p 'test_*.py' -v
python research\experiments\wave_v3_cpu\run_aiopsarena_v3.py `
  --dataset-root 'C:\Users\00001\Downloads\datasets_aim\AIOpsArena'
```

O conjunto produziu **300.831 janelas candidatas**; **73.481** ficaram com status `ok` e saída v3 válida (24,4%). As demais foram 226.265 `partial/no_traffic` e 1.085 `missing/missing_counts`. Por caso, houve 54.979 janelas válidas no Case-1 e 18.502 no Case-2. A cadência predominante foi 15 s; não houve reamostragem para 5 s.

| Verificação do adaptador | Case-1 | Case-2 |
|---|---:|---:|
| CPU intervals válidos | 223.206 | 77.625 |
| Intervalos Istio de requests válidos | 784.929 | 250.056 |
| CPU sem API correspondente | 1.062 | 23 |
| API sem CPU correspondente | 104 | 1 |
| Deltas fracionários de requests | 0 | 0 |
| Intervalos de reset CPU | 53 | 0 |

São 54 grupos caso/instância (27 por caso), mas a correlação CPU×latência foi calculável em apenas 23; CPU×erro, em apenas 6, por falta de variação/valores utilizáveis. O resumo computado de Spearman por instância teve estas faixas e medianas entre valores definidos:

| Associação por instância | n grupos com rho | Faixa de rho | Mediana |
|---|---:|---:|---:|
| CPU × latência média API | 23 | -0,057 a 0,107 | 0,013 |
| CPU × throughput API | 23 | -0,026 a 0,259 | 0,094 |
| CPU × percentual de erro | 6 | -0,040 a -0,003 | -0,021 |
| CPU × P da v3 | 23 | -0,026 a 0,261 | 0,083 |
| CPU × D da v3 | 23 | -0,261 a 0,026 | -0,083 |

Os coeficientes são descritivos e heterogêneos. CPU×P/D é uma comparação com saídas determinísticas da API; como CPU não participa das fórmulas, essa comparação não demonstra contribuição da CPU para o modelo. A baixa variação/zeros em CPU e a pequena cobertura de erros tornam especialmente frágil a leitura desses coeficientes.

O ground truth incluiu 52 janelas CPU ativas alinhadas a grupos com API válida (22 no Case-1 e 30 no Case-2), distribuídas por poucos grupos/episódios. Não é base suficiente para afirmar poder de detecção, antecipação ou relação causal. Falha injetada de CPU é rótulo de intervenção, não rótulo independente de impacto API. A duração disponível é média agregada, não p95.

## Resultado palpável para o AIM

Sim: agora existe um fluxo offline reprodutível que lê CPU, deriva uma unidade interpretável (cores médios por intervalo), a carrega junto à entrada API, calcula a saída v3 sem alterar o contrato e exporta uma tabela/summary apropriados para análise posterior. O resultado demonstra viabilidade técnica do caminho CPU + API + Wave v3 e preserva proveniência por hashes, estados e auditoria de cobertura.

Esta rodada **não** demonstra que CPU melhore classificação ou detector AIM, nem que a associação seja causal. O resultado atual sugere associações fracas a moderadas em algumas instâncias, com disponibilidade insuficiente para conclusão geral. Também não é integração OTLP contínua nem foi movido para `system/`.

## Reprodutibilidade e arquivos

- Guia e comandos: [experimento v3 CPU](../../experiments/wave_v3_cpu/README.md).
- Especificação de contrato: [Wave v3 com CPU covariável](../../../docs/pesquisa/especificacao-wave-v3-cpu-covariavel.md).
- `summary.json` e CSV integral estão em `research/reports/wave_v3_cpu/generated/`, ignorado pelo Git. O JSON guarda SHA-256 das fontes, contagens, auditoria e correlações; o CSV guarda observações/saídas por janela.
- Testes locais: **16 passaram**, incluindo paridade com as funções originais, invariantes v3, CPU invariante para a geometria, tráfego zero distinto de dado ausente, validação de contadores e covariável.

## Próximas etapas recomendadas

1. Confirmar a semântica e direção dos identificadores Istio e melhorar cobertura de séries CPU constantes/zeradas.
2. Validar CPU e API em janelas com falha por episódio, com controles e baseline, antes de falar em utilidade para detector.
3. Fixar previamente a tarefa AIM e o split por caso/episódio; comparar API-only com CPU adicionada como feature, sempre sem alterar esta v3.
4. Se a hipótese científica exigir CPU dentro da geometria, formalizar uma variante e `model_id` novos; manter a v3 e esta paridade intactas.
