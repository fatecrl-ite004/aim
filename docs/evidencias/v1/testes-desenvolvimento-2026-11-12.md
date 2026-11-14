# Evidência dos testes de desenvolvimento da V1

**Data da execução:** 12/11/2026

**Escopo:** backend, testes unitários do frontend, fluxos Playwright, teste live contra Docker e build de produção.

## Resultados

| Verificação | Comando/configuração | Resultado |
| --- | --- | --- |
| Backend | `$env:PYTHONPATH='system/backend'; .\.venv\Scripts\python.exe -m pytest system/backend/tests -p no:cacheprovider -q` | 36 aprovados; 1 aviso de depreciação do `starlette.testclient` com `httpx`. |
| Frontend unitário | `npm test` em `frontend/` | 27 aprovados em 2 arquivos. |
| Fluxos da interface | `npm run test:e2e` em `frontend/` | 11 aprovados; execução Playwright local com interface e API simuladas para os fluxos definidos. |
| Integração live | `$env:AIM_FRONTEND_BASE_URL='http://127.0.0.1:8080'; npm run test:live` | 1 aprovado contra a composição Docker; conferiu 282 pontos brutos e suas colunas de proveniência, métricas persistidas nas versões 15 s e 60 s, exportações CSV, cobertura e layout móvel. |
| Build de produção | `npm run build` em `frontend/` | TypeScript e build Vite concluídos sem erro. |
| Composição local | `docker compose --env-file .env.v1 -f infra/compose.v1.yml -f infra/compose.docker.yml --profile full up --build -d --wait` | API, frontend, Collector e PostgreSQL prontos; volume PostgreSQL existente preservado durante a recriação. |

## Evidência de dados e escopo

O recibo de integração da execução anterior, descrito em `revisao-docker-2026-11-11.md`, registra 282 pontos de origem conferidos contra o recorte AIOpsArena, sem divergências; 92 janelas de 15 s; 276 células de cobertura; e 23 buckets de 60 s com 69 células. O teste live desta data confirmou as quantidades de consulta e exportação para ambas as versões no serviço ativo.

O conjunto Playwright de 11 casos inclui as demais telas simuladas, mas isso valida suas interações locais, não sua integração com API ou banco. Os testes automatizados e live são evidências de desenvolvimento e integração. Não houve ainda teste final com participantes do público-alvo; essa sessão permanece necessária para avaliar compreensão e adequação de uso.

## Incidente de configuração do teste live

A primeira execução do teste live usou por padrão o frontend Vite local e seu proxy para `127.0.0.1:8000`, um processo host anterior à reconstrução da composição. O teste, por isso, encontrou uma seleção padrão divergente. A composição Docker foi reconstruída sem remover o volume; a execução final definiu `AIM_FRONTEND_BASE_URL=http://127.0.0.1:8080` e passou contra o frontend Nginx e a API atuais. A divergência era do destino usado pelo teste, não dos dados ou da regra da API.
