# Dicionário de dados — rascunho

Os nomes abaixo descrevem informação a documentar, não campos de um schema já implementado.

| Informação | Conteúdo esperado | Estado |
| --- | --- | --- |
| metric_name | Nome estável da métrica emitida. | A definir por cenário e convenção de instrumentação. |
| value | Valor observado. | Tipo, precisão e validação pendentes. |
| unit | Unidade física/lógica do valor. | Deve ser explicitada; lista pendente. |
| timestamp | Horário do evento/observação e fuso/referência temporal. | Semântica e precisão pendentes. |
| entity/resource | Serviço, instância ou componente a que o sinal pertence. | Atributos OTLP efetivos pendentes. |
| attributes | Dimensões contextuais relevantes. | Selecionar para evitar cardinalidade desnecessária. |
| event_start / event_end | Intervalo de evento rotulado. | Definição de ground truth pendente. |
| event_type | Cenário ou tipo de degradação. | Taxonomia pendente. |
| split | Partição temporal de treino, validação ou teste. | Protocolo pendente. |
| score / threshold | Saída do método e critério de decisão. | Método e limiar por cenário pendentes. |

Dados devem preservar ordem temporal, procedência, unidade e regra de transformação. Documentar ausências, duplicatas, reamostragem e agregação. Não materializar dado bruto sensível ou de licença incerta no repositório.
