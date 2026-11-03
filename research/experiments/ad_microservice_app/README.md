# AD-microservice-app: inventário CPU/API

Experimento de pesquisa com os CSVs externos em `C:\Users\00001\Downloads\AD-microservice-app-main\AD-microservice-app-main`. O AIM não copia nem versiona os dados. O adaptador preserva a distinção entre labels de anomalia/FIS e impacto de API; nomes de campos são candidatos até a unidade e semântica serem comprovadas.

## Executar

Na raiz do AIM:

```powershell
python research\experiments\ad_microservice_app\run_analysis.py `
  --dataset-root 'C:\Users\00001\Downloads\AD-microservice-app-main\AD-microservice-app-main'
```

Saídas em `research/reports/ad_microservice_app/generated/` (ignorado pelo Git): inventário de cada dia, hashes SHA-256 e análise por ação CPU-stress. Cada evento compara candidatos nos cinco minutos antes, durante a ação e cinco minutos depois. Episódios sobrepostos ficam identificados; a análise não os chama de controles independentes.

## Contratos e limitações

- Timestamp UTC, cadência observada e duplicatas são auditados; dados sem horário válido falham explicitamente.
- Ações FIS são preservadas como intervenção anotada. `anomaly_load`, `anomaly_fis` e `anomaly` não são usados como rótulo de impacto da API.
- CPU de pod e CPU de node ficam separadas. O sufixo de serviço após `||` é apenas vínculo candidato.
- O relatório mede e registra igualdade entre `*_req_rate`/`*_req_ok` e `*_avg_rt`/`*_avg_ok_rt`, além de valores não zero em `*_req_ko`.
- **Não alimenta Wave v3 neste estágio.** A relação observada entre as colunas de API é internamente inconsistente para inferir conclusões/falhas, e a unidade de tempo de resposta precisa de confirmação documental. Não estime `completed`, `failed` ou latência média a partir dessas colunas sem um contrato de origem.
- A análise é descritiva, não causal, preditiva ou de desempenho de detector.

## Testes

```powershell
$env:PYTHONPATH = "$PWD\research\src;$PWD"
python -m unittest research.tests.test_ad_microservice_app -v
```

Fixtures são sintéticas e cobrem o gate de semântica, não a interpretação oficial do dataset.
