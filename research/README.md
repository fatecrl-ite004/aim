# Pesquisa executável

`research/` é o espaço reservado a código, notebooks, configurações e resultados de experimentos reproduzíveis. Isso o distingue de `docs/pesquisa/`, que contém sínteses e protocolos escritos, e de `system/`, reservado à aplicação PoC.

**Estado atual:** há um experimento exploratório executável Wave CPU/API em `experiments/wave_cpu_api/`, com port matemático em `src/aim_wave/`, fixtures/testes em `tests/` e relatório em `reports/wave_cpu_api/`. Isso não implementa ingestão OTLP, detector AIM ou integração de produção.

O estudo Wave usa AIOpsArena local, sem banco; os CSVs derivados volumosos ficam em `reports/wave_cpu_api/generated/`, ignorado pelo Git. Consulte o [guia de execução](experiments/wave_cpu_api/README.md), a [especificação](../docs/pesquisa/especificacao-adaptacao-wave-cpu-api.md) e o [resultado exploratório 001](reports/wave_cpu_api/resultado-exploratorio-001.md). O snapshot documental e o manifesto de hashes da origem estão em `vendor/wave-source/`. Consulte também `docs/pesquisa/protocolo-experimental.md`.

Há também o estudo [Wave v3 com CPU como covariável](experiments/wave_v3_cpu/README.md), especificado em `docs/pesquisa/especificacao-wave-v3-cpu-covariavel.md` e reportado em `reports/wave_v3_cpu/resultado-v3-cpu-001.md`. Ele valida paridade com as funções v3 originais e preserva CPU junto às saídas; CPU não modifica a geometria v3. Seus artefatos integrais também ficam em pasta `generated/` ignorada.

O teste complementar [Wave v3 por episódios com traces](experiments/wave_v3_cpu/README.md#teste-por-episódio-com-traces) avalia latência por span antes/durante/depois de eventos anotados. Percentis de trace não entram na v3. Consulte `reports/wave_v3_cpu/resultado-event-study-traces-001.md`; os traces originais permanecem fora do repositório.

Há um estudo [AD-microservice-app](experiments/ad_microservice_app/README.md) com inventário de CPU de pod/node, ações FIS e métricas de serviço. O Wave v3 fica bloqueado até resolver o contrato request/response; consulte o [resultado de auditoria 001](reports/ad_microservice_app/resultado-auditoria-001.md). Os CSVs de origem permanecem fora do repositório.
