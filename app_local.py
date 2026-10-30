import pandas as pd
import streamlit as st

from dataagent.analise import analisar
from dataagent.leitura import ErroLeitura, ler_arquivo
from dataagent.modelo import ErroModelo
from dataagent.perfil import gerar_perfil
from dataagent.sql import ErroConsulta

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
    df = ler_arquivo(uploaded.getvalue(), uploaded.name, csv_options)
except ErroLeitura:
    st.error("Não foi possível ler o arquivo: formato ou conteúdo inválido.")
    st.info("Se for CSV, confira o separador, a codificação e o separador decimal nas configurações acima.")
    st.stop()

if df.empty or len(df.columns) == 0:
    st.warning("O arquivo não contém linhas de dados para analisar.")
    st.stop()

st.subheader("Prévia dos dados")
st.dataframe(df.head(100), width="stretch")
st.caption(f"{len(df):,} linhas e {len(df.columns)} colunas. A prévia mostra até 100 linhas; as consultas usam a tabela completa.")
if uploaded.name.lower().endswith('.csv'):
    st.caption('Na leitura CSV, o pandas infere tipos e reconhece células vazias e marcadores padrão como ausentes; esses marcadores não podem ser diferenciados depois da leitura.')
st.write("Colunas:", ", ".join(map(str, df.columns)))

perfil = gerar_perfil(df)
with st.expander("Perfil e qualidade dos dados", expanded=False):
    st.caption(
        f"Perfil das primeiras {perfil.linhas_analisadas:,} de {perfil.linhas_totais:,} linhas "
        f"e {perfil.colunas_analisadas:,} de {perfil.colunas_totais:,} colunas. "
        "Contagens, resumos e indícios usam somente essa parcela; células vazias em texto não são contadas como ausentes. "
        "Indícios não confirmam o tipo e não alteram os dados."
    )
    st.dataframe(pd.DataFrame(perfil.colunas), width="stretch")
    st.caption(
        "Quando usado, o Ollama local recebe a pergunta e o perfil limitado, incluindo nomes, tipos, contagens e resumos numéricos ou de datas. "
        "O perfil não contém exemplos de texto; dados enviados ainda podem ser sensíveis."
    )

with st.form("pergunta"):
    question = st.text_area("O que você deseja saber sobre os dados?", placeholder="Ex.: Qual é a média de vendas por produto?")
    submitted = st.form_submit_button("Analisar")

if submitted:
    if not question.strip():
        st.warning("Digite uma pergunta antes de analisar.")
    else:
        try:
            with st.spinner("Analisando os dados..."):
                resultado = analisar(df, question)
            if resultado.aviso:
                st.warning(resultado.aviso)
            else:
                st.subheader("Resultado")
                st.caption(resultado.limitacoes)
                st.dataframe(resultado.dados, width="stretch")
                if resultado.truncado:
                    st.caption("Exibindo as primeiras 1.000 linhas do resultado.")
                with st.expander("Ver consulta usada"):
                    st.code(resultado.sql, language="sql")
        except ErroModelo:
            st.error("Não foi possível obter uma resposta válida do modelo.")
            st.info("Verifique se o Ollama está aberto e se o modelo llama3.2 está instalado.")
        except ErroConsulta:
            st.error("Não foi possível preparar ou executar a consulta gerada.")
            st.info("Confira a pergunta e os formatos dos dados e tente novamente.")
