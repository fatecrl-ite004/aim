# Infraestrutura local

A composição completa da PoC V1 está descrita em [`deploy.md`](../deploy.md) e adicionada como overlay a `compose.v1.yml`. Ela inclui FastAPI, PostgreSQL, frontend Nginx, Collector OTLP e um runner sob demanda. A pipeline OTLP é síncrona e não aplica batching, fila ou compressão, para o receptor persistir o lote antes de confirmar a resposta.

`otel-collector.yaml` e `nginx/aim.conf` configuram a composição Docker. `otel-collector.host.yaml` configura o Collector instalado no Windows, com destino na API em loopback. Nenhum segredo ou arquivo do AIOpsArena deve ser adicionado a esta pasta ou à imagem da aplicação.
