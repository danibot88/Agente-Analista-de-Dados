# Arquitetura do DataAgent

## Objetivo e escopo

O DataAgent recebe um CSV ou XLSX, apresenta o perfil da base e responde perguntas em português. O Ollama local gera SQL para DuckDB e, após a execução, uma interpretação fundamentada. O usuário pode conferir a tabela e o SQL. A primeira entrega cobre arquitetura, perfil e resposta; histórico, gráficos e escolha de aba são posteriores.

## Fluxo implementado

```text
Streamlit → leitura do arquivo → DataFrame → prévia e perfil limitado
Pergunta → análise
  ├─ Pergunta livre → Ollama → validação do SQL
  └─ Comando exato de moeda ou data → SQL montado pelo aplicativo
Ambos → DuckDB em memória → resultado limitado
  ├─ Resultado vazio → mensagem local
  └─ Resultado não vazio → Ollama seleciona linhas → aplicativo monta o texto
Interface → tabela, SQL, resposta e avisos conforme o resultado
```

Os dados recebidos do arquivo, a pergunta e o conteúdo produzido pelo modelo são entradas não confiáveis. O limite de linhas exibidas não garante, por si só, limite de custo de execução da consulta.

## Estrutura do projeto

```text
app_local.py                 Entrada Streamlit
iniciar_local.bat            Inicialização no Windows
dataagent/
  leitura.py                Leitura de CSV/XLSX
  perfil.py                 Perfil e diagnósticos de qualidade
  analise.py                Orquestração e contexto para geração de SQL
  modelo.py                 Cliente Ollama e validação das respostas do modelo
  politica.py               Política SQL e montagem dos planos controlados
  sql.py                    Validação e execução no DuckDB
  resposta.py               Contexto do resultado e montagem da resposta textual
tests/                      Testes automatizados
```

## Contratos dos componentes

- **Leitura:** recebe bytes, nome e opções de CSV. Retorna um DataFrame ou uma falha específica. O pandas pode inferir tipos na leitura.
- **Perfil:** recebe o DataFrame e calcula tipos, contagens, ausências e resumos em uma parcela limitada da base.
- **Geração SQL:** pergunta e perfil entram; SQL e explicação ou motivo para não responder saem. Respostas malformadas devem ser tratadas.
- **Execução:** validar uma única instrução de leitura com o parser do DuckDB, manter acesso externo desabilitado, registrar `uploaded_data` e fechar a conexão. Resultado deve carregar informação sobre truncamento. Avaliar e testar limites de execução; documentar o que não for possível garantir.
- **Interpretação:** pergunta, consulta e resultado efetivamente disponível entram; texto em português e avisos saem. Informar se somente parte do resultado foi enviada; não inventar conclusões.
- **Interface:** apresentar perfil, erros por etapa, resposta, dados e SQL, sem depender de regras de negócio espalhadas por componentes.

## Privacidade e validação

O Ollama roda localmente. Na geração de SQL, recebe a pergunta com os espaços das extremidades removidos e o perfil limitado. A aplicação não trunca a pergunta nessa etapa. Na seleção de linhas para a resposta, recebe um recorte do resultado e a pergunta limitada a 2.000 caracteres. Nomes, resumos e células enviados podem conter informações sensíveis. A suíte básica usa dados sintéticos e um cliente simulado. A integração opcional usa o Ollama local com um CSV sintético em memória.

## Serviços principais

O fluxo implementado é `app_local.py → leitura → análise → modelo / SQL → interface`. A interface conserva as opções e a prévia, e apresenta o resultado, o SQL e o aviso de truncamento. Os serviços não importam Streamlit:

- `dataagent/leitura.py`: `ler_arquivo(conteudo, nome, opcoes_csv)` recebe bytes, nome e opções do pandas para CSV e retorna um DataFrame. XLSX usa a primeira aba. Falhas geram `ErroLeitura`, com causa original encadeada; a interface mostra mensagem sem conteúdo da exceção. O DataFrame vazio é tratado pela interface.
- `dataagent/modelo.py`: `ClienteOllama.gerar_sql(mensagens)` consulta `llama3.2:latest` no Ollama local e retorna conteúdo bruto, SQL e explicação. Falhas de comunicação e JSON inválido geram `ErroModelo`. Em retentativas, a orquestração inclui a resposta bruta anterior do modelo e uma instrução fixa de correção. Para erros de consulta, a instrução usa a categoria do erro e omite a exceção bruta.
- `dataagent/sql.py`: `ExecutorSQL(dados)` abre DuckDB em memória com acesso externo desabilitado e registra `uploaded_data`. `executar(query, preservar_decimal=False)` usa o parser para exigir uma única instrução SELECT e retorna até 1.001 linhas. Problemas geram `ErroConsulta`. O gerenciador de contexto fecha a conexão ao sair, inclusive em caso de erro. Uma falha de registro também fecha a conexão aberta.
- `dataagent/analise.py`: `analisar(dados, pergunta, cliente=None, executor_factory=ExecutorSQL)` coordena até três tentativas. Retorna `ResultadoAnalise` com DataFrame de até 1.000 linhas, SQL e indicador de truncamento, ou aviso quando o modelo não fornece SQL. `ErroModelo` e `ErroConsulta` são tratados separadamente pela interface. Cliente e fábrica de executor podem ser substituídos em testes.

O SQL executado e a tabela permanecem disponíveis para conferência. O limite de linhas retornadas é independente dos limites de recursos descritos na T06.

## Perfil implementado na T03

`dataagent/perfil.py` expõe `gerar_perfil(DataFrame)`, que retorna um `Perfil` com totais, dimensões analisadas e uma lista de resumos por coluna. O cálculo examina no máximo as primeiras 1.000 linhas e 50 colunas; nomes exibidos são limitados a 100 caracteres mais reticências. As contagens de ausentes e não ausentes e os resumos referem-se apenas às linhas analisadas. Valores nulos do pandas são ausentes; texto vazio não é considerado ausente. Valores numéricos e datas têm mínimo e máximo; booleanos têm contagens de verdadeiro e falso. O perfil não mostra exemplos de texto.

Para texto, expressões simples identificam indícios de números ou datas em valores de até 100 caracteres. São apenas indícios de formato, não validação de data, garantia de conversão ou inferência definitiva; códigos com zeros à esquerda podem parecer números. A base e seus tipos não são modificados. A interface informa os limites e o caráter parcial. A seleção e o envio do perfil ao modelo são descritos na seção T04.

O perfil é exibido em uma seção recolhida por padrão, para não ocupar espaço na tela principal. O cálculo continua disponível independentemente da apresentação.

## Contexto e execução na T04

`analisar` envia a pergunta e o perfil limitado de T03 ao Ollama local: no máximo 1.000 linhas e 50 colunas no perfil, com nomes limitados, tipos, contagens, resumos numéricos ou de datas e indícios de formato. A lista de nomes é enviada separadamente dos metadados, na mesma ordem. O prompt orienta o modelo a incluir na projeção a coluna que identifica cada grupo. Não são enviadas amostras textuais pelo perfil, mas nomes, resumos e a própria pergunta podem ser sensíveis. A resposta JSON permite consulta simples, recusa ou planos controlados de soma por moeda e contagem por data; respostas inválidas são rejeitadas. A interface informa o contexto enviado.

`dataagent/politica.py` limita o SQL livre gerado a projeções e agregações simples, filtros textuais diretos de igualdade/desigualdade e testes de nulidade, COUNT DISTINCT e LIMIT de até 1.000. Junções, conversões arbitrárias e CTEs continuam bloqueadas. Com coluna de moeda reconhecida, somas e médias livres são recusadas. A detecção por nome é limitada, portanto não assegura reconhecer moeda em qualquer base. A execução continua usando o parser DuckDB e acesso externo desabilitado. Planos controlados constroem SQL internamente e exigem coluna única e parâmetros válidos; não eliminam identificadores repetidos. Soma monetária exige uma única coluna de moeda reconhecida, separa os grupos, não soma valores sem moeda e não aplica câmbio. Contagens globais de ausentes, inválidos e valores válidos sem moeda são calculadas antes do limite de exibição. Valores monetários em texto usam separador decimal explícito, sem separadores de milhares e com até seis casas decimais. Colunas numéricas tipadas são somadas no tipo disponível; o separador não se aplica, e infinitos são inválidos. Decimal é preservado e ponto flutuante pode ser aproximado. Datas em texto aceitam `AAAA-MM-DD`; colunas já tipadas como data ou datetime são agrupadas por dia, descartando o horário e usando o fuso original quando tipado. Objetos datetime com fuso em coluna genérica são recusados. Linhas ausentes ou sem conversão válida aparecem em grupo separado.

Operações controladas usam todas as linhas sem filtros; o modelo deve recusar perguntas que exijam filtros, mas pode interpretar a pergunta incorretamente. A interface informa o escopo e o formato efetivamente usado para conferência. A leitura de CSV ainda infere tipos e reconhece marcadores padrão como nulos, sem manter a distinção do marcador original. Verifique o resultado e o SQL; não há garantia de identificação semântica universal de moeda, nem tratamento automático de todos os formatos de data ou número.

### Garantia de escopo dos planos de conversão

Os planos `somar_por_moeda` e `contar_por_data` usam todas as linhas e não suportam filtros. `interpretar_comando_sem_filtro` reconhece os comandos exatos documentados no [README](../README.md#conversões-e-moedas). A soma também exige um separador decimal explícito. O aplicativo monta e executa o SQL desses comandos localmente. Depois da execução, um resultado não vazio segue para a seleção de linhas pelo Ollama. Se o modelo propuser um desses planos para uma pergunta livre, `confirma_operacao_sem_filtro` exige a correspondência com o comando exato, rejeita parâmetros extras e SQL contraditório. A interface informa a recusa quando a verificação falha. Confira se o SQL aceito corresponde à intenção da pergunta.

## Resposta fundamentada na T05

`dataagent/resposta.py` recebe pergunta, SQL e DataFrame resultante da execução, mais o indicador de truncamento. Resultado vazio gera mensagem local sem consultar o modelo. Para resultados não vazios, envia ao Ollama no máximo 10 linhas e 8 colunas, com até 120 caracteres por nome ou valor, 2.000 caracteres de pergunta e 4.000 de SQL. O cliente retorna somente índices de até três linhas; o serviço valida os índices e constrói o texto com as células disponíveis, sem reproduzir explicações livres do modelo. A seleção pode ser incompleta ou inadequada para a pergunta e não garante que o SQL corresponda à intenção do usuário.

A interface informa quando o resultado, o contexto ou o perfil usado para gerar SQL é parcial. Falha ou resposta inválida do modelo gera aviso, preservando tabela e SQL. O recorte do resultado é enviado ao Ollama antes da seleção dos índices. O limite de exibição e do contexto não limita o custo da consulta.

## Limites e verificação da T06

Cada `ExecutorSQL` configura o DuckDB com `memory_limit=256MB`, `threads=2`, `max_temp_directory_size=0B` e acesso externo desabilitado. O limite é da memória gerenciada pelo DuckDB e não é um teto para a memória total do processo: estruturas externas ao gerenciador, pandas, resultados materializados em Python, Streamlit e Ollama podem consumir memória adicional. Não há limite de tempo de consulta implementado. O limite de 1.001 linhas buscadas e 1.000 exibidas não limita o trabalho necessário para obter o resultado. Consultas de ordenação, agregação e contagem de valores distintos ainda podem exigir processamento relevante.

Uma exceção de memória do DuckDB recebe categoria `recursos`, interrompe as tentativas e gera mensagem específica na interface; conexões continuam fechadas pelo gerenciador de contexto. A suíte testa os valores de configuração, um esgotamento real com limite reduzido a 16 MB em dados sintéticos, a ausência de novas tentativas e a apresentação do erro. Não se presume que toda alocação do processo será interrompida nesse limite ou que toda consulta onerosa o atingirá.
