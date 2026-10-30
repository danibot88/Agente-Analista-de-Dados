from io import BytesIO
import json

import duckdb
import pandas as pd
import streamlit as st
from ollama import Client

st.set_page_config(page_title="Analista de dados", page_icon="📊", layout="wide")
st.title("📊 Analista de dados")
st.write("Envie um arquivo CSV ou Excel e faça perguntas sobre seus dados.")

st.caption("A análise usa o modelo llama3.2 no Ollama do seu computador. Não é necessária chave de API.")

uploaded = st.file_uploader("Arquivo de dados", type=["csv", "xlsx"])
if uploaded is None:
    st.info("Envie um arquivo para começar.")
    st.stop()

csv_options = {}
if uploaded.name.lower().endswith(".csv"):
    with st.expander("Configurações do CSV", expanded=False):
        separator = st.selectbox("Separador", ["Automático", ";", ",", "Tabulação"])
        encoding = st.selectbox("Codificação", ["utf-8-sig", "cp1252", "latin-1"])
        decimal = st.selectbox("Separador decimal", [".", ","])
    csv_options = {"sep": {"Automático": None, "Tabulação": "\t"}.get(separator, separator),
                   "encoding": encoding, "decimal": decimal}

try:
    data = BytesIO(uploaded.getvalue())
    if uploaded.name.lower().endswith(".csv"):
        df = pd.read_csv(data, engine="python", **csv_options)
    else:
        df = pd.read_excel(data, engine="openpyxl")
    if df.empty or len(df.columns) == 0:
        st.warning("O arquivo não contém linhas de dados para analisar.")
        st.stop()
except Exception as exc:
    st.error(f"Não foi possível ler o arquivo: {exc}")
    st.info("Se for CSV, confira o separador, a codificação e o separador decimal nas configurações acima.")
    st.stop()

st.subheader("Prévia dos dados")
st.dataframe(df.head(100), width="stretch")
st.caption(f"{len(df):,} linhas e {len(df.columns)} colunas. A prévia mostra até 100 linhas; as consultas usam a tabela completa.")
st.write("Colunas:", ", ".join(map(str, df.columns)))

with st.form("pergunta"):
    question = st.text_area("O que você deseja saber sobre os dados?", placeholder="Ex.: Qual é a média de vendas por produto?")
    submitted = st.form_submit_button("Analisar")

if submitted:
    if not question.strip():
        st.warning("Digite uma pergunta antes de analisar.")
    else:
        conn = None
        try:
            with st.spinner("Analisando os dados..."):
                conn = duckdb.connect(database=":memory:", config={"enable_external_access": "false"})
                conn.register("uploaded_data", df)
                client = Client(host="http://localhost:11434", trust_env=False, timeout=180)
                columns = [{"nome": str(name), "tipo": str(dtype)} for name, dtype in df.dtypes.items()]
                schema = {
                    "type": "object",
                    "properties": {"sql": {"type": "string"}, "explicacao": {"type": "string"}},
                    "required": ["sql", "explicacao"],
                }
                messages = [
                    {"role": "system", "content": (
                        "Você converte perguntas em uma única consulta SQL de leitura para DuckDB. "
                        "A única tabela disponível chama-se uploaded_data. Use os nomes de coluna exatos, "
                        "entre aspas duplas. Não invente colunas ou valores. Não use arquivos externos. "
                        "Retorne JSON com sql e uma explicação curta em português. "
                        "Se a pergunta não puder ser respondida com as colunas, deixe sql vazio e explique."
                    )},
                    {"role": "user", "content": "Colunas e tipos: " + json.dumps(columns, ensure_ascii=False) + "\nPergunta: " + question.strip()},
                ]
                last_error = None
                for _ in range(3):
                    response = client.chat(model="llama3.2:latest", messages=messages, format=schema, options={"temperature": 0})
                    raw = response.message.content or "{}"
                    result = json.loads(raw)
                    query = str(result.get("sql", "")).strip().rstrip(";").strip()
                    explanation = str(result.get("explicacao", ""))
                    if not query:
                        st.warning(explanation or "Não consegui montar uma consulta para essa pergunta.")
                        break
                    try:
                        statements = conn.extract_statements(query)
                        if len(statements) != 1 or statements[0].type != duckdb.StatementType.SELECT:
                            raise ValueError("A consulta precisa ser um único SELECT.")
                        result_df = conn.execute("SELECT * FROM (" + query + ") AS resultado LIMIT 1001").df()
                        st.subheader("Resultado")
                        st.dataframe(result_df.head(1000), width="stretch")
                        if len(result_df) > 1000:
                            st.caption("Exibindo as primeiras 1.000 linhas do resultado.")
                        with st.expander("Ver consulta usada"):
                            st.code(query, language="sql")
                        break
                    except Exception as query_error:
                        last_error = str(query_error)
                        messages.extend([
                            {"role": "assistant", "content": raw},
                            {"role": "user", "content": "A consulta falhou: " + last_error + ". Corrija o SQL usando os nomes exatos das colunas."},
                        ])
                else:
                    st.error("Não consegui executar a consulta gerada: " + (last_error or "erro desconhecido"))
        except Exception as exc:
            st.error(f"Não foi possível concluir a análise: {exc}")
            st.info("Verifique se o Ollama está aberto e se o modelo llama3.2 está instalado. Confira também os formatos dos dados.")
        finally:
            if conn is not None:
                conn.close()
