# Sistema PoC

`system/` permanece como destino previsto para os componentes do produto/PoC. O mock de interface executável está em [`frontend/`](../frontend/) e pode ser iniciado conforme o [README do repositório](../README.md).

O frontend atual reproduz fluxos de demonstração com dados fictícios e persistência local no navegador. Ele não se conecta a backend, banco de dados, OpenTelemetry, e-mail ou aplicações monitoradas. Portanto, sua presença não representa serviços da PoC implantados nem uma arquitetura de processos aprovada.

Uma decisão futura ainda deve definir as fronteiras e a implementação do backend e da inferência, com requisitos de latência, escala, operação e dados.
