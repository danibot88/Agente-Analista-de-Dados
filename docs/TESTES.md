Data: 30/10/2026
Tarefa: T02
Comando: python -m unittest discover -s tests -v
Resultado: 15 testes aprovados
Limitações: Ollama real não testado; AppTest não concluído
Observação: revisar a informação enviada ao modelo após erro de SQL

Data: 30/10/2026
Tarefa: orientações para agentes e verificação do exemplo
Verificação: leitura de exemplo.csv e soma por produto da coluna quantidade.
Resultado esperado: Café = 5; Chá = 2. Menor quantidade: Chá.
Teste manual relatado pelo usuário: pergunta sobre o produto com menor quantidade de vendas; resposta considerada incorreta. Resultado exibido e SQL não informados, portanto a falha não foi reproduzida nem diagnosticada.
Alterações de documentação: instruções para registro de testes e commits; testes automatizados não executados nesta tarefa, pois não houve alteração no código da aplicação.

Data: 30/10/2026
Tarefa: revisão da T02 — motivo sanitizado para correção de SQL
Comando: .\.venv\Scripts\python.exe -m unittest discover -s tests -v
Resultado: 18 testes aprovados, incluindo correção na segunda tentativa com modelo simulado, categorias de erro e ausência de texto sensível das exceções nas mensagens de correção. A primeira execução encontrou falhas em dois testes por codificação dos literais de teste; após corrigir os literais, a suíte passou.
Limitações: Ollama real e teste manual no navegador não executados. O SQL anterior gerado pelo modelo continua sendo enviado na tentativa de correção.

Data: 30/10/2026
Tarefa: verificação independente da revisão T02
Comando: python -m unittest discover -s tests -v (usando a .venv do projeto e PYTHONPATH da raiz)
Resultado: 18 testes aprovados. Revisadas as categorias fixas de erro e a retentativa com modelo simulado.
Limitações: Ollama real e interface no navegador não foram executados nesta verificação.

Data: 30/10/2026
Tarefa: T03 — perfil e qualidade dos dados
Comando: .\.venv\Scripts\python.exe -m unittest discover -s tests -v
Resultado: 22 testes aprovados. Verificados ausência, tipos, resumos, indícios ambíguos, limites, preservação da base e exibição do perfil. Os testes da T01 continuam aprovados, incluindo o exemplo de vendas com DuckDB real e Ollama simulado.
Verificação integrada: inicialização headless do Streamlit com endpoint de saúde HTTP 200; a integração de upload, perfil e consulta foi exercitada com interface e cliente simulados.
Limitações: não houve teste manual no navegador nem com Ollama real; o perfil usa as primeiras 1.000 linhas e 50 colunas, e indícios de texto são heurísticos.

Data: 30/10/2026
Tarefa: revisão da T03 — perfil recolhido na interface
Comando: python -m unittest discover -s tests -v, em cópia de trabalho com a .venv do projeto
Resultado: 22 testes aprovados, incluindo verificação de que a seção do perfil começa recolhida e o fluxo do exemplo permanece funcional com cliente simulado.
Limitações: interface após o ajuste não foi testada no navegador; o perfil não é enviado ao modelo até a T04.

Data: 30/10/2026
Tarefa: T04 — contexto limitado e conversões controladas
Comando: .\.venv\Scripts\python.exe -m unittest discover -s tests -v
Resultado: 28 testes aprovados; suíte automatizada com dados sintéticos cobre perfil enviado, recusa, respostas inválidas, falhas de SQL, separação de moedas, repetição de identificadores, números e datas inválidos, valores ausentes e contagem de exclusões. Não requer Ollama.
Verificação complementar local: leitura da planilha ignorada pelo Git e execução de soma por moeda usando cliente simulado e ponto decimal; comparação independente com Decimal e contagens por grupo aprovada. Hash do arquivo antes e depois igual. Dados e resultados da planilha não foram registrados aqui.
Limitações: não houve teste manual no navegador ou com Ollama real. O modelo pode interpretar a pergunta de modo incorreto; operações controladas usam todas as linhas e formatos limitados, e a inferência de CSV e a detecção de moeda têm limitações descritas no README.

Data: 30/10/2026
Tarefa: investigação de consultas sem resposta — T04
Resultado: reproduzida a rejeição indevida de COUNT(*) pelo validador. Corrigida a representação count_star do parser DuckDB. Suíte em cópia de trabalho: 30 testes aprovados, incluindo contagens e rejeição de SQL múltiplo e filtros em agregação.
Verificação integrada: a contagem total com Ollama real bateu com o valor esperado após três tentativas, usando código corrigido em cópia de trabalho. A base foi somente lida.
Limitações: a T04 ainda restringe filtros, LIMIT e COUNT DISTINCT e não cobre todas as perguntas sugeridas. Não foi executado teste no navegador após a correção.

Data: 30/10/2026
Tarefa: revisão da T04 — perguntas simples e validação com Ollama
Comandos: .\.venv\Scripts\python.exe -m unittest discover -s tests -v; $env:DATAAGENT_TESTE_OLLAMA='1'; .\.venv\Scripts\python.exe -m unittest discover -s tests -p test_ollama_local.py -v
Resultado: suíte padrão: 34 testes aprovados e um teste opcional ignorado. Os testes sintéticos verificam filtros textuais, nulidade, DISTINCT e LIMIT, além da rejeição de coerções, funções arbitrárias e SQL múltiplo. Teste opcional com Ollama: 1 teste aprovado. Teste opcional com Ollama real verificou duas contagens solicitadas e o SQL efetivamente executado. Arquivo local ignorado pelo Git foi somente lido, com hash igual antes e depois.
Limitações: o modelo pode errar ou recusar perguntas; filtros complexos e conversões livres continuam bloqueados. Planos de conversão usam todas as linhas e ainda não aceitam filtros. Não houve teste no navegador.

Data: 30/10/2026
Tarefa: T04 — impedir que planos de conversão ignorem filtros
Comandos: .\.venv\Scripts\python.exe -m unittest discover -s tests -v; $env:DATAAGENT_TESTE_OLLAMA='1'; .\.venv\Scripts\python.exe -m unittest discover -s tests -p test_ollama_local.py -v
Resultado: 37 testes padrão aprovados e 1 teste opcional ignorado na suíte básica; o teste opcional separado passou com Ollama real, conferindo contagens e SQL. Testes sintéticos verificaram que planos de conversão sem suporte a filtro são recusados antes de executar SQL quando a pergunta contém filtro ou é ambígua, e que comandos exatos sem filtro usam o plano local. Teste com a planilha local e modelo simulado adversarial confirmou a recusa sem SQL; o comando explícito sem filtro executou e contabilizou todas as linhas. Hash da planilha igual antes e depois.
Limitações: uma pergunta de soma filtrada ao Ollama real não retornou dentro do tempo de 15 segundos configurado para a verificação e não executou SQL. Os planos de conversão aceitam somente comandos exatos para todas as linhas; não há garantia semântica para SQL gerado a partir de outras perguntas. Não foi realizado teste no navegador.

Data: 30/10/2026
Tarefa: revisão T04 — números e datas já tipados
Comando: .\.venv\Scripts\python.exe -m unittest discover -s tests -v
Resultado: 44 testes aprovados; 1 teste opcional com Ollama ignorado. A suíte cobre inteiros anuláveis, float, infinitos, Decimal sem arredondamento, datas, datetime, fuso horário e ausências; verifica também preservação dos dados, recusa de filtros e leitura e análise integrada de XLSX sintético. O teste do exemplo CSV da T01 permanece aprovado. Uma execução intermediária falhou por datas com formatos inconsistentes no próprio teste XLSX; a massa sintética foi corrigida e a suíte passou.
Limitações: ponto flutuante pode produzir soma aproximada; datetime é agrupado por dia, sem horário; objetos datetime com fuso em coluna genérica não são suportados. Planos de conversão continuam sem filtros. Ollama real e navegador não foram testados nesta revisão.

Data: 30/10/2026
Tarefa: revisão final da T04
Comandos: python -m unittest discover -s tests -v; DATAAGENT_TESTE_OLLAMA=1 com test_ollama_local.py (na .venv do projeto).
Resultado: 44 testes padrão aprovados e um opcional ignorado. O teste integrado opcional com Ollama real confirmou a contagem total e a contagem com filtro. Repetidos exemplos sintéticos de soma numérica e contagem de datas tipadas com ausências. O teste integrado verificou o hash da base antes e depois da leitura.
Limitações: não houve teste no navegador; o modelo pode gerar SQL que não corresponde à pergunta. Conversões com filtros seguem não suportadas; comandos de escopo completo exigem sintaxe exata. Ponto flutuante pode ser aproximado.

Data: 04/11/2026
Tarefa: T05 — resposta fundamentada e atualização do README
Comando: .\.venv\Scripts\python.exe -m unittest discover -s tests -q
Resultado: 51 testes aprovados e um teste opcional ignorado. Testados resposta com células executadas, resultado vazio, limites e truncamento, seleção inválida, falha do modelo e preservação da tabela e do SQL; exemplo CSV da T01 aprovado.
Verificação integrada: script Python executado via .venv com dados sintéticos, DuckDB e Ollama local llama3.2:latest conferiu a consulta de contagem, o resultado e a resposta. A primeira tentativa de interpretação falhou porque o modelo retornou índice inválido; após especificar índices permitidos, a repetição passou.
Limitações: não houve teste manual no navegador nem com arquivo real nesta tarefa. O modelo pode selecionar linhas pouco relevantes ou gerar SQL que não corresponda à pergunta. Os limites de contexto e exibição não limitam custo de consulta; revisão de recursos permanece na T06.

Data: 04/11/2026
Tarefa: T06 — integração, limites e documentação
Comando: .\.venv\Scripts\python.exe -m unittest discover -s tests -v
Resultado: 54 testes aprovados e um teste opcional ignorado. Verificados configuração do DuckDB, acesso externo desabilitado, erro de memória, ausência de novas tentativas e apresentação na interface simulada. A suíte manteve o exemplo CSV aprovado.
Verificação de recursos: consulta sintética com limite de DuckDB reduzido a 16 MB provocou erro real de memória e foi tratada como `recursos`. Com o padrão de 256 MB, consultas sintéticas distintas de maior volume terminaram sem atingir o limite; isso não estabelece limite de tempo nem de memória total.
Verificação integrada manual: script Python executado na .venv com o CSV de exemplo, DuckDB e Ollama local confirmou SQL, totais esperados e resposta. A primeira tentativa excedeu o prazo de 30 segundos do cliente de teste; a segunda, com prazo de 60 segundos, passou.
Limitações: não foi feito teste manual no navegador. Não há limite de tempo de consulta, nem teto para o consumo total do processo, pandas, Streamlit ou Ollama; a memória gerenciada pelo DuckDB tem limite de 256 MB e os arquivos temporários do DuckDB estão limitados a 0 bytes. A seleção de linhas e o SQL gerados pelo modelo podem não corresponder à intenção do usuário.

Data: 04/11/2026
Tarefa: avaliação do estado do projeto e atualização da documentação
Comando: .\.venv\Scripts\python.exe -m unittest discover -s tests -q
Resultado: 54 testes aprovados e um teste opcional com Ollama ignorado. O teste do exemplo CSV está incluído na suíte. Revisados o quadro de tarefas, o README e os limites documentados; a alteração é apenas documental.
Limitações: Ollama real e fluxo manual no navegador não foram executados nesta avaliação. A suíte usa dados sintéticos e não comprova que o modelo gere SQL semanticamente correto para perguntas arbitrárias.

Data: 25/11/2026
Tarefa: finalização de T01–T06
Comandos: `.\.venv\Scripts\python.exe -m unittest discover -s tests -q`, `.\.venv\Scripts\python.exe -m pip check` e `.\.venv\Scripts\python.exe -m compileall -q app_local.py dataagent tests`.
Resultado: 54 testes aprovados e um opcional ignorado. Dependências e compilação verificadas com Python 3.14.7.
Integração: `ollama list` confirmou `llama3.2:latest`. Um script executado com `.\.venv\Scripts\python.exe -X utf8 -` chamou `ler_arquivo`, `analisar` e `responder` com `exemplo.csv`, separador `;`, decimal `,` e a pergunta do README. As primeiras verificações encontraram SQL inválido ou sem identificação do produto. Após o ajuste no contexto, o SQL executado agrupou por produto e retornou Café 220,50 e Chá 80,00. A etapa de resposta retornou texto sem aviso.
Limitações: teste manual no navegador adiado a pedido do usuário. O teste opcional com a planilha privada permaneceu desativado. O resultado do exemplo não garante a qualidade de consultas arbitrárias.

Data: 25/11/2026
Tarefa: revisão de privacidade dos arquivos publicados
Comandos: `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -q`, `.\.venv\Scripts\python.exe -B -m pip check`, `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_ollama_local.py -v` com `DATAAGENT_TESTE_OLLAMA=1`, e `git diff --check`.
Resultado: 54 testes aprovados na suíte básica e um opcional ignorado. Dependências verificadas. O teste opcional passou separadamente com Ollama e CSV sintético em memória, conferindo a contagem total, a contagem com filtro e o SQL executado.
Limitação: teste manual no navegador segue adiado.

Data: 25/11/2026
Tarefa: alinhamento da documentação do projeto
Verificação: revisão dos cinco arquivos Markdown versionados, conferência dos links relativos e da âncora dos comandos de conversão, e `git diff --check`.
Comando: `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -q` com `DATAAGENT_TESTE_OLLAMA=0`.
Resultado: 54 testes aprovados e um opcional ignorado. Links e diff verificados.
Limitação: revisão exclusivamente documental. A integração com Ollama real e o teste manual no navegador ficaram fora desta rodada.

Data: 25/11/2026
Tarefa: checklist de revisão e publicação
Verificações: `git diff --check` e leitura do diff para conferir os três passos e o escopo documental.
Resultado: checklist incluído em `AGENTS.md`.
Limitação: a suíte não foi executada nesta tarefa porque a mudança afeta apenas as orientações de trabalho.
