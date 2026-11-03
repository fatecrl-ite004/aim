# AD-microservice-app: auditoria inicial de CPU e API

**Escopo:** organizar testes locais para dois dias do dataset, sem importar dados para AIM e sem alterar Wave v3.

## Dados observados

Os arquivos em `C:\Users\00001\Downloads\AD-microservice-app-main\AD-microservice-app-main` incluem dias `13-05-2024` e `20-05-2024`. Cada CSV de métricas tem 471 colunas (timestamp + 470 séries/labels): 125 node, 252 pod, 90 service e três rótulos (`anomaly_load`, `anomaly_fis`, `anomaly`). Os dias têm 10.080 e 10.081 linhas, sem timestamp duplicado nem células ausentes; a cadência é exatamente 60 segundos. Os timestamps são UTC.

Há 147 e 159 ações FIS, total 306. O recorte contém 21 e 30 ações de CPU-stress, respectivamente. Cinco ações de CPU têm sobreposição com outra intervenção (uma no primeiro dia, quatro no segundo). Uma ação do conjunto geral não tem horário final; ela não pode compor comparação durante/pós. O nome de entidade depois de `||` no alvo pod é preservado como vínculo candidato. CPU de pod e CPU de node são campos separados.

## Auditoria dos sinais de API

Em ambos os dias, para os dez serviços, `*_req_rate` é idêntico a `*_req_ok` em todas as linhas. Também `*_avg_rt` é idêntico a `*_avg_ok_rt` em todas as linhas. Ao mesmo tempo, os campos `*_req_ko` têm valores não zero em quase todas as linhas de cada serviço (mínimo observado: 10.047/10.080 no primeiro dia e 10.047/10.081 no segundo). Essa inconsistência impede atribuir com segurança os campos a contagem de requests totais, concluídos, falhos ou latência média.

O README do dataset identifica os campos como métricas de serviços, mas não documenta neste checkout unidade/temporality suficiente para resolver o contrato. `anomaly*` e ações FIS são rótulos/intervenções; não são um rótulo independente de impacto na API.

## Estudo descritivo

O runner gera, para cada ação CPU com início e fim, medianas de campos candidatos de CPU e `front-end` em três períodos alinhados aos timestamps: cinco minutos antes, duração da intervenção e cinco minutos após. Mantém marcados eventos sobrepostos; não os usa como controle independente. Por a cadência ser de um minuto e ações iniciarem em segundos, o pareamento temporal tem resolução de até um minuto.

O output por evento e o inventário com hashes estão em `research/reports/ad_microservice_app/generated/` (ignorado pelo Git). Os resultados são descritivos e de coocorrência, não demonstram causalidade.

## Gate para Wave v3

Wave v3 não foi executado sobre este dataset. Não existe mapeamento sustentado para `completed`, `failed` e latência média na janela atual; converter os campos pelo nome violaria o rigor e poderia fabricar índices P/Q/S/D. Próximo passo é obter definição do produtor dos sinais ou os artefatos da consulta/export original e validar o contrato. Só depois executar v3 sem alterar fórmulas ou referências.

## Reprodutibilidade

Na raiz do AIM:

```powershell
python research\experiments\ad_microservice_app\run_analysis.py `
  --dataset-root 'C:\Users\00001\Downloads\AD-microservice-app-main\AD-microservice-app-main'
$env:PYTHONPATH = "$PWD\research\src;$PWD"
python -m unittest research.tests.test_ad_microservice_app -v
```

Dois testes sintéticos passaram. Fontes CSV não foram alteradas ou copiadas. Os hashes SHA-256 estão no JSON gerado para reexecução e comparação.
