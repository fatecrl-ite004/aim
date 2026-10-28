# Protocolo experimental — estrutura proposta

Este é um roteiro inicial derivado das sínteses locais, não um protocolo aprovado. Preencher cada item antes de executar comparação confirmatória.

1. **Pergunta e unidade:** declarar se alvo é ponto, janela, evento, valor futuro, risco em horizonte ou mudança de regime.
2. **Cenário e rótulos:** registrar carga, sistema, início/fim do evento, componente, impacto, origem e incerteza do ground truth.
3. **Dados e qualidade:** documentar métricas/unidades, frequência, timestamp, ausências, duplicatas, alinhamento, agregação, procedência e overhead de coleta quando viável.
4. **Partições temporais:** definir treino, validação e teste futuro antes do ajuste. Impedir sobreposição de observações/alvos que permita compartilhar informação; ajustar normalização e seleção apenas com dados de treino; calibrar no máximo na validação.
5. **Baselines:** comparar ao menos alternativas simples pertinentes (por exemplo limites fixos por cenário ou baseline estatístico) com os mesmos dados e regras.
6. **Métodos e ablações:** descrever implementação, parâmetros, seeds e custo. Retirar componentes ou grupos de sinais um a um para medir contribuição incremental.
7. **Decisão:** congelar limiar/regra antes do teste final; especificar eventual método variável e condições de atualização.
8. **Métricas:** precisão, recall, F1 e PR-AUC quando apropriadas; event-wise com tolerância; alertas por tempo/entidade, atraso, eventos perdidos, antecedência para risco definido e custo. Evitar point-adjust como única evidência.
9. **Análise:** reportar por cenário/entidade, incerteza e repetições quando couber; não comparar diretamente números de artigos com números da PoC.
10. **Reprodutibilidade:** guardar código/configuração, versão dos dados (sem dados privados), ambiente, comando de execução, resultados, limitações e falhas experimentais.

Para risco antecipado, declarar horizonte, início do evento e regra de sucesso. Para associação/RCA, esclarecer que relação temporal não prova causa e definir ground truth independente ou avaliação especializada. Dados do teste não devem ser usados para escolher modelo, limiar, features ou narrativa de resultado.
