# Validação da entrega

Revisão concluída em 03/11/2026.

- `npm run build`: compilação TypeScript e produção Vite aprovadas.
- `npm test`: **24 testes de domínio aprovados**.
- `npm run test:e2e`: **7 testes de fluxos aprovados em Chromium**, executando a aplicação real.

Os testes de domínio cobrem pausa global/individual, risco de origem/reflexo/indeterminado, guardas de normalização, atualização da projeção, arquivamento, retenção do histórico, cadastro duplicado, endpoints permitidos, e-mail, persistência corrompida, filtros combinados e serialização dos oito campos experimentais.

Os testes de navegador cobrem:

1. Dashboard, pausa global/individual, seleção de serviço, período temporal e persistência após recarregar.
2. Cadastro com texto digitado, endpoint inválido, escolha de runtime, conectividade simulada e desvinculação.
3. Incidente, seleção de nó no modal, fechamento com Esc, normalização e arquivamento com timestamp no histórico.
4. E-mail inválido/duplicado, aviso sem destinatários ativos, reativação e envio simulado.
5. Filtros independentes, ausência de resultados e download de JSON validado quanto a conteúdo e oito campos.
6. Falha de endpoint, nova tentativa e recuperação de telemetria desatualizada.
7. Ativos SVG locais carregados, layout desktop e ausência de overflow global no dashboard mobile.

Foram inspecionadas renderizações do dashboard em 1440 × 900, detalhe das métricas, modal de topologia e dashboard em viewport mobile de 390 × 844. SVGs do Figma estão incluídos localmente; as fontes também são locais. Não há dependência de URLs temporárias de ativos do Figma durante a execução.

Esta validação verifica a implementação mockada. Não mede a eficácia operacional de alertas, não comprova as metas de tempo de triagem com operadores e não testa integrações OTel, SMTP ou ambientes reais. Essas integrações não fazem parte deste projeto.
