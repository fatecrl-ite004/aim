# Especificação de pesquisa: Wave, CPU e comportamento de API

**Estado:** especificação experimental inicial, não decisão de produto nem validação do modelo.  
**Data:** 2 de novembro de 2026.  
**Escopo:** CPU observada em contêiner e comportamento de API/RPC; avaliação local, sem banco de dados.  
**Código experimental:** `research/src/aim_wave/` e `research/experiments/wave_cpu_api/`.  
**Plano de trabalho local:** `plans/adaptacao-wave-aim.md` (ignorado pelo Git).

## 1. Pergunta

É possível calcular a coordenada CPU do candidato harmônico documentado no Wave a partir de uma série real de CPU, combiná-la com uma coordenada de desempenho API derivada de throughput, latência e erros, e obter uma representação reproduzível que possa ser avaliada como resumo/feature para análise temporal do AIM?

Perguntas secundárias:

1. Como a CPU observada varia junto com throughput, latência média e proporção de erros API?
2. As coordenadas preservadas pelo Wave (`A_cpu_normalized`, `P_api`) e sua representação polar `(R, phi)` mantêm proveniência e estados de ausência/invalidade?
3. Em intervalos de falha `cpu` do ground truth, os sinais CPU e API diferem descritivamente de janelas fora dos intervalos?

Esta etapa mede associação e executa a transformação matemática. Não afirma causalidade, eficiência real, antecipação ou superioridade de detector.

## 2. Base no Wave e controle de versões matemáticas

O contrato legado em `Wave-dev/math/README.md` especifica CPU C com referência explícita, `A=C/100`, desempenho API P gradual baseado em latência, throughput e erro e codificação harmônica das coordenadas A/P por `R=hypot(A,P)` e `phi=atan2(P,A)`. O mesmo documento ressalta que R não é energia física e que a onda é codificação, não periodicidade da aplicação.

O Wave contém outras formulações. Em particular, `s-fixed-reference-quality-v3` fixa S=1, calcula P a partir de goodput/latência e deixa CPU/RSS como covariáveis; a variante Activity acrescenta intensidade de solicitações/trabalho ativo. **Esta especificação não mistura essas fórmulas.** O candidato desta experiência recebe `model_id=wave-cpu-api-harmonic-v0.1`; não altera nem substitui as demais versões.

A pasta Wave fornecida descreve o núcleo C++ `aim_metrics.hpp` e um candidato CPU, mas esses arquivos de implementação não estão presentes na cópia examinada. O AIM faz uma implementação de referência Python a partir das fórmulas documentadas, identificada explicitamente como port experimental. Antes de atribuí-la como reprodução binária/paridade do núcleo de João, deve-se obter o código-fonte e fixtures originais.

### Fórmulas preservadas

Para janela de duração Δ, delta CPU em segundos `cpu_delta_seconds`, referência positiva `cpu_reference_cores`, total de requisições N, falhas F, latência média L em segundos, referências positivas `Tmax` e `Lmax`:

```text
C_percent = 100 * cpu_delta_seconds / (Δ * cpu_reference_cores)
A = C_percent / 100
Treal = N / Δ
E_percent = 100 * F / N
NL = Lmax / max(L, Lmax)
P_gradual = NL * (Treal / Tmax) * (1 - E_percent / 100)
R = hypot(A, P_gradual)
phi = atan2(P_gradual, A)
y(tau) = A*cos(2*pi*f*tau) + P_gradual*sin(2*pi*f*tau)
```

`cpu_reference_cores` é denominador de consumo. `A` pode exceder 1 (ou C_percent, 100%); não será limitado. `P_gradual` pode exceder 1; não será limitado. Não existe domínio triangular `P<=A` nesta hipótese harmônica de duas coordenadas independentes. R/phi é uma mudança de coordenadas, não nova informação quando o par A/P é preservado. Se A=P=0, a convenção do Wave registra phi=0, junto com `phase_identifiable=false` para tornar explícita a não identificabilidade matemática da fase.

Referências preliminares herdadas do contrato exploratório do Wave: `cpu_reference_cores=1`, `Tmax=100 req/s`, `Lmax=0,1 s`, portadora `f=1 Hz`. São referências experimentais fixadas antes da execução do script, não capacidade conhecida, SLO, ótimo ou ajuste aos resultados AIOpsArena. O relatório sempre as acompanha. Qualquer alteração cria novo `model_id`/rodada documentada.

## 3. Dados AIOpsArena disponíveis e limites

Nos arquivos locais examinados de Case-1 e Case-2 há:

- CPU cumulativa por contêiner em `container_cpu_usage_seconds_total`; usar delta entre timestamps da mesma série, nunca o valor acumulado como utilização instantânea.
- Sinais de CPU adicionais, como user/system time, load average, períodos/segundos throttled e CPU quota/period; fora do escopo da primeira hipótese, mas podem auditar/interpretrar CPU depois.
- Métricas Istio `istio_requests_total.grpc.<http-status>.<grpc-status>` e `istio_request_duration_milliseconds_sum.grpc.<http-status>.<grpc-status>`, com identificadores de aresta e instância em cmdb_id.
- Ground truth com `timestamp`, `duration`, `service`, `cmdb_id` e `failure_type`, incluindo eventos `cpu`.

As séries selecionadas examinadas usam timestamps espaçados em geral por 15 s. A janela observacional do AIOpsArena não é a janela nominal de 5 s usada nas capturas laboratoriais do Wave; o estudo usa intervalos efetivos entre pontos do dataset e registra `window_seconds`. Não interpolar para simular cadência de 5 s.

O conjunto permite medir contagem/taxa de chamadas Istio e duração média por soma-duração/soma-contagem, além de identificar status gRPC diferentes de `grpc.200.0` como erros do protocolo no recorte observado. Não há, nas métricas selecionadas, histograma de duração/buckets para calcular p95. A duração média não é cauda de latência nem necessariamente latência percebida pelo usuário final. `failure_type=cpu` anota a falha injetada; não é rótulo de degradação API.

### Chave de junção provisória

Para esta primeira leitura local, remover `observe.` de `container cmdb_id`; usar o segmento inicial do `Istio cmdb_id` (antes do primeiro ponto) como instância; agregar as arestas Istio desse prefixo por intervalo e associar à série CPU da instância. Isso é hipótese de mapeamento, não contrato oficial já confirmado do dataset. Guardar a chave original, direção/aresta, contagens e cobertura. Antes de promover resultado a evidência confirmatória, verificar topologia e semântica dos rótulos de origem/destino para evitar dupla contagem.

## 4. Entrada, pré-filtro e saída do protótipo

### Entrada canônica por intervalo

```json
{
  "case": "Case-1",
  "instance": "checkoutservice-0",
  "window_start_epoch_seconds": 1719205200,
  "window_end_epoch_seconds": 1719205215,
  "cpu_delta_seconds": 0.8,
  "requests_total": 100,
  "requests_failed": 2,
  "mean_latency_seconds": 0.045
}
```

O exemplo é ilustrativo, não amostra declarada do dataset. O adaptador preserva cada intervalo selecionado em CSV de features e registra estado/cobertura. As regras atuais excluem counters com reset/decréscimo, intervalos não positivos e pares de dados API não alinhados; não imputam zero. Valores inválidos são registrados como exclusões/parciais em vez de forçados ao domínio.

### Pré-filtragem

1. Validar schema, tipos, timestamp crescente, unidade e identidade da série.
2. Derivar deltas por série cumulativa; excluir delta negativo/reset e janela com Δ<=0 com motivo explícito.
3. Somar contadores/latências somente após manter escopo e intervalo compatíveis; derivar média de latência como delta de `duration_sum` dividido por delta de requests correspondente.
4. Mapear gRPC status zero como sucesso e demais status observados como falha nesta hipótese. Preservar os contadores/status originais.
5. Junção CPU↔Istio provisória por instância. A janela sem API correspondente permanece `partial`; não vira erro zero nem requisição zero.
6. Calcular A e P com referências congeladas; manter brutos e derivados. Não remover picos de CPU como outliers automaticamente: são potencialmente o sinal-alvo.

### Saídas

Por janela: IDs, timestamps, Δ, contadores/deltas originais, CPU usada e referência, throughput, erro percentual, latência média, `A_cpu_normalized`, `P_api`, `R`, `phi_radians`, status, reason, `model_id`, flags/proveniência e rótulos do ground truth em campo separado. A onda pode ser reconstruída se `f` e fase/tempo de portadora forem registrados; uma senoide amostrada não será contada como novas observações.

Para AIM, o par A/P ou R/phi pode futuramente ser uma feature de detector, mas o teste deve comparar representações e métricas brutas. O extrator não declara classe de anomalia. O detector posterior teria sua própria saída (score/evento/limiar/contribuições).

## 5. Protocolo experimental desta rodada

1. Fixar versão/hash dos dois casos e referências deste documento; dados brutos permanecem na pasta local externa ao AIM e não são copiados para Git.
2. Processar Case-1 e Case-2 localmente, sem banco, emitindo CSV de janelas derivadas e JSON de resumo em `research/reports/wave_cpu_api/generated/` (ignorado pelo Git), com relat?rio interpretativo versionado em `research/reports/wave_cpu_api/resultado-exploratorio-001.md`. Script e logs de execução ficam no repositório; resultados derivados grandes ficam em diretório local ignorado.
3. Calcular Spearman descritivo por caso/serviço entre CPU normalizada e cada desfecho API: latência média, throughput, percentual de erro; também CPU×P e estatísticas de R. Reportar n e casos sem variância.
4. Comparar janelas do mesmo serviço dentro/fora dos intervalos `cpu` de ground truth, reportando contagens e resumos descritivos. Não usar janelas vizinhas como amostras independentes para p-valores.
5. Reportar cobertura de join, quantas janelas `ok/partial/invalid`, cadência efetiva, ausência/reset e possíveis duplicações de arestas.
6. Não treinar detector nem declarar predição nesta fase. Após auditar o join, uma rodada separada pode avaliar detecção por episódio com split por caso/episódio e métricas event-wise.

## 6. Plano de testes e registro de evidências

Cada execução registra `experiment_id`, data UTC, Python/dependências, comando, hash SHA-256 dos CSVs utilizados, configuração/referências, revisão do código e caminhos de saída. Não incluir conteúdo bruto/logs de dados no relatório versionado.

| Nível | Verificação | Evidência esperada | O que não demonstra |
|---|---|---|---|
| Unitário matemático | Fórmulas A/P/R/phi, reconstrução polar | `research/tests/test_wave_cpu_api.py` | Significado operacional dos índices |
| Bordas matemáticas | CPU > referência preservada; zero-vector; faltantes; janela inválida | Estados e valores explícitos nos testes | Robustez a todo exporter/dataset |
| Adaptador fixture | Delta de contadores, erro gRPC, conversão ms→s, chave por instância e overlap de ground truth | `research/tests/test_aiopsarena_adapter.py` (pareamento por edge/status/intervalo, resets, duplicatas e cobertura) | Semântica verdadeira da topologia sem verificação externa |
| Dados locais | Inventário, cadência, cobertura de join e correlações descritivas | JSON/CSV local + relatório de execução | Causalidade, independência temporal ou generalização |
| Paridade com Wave original | Mesmo corpus de fixtures e execução do núcleo C++ oficial quando obtido | Comparação numérica/estados por fixture com tolerância pré-fixada | Equivalência com versão não identificada |

Não ampliar tolerância para esconder divergência. Diferença em valores, estado, flags ou ausências interrompe a comparação e exige diagnóstico. Reconstrução exata da onda verifica algebra/implementação, não a validade do indicador para operação.

## 7. Critérios para avançar à integração futura

- A semântica de cada métrica e a junção AIOpsArena ficam auditadas.
- A implementação coincide com o contrato documentado e, quando código/fixtures do Wave forem obtidos, passa teste de paridade.
- Saídas mantêm valores brutos, referência, `model_id`, estados e motivos.
- Associação CPU/API é avaliada por execução/episódio e comparada às séries brutas; evidência não depende de correlação algébrica com a própria fórmula.
- Um possível uso como feature melhora uma tarefa de detecção definida em split temporal/por episódio e sob baseline equivalente.

Somente após esses critérios uma decisão registrada poderia migrar o componente experimental de `research/` para a arquitetura de `system/`. Até então, esta especificação e o código são pesquisa reproduzível, não funcionalidade existente do AIM.
