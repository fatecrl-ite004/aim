# AIM — Frontend com replay histórico e protótipo navegável

Implementação navegável do [AIM — Protótipo de Alta Fidelidade](https://www.figma.com/design/qnyP4YsWrH0l6ZzrqvcEjH), da Emendata. Interface em português brasileiro para equipes SRE, DevOps e Backend.

A entrada **Replay histórico AIOpsArena** na Visão geral consulta a API FastAPI e o PostgreSQL. Ela abre o detalhe da instância com CPU em núcleos médios, taxa de respostas 200 e latência média dessas respostas, provenientes da transformação executada após a ingestão OTLP. As demais telas continuam como mock, com dados e ações simulados identificados na interface.

## Executar

1. Instale **Node.js 22.12 ou superior**, com npm.
2. Na raiz do repositório AIM, entre na pasta do frontend e instale as dependências:

```sh
cd frontend
npm ci
```

3. Inicie o servidor de desenvolvimento:

```sh
npm run dev -- --host 127.0.0.1
```

Abra o endereço exibido no terminal, normalmente **http://localhost:5173**. Para encerrar, pressione `Ctrl+C`. Não abra `index.html` diretamente: o projeto usa módulos e precisa do servidor local.

Para a jornada conectada, inicie a API em **http://127.0.0.1:8000** e clique em **Iniciar demonstração** na entrada do replay. O frontend solicita uma execução pela API, acompanha os marcos persistidos e abre as séries quando estiverem disponíveis. O dataset e os destinos OTLP são configurados no backend; a interface não envia caminhos nem endereços de origem. A execução manual do replay e do batch continua disponível como alternativa técnica no [setup do backend](../system/backend/README.md). O Vite encaminha `/api` para essa API no desenvolvimento e no preview. Para outra porta local, copie `.env.example` para `.env.local` e ajuste `AIM_API_PROXY_TARGET`. `VITE_API_BASE_URL` só é necessário para chamar outra origem diretamente, com CORS permitido no backend. O frontend e a API devem permanecer em loopback nesta prova sem autenticação.

Sem backend, a entrada histórica apresenta a falha de conexão; as telas mock continuam navegáveis. Uma API sem replays apresenta **Nenhum replay persistido**. A área conectada não substitui erros ou ausência de dados por exemplos locais.

## Tecnologias

- **React 19** para componentes, navegação e interação.
- **TypeScript** para tipos e regras de estado.
- **CSS** com variáveis semânticas, grid e flexbox, sem Tailwind.
- **Vite** para desenvolvimento e compilação.
- **Vitest e Playwright** para testes.
- **Inter** servida localmente por `@fontsource/inter`, sem depender de Google Fonts.

React é a biblioteca principal. TypeScript, CSS e Vite completam o projeto. A jornada histórica depende da API e do PostgreSQL locais; os fluxos mock funcionam no navegador. `node_modules` não está no ZIP: `npm ci` instala as dependências do arquivo de lock. A primeira instalação requer internet.

## O que funciona

- Consulta de replays e instâncias reais pela API na Visão geral e abertura do detalhe histórico.
- Início idempotente da demonstração, acompanhamento do status e dos lotes/pontos persistidos, seleção do novo replay e reabertura do último status após recarregar a página.
- Seleção explícita da execução de transformação, sem misturar versões dos resultados.
- Séries por intervalo com unidades, cobertura, motivo e tabela de valores consultável. Lacunas e latência indefinida por ausência de tráfego interrompem a curva; zero observado continua visível.
- Marcador separado de falha de CPU injetada e identificadores de proveniência. Os timestamps do dataset permanecem históricos, exibidos em UTC.
- Estados de carregamento, replay vazio, transformação pendente e falha de API.

Os itens seguintes pertencem ao mock navegável:

- Visão geral da malha com conectividade, monitoramento e risco separados.
- Pausa global e individual; retomar o global preserva as pausas individuais.
- Cadastro com entrada livre de identificador, runtime e endpoint OTel; validação e verificação simulada em 1,2 segundo.
- Menus por serviço, confirmação de desvinculação e histórico preservado.
- Detalhes por serviço com latência média/P99, conexões/pool, CPU e memória; janelas de 5 min, 15 min, 1 hora e 24 horas.
- Curvas e tooltips coerentes com serviço, período e estado. Em pausa, as amostras permanecem congeladas e o risco fica não avaliado.
- Triagem com origem, divergência, projeção estimada e afetados; modal de topologia com seleção dos nós.
- Estabilização após sinais simulados, timestamp e arquivamento explícito.
- Auditoria com filtros independentes, ordenação cronológica e **download real de CSV e JSON** dos registros filtrados.
- Cadastro, validação, ativação, remoção e envio de teste de destinatários.
- Persistência no `localStorage`, navegação por hash, histórico de voltar/avançar do navegador e adaptação básica a telas menores.

## Roteiro rápido da demonstração

Para demonstrar a integração, abra **Visão geral → Replay histórico AIOpsArena** e clique em **Iniciar demonstração**. Acompanhe o status e os pontos OTLP persistidos; quando uma transformação e uma instância estiverem disponíveis, o detalhe abre e continua consultando novos marcos. No detalhe, confira fonte, instância e período; escolha uma transformação; inspecione a cobertura e a tabela de intervalos. O seletor conserva os replays anteriores. O evento é ground truth de falha injetada, sem inferência de causalidade ou saída de detector. As capturas abaixo dos testes de UI validam o contrato com respostas controladas; a prova de banco/API real deve ser realizada pelo roteiro integrado do backend.

Para percorrer o mock:

1. A tela inicial abre em operação nominal. Clique em um serviço para ver suas métricas.
2. Use **Demonstração → Incidente ativo**. O modo reinicia os dados de exemplo.
3. Abra `checkout-service`. Inspecione a topologia e selecione os três nós. Feche com o botão ou `Esc`.
4. Após representar uma mitigação externa, abra **Demonstração → Simular sinais normalizados**.
5. Revise o timestamp e clique em **Arquivar incidente**. O sistema retorna à supervisão silenciosa.
6. Em **Serviços**, cadastre um serviço com dados próprios ou use **Preencher exemplo** no drawer. Desvincule pelo menu de ações da linha.
7. Em **Notificações**, adicione um endereço, pause todos e reative um para verificar o aviso e o botão de teste.
8. Em **Auditoria**, filtre por serviço e tipo e exporte os resultados. Serviços desvinculados continuam presentes no histórico.

O menu **Estados excepcionais** contém ausência de serviços, telemetria desatualizada, métricas sem dados, endpoint indisponível, falha de e-mail, ausência de destinatários e auditoria vazia. Endpoint inválido e e-mail duplicado são reproduzidos nos próprios formulários.

Nos modos de falha, a primeira verificação ou envio falha; a ação de tentar novamente simula recuperação. Um endpoint que contenha `indisponivel` também produz a falha inicial, sem realizar acesso de rede. Fechar um drawer ou sair da página cancela sua operação pendente.

**Demonstração reinicia os dados locais.** Para manter alterações, continue navegando sem selecionar outro modo. Recarregar a página mantém serviços, destinatários, pausas e incidentes no mesmo navegador/origem. Para limpar tudo, selecione Operação normal ou apague o armazenamento do site. A chave utilizada é `aim-react-mock-v1`.

## Limites do mock

Datas e métricas reproduzem o cenário fictício de **08/10/2026, em BRT (UTC−03)**. Não representam a data real nem tráfego ao vivo.

- No mock, nenhuma coleta OTel, envio SMTP, injeção de falha ou mitigação real é executada. A jornada histórica lê da API dados que o replayer enviou ao backend por OTLP.
- Logs e traces abrem uma apresentação local da integração futura.
- A projeção exibe a estimativa predefinida de aproximadamente 08:30 e, após 30 segundos de supervisão válida, uma atualização para aproximadamente 08:00. Não é um algoritmo preditivo nem um diagnóstico de causa raiz.
- MTTA/antecedência e MTTR permanecem como **Não calculado**: os documentos não fixam todos os marcos necessários. A exportação preserva os oito campos experimentais sem inventar fórmulas.
- Os objetivos de escaneamento em menos de 5 s e triagem em menos de 15 s exigem testes com operadores; não são garantias desta implementação.
- Os dados são locais à origem do navegador e não são compartilhados entre dispositivos ou usuários.

O replay não fornece taxa de erro geral, p95/p99, predição, detector validado ou conclusão causal. Ele contém apenas os sinais `grpc.200.0` selecionados, com mapeamento experimental da identidade Istio. As decisões do mock e a relação entre os **11 requisitos funcionais e os 10 casos de uso** estão em [docs/REQUISITOS.md](docs/REQUISITOS.md); o contrato da jornada conectada está em [docs/INTEGRACAO-REPLAY.md](docs/INTEGRACAO-REPLAY.md).

## Compilar e testar

```sh
npm run build
npm run preview
```

`dist/` é gerada pela compilação e não é incluída no repositório. Para disponibilizar a versão compilada, execute `npm run build` e sirva essa pasta como conteúdo estático. A navegação por hash dispensa regras de reescrita para as rotas da aplicação. O projeto também pode ser servido em subpastas.

```sh
npm test
npx playwright install chromium
npm run test:e2e
```

Em Linux, o Playwright pode solicitar dependências adicionais: `npx playwright install --with-deps chromium`. Os testes de interface iniciam o servidor local automaticamente quando necessário. Capturas e rastros de falhas ficam em `test-results/` e não fazem parte do ZIP.

## Organização do código

| Caminho               | Responsabilidade                                                |
| --------------------- | --------------------------------------------------------------- |
| `src/App.tsx`         | Shell, rotas por hash e feedback global                         |
| `src/pages/`          | Dashboard, detalhe, serviços, notificações e auditoria          |
| `src/components/`     | Botões, switches, banners, dialogs, cards, gráficos e topologia |
| `src/domain/model.ts` | Tipos, regras de estado, métricas e dados simulados             |
| `src/domain/audit.ts` | Filtros e serialização CSV/JSON                                 |
| `src/domain/replay.ts` | Tipos da API, formatação UTC e séries com cobertura              |
| `src/api/replays.ts`  | Consultas HTTP da jornada histórica                              |
| `src/state/Store.tsx` | Estado compartilhado e persistência local                       |
| `src/styles.css`      | Tokens visuais e estilos responsivos                            |
| `public/assets/`      | SVGs locais obtidos do arquivo Figma                            |
| `tests/`              | Regras de domínio e fluxos no navegador                         |
| `docs/`               | Rastreabilidade e decisões                                      |

O reducer continua responsável apenas por pausas e ciclo do incidente simulados. A jornada de replay consulta a API por uma camada separada e não usa `localStorage` para simular persistência do banco. Esta prova não implementa autenticação, autorização, multiusuário ou algoritmos de detecção.
