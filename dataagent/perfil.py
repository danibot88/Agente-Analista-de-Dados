"""Perfil limitado de dados, sem alterar a base de entrada."""
from dataclasses import dataclass
import re

from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_numeric_dtype

MAX_LINHAS = 1000
MAX_COLUNAS = 50
MAX_NOME = 100
MAX_TEXTO = 100
NUMERO = re.compile(r'^[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)$')
DATA = re.compile(r'^(?:\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})$')


@dataclass
class Perfil:
    linhas_totais: int
    colunas_totais: int
    linhas_analisadas: int
    colunas_analisadas: int
    colunas: list


def gerar_perfil(dados):
    amostra = dados.iloc[:MAX_LINHAS, :MAX_COLUNAS]
    colunas = []
    for posicao in range(amostra.shape[1]):
        serie = amostra.iloc[:, posicao]
        nome = str(dados.columns[posicao])
        nao_nulos = serie.dropna()
        resumo = ''
        indicios = []
        if is_bool_dtype(serie.dtype):
            resumo = f'Verdadeiro: {int((nao_nulos == True).sum())}; falso: {int((nao_nulos == False).sum())}'
        elif is_numeric_dtype(serie.dtype) and not nao_nulos.empty:
            resumo = f'Mínimo: {nao_nulos.min()}; máximo: {nao_nulos.max()}'
        elif is_datetime64_any_dtype(serie.dtype) and not nao_nulos.empty:
            resumo = f'Mínimo: {nao_nulos.min()}; máximo: {nao_nulos.max()}'
        elif not is_numeric_dtype(serie.dtype) and not is_datetime64_any_dtype(serie.dtype):
            numeros = datas = 0
            for valor in nao_nulos:
                if not isinstance(valor, str):
                    continue
                texto = valor.strip()
                if len(texto) <= MAX_TEXTO:
                    numeros += bool(NUMERO.fullmatch(texto))
                    datas += bool(DATA.fullmatch(texto))
            if numeros:
                indicios.append(f'{numeros} possível(is) número(s) como texto')
            if datas:
                indicios.append(f'{datas} possível(is) data(s) como texto')
        colunas.append({
            'Coluna': nome if len(nome) <= MAX_NOME else nome[:MAX_NOME] + '…',
            'Tipo': str(serie.dtype),
            'Não ausentes': int(serie.notna().sum()),
            'Ausentes': int(serie.isna().sum()),
            'Resumo': resumo,
            'Indícios': '; '.join(indicios),
        })
    return Perfil(len(dados), dados.shape[1], len(amostra), amostra.shape[1], colunas)
