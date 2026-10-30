"""Coordenação da geração e execução de consultas."""
from dataclasses import dataclass
import json

import pandas as pd

from dataagent.modelo import ClienteOllama
from dataagent.sql import ErroConsulta, ExecutorSQL


@dataclass
class ResultadoAnalise:
    dados: pd.DataFrame | None = None
    sql: str = ''
    aviso: str = ''
    truncado: bool = False


def analisar(dados, pergunta, cliente=None, executor_factory=ExecutorSQL):
    columns = [{'nome': str(name), 'tipo': str(dtype)} for name, dtype in dados.dtypes.items()]
    messages = [
        {'role': 'system', 'content': (
            'Você converte perguntas em uma única consulta SQL de leitura para DuckDB. '
            'A única tabela disponível chama-se uploaded_data. Use os nomes de coluna exatos, '
            'entre aspas duplas. Não invente colunas ou valores. Não use arquivos externos. '
            'Retorne JSON com sql e uma explicação curta em português. '
            'Se a pergunta não puder ser respondida com as colunas, deixe sql vazio e explique.'
        )},
        {'role': 'user', 'content': 'Colunas e tipos: ' + json.dumps(columns, ensure_ascii=False) + '\nPergunta: ' + pergunta.strip()},
    ]
    with executor_factory(dados) as executor:
        if cliente is None:
            cliente = ClienteOllama()
        for _ in range(3):
            raw, query, explanation = cliente.gerar_sql(messages)
            if not query:
                return ResultadoAnalise(aviso=explanation or 'Não consegui montar uma consulta para essa pergunta.')
            try:
                resultado = executor.executar(query)
                return ResultadoAnalise(dados=resultado.head(1000), sql=query, truncado=len(resultado) > 1000)
            except ErroConsulta as erro:
                messages.extend([
                    {'role': 'assistant', 'content': raw},
                    {'role': 'user', 'content': 'A consulta falhou. ' + erro.motivo_correcao + ' Corrija o SQL usando os nomes exatos das colunas.'},
                ])
        raise ErroConsulta('Não consegui executar a consulta gerada após três tentativas.')
