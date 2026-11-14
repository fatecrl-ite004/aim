# Diagramas da PoC V1 do AIM

Esta página reúne os diagramas prontos para abrir no diagrams.net ou na extensão draw.io. Eles representam o corte local da PoC V1; não são o desenho completo do produto AIM.

| Diagrama | Arquivo editável draw.io | Versão textual para leitura rápida |
| --- | --- | --- |
| Fluxo de replay AIOpsArena → OTLP → PostgreSQL → batch → API → UI; ground truth em caminho separado | [fluxo-replay-v1.drawio](../arquitetura/fluxo-replay-v1.drawio) | [fluxo-replay-v1.md](../arquitetura/fluxo-replay-v1.md) |
| Casos de uso da V1, com operador do replay e usuário técnico | [diagrama-caso-de-uso-v1.drawio](diagrama-caso-de-uso-v1.drawio) | [imagem](caso-de-uso-v1.png) |
| MER do schema PostgreSQL aplicado | [mer-v1.drawio](mer-v1.drawio) | [descrição e cardinalidades](mer-v1.md) · [visão geral](mer-visao-geral-v1.png) |

## Abrir e editar

Baixe/abra o arquivo `.drawio` na extensão diagrams.net do VS Code ou no editor do diagrams.net. Os arquivos são editáveis; o texto Markdown permanece como descrição e referência de cardinalidades/limites. Depois de editar um diagrama, atualize a cópia Markdown relacionada para manter a documentação sincronizada.

## Limites representados

- Papéis de caso de uso são tarefas da demonstração em laboratório, não personas validadas.
- Ground truth é falha injetada de referência, não detecção feita pelo AIM.
- MER deriva da migration atual da PoC; não representa o banco operacional futuro.
- Fluxo usa replay histórico local; não implica ingestão contínua em cliente.
