# Analista de dados com Ollama

Aplicativo local para fazer perguntas em português sobre dados de arquivos CSV ou Excel. O aplicativo usa Streamlit para a interface, Ollama com o modelo `llama3.2:latest` para criar consultas SQL e DuckDB para executá-las em memória. Não é necessária uma chave de API.

## Imagens do aplicativo

Prévia dos dados e pergunta sobre o arquivo de exemplo:

![Prévia do arquivo de exemplo e campo para fazer uma pergunta](images/screenshot1.png)

Resultado da análise e consulta SQL utilizada:

![Resultado do total de vendas por produto e consulta SQL](images/screenshot2.png)

## Requisitos

- Python instalado e disponível no terminal (instalação testada com Python 3.14).
- Ollama instalado e em execução.
- Modelo `llama3.2` baixado no Ollama.
- Conexão com a internet para instalar as bibliotecas e baixar o modelo na primeira utilização.
- Memória suficiente para carregar os dados e executar o modelo.

Para baixar o modelo, execute uma vez no terminal:

```powershell
ollama pull llama3.2
```

## Executar no Windows

1. Abra o Ollama e mantenha-o em execução.
2. Dê dois cliques em `iniciar_local.bat`. Na primeira execução, ele cria um ambiente virtual `.venv` na pasta do projeto e instala as dependências.
3. Mantenha a janela do terminal aberta enquanto usa o aplicativo. O navegador deve abrir automaticamente.
4. Envie um arquivo CSV ou XLSX e faça uma pergunta sobre os dados.

## Executar pelo terminal

No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements_local.txt
.\.venv\Scripts\python.exe -m streamlit run app_local.py --server.address localhost
```

O Ollama deve estar em execução antes de enviar uma pergunta. Para conferir os modelos disponíveis, use `ollama list`.

## Exemplo

Envie o arquivo `exemplo.csv`. Em **Configurações do CSV**, escolha `;` como separador e `,` como separador decimal. Pergunte: “Qual o total de vendas por produto?”

O resultado esperado é **Café: 220,50** e **Chá: 80,00**.

## Estado do projeto

A entrega inicial do plano, tarefas T01 a T06, está concluída: o aplicativo possui serviços separados, perfil limitado, geração e execução de SQL, resposta baseada em linhas do resultado e limites de recursos no DuckDB. A resposta textual é uma seleção de linhas, não uma interpretação completa garantida. O plano e as evidências estão em [TASKS.md](TASKS.md), [docs/ARQUITETURA.md](docs/ARQUITETURA.md) e [docs/TESTES.md](docs/TESTES.md).

Estão pendentes a seleção de aba Excel (T07), o histórico de perguntas por base (T08) e gráficos e exportação (T09). A ordem de implementação dessas funcionalidades ainda depende de priorização. O fluxo integrado com Ollama foi verificado por script com o CSV de exemplo. O teste manual no navegador ficou para uma rodada posterior.

## Como funciona e limitações

- O aplicativo lê a primeira aba de arquivos Excel. A prévia mostra até 100 linhas, mas as consultas usam todas as linhas carregadas.
- Para CSV, é possível ajustar o separador, a codificação e o separador decimal.
- O perfil examina as primeiras 1.000 linhas e 50 colunas, mostrando tipos, ausências, resumos e possíveis números ou datas em texto. Esses indícios não alteram os dados nem garantem que a conversão seja correta. Nomes no perfil são limitados a 100 caracteres.
- O perfil fica em uma seção recolhida. Quando o Ollama gera SQL, ele recebe a pergunta e o perfil limitado, incluindo nomes, tipos, contagens e resumos numéricos ou de datas, mas não exemplos de texto. Esses dados podem ser sensíveis.
- Cada pergunta é independente. A consulta gerada é limitada a projeções, contagens e agregações simples, com filtros textuais diretos e sem conversões arbitrárias; solicitações incompatíveis podem ser recusadas.
- Após executar a consulta, o aplicativo pede ao Ollama que selecione até três linhas e monta a resposta com os valores efetivamente retornados. A seleção pode não responder completamente à pergunta; confira a tabela e o SQL.
- Para essa seleção, são enviados ao Ollama local a pergunta (até 2.000 caracteres), o SQL (até 4.000), os nomes e valores de até 10 linhas e 8 colunas do resultado (até 120 caracteres por campo). O aplicativo avisa quando o contexto ou resultado é parcial. Esses dados podem ser sensíveis.
- As consultas são executadas em um banco DuckDB em memória. O aplicativo limita a exibição a 1.000 linhas de resultado.
- Cada conexão DuckDB é configurada com `memory_limit` de 256 MB, até duas threads e tamanho máximo de arquivos temporários de 0 bytes. Se o DuckDB informar falta de memória, a análise é interrompida e a interface mostra um erro específico.
- Esse limite cobre a memória gerenciada pelo DuckDB, não o consumo total do processo, os arquivos carregados pelo pandas ou o Ollama. Não há limite de tempo de execução das consultas; consultas caras ainda podem demorar ou consumir outros recursos.
- A IA pode cometer erros; confira a consulta exibida e valide resultados importantes, especialmente números e datas.
- O `.gitignore` exclui planilhas e CSVs locais por padrão, com exceção de `exemplo.csv`, para ajudar a evitar a inclusão acidental de dados privados no Git.

## Conversões e moedas

Os dois planos de conversão ainda não implementam filtros. Para impedir que uma pergunta filtrada seja executada sobre a tabela inteira, eles só são executados com um dos comandos exatos abaixo; ajuste os nomes e o separador, mantendo as aspas duplas:

```text
somar "valor" por "moeda" decimal "." em todas as linhas
contar por data "data" em todas as linhas
```

Esses comandos geram e executam o SQL sem depender do modelo; a seleção de linhas para a resposta textual usa o Ollama. Perguntas livres ou filtradas que gerem esses planos são recusadas. Consultas SQL simples continuam usando o modelo: a validação de segurança não garante que o SQL expresse corretamente todos os filtros pedidos em linguagem natural; confira a consulta exibida.

Para somar uma coluna monetária em texto, o plano controlado exige uma única coluna de moeda reconhecida (`currency`, `moeda`, `currency_code` ou `codigo_moeda`) e um separador decimal explícito. A operação usa todas as linhas, sem filtros, agrupa as moedas como aparecem e não converte câmbio. Valores com moeda ausente não são somados; identificadores repetidos não são removidos. A tabela e o aviso informam contagens de valores inválidos, ausentes e válidos sem moeda. Para valores em texto, aceitam-se até seis casas decimais e não se aceita separador de milhares; formatos diferentes são contados como inválidos. Colunas já numéricas são somadas no tipo disponível, sem aplicar o separador informado; ponto flutuante pode produzir valores aproximados e infinitos são contados como inválidos. Não há normalização de códigos de moeda.

A contagem por data aceita colunas de data ou datetime já tipadas e texto no formato `AAAA-MM-DD`, mantendo ausentes e inválidos em um grupo separado. Para datetime, agrupa pelo dia e desconsidera o horário; colunas com fuso tipado usam o dia no fuso original. Objetos datetime com fuso em coluna de tipo genérico não são suportados. Essas operações usam apenas os planos controlados; conversões arbitrárias em SQL gerado são recusadas. Planos de conversão com filtros ou formatos diferentes precisam de outra abordagem. A identificação de moeda depende dos nomes reconhecidos e não compreende automaticamente todas as semânticas de uma base. Confira o SQL e os resultados; o modelo pode escolher uma coluna ou formato inadequado.

Na leitura de CSV, pandas infere tipos e reconhece marcadores padrão como ausentes; esses marcadores não podem ser distinguidos depois da leitura. O limite de exibição é de 1.000 linhas; as contagens globais das conversões permanecem disponíveis mesmo se os grupos forem truncados.

## Comportamento atual e testes

O CSV é lido com pandas: o separador pode ser automático, `;`, `,` ou tabulação; a codificação pode ser `utf-8-sig`, `cp1252` ou `latin-1`; o separador decimal pode ser `.` ou `,`. As opções padrão são automático, `utf-8-sig` e `.`. O XLSX é lido pela primeira aba, com `openpyxl`, sem opção de seleção de aba. Todo o arquivo é carregado em memória; a prévia mostra até 100 linhas. A consulta usa a tabela completa `uploaded_data` e exibe até 1.000 linhas do resultado.

Um arquivo lido sem linhas de dados gera um aviso; um arquivo CSV totalmente vazio, codificação incompatível ou XLSX inválido pode gerar erro de leitura. A interface apresenta mensagens específicas para falhas de leitura, modelo e consulta sem exibir o texto das exceções. Se a interpretação falhar, o resultado e o SQL permanecem disponíveis. Na análise, o modelo tem até três tentativas de consulta, e o DuckDB valida uma única instrução de leitura com acesso externo desabilitado. O limite de exibição não limita o custo da consulta.

Para executar os testes automatizados no PowerShell, após instalar as dependências do projeto na `.venv`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes usam arquivos sintéticos e o `exemplo.csv`, simulam a interface e o cliente Ollama, verificam os serviços isoladamente e executam consultas no DuckDB real. Não exigem o serviço Ollama. Eles não substituem uma verificação manual no navegador com o modelo local.

Para a verificação opcional com `llama3.2:latest` no Ollama e a planilha local esperada em `dados_locais`, execute:

```powershell
$env:DATAAGENT_TESTE_OLLAMA = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_ollama_local.py -v
Remove-Item Env:DATAAGENT_TESTE_OLLAMA
```

O teste lê a planilha sem modificá-la, verifica as contagens e o SQL executado e exige o arquivo e o serviço locais. Os dados são enviados ao processo Ollama conforme o perfil documentado; o teste padrão permanece independente do serviço.
