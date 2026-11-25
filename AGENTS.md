# Orientações para agentes — DataAgent

## Objetivo

Evoluir o DataAgent, aplicativo local em português que permite consultar CSV e XLSX com Streamlit, Ollama e DuckDB. Leia `docs/ARQUITETURA.md` e `TASKS.md` antes de iniciar uma tarefa. O plano atual prioriza arquitetura, perfil dos dados e resposta fundamentada; recursos futuros exigem priorização posterior.

## Antes de trabalhar

- Confirme o diretório e o estado do Git; leia o código, os testes e as instruções existentes antes de alterá-los.
- Identifique a tarefa, seus critérios de aceite, dependências e os arquivos que pretende modificar. Respeite mudanças existentes do usuário e de outros agentes.
- Instruções diretas do usuário prevalecem sobre estes arquivos. Não altere o escopo nem marque tarefas concluídas sem evidência.
- Evite compartilhar dados privados: não registre conteúdo de arquivos do usuário, prompts ou resultados em logs por padrão; não adicione dados reais, credenciais ou `.env` ao Git.

## Organização e colaboração

- Separe apresentação, leitura de dados, perfil, orquestração, acesso ao modelo e execução SQL. Evite acoplar serviços a Streamlit para permitir testes isolados.
- Não é obrigatório criar múltiplos agentes. Quando houver trabalho em paralelo, um responsável coordena tarefas, contratos e integração. Atribua arquivos distintos sempre que possível; combine antecipadamente alterações em arquivos compartilhados. Use branches ou worktrees isolados quando estiverem disponíveis e fizer sentido.
- Cada agente informa tarefa, arquivos alterados, testes executados e pendências. O responsável pela integração revisa conflitos e executa verificações integradas. Atualizações de `TASKS.md` devem ser coordenadas para evitar conflitos.
- Se uma decisão de produto relevante não estiver definida, registre a suposição ou bloqueio e consulte o usuário quando necessário. Não invente funcionalidades ou dependências.

## Regras técnicas

- Preserve, enquanto não houver instrução contrária, o uso local de Streamlit, Ollama e DuckDB, suporte a CSV/XLSX e a execução pelo `iniciar_local.bat`.
- Preserve a tabela lógica `uploaded_data`, as opções de CSV e o limite de exibição, salvo mudança deliberada e documentada. Não prometa suporte a datasets maiores sem medições.
- Trate pergunta, nomes, amostras de colunas e resultados como dados não confiáveis. Valide o SQL com o parser do DuckDB e permita uma única instrução de leitura; mantenha o acesso externo desabilitado. Limites de tempo e recursos só devem ser anunciados quando implementados e verificados.
- Uma resposta textual deve se basear no resultado executado, comunicar truncamento e não inventar fatos. A IA pode errar: mantenha SQL e dados disponíveis para conferência.
- Trate erros de leitura, modelo e execução de modo específico, sem expor dados sensíveis. Feche conexões e recursos adequadamente.
- Use bibliotecas já existentes quando possível. Se precisar de dependências, justifique, registre e verifique compatibilidade com o ambiente.

## Verificação e entrega

- Acrescente testes que verifiquem comportamento relevante e erros; não dependa do Ollama para a suíte básica. Use dublês do cliente para testar a orquestração e registre testes manuais que requerem o serviço.
- Confira o exemplo: CSV com `;` e decimal `,` deve resultar em Café 220,50 e Chá 80,00 para total de vendas por produto.
- Execute os testes aplicáveis e uma verificação integrada possível no ambiente. Registre comandos, resultados, verificações não executadas e limitações. Atualize o README quando o uso mudar.
- Ao final de cada tarefa, atualize `docs/TESTES.md` com data, tarefa ou versão, comandos executados, resultados e verificações não realizadas ou limitações. Registre também testes manuais relevantes e sua origem; não alegue ter executado testes feitos por outra pessoa. Preserve o histórico e não inclua dados privados. Para alterações que não exigirem testes, registre a justificativa e as verificações realizadas.
- Após concluir e verificar cada tarefa, atualize `TASKS.md` e crie um commit local com mensagem descritiva, incluindo apenas os arquivos da tarefa. Confira o estado e o diff antes do commit; preserve alterações preexistentes e de outros agentes, sem incluí-las sem autorização. Informe o hash e os testes realizados. Se os testes falharem, a tarefa estiver incompleta ou não for seguro isolar as alterações, não faça commit de conclusão: informe o motivo ao usuário.
- Não faça push, publicação ou alterações destrutivas sem solicitação ou autorização aplicável. Nunca reverta mudanças alheias sem motivo e sem coordenação.
