# AIM Personas

**Revisado em:** 3 de novembro de 2026

AIM — Personas

Personas para o contexto de monitoramento inteligente e análise de telemetria

Neste documento, **SOC Lead** designa a liderança de suporte operacional e triagem de eventos de produtos; o termo não amplia o escopo do AIM para operações de cibersegurança.

1. Carlos Henrique — Arquiteto de Soluções

2. SOC Lead

3. Product Owner

4. SRE — Site Reliability Engineer

## Situação de validação e aderência à primeira versão

As personas abaixo são hipóteses documentais: o repositório não registra entrevistas ou validação empírica que confirme que representam usuários reais do AIM. Carlos é um perfil nominal construído para representar um arquétipo, não uma evidência de usuário entrevistado. SOC Lead, Product Owner e SRE também descrevem papéis presumidos.

Para a validação inicial em laboratório, a equipe prevê desenvolvedores como usuários técnicos e orientador/colegas convidados como possíveis participantes de avaliação. Isso ainda precisa ser confirmado com pessoas. O administrador da plataforma é um papel funcional previsto para cadastrar aplicações, fontes e usuários; as responsabilidades específicas e permissões RBAC ainda não foram definidas. Consulte a [direção preliminar da primeira versão](../projeto/escopo-primeira-versao.md).

| Perfil existente | Aderência preliminar | Evidência atual |
| --- | --- | --- |
| SRE | Mais próximo do usuário técnico que acompanha sinais e investiga degradações. | A equipe indicou desenvolvedores como público inicial; SRE ainda não foi validado diretamente. |
| Arquiteto de Soluções | Stakeholder potencial para validar ambientes de teste e confiabilidade arquitetural. | Persona hipotética; uso direto do AIM não confirmado. |
| SOC Lead | Possível papel de triagem operacional de produto. | Persona hipotética; não implica escopo de cibersegurança nem foi confirmado como usuário. |
| Product Owner | Stakeholder potencial interessado no impacto no produto. | Persona hipotética; necessidade de operar a interface não confirmada. |
| Orientador/colega de teste | Participante de avaliação da PoC em laboratório, conforme recrutamento. | Grupo sugerido pela equipe, não persona de usuário de cliente. |
| Desenvolvedor | Público técnico inicial e possível responsável por configurar/consultar aplicações. | Intenção da equipe; ainda não detalhada como persona nem validada com usuários. |

A primeira validação deve observar quem executa cada tarefa e quais permissões precisa. Só então as personas e o RBAC devem ser consolidados como requisitos.

## Perspectivas profissionais para a equipe do projeto

Além das personas de usuário, a equipe pretende incorporar perspectivas profissionais para analisar partes diferentes da solução. Isso não significa que esses perfis serão usuários do produto:

| Perspectiva | Contribuição esperada ao projeto | Relação com o usuário do AIM |
| --- | --- | --- |
| Engenheiro de dados | Modelagem, ingestão, qualidade, proveniência, séries temporais e retenção. | Consultoria/revisão; acesso ao produto depende de tarefa real. |
| Engenheiro de machine learning | Definição de alvos/features, baselines, treino/validação/teste e avaliação de detectores. | Consultoria/revisão; pode usar ferramentas de pesquisa, sem necessariamente ser usuário operacional. |
| Arquiteto de soluções | Implantação on-premises, integração, fronteiras de rede, segurança e operação. | A persona existente é hipótese; validar se terá acesso direto ao AIM. |

Visão das personas no AIM

As personas enxergam o mesmo problema em níveis diferentes. O Arquiteto de Soluções está principalmente preocupado com a arquitetura e a confiabilidade da solução; o SRE com a confiabilidade operacional; o SOC Lead com eventos, alertas e incidentes; e o Product Owner com o impacto do comportamento técnico no produto e no usuário.



| Nome | Carlos Henrique |

| Idade | 35 |

| Profissão | Arquiteto de Soluções |

| Localização | São Paulo, SP |

| Competência Digital | Alta. Possui conhecimento sobre arquitetura de aplicações, sistemas distribuídos, APIs, bancos de dados, integrações e tecnologias utilizadas no desenvolvimento de soluções. |

| Objetivos | • Garantir disponibilidade das aplicações criadas. / • Garantir que as soluções arquitetadas sejam confiáveis e resilientes. / • Identificar possíveis problemas que possam comprometer o funcionamento das aplicações. / • Garantir que os diferentes componentes da solução funcionem adequadamente em conjunto. |

| Frustrações/Dores | • Falhas em sistemas não monitoradas e previstas. / • Descobrir problemas na aplicação somente após impacto para o usuário. / • Dificuldade para identificar antecipadamente sinais de degradação da solução. / • Dificuldade para relacionar problemas entre API, servidor e banco de dados. |

| Expectativas | • Geração de previsões de possíveis erros ou degradações nas soluções criadas. / • Receber notificações contextualizadas sobre sinais observados e, quando validado, possíveis riscos para a aplicação. / • Identificar relações entre diferentes componentes que possam indicar um problema futuro. / • Utilizar dados históricos para compreender e melhorar a confiabilidade das aplicações. |

| Contextos de Uso | • Durante o acompanhamento de aplicações desenvolvidas e arquitetadas. / • Durante a validação da confiabilidade de uma nova solução. / • Quando uma aplicação apresenta sinais de degradação. / • Ao investigar problemas relacionados à API, servidor e banco de dados. |

| Citação Representativa | “Preciso saber que a solução está começando a apresentar sinais de degradação antes que isso se transforme em um problema para o usuário.” |



| Nome | A definir |

| Idade | A definir |

| Profissão | SOC Lead |

| Localização | A definir |

| Competência Digital | Alta. Possui conhecimento em monitoramento de aplicações e infraestrutura, análise de eventos operacionais, gestão de incidentes de produto e ferramentas de observabilidade e suporte. |

| Objetivos | • Garantir que eventos relevantes sejam identificados rapidamente. / • Reduzir o tempo entre a identificação e a comunicação de um incidente. / • Garantir que eventos críticos recebam a devida atenção. / • Reduzir o impacto de incidentes sobre os sistemas e serviços. |

| Frustrações/Dores | • Grande volume de alertas para analisar. / • Alertas que chegam somente depois que o problema já ocorreu. / • Dificuldade em identificar quais eventos representam risco real. / • Necessidade de analisar informações de diferentes fontes. / • Falsos positivos que geram ruído e consomem tempo da equipe. |

| Expectativas | • Receber alertas relevantes em tempo real. / • Identificar sinais de degradação antes que se transformem em incidentes maiores. / • Reduzir ruído nos alertas. / • Ter informações correlacionadas para compreender melhor o evento. |

| Contextos de Uso | • Durante o monitoramento dos ambientes e aplicações. / • Quando ocorre uma anomalia em uma aplicação ou infraestrutura. / • Durante a análise de incidentes. / • Ao receber uma notificação de risco ou degradação. |

| Citação Representativa | “Não preciso de mais alertas; preciso saber quais eventos realmente representam um risco para o ambiente.” |



| Nome | A definir |

| Idade | A definir |

| Profissão | Product Owner |

| Localização | A definir |

| Competência Digital | Média/Alta. Possui conhecimento sobre produtos digitais, processos de desenvolvimento, indicadores de negócio e acompanhamento de equipes técnicas. |

| Objetivos | • Garantir que o produto esteja disponível para os usuários. / • Garantir qualidade e confiabilidade da solução entregue. / • Reduzir impactos de falhas sobre os usuários. / • Acompanhar indicadores que demonstrem a qualidade do produto. |

| Frustrações/Dores | • Descobrir problemas do produto por meio de reclamações dos usuários. / • Indisponibilidade ou degradação afetando a experiência do usuário. / • Dificuldade para compreender problemas técnicos e seus impactos no produto. / • Falta de previsibilidade sobre possíveis problemas de disponibilidade. |

| Expectativas | • Ser informado sobre problemas que possam afetar o produto. / • Receber alertas antecipados sobre riscos relevantes. / • Ter uma visão clara do impacto de uma degradação na aplicação. / • Receber informações técnicas apresentadas de maneira compreensível. |

| Contextos de Uso | • Durante o acompanhamento da disponibilidade do produto. / • Durante reuniões com equipes técnicas. / • Quando uma aplicação apresenta degradação que pode afetar usuários. / • Ao receber uma notificação sobre um possível problema futuro. |

| Citação Representativa | “Quero saber que existe um problema antes que ele vire uma reclamação de usuário.” |



| Nome | A definir |

| Idade | A definir |

| Profissão | Site Reliability Engineer (SRE) |

| Localização | A definir |

| Competência Digital | Alta. Possui conhecimento técnico em sistemas distribuídos, infraestrutura, observabilidade, automação, monitoramento, desempenho, confiabilidade e análise de incidentes. |

| Objetivos | • Garantir confiabilidade e disponibilidade dos sistemas. / • Detectar degradações rapidamente. / • Antecipar incidentes quando possível. / • Reduzir o impacto e a duração de incidentes. / • Utilizar dados para melhorar a confiabilidade dos serviços. |

| Frustrações/Dores | • Alertas disparados somente quando o problema já está ocorrendo. / • Grande quantidade de métricas para analisar simultaneamente. / • Dificuldade para correlacionar sinais entre aplicação, servidor e banco de dados. / • Falsos positivos que geram alertas desnecessários. / • Falsos negativos que permitem que incidentes ocorram sem alerta antecipado. |

| Expectativas | • Investigar degradações e avaliar se alguns sinais podem ser identificados antes dos eventos. / • Correlacionar métricas de diferentes componentes. / • Utilizar histórico para identificar padrões recorrentes. / • Receber informações contextualizadas e, se validado nos cenários, sinais de risco além de limites simples. / • Reduzir falsos positivos sem aumentar falsos negativos de forma excessiva. |

| Contextos de Uso | • Monitoramento contínuo dos serviços. / • Durante análise de desempenho e confiabilidade. / • Durante investigação de incidentes. / • Ao receber alertas sobre degradação ou risco futuro. / • Na análise de métricas históricas. |

| Citação Representativa | “Se conseguirmos identificar o padrão antes do incidente, conseguimos ganhar tempo para investigar e evitar que ele chegue ao usuário.” |



| Persona | Principal preocupação | Valor do AIM |

| Arquiteto de Soluções | Confiabilidade da aplicação e da arquitetura | Identificar sinais de degradação antes do impacto |

| SOC Lead | Relevância e contexto dos eventos | Reduzir ruído e melhorar a qualidade dos alertas |

| Product Owner | Impacto no produto e no usuário | Antecipar problemas que possam virar impacto ao usuário |

| SRE | Confiabilidade operacional | Correlacionar sinais e antecipar incidentes |






