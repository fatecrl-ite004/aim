# AIM — Mapas de Empatia

> Hipóteses de experiência das personas no contexto do projeto.
>
> Estrutura: **Pensa e Sente • Vê • Ouve • Fala e Faz • Dores • Ganhos**
>
> Observação: os mapas representam hipóteses sobre a experiência das personas no contexto do AIM.

---

# 🧑‍💻 Carlos Henrique — Arquiteto de Soluções

**Contexto do mapa:** validação e acompanhamento da confiabilidade de uma solução distribuída.

## 🧠 Pensa e Sente

Carlos se preocupa em garantir que a solução que projetou seja confiável, disponível e capaz de suportar as condições para as quais foi planejada. Antes de colocar uma aplicação em produção, quer ter confiança de que a arquitetura suporta as condições previstas. Quando um problema aparece somente em produção, sente que parte da situação poderia ter sido identificada anteriormente.

Ele valoriza informações que permitam justificar decisões arquiteturais com evidências, principalmente quando precisa decidir entre manter, alterar ou evoluir um componente da solução.

## 👁️ Vê

Carlos observa diferentes componentes da solução e informações vindas de diferentes fontes.

- APIs e outros serviços
- Servidores e bancos de dados
- Resultados de testes
- Métricas de desempenho
- Indicadores de disponibilidade
- Relatos das equipes técnicas
- Comportamento da aplicação em produção

Nem sempre ele possui uma visão consolidada desses elementos.

## 👂 Ouve

No dia a dia, Carlos recebe informações de desenvolvedores, SREs, suporte e gestores. Pode ouvir que uma aplicação está apresentando lentidão, que um banco está sobrecarregado ou que usuários estão enfrentando dificuldades.

Também recebe questionamentos sobre escalabilidade, disponibilidade e capacidade da arquitetura de suportar o crescimento da solução.

## 🗣️ Fala e Faz

Carlos participa da definição e revisão da arquitetura, acompanha testes, discute decisões técnicas e avalia problemas que aparecem durante a operação da solução.

Quando recebe uma informação sobre degradação, procura entender se ela está relacionada à arquitetura e quais componentes podem estar envolvidos. A partir disso, discute possíveis mudanças com as equipes responsáveis.

## 😣 Dores

A principal dor está em descobrir limitações arquiteturais tarde demais.

Problemas que só aparecem quando a aplicação recebe carga real podem gerar retrabalho e exigir mudanças em uma solução que já está em operação. Outra dificuldade é precisar reunir informações de API, servidor e banco para entender o comportamento da arquitetura como um todo.

## 🌟 Ganhos

Carlos ganha confiança quando consegue validar uma arquitetura com base em evidências e identificar sinais de limitação antes que eles se transformem em problemas maiores.

Para ele, uma solução que consolida o comportamento dos diferentes componentes pode facilitar a tomada de decisão e contribuir para uma arquitetura mais confiável.

---

# 🛡️ SOC Lead / Líder de Suporte de Produtos

**Contexto do mapa:** acompanhamento e triagem de problemas reportados ou identificados nos produtos.

## 🧠 Pensa e Sente

O SOC Lead precisa decidir rapidamente quais eventos realmente merecem atenção. Ao receber muitos alertas ou chamados, sua preocupação é entender o que é relevante, qual produto está sendo afetado e qual equipe precisa ser acionada.

Existe pressão constante por tempo de resposta e por evitar que problemas permaneçam sem tratamento.

## 👁️ Vê

Durante a rotina, ele se depara com:

- Chamados de usuários
- Alertas de sistemas
- Incidentes em andamento
- Diferentes níveis de prioridade
- Informações de suporte
- Mensagens de equipes técnicas
- Histórico de problemas

O volume de informações pode dificultar a identificação dos eventos mais importantes.

## 👂 Ouve

Ele recebe relatos de usuários sobre lentidão, indisponibilidade ou erros. Também ouve analistas de suporte, desenvolvedores, SREs e gestores.

Frequentemente precisa transformar relatos diferentes sobre o mesmo problema em uma visão única do incidente.

## 🗣️ Fala e Faz

O SOC Lead acompanha chamados, supervisiona ou realiza a triagem, define prioridades e encaminha problemas para as equipes responsáveis.

Quando recebe um alerta, procura entender o que aconteceu, qual produto foi afetado e qual é a gravidade do evento. Depois, acompanha o incidente e mantém as pessoas envolvidas informadas.

## 😣 Dores

A principal dor é o excesso de ruído e a falta de contexto.

Um alerta isolado pode exigir consultas adicionais para descobrir se o evento representa um problema real. Isso consome tempo da equipe e pode atrasar o encaminhamento de incidentes relevantes.

Outro problema é descobrir uma situação somente depois que os usuários começam a reportá-la.

## 🌟 Ganhos

O SOC Lead ganha quando consegue identificar rapidamente eventos relevantes, reduzir triagens desnecessárias, entender qual produto e componente estão envolvidos e receber contexto suficiente para encaminhar o problema.

O valor do AIM para essa persona está principalmente em transformar muitos sinais em informações mais úteis para a triagem.

---

# 📦 Product Owner

**Contexto do mapa:** acompanhamento da confiabilidade do produto e de problemas que podem impactar usuários.

## 🧠 Pensa e Sente

O Product Owner está menos preocupado com a métrica técnica isolada e mais com o que aquela situação representa para o produto e para o usuário.

Quando ocorre um problema, ele pensa:

> "Isso está afetando meus usuários?"

> "Qual é o impacto real desse problema?"

Também existe a necessidade de conseguir explicar para stakeholders por que determinado indicador de confiabilidade piorou.

## 👁️ Vê

O Product Owner acompanha:

- Indicadores do produto
- Metas de confiabilidade
- Feedback dos usuários
- Chamados
- Backlog
- Relatórios
- Resultados de acompanhamento do produto

Ele normalmente não precisa acompanhar cada métrica técnica individualmente.

## 👂 Ouve

Recebe informações de suporte, desenvolvimento, SRE, usuários e diretoria.

Pode ouvir que uma determinada API está lenta, que usuários estão enfrentando erros ou que uma determinada funcionalidade apresentou indisponibilidade.

## 🗣️ Fala e Faz

O Product Owner acompanha indicadores, prioriza demandas, discute problemas com as equipes técnicas e decide quais questões devem receber atenção do produto.

Quando recebe informações sobre um problema, procura entender seu impacto e sua relevância antes de transformar a situação em uma nova demanda.

Também apresenta resultados e indicadores para stakeholders.

## 😣 Dores

Uma das principais dores é descobrir problemas por meio dos próprios usuários.

Outra é receber informações técnicas sem contexto suficiente para determinar a relevância do problema para o produto. Isso pode gerar tanto priorizações equivocadas quanto retrabalho com problemas de baixo impacto.

## 🌟 Ganhos

O Product Owner ganha quando consegue saber antecipadamente que existe uma situação que pode afetar o produto.

Também se beneficia de informações que traduzam dados técnicos em impacto, relevância e contexto, permitindo priorizar melhor e comunicar a situação para a gestão.

---

# ⚙️ SRE — Site Reliability Engineer

**Contexto do mapa:** investigação de uma degradação em uma aplicação distribuída.

## 🧠 Pensa e Sente

O SRE precisa descobrir rapidamente o que está acontecendo e qual componente está relacionado ao problema.

Quando uma aplicação começa a se comportar de forma diferente, sua preocupação é entender o que mudou, quando começou, qual componente apresentou o primeiro sinal e se a situação está evoluindo.

Existe pressão para reduzir o tempo de investigação e manter a confiabilidade do serviço.

## 👁️ Vê

O SRE trabalha diretamente com:

- Métricas
- Dashboards
- Logs
- Alertas
- API
- Servidores
- Bancos de dados
- Histórico de incidentes
- Comportamento das aplicações ao longo do tempo

Muitas vezes precisa alternar entre diferentes fontes para montar o contexto completo.

## 👂 Ouve

Durante um incidente, o SRE recebe informações do suporte, desenvolvimento, operações e outras equipes.

Pode receber mensagens como "A API está lenta", "Usuários estão recebendo erros" ou "O banco começou a apresentar aumento de latência". Essas informações precisam ser relacionadas para formar uma hipótese sobre o problema.

## 🗣️ Fala e Faz

O SRE monitora os serviços, investiga alertas, compara métricas e analisa a evolução dos eventos.

Quando percebe uma degradação, procura determinar:

- O que mudou?
- Quando mudou?
- Onde começou?
- Qual componente está relacionado?
- A degradação está evoluindo?

Depois comunica a situação às equipes envolvidas e acompanha o incidente.

## 😣 Dores

A principal dificuldade é a necessidade de correlacionar manualmente informações de diferentes componentes.

Um aumento de latência na API pode ter origem no próprio serviço, no servidor ou no banco. Sem uma visão integrada, o SRE pode precisar investigar várias fontes antes de encontrar uma relação entre os eventos.

## 🌟 Ganhos

O SRE ganha principalmente tempo e contexto para investigar.

Uma visão que reúna API, servidor e banco, considere a evolução temporal dos sinais e destaque comportamentos relevantes pode ajudá-lo a direcionar a investigação mais rapidamente.

Para essa persona, o valor central do AIM é ajudá-lo a entender o que está acontecendo antes que precise descobrir tudo manualmente.
