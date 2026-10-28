# AIM — Cenários de Uso

**Revisado em:** 28 de outubro de 2026

> Os cenários registram situações e resultados desejados, não funcionalidades implementadas. Sinalização de risco depende de validação experimental; correlação temporal não comprova causalidade.

Template: Persona, Objetivo, Contexto, Motivação, Ações, Resultado Esperado, Problema Identificado e Oportunidade de Design

Arquiteto de Soluções — Cenário 1

Mapear possíveis gaps de arquitetura em ambientes de testes

Arquiteto de Soluções — Cenário 2

Identificar limitações da arquitetura a partir do comportamento em produção

SOC Lead / Líder de Suporte de Produtos — Cenário 1

Diminuir o tempo entre o surgimento de um problema e sua identificação

SOC Lead / Líder de Suporte de Produtos — Cenário 2

Reduzir a quantidade de alertas e eventos irrelevantes

Product Owner — Cenário 1

Acompanhar a confiabilidade do produto

Product Owner — Cenário 2

Reduzir o ruído no backlog de produto

SRE — Cenário 1

Diminuir o tempo para identificar o componente relacionado a uma degradação

| Campo | Descrição |
| --- | --- |
| Persona | Arquiteto de Soluções |
| Objetivo | Mapear possíveis gaps de arquitetura em ambientes de testes, visando aumentar a precisão em relação às limitações do sistema. |
| Contexto | Carlos está validando uma nova solução antes de disponibilizá-la para produção. A arquitetura possui uma API, um servidor e um banco de dados, e ele precisa verificar se esses componentes conseguem operar adequadamente dentro das condições esperadas. |
| Motivação | Mitigar possíveis problemas arquiteturais antes da disponibilização da solução. |
| Ações | Carlos acompanha o ambiente de testes durante a execução dos cenários planejados. Consulta os indicadores da aplicação e recebe notificações do AIM quando a análise destacar um comportamento relevante; eventual sinalização de risco dependerá de validação no cenário. Em seguida, verifica o componente envolvido, discute o comportamento com a equipe técnica e avalia se alguma alteração na arquitetura é necessária. |
| Resultado Esperado | Menor quantidade de problemas arquiteturais identificados somente após a entrada em produção e redução de retrabalho. |
| Problema Identificado | Dificuldade de identificar, ainda em ambiente de testes, comportamentos de API, servidor ou banco que possam revelar limitações da arquitetura antes da implantação. |
| Oportunidade de Design | Oferecer uma visão integrada do comportamento da solução, com monitoramento, análise de métricas, identificação de riscos e notificações que apoiem a decisão antes da entrada em produção. |

| Campo | Descrição |
| --- | --- |
| Persona | Arquiteto de Soluções |
| Objetivo | Identificar comportamentos em produção que possam indicar limitações da arquitetura e apoiar a evolução da solução. |
| Contexto | Carlos é responsável por uma solução que já está em produção. Com o aumento do volume de usuários e requisições, componentes da arquitetura podem apresentar comportamentos diferentes dos observados nos testes. Por exemplo, a API pode apresentar aumento de latência enquanto o banco e o servidor também mostram alterações. |
| Motivação | Identificar limitações arquiteturais que só aparecem durante o uso real e obter evidências para orientar futuras decisões de evolução da arquitetura. |
| Ações | Carlos acompanha periodicamente os indicadores da solução. Ao receber uma notificação do AIM, consulta as métricas da API, do servidor e do banco relacionadas ao evento, compara o comportamento atual com o histórico e verifica relações entre os sinais observados. Depois, discute com a equipe se é necessário dimensionar, alterar ou evoluir algum componente. |
| Resultado Esperado | Identificação de comportamentos relevantes e geração de evidências para orientar a investigação de limitações arquiteturais em produção. |
| Problema Identificado | Limitações arquiteturais podem aparecer somente após a solução começar a receber carga real, tornando a identificação e a análise mais reativas. |
| Oportunidade de Design | Apresentar uma visão histórica e correlacionada dos componentes da solução, permitindo comparar comportamento esperado e observado e apoiar decisões de evolução. |

| Campo | Descrição |
| --- | --- |
| Persona | SOC Lead / Líder de Suporte de Produtos |
| Objetivo | Diminuir o tempo entre o surgimento de um problema e sua identificação pelo time responsável. |
| Contexto | O time de suporte recebe diversos eventos relacionados às aplicações acompanhadas. Durante o expediente, os analistas precisam verificar quais eventos representam problemas relevantes e encaminhá-los para as equipes responsáveis. |
| Motivação | Diminuir o tempo de identificação dos problemas e, consequentemente, a duração dos chamados e o risco de impacto nos SLAs. |
| Ações | O SOC Lead acompanha os eventos recebidos pelo time e, ao receber uma notificação do AIM, verifica qual aplicação e componente foram afetados. Consulta as informações relacionadas ao evento, acompanha sua evolução, registra ou atualiza o chamado e direciona o incidente para a equipe responsável. |
| Resultado Esperado | Redução do tempo de identificação e encaminhamento dos problemas e aumento da velocidade de resposta do time. |
| Problema Identificado | A identificação de um problema pode depender de triagem manual de múltiplos eventos e da coleta de informações em diferentes fontes. |
| Oportunidade de Design | Concentrar em uma notificação as informações relevantes sobre o evento, o serviço envolvido e os principais sinais observados, reduzindo o tempo necessário para iniciar a triagem. |

| Campo | Descrição |
| --- | --- |
| Persona | SOC Lead / Líder de Suporte de Produtos |
| Objetivo | Reduzir a quantidade de alertas e eventos que exigem triagem sem representar um problema relevante. |
| Contexto | Durante o dia, o time de suporte recebe um grande volume de eventos. Muitos apresentam pequenas alterações que não representam necessariamente um incidente e precisam ser avaliados antes de gerar um chamado. |
| Motivação | Permitir que o time concentre seu tempo nos eventos mais relevantes e reduza o esforço gasto com ruído operacional. |
| Ações | O SOC Lead acompanha os eventos recebidos e utiliza as informações do AIM para verificar quais apresentam comportamento anormal ou risco de degradação. Ele compara o contexto apresentado, decide quais eventos precisam ser encaminhados para investigação e quais podem continuar em acompanhamento. |
| Resultado Esperado | Menor quantidade de eventos irrelevantes encaminhados para investigação e maior eficiência da equipe. |
| Problema Identificado | O volume de alertas pode dificultar a identificação dos eventos que realmente apresentam risco para o produto. |
| Oportunidade de Design | Usar contexto, histórico e correlação de métricas para destacar eventos relevantes e facilitar a priorização dos alertas. |

| Campo | Descrição |
| --- | --- |
| Persona | Product Owner |
| Objetivo | Acompanhar a confiabilidade do produto e identificar problemas que possam afetar os usuários. |
| Contexto | O Product Owner acompanha um produto digital e precisa apresentar periodicamente indicadores de qualidade e confiabilidade para a diretoria. |
| Motivação | Existe cobrança da diretoria em relação à confiabilidade do produto. O Product Owner precisa de informações que permitam acompanhar os indicadores e entender situações que possam comprometer essa meta. |
| Ações | Durante o acompanhamento do produto, o Product Owner consulta os indicadores de confiabilidade e recebe notificações do AIM quando são identificados problemas ou riscos relevantes. Quando necessário, entra em contato com as equipes técnicas para entender o impacto do evento, acompanha sua evolução e utiliza os dados em reuniões e apresentações para a diretoria. |
| Resultado Esperado | Melhor acompanhamento da confiabilidade do produto, maior visibilidade sobre fatores que impactam seus indicadores e redução do impacto de problemas sobre os usuários. |
| Problema Identificado | Indicadores de produto podem mostrar o resultado de uma degradação sem fornecer contexto suficiente sobre os sinais técnicos que antecederam o problema. |
| Oportunidade de Design | Traduzir informações técnicas e previsões de risco em indicadores e notificações compreensíveis, apoiando a comunicação entre produto, área técnica e diretoria. |

| Campo | Descrição |
| --- | --- |
| Persona | Product Owner |
| Objetivo | Reduzir o número de problemas que chegam ao time de produto sem necessidade de tratamento como uma nova demanda. |
| Contexto | O Product Owner recebe informações de diferentes fontes sobre problemas identificados na aplicação. Parte desses problemas é pontual, recorrente ou de baixo impacto e acaba gerando retrabalho para o time. |
| Motivação | Permitir que o time de produto concentre seus esforços nos problemas que realmente possuem impacto para o produto e seus usuários. |
| Ações | Ao receber informações sobre um problema, o Product Owner consulta os dados disponíveis no AIM para verificar o comportamento do erro, sua recorrência e os componentes envolvidos. Com essas informações, decide junto ao time se o problema deve gerar uma nova issue, ser acompanhado ou ser encaminhado para a equipe técnica responsável. |
| Resultado Esperado | Redução de issues desnecessárias, menor retrabalho do time de produto e melhor priorização dos problemas com impacto real. |
| Problema Identificado | O time de produto pode receber problemas sem contexto suficiente para saber se são recorrentes, relevantes ou realmente exigem uma nova demanda. |
| Oportunidade de Design | Disponibilizar informações previamente analisadas e contextualizadas sobre recorrência, impacto e comportamento dos erros para apoiar a decisão de priorização. |

| Campo | Descrição |
| --- | --- |
| Persona | Site Reliability Engineer (SRE) |
| Objetivo | Diminuir o tempo necessário para identificar qual componente está relacionado a uma degradação da aplicação. |
| Contexto | Durante o monitoramento, o SRE percebe que a API está apresentando aumento de latência. Ainda não está claro se o problema está na própria API, no servidor ou no banco de dados. |
| Motivação | Evitar uma investigação baseada exclusivamente em métricas isoladas e encontrar mais rapidamente a origem provável do problema. |
| Ações | O SRE recebe ou identifica um alerta do AIM, consulta o comportamento recente da API e compara os dados com as métricas do servidor e do banco. Observa a sequência em que as alterações ocorreram, verifica se existe relação entre os eventos e utiliza essas informações para direcionar sua investigação para o componente mais provável. |
| Resultado Esperado | Redução do tempo de investigação e maior precisão no direcionamento da análise. |
| Problema Identificado | A investigação de uma degradação pode exigir a consulta manual de diferentes componentes e a comparação de métricas espalhadas em diferentes fontes. |
| Oportunidade de Design | Correlacionar informações da API, servidor e banco em um único contexto de incidente, apresentando a sequência temporal dos eventos e os sinais mais relevantes para a investigação. |







