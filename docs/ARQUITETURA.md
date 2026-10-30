# Arquitetura proposta — DataAgent

## Objetivo e escopo

O DataAgent recebe um CSV ou XLSX, apresenta o perfil da base e responde perguntas em português. O Ollama local gera SQL para DuckDB e, após a execução, uma interpretação fundamentada. O usuário pode conferir a tabela e o SQL. A primeira entrega cobre arquitetura, perfil e resposta; histórico, gráficos e escolha de aba são posteriores.

## Fluxo proposto

```text
Streamlit → leitura do arquivo → DataFrame → perfil limitado
                                           ↓
Pergunta + perfil → Ollama → SQL → validação → DuckDB em memória
                                               ↓
             resposta em português ← resultado limitado + contexto
                       ↓
             resposta, tabela, SQL e avisos na interface
```

O perfil e o resultado enviados ao modelo devem ter limites explícitos. Os dados recebidos do arquivo, a pergunta e o conteúdo produzido pelo modelo são entradas não confiáveis. O limite de linhas exibidas não garante, por si só, limite de custo de execução da consulta.

## Responsabilidades sugeridas

```text
app_local.py                 Entrada Streamlit
dataagent/
  interface/                Apresentação e estado da interface
  ingestion/                Leitura de CSV/XLSX e opções
  profiling/                Perfil e diagnósticos de qualidade
  analysis/                 Coordenação dos passos e contratos
  llm/                      Cliente Ollama, prompts e respostas
  database/                 Validação e execução SQL no DuckDB
tests/                      Testes automatizados
```

A árvore é uma proposta, não uma exigência de criar pastas vazias. Ajustes devem manter fronteiras claras e ser refletidos neste documento. `app_local.py` e `iniciar_local.bat` continuam como pontos de entrada enquanto compatibilidade estiver no escopo.

## Contratos a definir na implementação

- **Leitura:** bytes, formato e opções entram; DataFrame ou erro específico sai. Não converter silenciosamente tipos ambíguos.
- **Perfil:** DataFrame entra; estrutura limitada com tipos, contagens, ausências e estatísticas sai. Definir limites de amostras e dados enviados.
- **Geração SQL:** pergunta e perfil entram; SQL e explicação ou motivo para não responder saem. Respostas malformadas devem ser tratadas.
- **Execução:** validar uma única instrução de leitura com o parser do DuckDB, manter acesso externo desabilitado, registrar `uploaded_data` e fechar a conexão. Resultado deve carregar informação sobre truncamento. Avaliar e testar limites de execução; documentar o que não for possível garantir.
- **Interpretação:** pergunta, consulta e resultado efetivamente disponível entram; texto em português e avisos saem. Informar se somente parte do resultado foi enviada; não inventar conclusões.
- **Interface:** apresentar perfil, erros por etapa, resposta, dados e SQL, sem depender de regras de negócio espalhadas por componentes.

Os nomes de funções e estruturas serão definidos conforme o código existente e os testes. Falhas entre etapas devem ser explícitas e não devem mascarar o erro original.

## Privacidade e validação

O modelo é acessado localmente, mas dados selecionados ainda são enviados ao processo Ollama. A interface e o README devem explicar quais categorias de informações são enviadas e suas limitações. Evitar logs com dados reais. Use testes com dados sintéticos e cliente de modelo simulado; faça uma verificação integrada com Ollama quando possível. Não afirme que a validação de SQL ou um limite de exibição elimina todos os riscos.

## Implementação atual após T02

O fluxo implementado é `app_local.py → leitura → análise → modelo / SQL → interface`. A interface conserva as opções e a prévia, e apresenta o resultado, o SQL e o aviso de truncamento. Os serviços não importam Streamlit:

- `dataagent/leitura.py`: `ler_arquivo(conteudo, nome, opcoes_csv)` recebe bytes, nome e opções do pandas para CSV e retorna um DataFrame. XLSX usa a primeira aba. Falhas geram `ErroLeitura`, com causa original encadeada; a interface mostra mensagem sem conteúdo da exceção. O DataFrame vazio é tratado pela interface.
- `dataagent/modelo.py`: `ClienteOllama.gerar_sql(mensagens)` consulta `llama3.2:latest` no Ollama local e retorna conteúdo bruto, SQL e explicação. Falhas de comunicação e JSON inválido geram `ErroModelo`. O cliente envia a pergunta e nomes e tipos das colunas; durante correções também envia o SQL retornado anteriormente e um motivo de falha escolhido de mensagens fixas por categoria (sintaxe, referência, conversão, restrição ou execução). A exceção bruta não é enviada; o SQL anterior continua no contexto de correção.
- `dataagent/sql.py`: `ExecutorSQL(dados)` abre DuckDB em memória com acesso externo desabilitado e registra `uploaded_data`. `executar(sql)` usa o parser para exigir uma única instrução SELECT e retorna até 1.001 linhas; problemas geram `ErroConsulta`. O gerenciador de contexto fecha a conexão, inclusive nas falhas; falha de registro também fecha a conexão aberta.
- `dataagent/analise.py`: `analisar(dados, pergunta, cliente=None, executor_factory=ExecutorSQL)` coordena até três tentativas. Retorna `ResultadoAnalise` com DataFrame de até 1.000 linhas, SQL e indicador de truncamento, ou aviso quando o modelo não fornece SQL. `ErroModelo` e `ErroConsulta` são tratados separadamente pela interface. Cliente e fábrica de executor podem ser substituídos em testes.

A T03 implementa o perfil descrito abaixo; a interpretação textual do resultado permanece planejada para T05. O SQL e os dados exibidos permanecem disponíveis para conferência. A limitação de linhas retornadas não impõe limite de tempo ou de recursos à execução.

## Perfil implementado na T03

`dataagent/perfil.py` expõe `gerar_perfil(DataFrame)`, que retorna um `Perfil` com totais, dimensões analisadas e uma lista de resumos por coluna. O cálculo examina no máximo as primeiras 1.000 linhas e 50 colunas; nomes exibidos são limitados a 100 caracteres mais reticências. As contagens de ausentes e não ausentes e os resumos referem-se apenas às linhas analisadas. Valores nulos do pandas são ausentes; texto vazio não é considerado ausente. Valores numéricos e datas têm mínimo e máximo; booleanos têm contagens de verdadeiro e falso. O perfil não mostra exemplos de texto.

Para texto, expressões simples identificam indícios de números ou datas em valores de até 100 caracteres. São apenas indícios de formato, não validação de data, garantia de conversão ou inferência definitiva; códigos com zeros à esquerda podem parecer números. A base e seus tipos não são modificados. A interface informa os limites, o caráter parcial e que o perfil ainda não é enviado ao modelo. A seleção e o envio de informações do perfil pertencem à T04; amostras e estatísticas selecionadas poderão ser enviadas ao Ollama local em uma etapa futura, com limites e aviso explícitos.

O perfil é exibido em uma seção recolhida por padrão, para não ocupar espaço na tela principal. O cálculo continua disponível independentemente da apresentação.
