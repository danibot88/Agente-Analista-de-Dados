# DataAgent — tarefas

Este arquivo é o quadro de trabalho do plano aprovado. Um coordenador atualiza os estados após conferir as evidências. Estados: `Pendente`, `Em andamento`, `Bloqueada`, `Concluída`. Ao concluir, registre responsável, arquivos, comandos/resultados e limitações; não marque como concluída apenas por ter escrito código.

## Entrega inicial: etapas 1 a 3

### T01 — Preparar base e testes de comportamento

- Estado: Concluída. Dependências: nenhuma.
- Registrar os fluxos atuais de CSV/XLSX, opções, limites e falhas; criar testes úteis para o carregamento e o exemplo, independentes de Ollama.
- Aceite: testes reproduzíveis verificam o cálculo Café 220,50 e Chá 80,00, CSV com `;` e `,`, arquivo vazio e erros de leitura. Registrar como executá-los.

### T02 — Separar a arquitetura

- Estado: Concluída. Dependências: T01.
- Extrair leitura de dados, cliente Ollama, execução SQL e orquestração da interface; manter entrada simples do Streamlit. Definir contratos em `docs/ARQUITETURA.md` conforme o código final.
- Aceite: comportamento atual e inicialização preservados; serviços testáveis sem Streamlit; erros e fechamento de conexão cobertos; testes da T01 passam.

### T03 — Perfil e qualidade dos dados

- Estado: Concluída. Dependências: T02.
- Gerar perfil limitado com nomes, tipos, contagens, ausências e resumos apropriados; sinalizar indícios de números ou datas como texto sem converter silenciosamente. Definir limites e evitar expor valores privados desnecessários.
- Aceite: perfil útil e limitado está disponível em seção recolhida por padrão; testes cobrem dados ausentes, tipos e casos ambíguos; texto explica que amostras e estatísticas selecionadas podem ser enviadas ao Ollama local.

### T04 — Contexto para gerar SQL

- Estado: Pendente. Dependências: T02 e T03.
- Usar perfil limitado junto com a pergunta e um contrato estruturado na geração do SQL. Permitir que o modelo informe impossibilidade ou ambiguidade. Manter tentativas de correção limitadas.
- Aceite: testes com cliente simulado cobrem SQL válido, resposta sem SQL, resposta inválida e falhas de consulta; acesso externo permanece desabilitado e somente uma instrução de leitura é aceita.

### T05 — Resposta fundamentada

- Estado: Pendente. Dependências: T04.
- Elaborar resposta em português usando apenas a pergunta, SQL e resultado executado, com limites explícitos para o conteúdo enviado ao modelo. Mostrar tabela e SQL; distinguir resultado vazio e resultado truncado.
- Aceite: testes simulam resposta baseada em resultado, vazio, truncamento e falha do modelo. A interface informa quando apenas uma parcela dos dados ou do resultado foi utilizada para interpretação; nenhuma análise completa é afirmada para uma amostra parcial.

### T06 — Integração, limites e documentação

- Estado: Pendente. Dependências: T01–T05.
- Revisar riscos de consultas caras e implementar limites de tempo ou recursos viáveis no ambiente, verificando seu efeito; se não forem viáveis, documentar limitações sem alegar proteção inexistente. Testar o fluxo completo e atualizar README.
- Aceite: suíte automatizada aprovada; execução manual com Ollama registrada quando disponível, ou impedimento explicitado; instruções de instalação, arquitetura, privacidade, limitações e verificações atualizadas.

## Futuro — não incluído na entrega inicial

### T07 — Seleção de aba Excel

- Estado: Pendente. Dependências: entrega inicial. Aceite: lista e carrega a aba escolhida, com testes para múltiplas abas.

### T08 — Histórico de perguntas

- Estado: Pendente. Dependências: entrega inicial. Aceite: perguntas de acompanhamento usam contexto delimitado à sessão e à base atual; trocar o arquivo limpa ou separa o histórico; testes cobrem troca de base.

### T09 — Gráficos e exportação

- Estado: Pendente. Dependências: entrega inicial. Aceite: gráficos apropriados aos tipos de resultado, dados de origem visíveis e exportação CSV testada; limites e truncamentos informados.

## Registro de execução

| Tarefa | Responsável | Evidência e pendências |
| --- | --- | --- |
| T01 | Codex | `tests/test_comportamento.py` e README; `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`: 6 testes aprovados, incluindo exemplo CSV e DuckDB real com Ollama simulado. Inicialização headless do Streamlit: health HTTP 200. Não houve teste manual no navegador com Ollama. |
| T02 | Codex | `app_local.py`, `dataagent/`, `tests/test_servicos.py`, `docs/ARQUITETURA.md` e README; `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`: 15 testes aprovados, inclusive T01. Streamlit headless: health HTTP 200; AppTest iniciou sem upload, mas a limpeza de diretório temporário retornou erro de permissão. Teste manual com Ollama não executado. |
| T02 — revisão | Codex | Mensagens de correção por categoria fixa, sem repassar a exceção bruta; teste com modelo simulado que usa o motivo e corrige na segunda tentativa. Suíte: 18 testes aprovados. Ollama real não testado. |
| T03 | Codex | `dataagent/perfil.py`, interface, testes e documentação; `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`: 22 testes aprovados; Streamlit headless: health HTTP 200. Perfil limitado a 1.000 linhas e 50 colunas. Ollama real e teste manual no navegador não executados. |
| T03 — revisão | Codex | Perfil disponível em seção recolhida a pedido do usuário; verificação independente e limitações registradas em `docs/TESTES.md`. |
| T04–T09 | A definir | Pendentes. |
