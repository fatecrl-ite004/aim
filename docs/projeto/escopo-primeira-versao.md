# Direção preliminar da primeira versão do AIM

**Revisado em:** 3 de novembro de 2026

**Estado:** entendimento inicial registrado a partir das decisões discutidas pela equipe. Os itens neste documento servem para organizar o trabalho; detalhes em aberto serão resolvidos um a um. Propostas de arquitetura no documento complementar são ideias para discussão, não decisões aprovadas.

## 1. Escopo do produto

A validação começa em laboratório e deve avançar para um ambiente de teste. A direção de implantação pretendida é on-premises, dentro da infraestrutura do cliente. A instância do AIM acompanhará apenas as aplicações que o administrador cadastrar e que sejam alcançáveis a partir do ambiente em que o AIM estiver hospedado. Alcance de rede, fronteiras entre ambientes e isolamento entre organizações ainda precisam ser especificados.

O foco inicial é analisar métricas selecionadas de infraestrutura computacional e sinais de API para investigar o impacto observado nas aplicações. A solução pretende reutilizar dados que o cliente já tenha disponíveis; não vai instrumentar tudo, ler toda a telemetria ou substituir a plataforma de observabilidade do cliente. Painéis podem consolidar os sinais e as análises relevantes.

Logs, traces distribuídos e topologia ficam fora da primeira versão. O usuário final das aplicações monitoradas não opera o AIM. A equipe AIM não fará alterações diretas no código-fonte ou na infraestrutura do cliente e o produto não fará remediação automática.

## 2. Usuários e permissões

As personas existentes em [`personas.md`](../requisitos/personas.md) são hipóteses documentais, não perfis confirmados por pesquisa com usuários. SRE é a persona mais próxima do usuário técnico que investiga degradações. Desenvolvedores são o público inicialmente imaginado pela equipe, mas ainda precisam ser detalhados e validados. Orientador e colegas convidados podem participar de testes em laboratório; isso não os torna automaticamente usuários do produto em cliente.

O administrador da plataforma será responsável por cadastrar aplicações, fontes de telemetria e usuários. O que cada perfil poderá consultar, configurar ou administrar ainda está em aberto. O RBAC será definido a partir das tarefas, das personas validadas e dos requisitos de segurança.

Também serão consideradas as perspectivas de engenheiro de dados, engenheiro de machine learning e arquiteto de soluções para revisar ingestão, qualidade e modelagem de dados, desenho analítico e implantação. Essas são competências necessárias à equipe/revisão do projeto; não são automaticamente personas que usarão a interface AIM. Consulte as [personas](../requisitos/personas.md), incluindo as perspectivas profissionais a incorporar na análise do projeto.

## 3. Fluxo principal de uso

O fluxo principal pretendido é o usuário receber uma notificação de uma anomalia detectada, tanto na interface quanto por e-mail, e abrir o AIM para entender o que foi detectado, onde e quando. O produto também deverá permitir registrar sistemas e consultar a cadeia de sinais/erros relacionada a um evento. O número e a sequência final dos casos de uso ainda serão mapeados a partir das personas.

A ingestão deverá receber dados das aplicações e fontes que o cliente escolher vincular ao AIM. Um middleware/collector OTLP é uma possibilidade a avaliar, não uma arquitetura decidida. O administrador configura o vínculo seguindo instruções; a equipe AIM não altera diretamente a aplicação do cliente. O sistema e as fontes do cliente são os participantes externos principais. O provedor ou serviço de e-mail ainda não foi escolhido.

A consulta contínua de dados, a consulta a análises históricas armazenadas localmente e a emissão de uma trigger/evento são objetivos propostos. Componentes, atualização, persistência, estado de falha e canal de notificação dependem de decisões posteriores.

## 4. Comportamento da análise

A direção de pesquisa inclui dois objetivos: detectar anomalias que já começaram e avaliar risco de eventos futuros. São tarefas diferentes e precisam de critérios, rótulos, horizontes e medidas separados. A revisão do estado da arte oferece conceitos e métodos para apoiar a definição; ainda será necessário operacionalizar os critérios por cenário AIM.

CPU deverá ser avaliada tanto como *feature* do detector quanto como contexto visível na investigação. Isso não modifica as fórmulas do experimento Wave v3 já especificado. LSTM é uma hipótese para aprender padrões temporais e uma possível memória de comportamento válido, não uma escolha final nem capacidade demonstrada. Um LLM pode ser investigado para síntese de alto nível apoiada por evidências, sem decidir pelo usuário nem transformar associação temporal em causalidade.

A forma de saída — score, evento, severidade e apresentação de evidências — ainda será especificada. A notificação deve comunicar, em alto nível, o que ocorreu, onde, quando e quais sinais sustentam a indicação.

## 5. Requisitos funcionais e aceite

O mock em [`frontend/`](../../frontend/) é a referência inicial para telas, cadastro de sistemas, visualização de métricas, filtros por aplicação/serviço/período e exportação CSV/JSON. É uma base de exploração, não uma especificação completa do produto.

A equipe pretende demonstrar atendimento aos requisitos com testes, capturas de tela e extrações/relatórios de validação, conforme o tipo de requisito. Os [testes de desenvolvimento da V1](../evidencias/v1/testes-desenvolvimento-2026-11-12.md) registram o recorte executado. Além das telas de mock, a PoC V1 acrescentou uma jornada conectada: replay histórico AIOpsArena por OTLP, FastAPI, PostgreSQL, processamento versionado e consulta no frontend. A composição Docker completa foi verificada em 11/11/2026; isso não torna conectadas as outras telas nem conclui os requisitos de produto descritos abaixo.

## 6. Arquitetura e dados de operação

A direção é hospedar o AIM on-premises no cliente e limitar a supervisão às aplicações cadastradas e alcançáveis a partir dessa instalação. A arquitetura de ingestão OTLP, a identificação de aplicação/serviço/instância/ambiente, autenticação, limites de rede e isolamento ainda precisam ser definidos.

O conjunto inicial de dados a persistir inclui métricas de CPU e de API, timestamp, origem e atributos necessários para interpretar a extração. Tipo, unidade, granularidade, atributos de identidade e demais métricas serão mapeados durante a validação. A equipe entende que os dados devem ser associados ao tempo e à configuração que os produziu; o identificador e o versionamento dessa configuração ainda precisam ser confirmados no modelo.

Os dados brutos serão descartados após um período de retenção X, ainda a decidir. O que será agregado e por quanto tempo análises, eventos, evidências e registros de auditoria serão mantidos ainda está em aberto. Para o replay local demonstrativo da P2, Pedro selecionou o AIOpsArena em 10/11/2026. Essa escolha atende a uma prova controlada e não define a fonte operacional da solução completa nem o dataset final de avaliação científica. Seu formato servirá como evidência para adaptação, não deve ser copiado automaticamente como schema operacional do AIM.

## 7. Casos de uso

Os objetivos iniciais que devem originar casos de uso serão derivados das personas e dos papéis confirmados. A lista candidata inclui:

- receber uma notificação de anomalia no frontend ou por e-mail e consultar o evento;
- registrar uma aplicação/sistema e vincular suas fontes de telemetria;
- acompanhar métricas e consultar uma análise ou evento histórico;
- visualizar a cadeia de sinais/erros relacionada ao evento;
- exportar dados ou resultados, conforme o fluxo já explorado no mock;
- administrar usuários e configurações da plataforma, se essa responsabilidade for confirmada no MVP.

O fluxo principal de notificação foi indicado: uma anomalia é detectada, o usuário recebe aviso no frontend e por e-mail e consulta o evento. Os casos de registro de sistemas e consulta da cadeia de sinais também foram indicados. Atores exatos, pré-condições, passos, alternativas, erros, resultado esperado, permissões e requisitos relacionados ainda serão mapeados. Não presumir uma “cadeia de erros” baseada em traces distribuídos, pois traces estão fora da primeira versão; definir essa visualização usando as métricas e evidências disponíveis.

Os sistemas do cliente e suas fontes de telemetria participam do registro e da ingestão. O serviço de e-mail participa do envio, mas ainda não foi escolhido. Ações que exigem permissões especiais ainda não foram definidas; o cadastro de aplicações/fontes/usuários é atribuição preliminar do administrador.

## 8. Dados e MER

Para a primeira operação, foram citados dados de CPU, dados de API e timestamps. A lista é inicial e incompleta. A extração deve permitir identificar tipo/nome da métrica, unidade, granularidade, instante, origem e entidade relacionada. A forma de representar aplicações, serviços, instâncias, ambientes, análises, eventos e evidências será definida ao mapear os fluxos e validar a fonte de dados.

A equipe considera que o vínculo entre dado, tempo e configuração produtora já foi discutido. O requisito é registrado aqui; a chave concreta e o versionamento precisam ser recuperados e incorporados ao modelo para garantir rastreabilidade.

O AIOpsArena foi selecionado para a prova local da P2 e segue como possibilidade a avaliar nos experimentos da pesquisa. Seus dados permitem estudar um mapeamento de importação/adaptação. Esse esquema será evidência para o modelo experimental, não a definição automática do MER operacional.

O período X para exclusão de dados brutos será definido. Agregações, resultados de análise, eventos, evidências e auditoria exigem políticas de retenção próprias. A proposta de MER está em [`escopo-primeira-versao-ideias.md`](escopo-primeira-versao-ideias.md), marcada como sugestão para revisão pelas perspectivas de engenharia de dados, machine learning e arquitetura de soluções.

## 9. Critérios de sucesso e avaliação

Um resultado útil para o usuário deve informar, em alto nível, **o que** foi detectado, **onde** (aplicação/serviço ou entidade identificada), **quando** ocorreu ou foi sinalizado e **como** os sinais observados sustentam o alerta. “Como” significa apresentar evidências e uma síntese compreensível; não afirmar causa raiz sem base apropriada.

A avaliação quantitativa deverá usar medidas da literatura para falsos alertas, eventos encontrados e atraso/antecedência. A seleção precisa corresponder ao alvo e ao protocolo: detecção de eventos iniciados e risco futuro não devem ser misturados numa única métrica. O protocolo local já lista candidatos como precisão, recall, F1, PR-AUC quando aplicável, medidas por evento, falsos alertas por tempo e atraso; as medidas definitivas e tolerâncias serão decididas com o cenário e os rótulos.

O dataset e o protocolo da avaliação científica ainda estão em validação. AIOpsArena está selecionado apenas para o replay técnico local da P2; isso não demonstra desempenho do Wave/detector nem encerra a escolha do conjunto experimental. A primeira avaliação poderá usar ambiente controlado com métricas artificiais/injetadas e rótulos conhecidos, conforme validação do desenho experimental. Quem participará da validação da aplicação e como o feedback será registrado também será definido. Testes de fluxo, evidências de tela/extração e feedback dos participantes devem ter registros rastreáveis.

## Pendências a resolver, uma a uma

1. Validar o caminho de ingestão: fontes do cliente, OTLP, middleware/collector, identificação de serviço/instância/ambiente, autenticação e limites de rede.
2. Confirmar personas e participantes do laboratório; definir tarefas dos perfis e permissões RBAC.
3. Mapear os casos de uso derivados das personas, incluindo atores, pré-condições, fluxo principal, alternativas, erros e resultados esperados.
4. Para a avaliação científica, validar dataset(s) e levantar formato, licença, cobertura, rótulos e limitações. O AIOpsArena já está selecionado para o replay técnico da P2; auditar seu recorte e proveniência em separado.
5. Definir o MER conceitual usando requisitos AIM e evidências do dataset, sem confundir esquema experimental com operacional.
6. Definir tipos, unidades, granularidade, origem e identidade de métricas; confirmar a ligação temporal e a versão da configuração produtora.
7. Definir o tratamento de falha, atraso, duplicidade e lacunas da telemetria.
8. Definir política X de retenção e descarte de dados brutos e política para agregados, análises, eventos e auditoria.
9. Especificar separadamente os alvos de detecção e de risco, critérios de anomalia por cenário, score/severidade, janela/horizonte e baselines.
10. Definir formato e ciclo de vida de eventos/triggers e notificações no frontend e por e-mail, incluindo provedor e erros.
11. Definir a cadeia de sinais/erros que pode ser mostrada sem traces, e quais evidências devem explicar o alerta.
12. Selecionar métricas quantitativas e protocolo da literatura adequados aos alvos, datasets e rótulos escolhidos.
13. Planejar ambiente controlado de métricas artificiais/injetadas, critérios de validação e participantes; registrar feedback.
14. Construir matriz de aceite ligando requisitos a testes, capturas de tela e extrações/relatórios verificáveis.

## Referências do repositório

- [Personas](../requisitos/personas.md) e [cenários de uso](../requisitos/cenarios-de-uso.md).
- [Ideias para primeira versão](escopo-primeira-versao-ideias.md), incluindo proposta conceitual de MER.
- [Modelo de dados](../arquitetura/dados/modelo-de-dados.md) e [dicionário de dados](../arquitetura/dados/dicionario-de-dados.md).
- Perguntas, hipóteses e protocolo experimental permanecem como material interno de pesquisa, fora da documentação selecionada para a P2.
