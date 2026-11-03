# Pesquisa documentada

Esta área contém conhecimento de pesquisa em formato documental: sínteses, hipóteses, protocolo e referências candidatas. Ela não contém experimento executável nem afirma implementação dos métodos estudados.

## Estado da arte local

As oito sínteses abaixo foram copiadas da pasta AIM docs para manter uma base versionável. Cópias incluem o conteúdo completo; os originais permanecem inalterados. As sínteses qualificam fontes e limites e não constituem afirmação de revisão global atualizada.

### Sínteses ampliadas

- [Seção 1 — Observabilidade](estado-da-arte/Sintese%20ampliada%20para%20AIM%20-%20Secao%201%20Observabilidade.md)
- [Seção 2 — Detecção de anomalias](estado-da-arte/Sintese%20ampliada%20para%20AIM%20-%20Secao%202%20Deteccao%20de%20anomalias.md)
- [Seção 3 — Séries temporais](estado-da-arte/Sintese%20ampliada%20para%20AIM%20-%20Secao%203%20Series%20temporais.md)
- [Seção 4 — Correlação e RCA](estado-da-arte/Sintese%20ampliada%20para%20AIM%20-%20Secao%204%20Correlacao%20e%20RCA.md)

### Resumos reutilizáveis

- [Seção 1 — Observabilidade](estado-da-arte/Resumo%20reutilizavel%20-%20Secao%201%20Observabilidade.md)
- [Seção 2 — Detecção](estado-da-arte/Resumo%20reutilizavel%20-%20Secao%202%20Deteccao%20de%20anomalias.md)
- [Seção 3 — Séries e mudanças](estado-da-arte/Resumo%20reutilizavel%20-%20Secao%203%20Series%20temporais%20e%20mudancas.md)
- [Seção 4 — RCA e causalidade](estado-da-arte/Resumo%20reutilizavel%20-%20Secao%204%20RCA%20e%20causalidade.md)

Use as sínteses para formular hipóteses e limites de evidência; registre decisões de escopo em [perguntas e hipóteses](perguntas-e-hipoteses.md), e procedimentos em [protocolo experimental](protocolo-experimental.md). Uma referência ou método descrito não é uma escolha aceita.

## Experimento executável Wave CPU/API

- [Especificação de adaptação Wave CPU/API](especificacao-adaptacao-wave-cpu-api.md): contrato matemático, dados AIOpsArena, filtros, limites e gates.
- [Guia passo a passo](../../research/experiments/wave_cpu_api/README.md): testes, execução local e interpretação dos arquivos.
- [Resultado exploratório 001](../../research/reports/wave_cpu_api/resultado-exploratorio-001.md): rodada local de Case-1/Case-2 e limites observados.

O código reside em `research/src/aim_wave/`; não há integração OTLP contínua ou detector AIM implementado nesta etapa.

## Experimento Wave v3 com CPU como covariável

- [Especificação v3 CPU](especificacao-wave-v3-cpu-covariavel.md): mantém o contrato v3; CPU é covariável e não altera P/Q/S/D.
- [Guia de execução v3](../../research/experiments/wave_v3_cpu/README.md): comandos, validações e leitura dos artefatos.
- [Resultado v3 CPU 001](../../research/reports/wave_v3_cpu/resultado-v3-cpu-001.md): execução AIOpsArena, cobertura, associações e limites.
- [Resultado por episódios e traces 001](../../research/reports/wave_v3_cpu/resultado-event-study-traces-001.md): comparação descritiva antes/durante/depois; traces são avaliação externa, não entrada da v3.

O código está em `research/src/aim_wave/v3.py` e `research/experiments/wave_v3_cpu/`. Trata-se de experimento offline. Não é ingestão OTLP contínua, detector AIM ou integração de produção.
