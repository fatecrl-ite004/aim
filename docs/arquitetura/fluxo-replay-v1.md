# Fluxo do replay histórico na V1 local

**Estado:** fluxo executado e verificado localmente. No Compose completo, o replayer envia OTLP via Collector; no modo host, é possível enviar diretamente à API FastAPI. Ground truth e amostras métricas seguem caminhos separados.

```mermaid
flowchart LR
  CSV["CSV AIOpsArena<br>pontos de origem"] --> REPLAY["CLI replayer<br>sem transformação"]
  REPLAY --> OTLP["OTLP/HTTP<br>Protobuf"]
  OTLP --> COLLECTOR["OpenTelemetry Collector<br>receiver OTLP/HTTP"]
  COLLECTOR --> RX["FastAPI receiver<br>/v1/metrics; commit antes do ACK"]
  RX -->|"transação + commit"| RAW[("PostgreSQL<br>pontos raw")]
  RAW --> BATCH["Batch AIM<br>versionado"]
  BATCH --> DERIVED[("PostgreSQL<br>derivadas + cobertura")]
  JSON["JSON AIOpsArena<br>ground truth"] --> IMPORT["CLI importador<br>etapa separada"]
  IMPORT --> EVENTS[("PostgreSQL<br>eventos de referência")]
  RAW --> READ["FastAPI<br>API de leitura"]
  DERIVED --> READ
  EVENTS --> READ
  READ --> UI["Frontend<br>Dashboard → detalhe"]
```

No Compose, o Collector encaminha as requisições de forma síncrona, sem compressão, fila ou batch processor. O receiver responde sucesso OTLP somente após o commit da transação; se o commit falhar, não há aceitação. O batch consulta apenas dados raw persistidos. Uma falha de CPU injetada do ground truth não é detector nem resultado de causalidade. Após reinício, o volume PostgreSQL mantém os dados e a UI consulta os mesmos IDs de replay e transformação.
