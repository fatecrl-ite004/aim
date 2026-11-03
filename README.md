# AIM — Active Intelligent Monitoring

O AIM (*Active Intelligent Monitoring*) é um projeto acadêmico de pesquisa aplicada e prova de conceito. O trabalho investiga a análise multivariada de anomalias temporais em métricas de infraestrutura e de aplicações/API, com o objetivo de apoiar equipes de desenvolvimento e confiabilidade na investigação de degradações.

**Título do TCC:** *AIM: Uma análise multivariada de anomalias temporais em infraestruturas computacionais*

**Estado:** pesquisa e definição da PoC. Há um mock React de frontend com dados simulados para explorar fluxos de interface; as funcionalidades analíticas, integrações e tecnologias descritas como previstas ainda não representam uma aplicação operacional implementada.

## Funcionalidades e escopo

A proposta de pesquisa e da PoC contempla:

- Receber métricas de infraestrutura e de aplicação/API por OTLP.
- Organizar séries temporais por serviço, componente ou cenário.
- Investigar métodos estatísticos e de aprendizado de máquina para detecção de anomalias.
- Relacionar temporalmente sinais de infraestrutura e sintomas observados em APIs, sem presumir causalidade.
- Apresentar séries, intervalos, scores, indicadores e contexto em uma aplicação web com controle de acesso por perfil (RBAC).
- Avaliar a detecção e, se houver cenários e rótulos adequados, a possível antecipação de eventos e o apoio à investigação.

Esses itens descrevem objetivos de pesquisa, não funcionalidades já disponíveis. Logs, traces e topologia podem ser considerados como complementos, mas não são requisitos assumidos para o núcleo baseado em métricas.

O AIM não prevê correções automáticas em código ou infraestrutura, criação de commits ou pull requests, deploy ou remediação autônoma. Um eventual uso de LLM seria complementar à apresentação de evidências, sem atuar como decisor.

## Tecnologias previstas

A stack indicada para o desenvolvimento é:

- **Linguagem:** Python.
- **Backend/API:** FastAPI.
- **Banco de dados:** PostgreSQL.
- **Aprendizado de máquina:** PyTorch.
- **Frontend:** React com Node.js no ambiente de desenvolvimento e build.

A integração entre os componentes, versões, ferramentas auxiliares e configuração ainda está **a definir**. A arquitetura conceitual não determina se a inferência será integrada ao backend ou executada como serviço independente.

## Pré-requisitos

Para consultar o repositório, é necessário ter Git instalado. Para executar o frontend demonstrativo, instale **Node.js 22.12 ou superior** e npm. A instalação do mock requer internet na primeira execução para baixar as dependências. Não é necessário configurar Python, PostgreSQL, backend, credenciais ou serviços externos para abrir a interface.

## Instalação e configuração

### Obter o código-fonte

```bash
git clone URL_DO_REPOSITORIO
cd aim
```

Substitua `URL_DO_REPOSITORIO` pelo endereço do repositório utilizado pela equipe. Se o repositório já estiver na máquina, abra um terminal na pasta raiz do AIM.

### Instalar as dependências do frontend

No terminal, a partir da raiz do repositório, execute:

```bash
cd frontend
npm ci
```

`npm ci` instala as versões registradas em `frontend/package-lock.json`.

## Execução em ambiente de desenvolvimento

Ainda dentro da pasta `frontend`, inicie o servidor local:

```bash
npm run dev
```

Abra no navegador o endereço informado no terminal, normalmente `http://localhost:5173`. Para encerrar, volte ao terminal e pressione `Ctrl+C`. Não abra `index.html` diretamente: a interface usa módulos que precisam do servidor Vite.

A aplicação é um mock de frontend com dados simulados e persistidos no `localStorage` do navegador. Não há backend nem integração real com OTel, SMTP, banco de dados ou serviços monitorados. As opções em **Demonstração** carregam cenários locais; selecione **Operação normal** para restaurar os dados iniciais. As métricas e datas exibidas são fictícias (cenário de 08/10/2026, BRT).

## Estrutura do projeto

```text
aim/
├── archive/   # Materiais da concepção anterior, preservados como histórico
├── data/      # Convenções e orientações para dados
├── docs/      # Projeto, requisitos, arquitetura, pesquisa e decisões
├── infra/     # Espaço reservado a materiais de infraestrutura
├── research/  # Espaço reservado a experimentos reproduzíveis
├── scripts/   # Espaço reservado a scripts de apoio
├── system/    # Destino previsto para os componentes da PoC
├── frontend/  # Mock React navegável com dados simulados
└── README.md  # Visão geral e navegação do projeto
```

`research/` reúne experimentos e materiais de pesquisa; consulte os READMEs dessa área para seus limites e instruções. `system/` continua reservado à PoC. O frontend demonstrativo está em `frontend/`: ele implementa fluxos de interface com dados locais simulados, sem backend ou integração operacional. Consulte `frontend/README.md` para detalhes do mock.

## Objetivos analíticos e limites

O projeto distingue objetivos que exigem definições e avaliações próprias:

- **Detecção de anomalias:** identificar observações, janelas ou eventos diferentes do comportamento de referência.
- **Previsão de valores:** estimar valores futuros; erro de previsão não equivale automaticamente a risco de incidente.
- **Estimativa de risco/antecipação:** estimar se um evento definido ocorrerá dentro de um horizonte, usando rótulos e critérios explícitos.
- **Detecção de mudança (change point):** localizar alteração de regime, que pode representar uma nova condição normal.
- **Associação temporal:** descrever sinais que variam juntos ou em sequência; isso não demonstra causa.
- **RCA e causalidade:** investigar causas candidatas com dados e hipóteses apropriados. O AIM não deve afirmar diagnóstico causal sem evidência que o sustente.

Limites estáticos e variáveis são alternativas a avaliar por cenário; nenhum método é assumido como universalmente superior. Autoencoders, LSTM, modelos baseados em grafos, filtragem por similaridade vetorial, retreinamento diante de mudanças, TopoMAD e InterFusion são linhas ou referências candidatas, não escolhas finais nem funcionalidades implementadas.

## Avaliação planejada

O protocolo experimental ainda precisa definir cenários, eventos e *ground truth* auditável; métricas e frequência; alinhamento e tratamento de lacunas; baselines e modelos; scores e limiares; e critérios de avaliação por ponto e por evento.

A avaliação deverá respeitar a cronologia dos dados: treino, validação e teste em períodos separados. Normalização, hiperparâmetros e limiares devem ser ajustados sem consultar o teste. As comparações precisam usar condições equivalentes e reportar falsos alertas, atraso de detecção, custos e limitações. Alegações de antecipação exigem horizonte e regra de correspondência definidos. O valor incremental das métricas de infraestrutura em relação às de API também permanece uma questão de pesquisa.

## Pesquisa e referências

As sínteses locais de literatura servem para orientar perguntas e protocolos; não provam que o AIM implementa os métodos descritos nem que supera alternativas. Entre as referências estudadas estão trabalhos sobre observabilidade cloud-native, avaliação de detecção por evento, séries temporais, mudança de regime, dependências entre métricas e RCA. Resultados publicados usam dados, rótulos e protocolos distintos e não devem ser comparados diretamente aos resultados futuros da PoC.

Consulte as [sínteses ampliadas do estado da arte](docs/pesquisa/estado-da-arte/) e o [protocolo experimental](docs/pesquisa/protocolo-experimental.md) para detalhes, referências e limites de evidência.

## Decisões em aberto

Permanecem a definir: cenários e rotulagem; métricas, frequência e retenção; modelos, baselines e limiares; protocolo temporal e métricas event-wise; requisitos da aplicação, perfis e visualizações; arquitetura da inferência; e custos de instrumentação, processamento e armazenamento. As decisões devem ser registradas quando houver uma escolha explícita e justificável. Até o momento, não há ADR aceita.

## Equipe

| Integrante | Responsabilidade |
| --- | --- |
| Pedro Augusto de Melo Borges | A definir |
| Thiago Guerra Soares | A definir |
| João Paulo Cruz de Almeida Lima | A definir |

## Documentação adicional

- [Visão e escopo](docs/projeto/visao-e-escopo.md), [estado atual](docs/projeto/estado-atual.md), [histórico](docs/projeto/historico.md) e [glossário](docs/projeto/glossario.md).
- [Requisitos](docs/requisitos/requisitos.md), [personas](docs/requisitos/personas.md), [mapas de empatia](docs/requisitos/mapas-de-empatia.md) e [cenários de uso](docs/requisitos/cenarios-de-uso.md).
- [Arquitetura conceitual](docs/arquitetura/visao-geral.md), [pipeline analítico](docs/arquitetura/pipeline-analitico.md), [backend](docs/arquitetura/backend.md), [frontend](docs/arquitetura/frontend.md) e [modelo de dados](docs/arquitetura/dados/modelo-de-dados.md).
- [Documentação da pesquisa](docs/pesquisa/README.md), [perguntas e hipóteses](docs/pesquisa/perguntas-e-hipoteses.md), [sínteses do estado da arte](docs/pesquisa/estado-da-arte/) e [decisões](docs/decisoes/README.md).
- [Pesquisa executável](research/README.md), [sistema PoC](system/README.md), [frontend demonstrativo](frontend/README.md), [dados](data/README.md), [infraestrutura](infra/README.md), [scripts](scripts/README.md) e [apresentações](docs/apresentacoes/README.md).
- [Histórico da migração](docs/desenvolvimento/migracao-2026-10-28.md) e [arquivo de materiais anteriores](archive/README.md).
