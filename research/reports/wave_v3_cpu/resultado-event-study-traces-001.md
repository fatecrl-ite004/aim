# Estudo de episódios Wave v3 + traces — rodada 001

**Data:** 2 de novembro de 2026  
**Modelo:** `s-fixed-reference-quality-v3`, sem alterações.  
**Pergunta:** em episódios anotados de CPU e delay, o que acontece com CPU, saídas v3, spans do serviço e latência de traces de entrada?  
**Desenho:** comparação descritiva de períodos iguais antes, durante e depois do evento.  
**Dados brutos:** AIOpsArena local; não foram copiados para o AIM.

## Garantia de fidelidade ao Wave

O cálculo Wave continua recebendo somente os campos do contrato v3, com `Tref=40 req/s`, `Lref=0,1 s` e `S=1`. A CPU continua covariável. As latências dos traces são **desfechos externos de avaliação**: não entram em `derive`, não substituem a latência média do contrato e não alteram P/Q/S/D. Nenhuma referência, corte ou fórmula foi ajustado aos eventos.

As injeções simultâneas nas três réplicas `currencyservice` do Case-2 foram agrupadas como **um episódio**, não três repetições independentes. As fases usam o intervalo de duração do evento imediatamente antes, durante e depois. A quantila é nearest-rank empírica, sem interpolação ou aparagem. O timestamp dos traces é interpretado como microssegundos pelo valor e alinhamento observado com o eixo temporal das métricas; essa unidade ainda deve ser confirmada pela documentação de origem.

## Resultado dos episódios de CPU

| Episódio | Traces de entrada p95 antes → durante → depois | Métricas por janela no AIM/Wave |
|---|---|---|
| Case-1 `recommendationservice-1` | 0 → 2 → 0 spans de entrada; insuficiente | Latência Istio média 2,8 → 19,4 → 3,5 ms; CPU média observada 0 cores nas três fases |
| Case-1 `paymentservice-1` | 47,0 → 48,8 → 47,9 ms; sem mudança relevante no p95 de entrada | CPU 0,006 → 0,250 → 0,006 cores; latência média Istio 2,2 → 27,5 → 2,0 ms; P 0,0065 → 0,0076 → 0,0065 |
| Case-2 `currencyservice` (três réplicas, um episódio) | 50,1 → 1.455,0 → 51,0 ms; 2.981 → 2.715 → 2.992 spans de entrada | CPU 0,0116 → 0,0926 → 0,0406 cores; latência média Istio 1,8 → 119,3 → 9,2 ms; P 0,528 → 0,402 → 0,528 |

O episódio Case-2 mostra coexistência clara de CPU maior, latência média Istio elevada e cauda da latência de entrada elevada durante a injeção, com recuperação posterior. É um **sinal exploratório dentro de um episódio**; não estabelece causalidade nem generalização. Os traces não contêm spans `request` identificados como `currencyservice` no episódio, e identificam serviço, não pod. Assim, a cauda observada é da entrada do sistema, não uma atribuição comprovada à réplica CPU afetada.

No Case-1 Payment há CPU e latência média Istio maiores durante o evento, porém o p95 dos traces de entrada permaneceu praticamente estável. Também não houve spans `request` identificados como `paymentservice`. A divergência pode refletir escopos/agregações diferentes ou uma junção ainda provisória; não se deve escolher a medida que confirme a hipótese e ignorar a outra.

O primeiro episódio Case-1 tem CPU constante/zero e cobertura trace quase nula; não permite medir a hipótese nessa fase.

## Eventos `delay`: controle positivo e limite da v3

Nos quatro episódios agrupados de `delay`, os spans `request` do serviço afetado tiveram p95 muito maior durante a injeção e voltaram próximo ao nível anterior depois:

- Case-1 checkoutservice: 50,5 → 2.208,8 → 49,5 ms.
- Case-1 frontend: 49,0 → 2.287,4 → 47,5 ms.
- Case-1 checkoutservice: 48,8 → 5.996,3 → 53,2 ms.
- Case-2 frontend: 49,6 → 2.117,9 → 53,3 ms. **Este episódio coincide com três falhas `pod-failure` de cartservice**, portanto não isola o efeito de delay.

O p95 de entrada acompanhou fortemente o aumento no episódio frontend de cada caso, mas não nos dois eventos checkoutservice. Isso sugere propagação distinta e/ou diferenças de cobertura/mapeamento; as distribuições não foram reconstruídas por `trace_id` para provar que os spans pertencem às mesmas requisições ponta a ponta.

O Case-2 frontend `delay` também mostra uma limitação importante da v3 sem que a fórmula deva ser mudada: o p95 de entrada subiu de 49,6 para 2.117,9 ms, mas a média Istio agregada por réplica ficou abaixo de `Lref=0,1 s` e P permaneceu saturado em 1 (`D=0`) antes, durante e depois. A v3 calcula qualidade a partir da **latência média** e seu corte é parte do contrato; não representa automaticamente cauda de latência. Esta observação é um diagnóstico de sensibilidade/escopo, não justificativa para reajustar Lref usando os mesmos dados. Referência ou entrada diferente requer protocolo e versão/model_id separados, autorizados pelo contrato Wave.

## Cobertura e limites

O leitor examinou 10.723.154 linhas no trace Case-1 e 3.729.683 no Case-2, sem linhas de timestamp/duração inválidas. Foram selecionados 35.219 root spans de entrada e 8.470 spans `request` dos serviços afetados nos intervalos estudados. Essas contagens são por categoria e não necessariamente disjuntas: um root frontend também pode ser span request do serviço alvo. A taxa de amostragem/completude do trace não está estabelecida. O CSV inteiro tem cerca de 2,36 GB; a execução lê em streaming e guarda apenas os eventos/estatísticas.

Limites centrais:

1. Há apenas dois episódios de CPU no Case-1 e um no Case-2; as três réplicas atingidas no Case-2 formam uma única injeção.
2. Spans identificam serviço, não necessariamente `cmdb_id` do contêiner CPU. Nos eventos CPU não houve spans `request` do serviço-alvo; só métricas Istio e root spans de entrada estão disponíveis para comparação.
3. A associação de Istio por prefixo de instância continua provisória e pode não representar exclusivamente tráfego servido pela réplica afetada.
4. Os spans não foram correlacionados por `trace_id` nem confrontados com a taxa de amostragem do exporter; suas distribuições são grupos de spans observados.
5. Contagens de janelas/spans dentro de um episódio não são repetições experimentais independentes. Não foram calculados p-values nem desempenho de detector.
6. Os eventos delay são rótulos de intervenção, não ground truth de latência API para qualquer tipo de falha. O evento Case-2 também tem co-injeção de pod-failure.

## Conclusão e próximo passo

O AIOpsArena ainda vale para uma prova de caminho e uma exploração de episódios: temos um sinal promissor no evento CPU do Case-2 e o método encontra as anomalias de cauda nas injeções de delay. A evidência não basta para validar CPU como preditor, classificador ou causa de problema API. **Não precisamos trocar dataset antes de fazer um teste mais controlado**, mas precisaremos de mais episódios CPU independentes para sustentar a hipótese.

O próximo passo é validar o mapeamento de serviço/pod e a semântica/amostragem dos traces, depois executar cenários de CPU repetidos com controles e identidade de réplica conhecida. Manter v3 e referências congeladas; avaliar p95 externamente como resultado. Se o AIM precisar de p95 como entrada, isso deve ser proposto como novo contrato Wave/model_id, não inserido silenciosamente na v3.

## Reprodução

Primeiro reproduza as janelas v3 conforme o [guia principal](../../experiments/wave_v3_cpu/README.md), depois rode:

```powershell
python research\experiments\wave_v3_cpu\run_trace_event_study.py `
  --dataset-root 'C:\Users\00001\Downloads\datasets_aim\AIOpsArena'
```

O JSON integral, hashes SHA-256 e auditorias ficam em `research/reports/wave_v3_cpu/generated/trace_event_study.json`, ignorado pelo Git. Testes de agrupamento de episódios, limites de janela, quantil e leitura/hash estão em `research/tests/test_trace_event_study.py`.
