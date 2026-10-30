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
Verificação integrada: pergunta de contagem na planilha local com Ollama real retornou 13.500 linhas após três tentativas, usando código corrigido em cópia de trabalho. O arquivo foi somente lido.
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
Resultado: 44 testes padrão aprovados e um opcional ignorado; teste integrado opcional com Ollama real aprovado, com 13.500 linhas e 2.950 registros EUR. Repetidos exemplos sintéticos de soma numérica e contagem de datas tipadas com ausências. O teste integrado verificou o hash da planilha antes e depois da leitura.
Limitações: não houve teste no navegador; o modelo pode gerar SQL que não corresponde à pergunta. Conversões com filtros seguem não suportadas; comandos de escopo completo exigem sintaxe exata. Ponto flutuante pode ser aproximado.
