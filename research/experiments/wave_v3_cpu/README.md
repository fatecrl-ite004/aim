# Executar a v3 do Wave com CPU como covariável

Este experimento aplica `s-fixed-reference-quality-v3` sem mudanças matemáticas. CPU é calculada por intervalo e preservada junto às saídas v3, mas não modifica P/Q/S/D. Não treina detector e não usa banco.

## Requisitos e dados

- Windows PowerShell, Python 3.11+.
- AIOpsArena local em `C:\Users\00001\Downloads\datasets_aim\AIOpsArena` ou outra pasta com:

```text
AIOpsArena/Case-1/Case-1/{metric/container,metric/istio,groundtruth}/
AIOpsArena/Case-2/Case-2/{metric/container,metric/istio,groundtruth}/
```

Os dados originais não são copiados para o repositório. A cadência observada é predominantemente 15 s; o runner não a reamostra.

## Passos para rodar

Na raiz do repositório AIM:

```powershell
$env:PYTHONPATH = "$PWD\research\src"
python -m unittest discover -s research\tests -p 'test_*.py' -v
python research\experiments\wave_v3_cpu\run_aiopsarena_v3.py `
  --dataset-root 'C:\Users\00001\Downloads\datasets_aim\AIOpsArena'
```

Para escolher outro diretório de saída:

```powershell
python research\experiments\wave_v3_cpu\run_aiopsarena_v3.py `
  --dataset-root 'D:\dados\AIOpsArena' `
  --out research\reports\wave_v3_cpu\generated
```

## Ver os resultados

Saídas completas em `research/reports/wave_v3_cpu/generated/` (ignorado pelo Git):

- `summary.json`: modelo/referências, SHA-256 das fontes, contagens por status, auditoria do join e correlações por instância.
- `wave_v3_cpu_windows.csv`: dados e saída da v3 por janela; filtre `case`, `instance`, `status` e `cpu_fault_active`.

O `summary.json` mostra também janelas `no_traffic`, `missing` e inválidas. Uma janela `ok` permite ler CPU junto com as métricas de API. Em nenhuma linha CPU entra na fórmula da v3. CPU×P ou CPU×D deve ser interpretada com cuidado porque P/D são derivados da API; veja também CPU×latência, CPU×throughput e CPU×erro.

O relatório desta execução fica em [resultado v3 CPU 001](../../reports/wave_v3_cpu/resultado-v3-cpu-001.md). As referências v3 são `S=1`, `Tref=40 req/s` e `Lref=0,1s`; não são automaticamente capacidade física ou SLO.

## Teste por episódio com traces

Depois de gerar `wave_v3_cpu_windows.csv` acima, execute o estudo externo dos spans:

```powershell
python research\experiments\wave_v3_cpu\run_trace_event_study.py `
  --dataset-root 'C:\Users\00001\Downloads\datasets_aim\AIOpsArena'
```

O script varre os CSVs de traces em streaming, agrupa injeções simultâneas no mesmo episódio e resume `request` spans por serviço e root spans nos períodos de duração equivalente antes/durante/depois. Percentis de trace são apenas resultados de avaliação; **não entram na fórmula v3**. O JSON fica em `research/reports/wave_v3_cpu/generated/trace_event_study.json` e registra hashes, cobertura e limites. Consulte [resultado por episódios 001](../../reports/wave_v3_cpu/resultado-event-study-traces-001.md).

O timestamp em microssegundos é inferido do conteúdo e precisa de confirmação da semântica do dataset. Traces agregados por serviço não identificam necessariamente a réplica de CPU; confirmar topologia, cobertura/amostragem e vínculo por `trace_id` antes de qualquer conclusão confirmatória.

## Como evoluir

1. Confirmar topologia e direção das arestas Istio, semântica da duração e amostragem dos traces; o join por prefixo continua provisório.
2. Investigar reset/contadores CPU constantes e falta de spans do serviço em episódios anotados.
3. Repetir injeções CPU independentes com controles e identificar pod/trace para testar atribuição; dividir avaliação por episódio.
4. Avaliar API-only, CPU-only e combinação como tarefa detector AIM, sem contar janelas do mesmo episódio como réplicas.
5. Se o objetivo pedir cauda p95 dentro da fórmula, propor primeiro novo contrato Wave/model_id; não trocar a média nem ajustar referências da v3 com este mesmo conjunto.

Não mover esse código de pesquisa para `system/` antes da avaliação e decisão documentada.
