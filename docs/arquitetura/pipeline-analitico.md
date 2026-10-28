# Pipeline analítico — proposta de avaliação

Fluxo conceitual: validar e identificar sinais → alinhar as séries no tempo → preparar partições cronológicas → ajustar baseline/modelo no treino → selecionar parâmetros e limiar na validação → congelar o procedimento → avaliar uma única vez no teste futuro → produzir relatório com limitações.

A preparação deve impedir que informação do teste influencie o treino, seleção de métricas, normalização, score ou limiar. Janelas compartilhando observações ou alvos entre partições, ou transformações ajustadas sobre dados futuros, podem introduzir vazamento. Defasagens e janelas devem ser definidas em relação ao momento em que a decisão estaria disponível.

## Objetivos avaliados separadamente

- Detecção: identificar ponto, janela ou evento anômalo já iniciado.
- Forecasting: estimar valor futuro de métrica.
- Risco: estimar evento-alvo dentro de horizonte fixado.
- Change point: sinalizar mudança de regime.
- Associação/RCA: descrever ou ranquear sinais; requer rótulos e validação próprios para alegar qualidade diagnóstica.

Baselines plausíveis incluem regras/limites estáticos por cenário e métodos estatísticos simples. Seleção final depende do protocolo. Medidas incluem precisão, recall, F1, PR-AUC quando aplicável, medidas por evento, falsos alertas por tempo/serviço, atraso, antecedência para um alvo de risco e custo. Point-adjust não deve ser a única medida. Métricas event-wise precisam explicitar tolerância e correspondência.

Consulte [protocolo experimental](../pesquisa/protocolo-experimental.md) para o desenho ainda pendente.
