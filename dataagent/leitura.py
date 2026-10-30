"""Leitura de arquivos recebidos pela interface."""
from io import BytesIO

import pandas as pd


class ErroLeitura(Exception):
    """Não foi possível interpretar o arquivo fornecido."""


def ler_arquivo(conteudo, nome, opcoes_csv=None):
    try:
        dados = BytesIO(conteudo)
        if nome.lower().endswith('.csv'):
            return pd.read_csv(dados, engine='python', **(opcoes_csv or {}))
        if nome.lower().endswith('.xlsx'):
            return pd.read_excel(dados, engine='openpyxl')
        raise ValueError('Formato não suportado')
    except Exception as exc:
        raise ErroLeitura('Não foi possível ler o arquivo.') from exc
