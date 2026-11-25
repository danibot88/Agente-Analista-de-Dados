# Auditoria de divergência — DataAgent

Data da auditoria: 25/11/2026

Repositório: <https://github.com/danibot88/Agente-Analista-de-Dados>

## Resumo executivo

O trabalho local não está perdido e não há conflito conhecido com o GitHub. O `main` remoto continua em `00e338a` (`docs: adiciona capturas de tela ao README`) e o `main` local está em `a8dc4df`, sete commits à frente e zero atrás. Os sete commits formam uma sequência linear baseada no commit remoto atual.

Além dos commits, existem três alterações documentais ainda não commitadas: `README.md`, `TASKS.md` e `docs/TESTES.md`. Nenhum arquivo de código está modificado fora dos commits. A suíte automatizada atual passou com 54 testes aprovados e um teste opcional com Ollama ignorado.

Conclusão: não é necessário fazer merge entre duas linhas de desenvolvimento divergentes. A estratégia mais segura é criar agora uma branch a partir do estado local, finalizar nela a documentação e a validação manual, enviá-la ao GitHub e abrir um pull request contra `main`.

## Estado comparado na abertura da auditoria

| Item | GitHub | Pasta local | Avaliação |
| --- | --- | --- | --- |
| Branch principal | `main` em `00e338a` | `main` em `a8dc4df` | Local está 7 commits à frente e 0 atrás |
| Branches remotas | Apenas `main` | Apenas `main` local | Falta uma branch de integração |
| Pull requests | Nenhum | Não aplicável | Ainda não existe revisão formal |
| Código da entrega T01–T06 | Ausente no remoto | Presente em 7 commits | Principal divergência a publicar |
| Alterações não commitadas | Não existem no remoto | 3 documentos modificados | Precisam ser revisadas e commitadas |
| Testes automatizados | Sem workflow de CI identificado | 54 aprovados, 1 ignorado | Evidência local boa; falta automação remota |
| Ollama e navegador | Não verificados nesta auditoria | Não executados nesta auditoria | A finalização registra as verificações em `docs/TESTES.md` |

Commits locais ainda não publicados, em ordem:

1. `fc70c37` — `docs: orienta registro de testes e commits`
2. `8826437` — `refactor: separa servicos e aprimora correcao SQL`
3. `ed49166` — `feat: adiciona perfil de qualidade dos dados`
4. `00ffa71` — `feat: adiciona contexto e consultas controladas`
5. `2d8ea61` — `chore: ignora pasta de dados locais`
6. `64f6bce` — `Adiciona resposta baseada no resultado executado`
7. `a8dc4df` — `Define limites de memoria do DuckDB`

## docs/ARQUITETURA.md

- Nenhuma divergência relevante entre a arquitetura documentada e o código atual foi confirmada.
- As separações entre interface, leitura, perfil, modelo, política, resposta, orquestração e SQL existem no código.
- Os limites documentados do DuckDB (`256MB`, duas threads e armazenamento temporário desabilitado), o limite de 1.001 linhas consultadas e 1.000 exibidas e a ausência de timeout estão refletidos na implementação.
- A documentação e o código deixam claro que o limite do DuckDB não limita toda a memória do processo e que o SQL gerado pode não corresponder semanticamente à pergunta.

## TASKS.md

- T01 a T06 estão marcadas como concluídas e possuem implementação e testes correspondentes no estado local.
- T07, T08 e T09 permanecem pendentes e não foram implementadas, coerentemente com o escopo documentado.
- A alteração não commitada troca `T04 — revisão em andamento` por `T04 — revisão de filtros`. A nova redação é mais coerente com o restante do documento e com a conclusão da tarefa, mas ainda não existe no GitHub.
- Antes de publicar, o registro deve receber somente evidências realmente executadas na finalização. Não marcar o teste manual no navegador como concluído sem realizá-lo.

## README.md

- A versão local documenta o comportamento implementado: primeira aba de XLSX, opções de CSV, perfil limitado, política conservadora de SQL, comandos controlados, resposta baseada em linhas, limites e riscos.
- A seção não commitada `Estado do projeto` é coerente com o código e com `TASKS.md`, mas ainda não existe no GitHub.
- A afirmação de que o fluxo integrado com Ollama foi exercitado é sustentada pelo histórico de testes de 04/11/2026; nesta auditoria o Ollama real não foi repetido.
- Não foi identificada instrução de uso que contradiga diretamente a implementação atual.

## docs/TESTES.md

- O histórico contém as verificações de T01 a T06 e diferencia testes automatizados, Ollama real e limitações.
- A entrada não commitada de 04/11/2026 registra 54 testes aprovados e um opcional ignorado, consistente com o resultado repetido nesta auditoria.
- Esta auditoria de 25/11/2026 ainda não está registrada no arquivo. Ao finalizar, acrescentar os comandos e resultados atuais, sem substituir o histórico.
- O teste manual completo no navegador continua ausente. Ele deve permanecer explicitamente como não executado até ser realizado.

## Divergências e riscos que exigem ação

### Confirmados

1. **Sete commits locais não estão no GitHub.** O remoto termina em `00e338a`; o local termina em `a8dc4df`.
2. **Há três documentos modificados fora de commit.** São `README.md`, `TASKS.md` e `docs/TESTES.md`.
3. **Não há branch de integração nem pull request.** O GitHub possui somente `main`.
4. **Não há workflow de CI no projeto.** Os testes do pull request dependerão de execução local até que uma automação seja adicionada.
5. **A validação manual no navegador não foi concluída.** A suíte não substitui upload, interação visual e resposta do Ollama no Streamlit.

### Não confirmados como defeito

- Nenhuma falha funcional foi encontrada pela suíte automatizada.
- Nenhum conflito com alterações remotas foi encontrado.
- Nenhuma divergência relevante entre arquitetura, tarefas e código atual foi confirmada.
- A qualidade semântica do SQL e da seleção de linhas pelo modelo não é garantida pelos testes simulados; isso é uma limitação conhecida, não um defeito novo confirmado.

## Verificações executadas nesta auditoria

```powershell
git status --short --branch
git remote -v
git branch -vv
git log --oneline --decorate -12
git diff --stat origin/main..HEAD
git diff --name-status origin/main..HEAD
git diff --check
git diff origin/main..HEAD --check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q app_local.py dataagent tests
```

Resultados:

- `unittest`: 55 testes encontrados; 54 aprovados e 1 teste opcional com Ollama ignorado.
- `pip check`: nenhuma dependência quebrada encontrada.
- `compileall`: concluído sem erro.
- `git diff --check`: nenhuma falha de whitespace; o Git apenas avisou que os três documentos modificados poderão usar CRLF quando forem regravados no Windows.
- GitHub consultado diretamente: `main` em `00e338ad7630bfa41c9dc1b7717cdd9703ef5303`, apenas a branch `main` e nenhum pull request.

Não executados nesta auditoria:

- teste opcional com Ollama real;
- teste manual completo no navegador;
- medição de desempenho com arquivos grandes;
- push, criação de pull request ou merge.

## Estratégia recomendada para finalizar

### 1. Isolar imediatamente o trabalho local

Criar uma branch a partir do estado atual, levando junto as alterações documentais ainda não commitadas:

```powershell
git switch -c codex/finalizar-entrega-inicial
```

Não usar `git reset`, `git checkout --`, `git clean` ou rebase neste momento. O estado atual é recuperável e linear; uma operação de reescrita só aumentaria o risco.

### 2. Roteiro de validação manual adiada

O usuário adiou esta etapa para depois da integração. O roteiro fica disponível para a próxima rodada de validação.

1. Iniciar o Ollama e confirmar `llama3.2:latest` com `ollama list`.
2. Executar `iniciar_local.bat`.
3. No navegador, enviar `exemplo.csv` com separador `;` e decimal `,`.
4. Perguntar o total de vendas por produto.
5. Confirmar Café `220,50`, Chá `80,00`, tabela, SQL exibido e avisos.
6. Verificar uma pergunta simples de contagem e uma pergunta que deva ser recusada pela política.
7. Registrar em `docs/TESTES.md` o que foi realmente observado, incluindo modelo, resultado e limitações, sem copiar dados privados.

Se o Ollama não estiver disponível, registrar o impedimento e não declarar o teste manual como aprovado. Isso não invalida a suíte básica, mas deve aparecer como limitação do pull request.

### 3. Revisar e fechar a documentação

- Manter as três alterações documentais atuais se a revisão confirmar o conteúdo.
- Acrescentar a evidência de 25/11/2026 em `docs/TESTES.md`.
- Atualizar `TASKS.md` apenas se houver nova evidência ou mudança real de estado.
- Incluir este relatório no commit de documentação ou em um commit separado de auditoria.
- Conferir `git diff` e `git status` antes de adicionar arquivos.

Exemplo de commit apenas com os documentos pretendidos:

```powershell
git add README.md TASKS.md docs/TESTES.md 2026-11-25_DRIFT_REPORT.md
git diff --cached --check
git diff --cached --stat
git commit -m "docs: consolida entrega inicial e plano de integracao"
```

### 4. Repetir as verificações antes do envio

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q app_local.py dataagent tests
git status --short --branch
git log --oneline --decorate origin/main..HEAD
```

O estado esperado é uma branch limpa, à frente de `origin/main`, com os sete commits de implementação e o commit final de documentação.

### 5. Publicar uma branch, não o `main` diretamente

```powershell
git push -u origin codex/finalizar-entrega-inicial
```

Abrir um pull request de `codex/finalizar-entrega-inicial` para `main`, resumindo T01–T06, testes, validação manual e limitações. Não fazer push direto para `main` enquanto houver trabalho sem revisão.

### 6. Método de merge recomendado

Usar **merge commit** no pull request. Não usar squash ou rebase merge nesta integração, porque os sete commits já existem no `main` local. Um merge commit mantém esses commits como ancestrais do `main` remoto e permite sincronizar o `main` local depois por fast-forward.

Depois do merge no GitHub:

```powershell
git switch main
git pull --ff-only origin main
git branch -d codex/finalizar-entrega-inicial
```

Excluir a branch remota é opcional e deve ser feito apenas após confirmar o merge e o estado local.

## Melhoria opcional recomendada

Adicionar um workflow simples de GitHub Actions para executar a suíte básica em pull requests, sem Ollama. Isso reduz a dependência de evidência manual e protege futuras alterações. A inclusão deve ser um commit separado, com versão de Python compatível e cache opcional, sem credenciais e sem dados locais.

Essa melhoria não precisa bloquear a publicação atual se a suíte local e o teste manual forem registrados, mas deve ser priorizada antes de T07–T09.

## Instruções para o próximo agente

1. Ler `AGENTS.md`, `docs/ARQUITETURA.md`, `TASKS.md`, `docs/TESTES.md` e este relatório antes de agir.
2. Confirmar novamente o estado remoto antes do push; o diagnóstico acima é válido para 25/11/2026.
3. Preservar `README.md`, `TASKS.md` e `docs/TESTES.md`; eram alterações preexistentes à auditoria.
4. Não implementar T07, T08 ou T09 durante a finalização da entrega inicial.
5. Não alterar a política SQL, limites do DuckDB ou contratos sem uma tarefa explícita e novos testes.
6. Não adicionar arquivos de `dados_locais`, planilhas, CSVs reais, `.env` ou credenciais ao Git.
7. Executar e registrar verificações próprias; não apresentar os testes desta auditoria como se tivessem sido executados por outro agente em outra data.
8. Criar a branch de integração antes de novos commits.
9. Abrir pull request e usar merge commit; não fazer push direto nem merge sem revisão e autorização aplicável.
10. Informar ao usuário arquivos alterados, comandos executados, resultados, limitações, hash do commit e URL do pull request quando essas ações forem autorizadas.

## Critério de pronto para o pull request

- [ ] Trabalho está em `codex/finalizar-entrega-inicial`.
- [ ] `git status` está limpo.
- [ ] Alterações documentais foram revisadas e commitadas.
- [ ] Suíte básica passou novamente.
- [ ] `pip check`, `compileall` e `git diff --check` passaram.
- [ ] Teste manual no navegador com Ollama foi executado e registrado, ou o impedimento foi documentado.
- [ ] Nenhum dado privado ou arquivo local foi incluído.
- [ ] O pull request descreve limitações conhecidas e não promete timeout ou segurança semântica inexistentes.
