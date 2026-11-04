"""Interpretação limitada de resultados já executados."""
from dataclasses import dataclass

import pandas as pd
from pandas.api.types import is_scalar

from dataagent.modelo import ClienteOllama, ErroModelo

MAX_LINHAS = 10
MAX_COLUNAS = 8
MAX_VALOR = 120
MAX_PERGUNTA = 2000
MAX_SQL = 4000


@dataclass
class Resposta:
    texto: str = ''
    aviso: str = ''
    parcial: bool = False


def _texto(valor):
    if is_scalar(valor) and pd.isna(valor):
        return 'ausente', False
    texto = str(valor)
    return (texto[:MAX_VALOR] + '…', True) if len(texto) > MAX_VALOR else (texto, False)


def responder(pergunta, sql, dados, truncado=False, cliente=None):
    """Usa apenas pergunta, SQL e resultado; monta o texto a partir de células reais."""
    if dados.empty:
        return Resposta(texto='A consulta não retornou linhas.')
    parcial = (truncado or len(dados) > MAX_LINHAS or len(dados.columns) > MAX_COLUNAS
               or len(pergunta) > MAX_PERGUNTA or len(sql) > MAX_SQL)
    colunas = []
    for nome in dados.columns[:MAX_COLUNAS]:
        texto, cortado = _texto(nome)
        colunas.append(texto)
        parcial |= cortado
    linhas = []
    for linha in dados.iloc[:MAX_LINHAS, :MAX_COLUNAS].itertuples(index=False, name=None):
        valores = []
        for valor in linha:
            texto, cortado = _texto(valor)
            valores.append(texto)
            parcial |= cortado
        linhas.append(valores)
    contexto = {'pergunta': pergunta[:MAX_PERGUNTA], 'sql': sql[:MAX_SQL],
                'colunas': colunas, 'linhas': linhas, 'indices_permitidos': list(range(len(linhas))),
                'parcial': parcial}
    try:
        if cliente is None:
            cliente = ClienteOllama()
        indices = cliente.selecionar_linhas(contexto)
        if (not isinstance(indices, list) or not 1 <= len(indices) <= 3
                or any(type(i) is not int or not 0 <= i < len(linhas) for i in indices)
                or len(set(indices)) != len(indices)):
            raise ErroModelo('Seleção inválida.')
    except (ErroModelo, AttributeError):
        return Resposta(aviso='Não foi possível interpretar o resultado com o modelo; confira a tabela e o SQL.', parcial=parcial)
    trechos = ['; '.join(f'{nome}: {valor}' for nome, valor in zip(colunas, linhas[i])) for i in indices]
    return Resposta(texto='Linhas selecionadas do resultado:\n' + '\n'.join(trechos), parcial=parcial)
