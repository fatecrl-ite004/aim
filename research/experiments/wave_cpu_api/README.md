# Rodar e evoluir o experimento Wave CPU/API

Esta é a primeira adaptação experimental do Wave dentro da pesquisa executável do AIM. Ela lê AIOpsArena localmente, sem banco de dados, calcula a candidata CPU/API de duas coordenadas e produz um resumo e CSV. Não inicia serviço, não recebe OTLP em tempo real e não treina detector.

## 1. Requisitos e pasta dos dados

- Windows PowerShell e Python 3.11 ou superior. O experimento usa a biblioteca padrão do Python; não instala pacotes.
- Dataset AIOpsArena descompactado com esta estrutura:

```text
AIOpsArena/
  Case-1/Case-1/{metric/container,metric/istio,groundtruth}/...
  Case-2/Case-2/{metric/container,metric/istio,groundtruth}/...
```

O caminho padrão usado nesta máquina é `C:\Users\00001\Downloads\datasets_aim\AIOpsArena`. Os arquivos originais ficam fora do repositório e não devem ser copiados para `data/` nem para Git.

## 2. Executar testes

A partir da raiz do repositório AIM:

```powershell
$env:PYTHONPATH = "$PWD\research\src"
python -m unittest discover -s research\tests -p 'test_*.py' -v
```

Os testes cobrem a fórmula Wave A/P/R/phi, reconstrução polar, CPU/API acima das referências sem corte, deltas fracionários, ausência, vetor nulo, janela inválida, pareamento de request/duração por aresta/status/intervalo, erro gRPC e reset de contador.

## 3. Executar a rodada AIOpsArena

```powershell
python research\experiments\wave_cpu_api\run_aiopsarena.py `
  --dataset-root 'C:\Users\00001\Downloads\datasets_aim\AIOpsArena'
```

Para outra pasta de saída:

```powershell
python research\experiments\wave_cpu_api\run_aiopsarena.py `
  --dataset-root 'D:\dados\AIOpsArena' `
  --out research\reports\wave_cpu_api\generated
```

A execução não usa base de dados. Ela lê apenas CPU usage counter, Istio requests, Istio duration sum e ground truth dos dois casos; não abre os CSVs grandes de logs/traces.

## 4. Abrir e interpretar resultados

O diretório local ignorado `research/reports/wave_cpu_api/generated/` recebe:

- `summary.json`: referências, hashes SHA-256 dos arquivos-fonte, contagens de resets/duplicatas/intervalos, cobertura de pareamento, resumo por caso/instância, correlações e diferenças evento/controle.
- `wave_cpu_api_windows.csv`: linha por intervalo CPU, incluindo cmdb IDs/arestas/status originais, deltas, saída Wave e falhas do ground truth que se sobrepõem. É um arquivo grande; filtre por `case`, `instance`, `status` e `cpu_fault_active` antes de abrir em uma planilha.

Imprimir resumo de janelas:

```powershell
python -c "import json; d=json.load(open(r'research/reports/wave_cpu_api/generated/summary.json',encoding='utf-8-sig')); print(d['input_window_rows'], d['joined_valid_rows'], d['partial_or_invalid_rows'])"
```

Imprimir as comparações dos episódios CPU anotados:

```powershell
python -c "import json; d=json.load(open(r'research/reports/wave_cpu_api/generated/summary.json',encoding='utf-8-sig')); [print(x['case'],x['instance'],'n=',x['cpu_fault_windows'],'CPU evento/controle=',x['mean_cpu_pct_reference_fault'],x['mean_cpu_pct_reference_control'],'latência=',x['mean_latency_s_fault'],x['mean_latency_s_control'],'rho CPU-latência=',x['spearman']['cpu_vs_latency_mean_s']['rho']) for x in d['summary_by_case_instance'] if x['cpu_fault_windows']]"
```

Significado das saídas:

- `A_cpu_normalized`: CPU-s consumida na janela dividida por duração e referência de cores. `A=1` equivale a um core na referência escolhida; valores acima de 1 são mantidos.
- `P_api`: índice combinado da candidata documentada: throughput relativo × qualidade de latência × fração não falha. Não é probabilidade nem rótulo de saúde; preservam-se throughput, média de latência e erro para inspeção independente.
- `R` e `phi`: coordenadas polares reversíveis do par A/P, quando R>0. A onda é codificação harmônica, não oscilação medida no serviço.
- `status=partial`: falta componente, normalmente um pareamento CPU/API; não equivale a zero.
- `cpu_fault_active`: sobreposição temporal do intervalo com o ground truth de injeção CPU. Não rotula degradação da API.
- `rho`: associação monotônica descritiva por instância; janelas temporais são dependentes. Não interpretar como teste inferencial/causal.

O mapeamento do prefixo `cmdb_id` Istio para instância de contêiner é provisório. As arestas podem representar escopos/direções diferentes. A “latência API” calculada é média por soma de duração/soma de requests; o dataset não dá p95 nesses arquivos. Status gRPC não fornece severidade crítica validada.

## 5. Resultado desta rodada

Consulte [resultado exploratório 001](../../reports/wave_cpu_api/resultado-exploratorio-001.md). Na execução em 2/11/2026 foram formadas 300.831 janelas candidatas; 73.481 (24,4%) tiveram entrada CPU/API suficiente. O resultado foi heterogêneo entre instâncias e não autoriza concluir que a coordenada CPU antecipa ou explica sozinha impacto API.

## 6. Como evoluir

1. Confirmar com a topologia AIOpsArena a semântica de `cmdb_id`, origem/destino e se agregar arestas duplica tráfego.
2. Investigar por que alguns contadores CPU ficam constantes durante episódios anotados como CPU; verificar série, instância, reinícios e cobertura.
3. Obter o código C++ e fixtures originais citados no README Wave para teste de paridade. Até lá, AIM é um port das fórmulas documentadas, não reprodução do binário/fonte ausente.
4. Comparar A/P/R/phi com CPU, throughput, latência e erro brutos, mais baselines, usando partições por execução/episódio/caso; não embaralhar janelas adjacentes.
5. Definir separadamente se erro crítico exige regra de severidade externa. AIOpsArena traz sufixos de status gRPC observados, mas não um rótulo “crítico” independente.
6. Só propor integração OTLP contínua depois de um contrato canônico de janela, teste de paridade, avaliação por episódio e decisão documentada. O componente permanece em `research/`; não movê-lo para `system/` ainda.
