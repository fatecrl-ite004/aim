# Escopo e rastreabilidade

Fontes do protótipo: **AIM - Matriz de Requisitos (PROTOTIPO).xlsx** e **AIM_Especificacao_Fluxos_Navegacao_Casos_de_Uso.docx**. Referência visual: [arquivo Figma AIM](https://www.figma.com/design/qnyP4YsWrH0l6ZzrqvcEjH), página 5. Esta conversão implementa o comportamento do protótipo; não implementa o core de observabilidade.

## Requisitos documentados

| Requisito                                                            | Caso de uso                      | Implementação                                        | Condição/limite                                                                            |
| -------------------------------------------------------------------- | -------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| RF-01: cadastrar identificador, runtime e endpoint OTel              | UC-01: Cadastrar Serviço         | `Services.tsx`, drawer Novo serviço                  | Validação sintática real; healthcheck predefinido de 1,2 s, sem requisição externa         |
| RF-02: suspender ou desvincular serviço                              | UC-02: Desvincular Serviço       | Menu de cada linha e confirmação                     | Histórico retido no estado; aplicação real não é acessada                                  |
| RF-03: alternar sentinela global e por serviço                       | UC-03: Alternar Estado Sentinela | `Toggle`, reducer, topbar e cards                    | Pausas independentes; global não sobrescreve a individual                                  |
| RF-04: status consolidado e supervisão silenciosa                    | UC-04: Visão Geral da Malha      | `Dashboard.tsx`, `ServiceCard.tsx`                   | Conectividade, monitoramento e risco separados; objetivo <5 s requer estudo com operadores |
| RF-05: séries temporais de latência, conexões, CPU e RAM             | UC-05: Inspecionar Métricas      | `ServiceDetail.tsx`, `MetricPanel.tsx`               | Média e P99 em ms, pool, CPU %, RAM GB; períodos 5 min, 15 min, 1 hora e 24 horas          |
| RF-06: card de apontamento com origem, métrica e taxa de divergência | UC-06: Triagem de Anomalia       | `Incident.tsx`                                       | Card persistente com quatro atributos; objetivo <15 s requer estudo com operadores         |
| RF-07: janela estimada de ação                                       | UC-06: Triagem de Anomalia       | Card e atualização temporizada no Store              | Projeção simulada em dois momentos; pausa/telemetria inválida suspende avaliação           |
| RF-08: serviços dependentes afetados em cascata                      | UC-07: Visualizar Cascata        | Modal Topologia, nó selecionável e painel de sintoma | Grafo direcional, origem e reflexos; correlação não comprova causa raiz                    |
| RF-09: sinalizar normalização com timestamp                          | UC-08: Acompanhar Estabilização  | Modo simulado de normalização, banner e arquivamento | Normalização guardada por monitoramento e dados válidos; arquivar é explícito              |
| RF-10: consultar e exportar cronologia experimental                  | UC-09: Exportar Histórico Artigo | `Audit.tsx`, `domain/audit.ts`                       | Filtros reais, CSV/JSON locais e oito campos; MTTA e MTTR sem fórmula inferida             |
| RF-11: gerenciar destinatários de alertas                            | UC-10: Gerenciar E-mails Alerta  | `Notifications.tsx`                                  | Cadastro, listagem, remoção, ativação, duplicado, validação sintática e teste simulado     |

## Decisões de implementação propostas

- React + TypeScript + CSS + Vite; sem backend. Estado centralizado em reducer/context e salvo no navegador.
- Rotas por hash para executar em hospedagem estática, com navegação de voltar/avançar.
- Componentes reutilizáveis, tokens extraídos do Figma e fontes locais. Grid e flexbox substituem coordenadas absolutas de telas completas.
- O código acrescenta entrada livre nos formulários e download real de arquivos; o Figma usava respostas e entradas predefinidas.
- A demonstração tem dois modos principais e estados excepcionais em uma seção secundária. Os mesmos formulários reproduzem validações sem telas duplicadas.
- O termo “origem do desvio” evita certeza diagnóstica implícita em “causa raiz”. Essa escolha já estava no protótipo aprovado.
- Indicadores estáticos, textos e ícones acompanham as cores; não há animações de atenção repetitivas.
- Dialog nativo oferece foco contido, fechamento com Esc e retorno de foco. Switches possuem nome acessível e estado; inputs separam nome de mensagem de erro.
- Adaptação básica para telas menores é uma extensão da direção desktop de 1440 × 900. Em telas pequenas, tabelas e grafo podem ter rolagem local.

## Oito campos experimentais

1. ID do ensaio.
2. Microsserviço.
3. Métrica divergente.
4. Timestamp da injeção de falha.
5. Timestamp da detecção proativa pelo AIM.
6. Tempo de antecedência alcançado (MTTA).
7. Timestamp de normalização.
8. Tempo de recuperação (MTTR).

MTTA é associado à antecedência nas fontes, mas falta um marco inequívoco do impacto previsto. Para MTTR, o marco inicial também não está explicitado. São definições pendentes de negócio/pesquisa; valores não são calculados a partir de diferenças arbitrárias entre timestamps. Arquivamento não substitui normalização nem é usado para calcular recuperação.

## Fronteira do produto

O AIM acompanha e apresenta informações. Ações de mitigação são externas pelo operador. Nenhum botão corrige serviços, desliga pods, injeta agentes ou muda a infraestrutura. O modo de normalização simula a chegada de novos sinais, e não executa uma ação corretiva.
