# Roteiro da apresentação P2 da V1 AIM

**Duração prevista:** 5 minutos. **Objetivo:** explicar a ideia materializada, mostrar uma jornada funcional, apresentar acertos e dificuldades e indicar a direção seguinte. Este roteiro descreve a V1 local comprovada.

## 0:00–0:35 — Contexto e proposta

“O AIM é nosso projeto de pesquisa aplicada sobre a análise temporal conjunta de métricas de infraestrutura e sinais de APIs. A ideia é apoiar a investigação técnica quando uma aplicação apresenta degradação. Para esta primeira materialização, construímos uma prova local que recebe métricas históricas, organiza os dados no tempo e permite consultar o que foi observado. O resultado ainda não é um detector de anomalias nem uma solução instalada em um ambiente cliente.”

## 0:35–1:15 — O que foi construído

“A jornada usa um recorte do AIOpsArena. Ao iniciar a demonstração na interface, a API envia as amostras por OTLP/HTTP Protobuf ao Collector, recebe os pontos e os persiste no PostgreSQL. A transformação calcula métricas derivadas e estados de cobertura e grava execuções versionadas. O frontend consulta a API para mostrar o andamento do replay, o detalhe de serviço e as séries temporais. O JSON de ground truth entra separadamente e aparece como falha injetada, não como alerta detectado.”

## 1:15–2:30 — Demonstração

1. Abrir **Visão geral → Replay histórico AIOpsArena** e clicar em **Iniciar demonstração**. Acompanhar o progresso e abrir o replay quando aparecer.
2. Apontar a fonte, o serviço, a instância e o intervalo histórico em UTC. Mostrar as amostras que chegam e a atualização suave dos gráficos.
3. Mostrar CPU, taxa de respostas bem-sucedidas e latência média; explicar a opção de janelas de 15 s e a agregação de 60 s.
4. Expandir **Consultar valores e cobertura por intervalo** e explicar que lacunas não viram zeros artificiais. Se houver tempo, mostrar a exportação CSV consultada do banco.
5. Apontar o marcador de falha injetada como anotação da fonte. Dizer explicitamente que associação temporal não demonstra causalidade.

**Preparação:** subir a composição conforme `deploy.md` e abrir `http://127.0.0.1:8080`. O recorte AIOpsArena deve estar no caminho local configurado em `.env.v1`; ele não faz parte do repositório. Manter também uma execução persistida disponível como plano de contingência.

## 2:30–3:20 — O que funcionou

“O caminho completo foi executado e conferido: 282 pontos de origem em três séries chegaram via OTLP; comparamos os pontos persistidos com a fonte e não encontramos amostras faltando, extras ou valores diferentes. O processamento gerou 92 janelas, 276 estados de cobertura e 207 valores numéricos. A API e a interface consultaram esses resultados. Também reiniciamos API e PostgreSQL e confirmamos que as contagens e os hashes dos dados continuaram iguais.”

## 3:20–4:20 — Dificuldades e limites

“Uma dificuldade importante foi separar a identidade real de cada série dos atributos que só servem para rastrear o arquivo e a linha de origem. Se misturássemos esses elementos, cada amostra poderia virar uma série artificial. Também verificamos que o arquivo tem passos de 15 segundos, mas os incrementos dos counters de API aparecem a cada 60 segundos e alinhados. Por isso, ‘sem incremento observado’ não quer dizer que provamos ausência de requisições em cada intervalo. O recorte seleciona respostas 200, então não permite calcular uma taxa geral de erros. Não treinamos modelo nem avaliamos detecção; Wave e modelo continuam fora da demonstração.”

## 4:20–5:00 — Direção seguinte

“A próxima etapa é avaliar cenários de uso com equipes técnicas e definir o protocolo para comparar métodos de detecção. Para uma solução completa ainda serão necessários segurança, cadastro de fontes e operação contínua em ambiente local. A V1 mostra que conseguimos persistir e consultar o replay com rastreabilidade; a utilidade operacional e o desempenho analítico ainda precisam de avaliação.”

## Checklist antes de apresentar

- Confirmar API pronta em `http://127.0.0.1:8080/health/ready`, Collector em `http://127.0.0.1:13133/` e interface em `http://127.0.0.1:8080`.
- Testar previamente o botão **Iniciar demonstração**; manter uma execução persistida para contingência.
- Deixar a tela no Dashboard e a rota de detalhe disponíveis; conferir fonte, período UTC e execução de transformação.
- Manter visíveis os rótulos de mock das demais áreas e dizer “falha injetada”, não “falha detectada”.
- Se a demo ao vivo falhar, narrar sobre capturas verificadas da jornada real; não substituir por cenário fictício sem identificá-lo como mock.
- Encerrar até cinco minutos e reservar perguntas para depois.
