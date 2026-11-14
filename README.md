# AIM — Active Intelligent Monitoring

O AIM (*Active Intelligent Monitoring*) é um projeto acadêmico de pesquisa aplicada e prova de conceito. O trabalho investiga a análise multivariada de anomalias temporais em métricas de infraestrutura e de aplicações/API, com o objetivo de apoiar equipes de desenvolvimento e confiabilidade na investigação de degradações.

**Título do TCC:** *AIM: Uma análise multivariada de anomalias temporais em infraestruturas computacionais*

**Estado:** a PoC V1 local integrada foi executada com FastAPI, PostgreSQL 18.1, OTLP/HTTP Protobuf, processamento AIM e uma jornada React conectada. Uma execução enviou e persistiu 282 pontos sem divergência com a fonte; gravou 92 janelas, 276 estados de cobertura e 207 valores derivados; a API e a interface foram consultadas antes e depois de reiniciar o banco. As outras telas permanecem um protótipo com dados simulados. Isso comprova o fluxo local controlado, não coleta contínua, detector validado, causalidade ou operação on-premises em cliente. Consulte a [demonstração pela interface](docs/evidencias/v1/demonstracao-pela-interface-2026-11-12.md) e os [testes de desenvolvimento](docs/evidencias/v1/testes-desenvolvimento-2026-11-12.md).

## Funcionalidades e escopo

A proposta de pesquisa e da PoC contempla:

- Receber métricas selecionadas de infraestrutura computacional e sinais de aplicação/API, avaliando ingestão por OTLP para as aplicações cadastradas pelo administrador.
- Organizar séries temporais por serviço, componente ou cenário.
- Investigar métodos estatísticos e de aprendizado de máquina para detecção de anomalias.
- Relacionar temporalmente sinais de infraestrutura e sintomas observados em APIs, sem presumir causalidade.
- Apresentar séries, intervalos, scores, indicadores e contexto em uma aplicação web com controle de acesso por perfil (RBAC).
- Avaliar a detecção e, se houver cenários e rótulos adequados, a possível antecipação de eventos e o apoio à investigação.

Esses itens descrevem objetivos de pesquisa, não funcionalidades já disponíveis. Logs, traces e topologia ficam fora da primeira versão. O AIM pretende reutilizar telemetria selecionada que o cliente já disponibiliza; não se propõe a coletar tudo nem a substituir sua plataforma de observabilidade. Consulte a [direção preliminar da primeira versão](docs/projeto/escopo-primeira-versao.md).

O AIM não prevê alterações diretas no código-fonte ou na infraestrutura do cliente, criação de commits ou pull requests, deploy ou remediação autônoma. Um eventual uso de LLM seria complementar à apresentação de evidências, sem atuar como decisor.

## Tecnologias previstas

A stack indicada para o desenvolvimento é:

- **Linguagem:** Python.
- **Backend/API:** FastAPI.
- **Banco de dados:** PostgreSQL.
- **Aprendizado de máquina:** PyTorch.
- **Frontend:** React com Node.js no ambiente de desenvolvimento e build.

Para a V1 acadêmica local, a stack é Python/FastAPI, PostgreSQL, OTLP/HTTP Protobuf e o frontend React/TypeScript existente. Há dois caminhos de execução: `scripts/start-v1.ps1` mantém API/frontend no host e usa Compose para PostgreSQL; o [deploy local completo](deploy.md) executa PostgreSQL, API, Collector OTLP, frontend e runner em contêineres. O Compose completo foi validado com replay real, persistência, ground truth separado, transformação e consulta da interface. Para usar PostgreSQL instalado no host, configure `AIM_DATABASE_URL` em `.env.v1` e inicie com `scripts/start-v1.ps1 -NoDatabase`. A arquitetura de inferência da solução completa ainda está **a definir**.

## Pré-requisitos

Para repetir a execução em contêineres no Windows, são necessários Docker Desktop e Compose v2. Para o caminho com API/frontend no host, instale também Python 3.14, Node.js 22.12 ou superior e npm. A primeira execução baixa imagens e dependências. O dataset AIOpsArena deve ser obtido separadamente e permanece fora do repositório; a licença/redistribuição ainda precisa ser confirmada.

## Instalação e configuração

### Obter o código-fonte

```bash
git clone https://github.com/fatecrl-ite004/aim.git
cd aim
```

O endereço acima corresponde ao remote `origin` deste checkout. Se o repositório já estiver na máquina, abra um terminal na pasta raiz do AIM.

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

A execução isolada do Vite mantém as telas demonstrativas navegáveis com dados simulados no `localStorage`. A entrada de replay histórico exige a API e o PostgreSQL; sem eles, mostra a falha de conexão. Para executar a V1 completa e iniciar a ingestão pela interface, siga o [guia de execução](deploy.md).

## Execução integrada local da V1 (Windows/PowerShell)

Na raiz do repositório, instale as dependências e crie `.env.v1` com uma credencial local aleatória:

```powershell
.\scripts\setup-v1.ps1 -DatasetRoot 'C:\caminho\AIOpsArena'
```

Confira no `.env.v1` o caminho do dataset (a senha é gerada e armazenada apenas nesse arquivo, ignorado pelo Git). Inicie PostgreSQL, API e frontend:

```powershell
.\scripts\start-v1.ps1
```

Esse modo híbrido mantém o banco no Docker e envia OTLP diretamente à API. Abra `http://127.0.0.1:5173` e use **Iniciar demonstração** em **Visão geral → Replay histórico AIOpsArena**. API: `http://127.0.0.1:8000/health/ready`. O [deploy.md](deploy.md) também descreve a composição Docker inteira e a execução totalmente sem Docker, com Collector no host. Para executar a bateria de backend, frontend, fluxo OTLP real, UI conectada e reinício persistente do PostgreSQL no modo híbrido:

```powershell
.\scripts\verify-v1.ps1 -Restart
```

O teste integrado registrado enviou os dados por OTLP/HTTP Protobuf, comparou 282 pontos persistidos com a origem, e após restart confirmou as mesmas contagens e hashes para pontos, derivados e evento. Para encerrar API/frontend mantendo o banco, execute `scripts/stop-v1.ps1`; para parar também o container, sem remover o volume, use `scripts/stop-v1.ps1 -Database`. A evidência detalhada fica localmente em `.runtime/v1/` e não inclui os CSV/JSON originais no Git.

Para um PostgreSQL já instalado no host, ajuste `AIM_DATABASE_URL` em `.env.v1` para essa instância e execute `scripts/start-v1.ps1 -NoDatabase`; a migration será aplicada normalmente e API/frontend serão iniciados. Esse caminho não reinicia o serviço externo e, portanto, não deve usar o teste `verify-v1.ps1 -Restart`, que reinicia o container Compose. A persistência nesse modo precisa ser conferida reiniciando o serviço externo de forma controlada.

## Estrutura do projeto

```text
aim/
├── data/      # Convenções e orientações para dados
├── docs/      # Projeto, requisitos, diagramas e evidências selecionadas
├── infra/     # Compose, Collector e proxy local
├── scripts/   # Instalação, demonstração e verificação
├── system/    # Backend Python/FastAPI da V1 e documentação do serviço
├── frontend/  # Replay conectado e outras telas demonstrativas
└── README.md  # Visão geral e navegação do projeto
```

`system/backend/aim/` contém o receiver OTLP, replayer, persistência e processamento Python/FastAPI da V1. O frontend em `frontend/` combina o mock original com a jornada de replay conectada; as outras telas permanecem simuladas. Consulte `system/README.md` e `frontend/README.md` para limites e instruções validados.

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

Os estudos de literatura e os experimentos exploratórios permanecem fora desta seleção da entrega P2. Os resultados da V1 estão delimitados nas [evidências de desenvolvimento](docs/evidencias/v1/testes-desenvolvimento-2026-11-12.md).

## Decisões em aberto

Permanecem a definir: cenários e rotulagem científica; frequência e retenção de produção; modelos, baselines e limiares; protocolo temporal e métricas event-wise; perfis e regras RBAC; arquitetura de inferência; e custos de instrumentação, processamento e armazenamento. As decisões de escopo local P2 e replay AIOpsArena foram registradas em ADRs; elas não fecham as decisões do produto completo.

## Equipe

| Integrante | Responsabilidade |
| --- | --- |
| Pedro Augusto de Melo Borges | A definir |
| Thiago Guerra Soares | A definir |
| João Paulo Cruz de Almeida Lima | A definir |

## Documentação adicional

- [Visão e escopo](docs/projeto/visao-e-escopo.md), [direção preliminar da primeira versão](docs/projeto/escopo-primeira-versao.md) e [glossário](docs/projeto/glossario.md).
- [Requisitos](docs/requisitos/requisitos.md), [personas](docs/requisitos/personas.md), [mapas de empatia](docs/requisitos/mapas-de-empatia.md) e [cenários de uso](docs/requisitos/cenarios-de-uso.md).
- [Arquitetura conceitual](docs/arquitetura/visao-geral.md), [pipeline analítico](docs/arquitetura/pipeline-analitico.md), [backend](docs/arquitetura/backend.md), [frontend](docs/arquitetura/frontend.md) e [modelo de dados](docs/arquitetura/dados/modelo-de-dados.md).
- [Índice dos diagramas prontos para draw.io](docs/diagramas/README.md): fluxo de replay, casos de uso e MER da PoC V1.
- [Demonstração pela interface](docs/evidencias/v1/demonstracao-pela-interface-2026-11-12.md), [testes de desenvolvimento](docs/evidencias/v1/testes-desenvolvimento-2026-11-12.md) e [roteiro P2 de cinco minutos](docs/apresentacoes/roteiro-p2-v1-5min.md).
- [Sistema PoC](system/README.md), [frontend demonstrativo](frontend/README.md), [dados](data/README.md), [infraestrutura](infra/README.md), [scripts](scripts/README.md) e [apresentações](docs/apresentacoes/README.md).
