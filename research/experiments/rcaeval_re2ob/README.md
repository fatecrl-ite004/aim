# RCAEval RE2-OB: primeira etapa do pipeline

Esta experiência avalia métricas computacionais e impacto em API nos casos RE2-OB de CPU e atraso, sem alterar a matemática do Wave. O código-fonte do RCAEval confirma a unidade de duração dos spans e define como conta requests/erros por serviço/operação. A operação de entrada `frontendservice/frontend`, porém, não tem status de erro; por isso a v3 é invocada, mas não produz P/Q/D válidos até obtermos uma fonte de falhas para essa API.

## Etapas

1. Obter somente os 30 casos RE2-OB de CPU e atraso, com o script de download seletivo abaixo.
2. Inventariar colunas, linhas, timestamps, cadência, momento da injeção e estrutura de traces.
3. Executar o estudo descritivo pré/pós-injeção. Ele mostra CPU do serviço injetado junto com sinais candidatos da API, sem tratar nomes de colunas como prova de unidade.
4. Revisar os nomes candidatos contra a documentação e os valores observados; registrar unidade, tipo (gauge/counter/rate), agregação, serviço e limites de validade.
5. Só então definir uma transformação sem perda de informação para a janela temporal v3. CPU fica como covariável; as fórmulas e referências `S=1`, `Tref=40 req/s`, `Lref=0,1s` permanecem congeladas.
6. Calcular/avaliar saída v3 por janela e associar ao impacto de API obtido separadamente dos traces. Falha injetada não serve como rótulo de impacto.
7. Avaliar por caso/episódio; as janelas dentro de um episódio não são réplicas independentes. Atraso atua como controle positivo de degradação de API, sem misturar com os casos CPU.

Dados baixados e resultados gerados ficam em pastas ignoradas pelo Git. O checkout do RCAEval contém código e utilitários, mas não os casos RE2-OB propriamente ditos.

## Download e inventário (PowerShell na raiz do AIM)

Requer `huggingface_hub`, `pandas` e `pyarrow` no ambiente Python. O download espera encontrar exatamente 15 casos CPU e 15 casos delay, falhando explicitamente se o catálogo remoto não corresponder.

```powershell
python research\experiments\rcaeval_re2ob\download_cpu_delay_subset.py
python research\experiments\rcaeval_re2ob\inspect_re2ob.py `
  --dataset-root research\data\rcaeval\re2ob_cpu_delay
```

O inventário JSON é escrito em `research/reports/rcaeval_re2ob/generated/inventory.json`. Ele marca candidatos por nome apenas e não equivale a mapeamento semântico nem a resultado experimental. Revise o relatório antes de avançar para cálculo Wave.

O estudo evento é executado assim:

```powershell
python research\experiments\rcaeval_re2ob\run_event_study.py `
  --dataset-root research\data\rcaeval\re2ob_cpu_delay
```

Ele compara a mediana de cada sinal nos 600 s anteriores e posteriores à injeção, por caso. `frontend_latency-50/-90` são percentis de latência conforme a documentação do RCAEval; a unidade dos valores ainda requer confirmação. `frontend-external_workload/error` são tratados como nomes candidatos, sem presumir taxa ou contagem.

O preflight conservador chama o `derive()` v3 inalterado por janela, selecionando `frontendservice/frontend` (a operação raiz observada que representa a entrada da loja):

```powershell
python research\experiments\rcaeval_re2ob\run_wave_v3_source_aligned.py `
  --dataset-root research\data\rcaeval\re2ob_cpu_delay
```

O código do RCAEval define `duration` Jaeger em microssegundos e trata gRPC `0` e HTTP `200–399` como sucesso. Esse cálculo seleciona a operação externa para não contar novamente as chamadas RPC aninhadas do serviço frontend. Os 549.502 spans dessa operação têm duração e timestamp, mas todos estão sem `statusCode`; logo a contagem de falhas é ausente e Wave marca 710 janelas como `missing` e 31 como `no_traffic`, sem calcular P/Q/D. CPU permanece ao lado como métrica candidata bruta: o código não confirma que a unidade seja cores.

O RCAEval também consome `tracets_err.csv`/`tracets_lat.csv` como séries auxiliares quando disponíveis. Esses arquivos não vieram no subset Parquet baixado; investigar a cópia Figshare/Zenodo é a próxima fonte possível para falhas por operação. Não usar o agregado de todas as operações `frontendservice`: ele inclui chamadas internas e satura P na referência fixa.

Para inventariar dados já obtidos em outra pasta:

```powershell
python research\experiments\rcaeval_re2ob\inspect_re2ob.py `
  --dataset-root 'D:\dados\re2ob_cpu_delay' `
  --out research\reports\rcaeval_re2ob\generated\inventory.json
```

## Validação local

```powershell
$env:PYTHONPATH = "$PWD\research\src;$PWD"
python -m unittest research.tests.test_rcaeval_re2ob -v
```

Os seis testes locais usam fixtures sintéticas e verificam parsing, seleção da suíte, união dos timestamps sem preenchimento, corte antes/depois da injeção, separação entre operação de entrada e RPC interno e o tratamento de status ausente. A execução do estudo nos 30 casos reais é descritiva, não uma validação preditiva/causal.

## Próxima evidência necessária

O inventário real precisa ser acompanhado por documentação da fonte para confirmar unidades, temporality e cardinalidade. Verifique também timestamp/timezone de `inject_time`, disponibilidade e amostragem dos traces e vínculo entre serviço da métrica e API avaliada. O esquema atual não traz contagens explícitas de concluídas/falhas e latência média exigidas pela entrada v3; não substitua isso por p50/p90 ou workload/error candidatos. Sem resolver essa lacuna, não produzir índices v3 válidos.
