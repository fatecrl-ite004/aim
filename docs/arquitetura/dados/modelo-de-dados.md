# Modelo de dados — conceitos preliminares

Este modelo conceitual deriva do escopo de métricas OTLP e avaliação temporal. Não é schema físico nem compromisso com banco, formato de arquivo ou API.

Entidades que provavelmente serão necessárias para tornar experimentos rastreáveis:

- **Observação de métrica:** nome, valor, unidade, timestamp, recurso/entidade e atributos de contexto.
- **Série:** sequência ordenada de observações para uma combinação documentada de métrica e entidade.
- **Evento rotulado:** início/fim, tipo de cenário, entidade afetada, impacto observado e origem do rótulo.
- **Execução experimental:** código/configuração, versão dos dados, split temporal, seed quando aplicável, resultados e ambiente.
- **Resultado de método:** score ou previsão, janela de disponibilidade, modelo/versão e limiar aplicado.

Campos obrigatórios, cardinalidade, chaves, granularidade, unidades, retenção e serialização devem ser decididos após validar fontes e cenários. Uma proposta exploratória de entidades e relacionamentos está na [seção 8 de escopo-primeira-versao-ideias.md](../../projeto/escopo-primeira-versao-ideias.md#8-dados-e-mer-conceitual-proposto); não é schema aprovado. AIOpsArena é apenas dataset candidato e poderá informar um mapeamento, sem determinar por si só o modelo operacional. Ver [dicionário](dicionario-de-dados.md).
