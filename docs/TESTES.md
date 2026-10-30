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
