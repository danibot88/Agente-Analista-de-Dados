"""Execução de uma consulta de leitura no DuckDB isolado."""
import duckdb
import pandas as pd


MOTIVOS_CORRECAO = {
    'sintaxe': 'Há um erro de sintaxe SQL. Revise a estrutura da consulta para DuckDB.',
    'referencia': ('Não foi possível resolver uma referência ou expressão SQL. '
                   'Confira tabela, colunas, funções e agregações disponíveis.'),
    'conversao': 'Uma conversão de tipos falhou. Confira a compatibilidade dos tipos usados na consulta.',
    'restricao': 'A consulta deve conter uma única instrução SELECT de leitura.',
    'politica': 'A operação solicitada não pode ser verificada com segurança. Use um plano de conversão suportado ou explique a impossibilidade.',
    'execucao': 'A consulta não pôde ser executada. Revise os tipos e as operações utilizadas.',
}


class ErroConsulta(Exception):
    """Falha SQL com categoria segura para orientar uma nova tentativa."""

    def __init__(self, mensagem, categoria='execucao'):
        super().__init__(mensagem)
        self.categoria = categoria if categoria in MOTIVOS_CORRECAO else 'execucao'

    @property
    def motivo_correcao(self):
        return MOTIVOS_CORRECAO[self.categoria]


class ExecutorSQL:
    def __init__(self, dados):
        self.conn = None
        try:
            self.conn = duckdb.connect(database=':memory:', config={'enable_external_access': 'false'})
            self.conn.register('uploaded_data', dados)
        except Exception as exc:
            if self.conn is not None:
                self.conn.close()
            raise ErroConsulta('Não foi possível preparar os dados para consulta.') from exc

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.conn.close()

    def executar(self, query, preservar_decimal=False):
        try:
            statements = self.conn.extract_statements(query)
            if len(statements) != 1 or statements[0].type != duckdb.StatementType.SELECT:
                raise ErroConsulta('A consulta precisa ser um único SELECT.', 'restricao')
            resultado = self.conn.execute('SELECT * FROM (' + query + ') AS resultado LIMIT 1001')
            if preservar_decimal:
                return pd.DataFrame(resultado.fetchall(), columns=[coluna[0] for coluna in resultado.description])
            return resultado.df()
        except ErroConsulta:
            raise
        except duckdb.ParserException as exc:
            raise ErroConsulta('A consulta é inválida ou não pôde ser executada.', 'sintaxe') from exc
        except (duckdb.BinderException, duckdb.CatalogException) as exc:
            raise ErroConsulta('A consulta é inválida ou não pôde ser executada.', 'referencia') from exc
        except duckdb.ConversionException as exc:
            raise ErroConsulta('A consulta é inválida ou não pôde ser executada.', 'conversao') from exc
        except Exception as exc:
            raise ErroConsulta('A consulta é inválida ou não pôde ser executada.') from exc
