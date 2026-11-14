# Visão e escopo

**Revisado em:** 10 de novembro de 2026.

AIM significa **Active Intelligent Monitoring**. O título do TCC é *AIM: Uma análise multivariada de anomalias temporais em infraestruturas computacionais*. A pesquisa aplicada propõe uma prova de conceito a validar primeiro em laboratório e depois em ambiente de teste. A direção de implantação futura é on-premises na infraestrutura do cliente. Para a V1 acadêmica local, autorizada em 10/11/2026, a equipe implementa uma jornada com Python/FastAPI, PostgreSQL, OTLP/HTTP Protobuf e o frontend React existente: replay histórico local AIOpsArena, persistência dos pontos originais, processamento AIM versionado e consulta pela API. Essa decisão técnica não transforma o replay em coleta contínua nem define a fonte operacional do produto completo.

O objetivo é avaliar se a análise conjunta e temporal ajuda a identificar degradações e a apoiar a investigação humana. Eventual antecipação de eventos, redução de alertas e melhoria operacional dependem de hipóteses, cenários, rótulos e avaliação; não são resultados existentes.

## Incluído na direção de pesquisa

- Métricas selecionadas de infraestrutura computacional — incluindo CPU como feature candidata e contexto — e sinais de API, como latência, throughput e erros, conforme telemetria disponível.
- Reutilização de dados de telemetria já disponíveis e avaliação de ingestão OTLP; preservar timestamps e analisar janelas temporais. A configuração detalhada do middleware/collector ainda não foi aprovada.
- Comparação de baselines simples e métodos estatísticos ou de aprendizado de máquina.
- Aplicação web com representação de séries, eventos e contexto, além de controle de acesso por perfil (RBAC).
- Avaliação de detecção, e de risco antecipado apenas se houver definição de evento e horizonte.

## Fora do escopo atual

O AIM não executa remediação automática, mudanças em código ou infraestrutura do cliente, commits, pull requests ou deploys. A decisão continua com pessoas. Logs, traces e topologia ficam fora da primeira versão. O AIM não pretende coletar toda a telemetria nem substituir as ferramentas de observabilidade existentes. LLM é uma possibilidade complementar a avaliar, sem autoridade de decisão.

## Limites conceituais

Detecção de anomalia, forecasting de valores, previsão de risco de evento, detecção de change point e RCA têm alvos distintos e requerem critérios próprios. Limites fixos e variáveis são alternativas a avaliar por cenário. Correlação ou precedência temporal indica associação observada e não comprova causalidade.

O desenho de implantação on-premises é a direção pretendida. Na V1 local da P2, a stack de receiver/API e banco já está definida; os detalhes de configuração e produção serão mantidos em separado dos testes da aplicação. Para operação futura continuam em aberto as fronteiras de rede, frequência de coleta, autenticação, retenção e resposta a falhas. Também permanecem a definir o modelo final, score, evento-alvo, horizonte de risco e limiar. A detecção de eventos iniciados e a estimativa de risco futuro são objetivos distintos e ambos deverão ser avaliados com critérios próprios. A arquitetura em [visão geral](../arquitetura/visao-geral.md) é conceitual.

Para as decisões e pendências da primeira versão, consulte [Direção preliminar da primeira versão](escopo-primeira-versao.md).
