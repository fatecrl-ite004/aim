# Dados

Convenções previstas; nenhum dataset foi incorporado nesta organização.

- `raw/`: captura original, imutável. Registrar fonte, licença, aquisição, período, fuso, granularidade, unidades, entidades e rótulos. Não sobrescrever para limpeza.
- `interim/`: transformações intermediárias reproduzíveis, acompanhadas de código/configuração e descrição de alterações.
- `processed/`: matrizes/séries preparadas para experimento. Registrar normalização, imputação, agregação, janelas, seleção de sinais e versão do protocolo.

Manter dados fora do Git quando forem volumosos, restritos ou de licença incerta. Nenhum dado deve ser copiado para este repositório sem autorização e análise de licença/privacidade. Índices e metadados podem ser versionados sem o conteúdo, após decisão. Ao criar splits, preservar cronologia e impedir compartilhamento de observações-alvo que cause vazamento.

Formato, particionamento, armazenamento, nomenclatura e estratégia de versão ainda não foram escolhidos.
