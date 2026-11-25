"""Verificação conservadora e consultas de conversão previamente definidas."""
import json
from datetime import date, datetime
from decimal import Decimal

from pandas.api.types import (is_numeric_dtype, is_bool_dtype, is_string_dtype,
                              is_datetime64_any_dtype, is_float_dtype)

NOMES_MOEDA = {'currency', 'moeda', 'currency_code', 'codigo_moeda'}

from dataagent.sql import ErroConsulta


def _ident(nome):
    return '"' + nome.replace('"', '""') + '"'


def tipo_coluna_conversao(serie):
    """Identifica tipos nativos suportados sem converter os valores."""
    if is_datetime64_any_dtype(serie.dtype):
        return 'datetime'
    if is_bool_dtype(serie.dtype):
        return 'nao_suportado'
    if is_numeric_dtype(serie.dtype):
        return 'float' if is_float_dtype(serie.dtype) else 'numerico'
    if serie.dtype == object:
        valores = serie.dropna()
        if not valores.empty and all(isinstance(valor, date) and
                                     (not isinstance(valor, datetime) or valor.tzinfo is None)
                                     for valor in valores):
            return 'datetime' if any(isinstance(valor, datetime) for valor in valores) else 'data'
        if not valores.empty and all(isinstance(valor, Decimal) for valor in valores):
            return 'numerico'
        if any(not isinstance(valor, str) for valor in valores):
            return 'nao_suportado'
    return 'texto'


def interpretar_comando_sem_filtro(pergunta):
    """Interpreta apenas a sintaxe exata documentada, sem inferir intenção."""
    if not isinstance(pergunta, str):
        return None
    texto = pergunta.strip()
    decoder = json.JSONDecoder()

    def ler_string(posicao):
        valor, fim = decoder.raw_decode(texto, posicao)
        if not isinstance(valor, str):
            raise ValueError()
        return valor, fim

    try:
        if texto.startswith('somar '):
            coluna, pos = ler_string(len('somar '))
            if not texto[pos:].startswith(' por '):
                return None
            moeda, pos = ler_string(pos + len(' por '))
            if not texto[pos:].startswith(' decimal '):
                return None
            decimal, pos = ler_string(pos + len(' decimal '))
            plano = {'acao': 'somar_por_moeda', 'coluna': coluna, 'moeda': moeda, 'decimal': decimal, 'sql': '', 'explicacao': ''}
        elif texto.startswith('contar por data '):
            coluna, pos = ler_string(len('contar por data '))
            plano = {'acao': 'contar_por_data', 'coluna': coluna, 'sql': '', 'explicacao': ''}
        else:
            return None
        if texto[pos:] != ' em todas as linhas' or not confirma_operacao_sem_filtro(texto, plano):
            return None
        return plano
    except (ValueError, TypeError):
        return None


def confirma_operacao_sem_filtro(pergunta, plano):
    """Exige comando inequívoco e parâmetros idênticos para o escopo completo."""
    acao = plano.get('acao')
    comuns = {'acao', 'sql', 'explicacao', 'coluna'}
    if not isinstance(pergunta, str) or not isinstance(plano.get('coluna'), str):
        return False
    coluna = json.dumps(plano['coluna'], ensure_ascii=False)
    if plano.get('sql', '') != '':
        return False
    if acao == 'somar_por_moeda':
        if set(plano) - (comuns | {'moeda', 'decimal'}):
            return False
        if not isinstance(plano.get('moeda'), str) or plano.get('decimal') not in ('.', ','):
            return False
        moeda = json.dumps(plano['moeda'], ensure_ascii=False)
        decimal = json.dumps(plano['decimal'])
        esperado = f'somar {coluna} por {moeda} decimal {decimal} em todas as linhas'
    elif acao == 'contar_por_data':
        if set(plano) - comuns:
            return False
        esperado = f'contar por data {coluna} em todas as linhas'
    else:
        return False
    return pergunta.strip() == esperado


def consulta_conversao(plano, dados):
    acao = plano.get('acao')
    coluna = plano.get('coluna')
    if not isinstance(coluna, str) or list(dados.columns).count(coluna) != 1:
        raise ErroConsulta('Coluna inválida ou ambígua no plano de conversão.')
    c = _ident(coluna)
    serie = dados[coluna]
    tipo = tipo_coluna_conversao(serie)
    if acao == 'somar_por_moeda':
        moeda = plano.get('moeda')
        decimal = plano.get('decimal')
        if (not isinstance(moeda, str) or list(dados.columns).count(moeda) != 1 or moeda == coluna
                or moeda.strip().lower() not in NOMES_MOEDA
                or sum(str(c).strip().lower() in NOMES_MOEDA for c in dados.columns) != 1
                or decimal not in ('.', ',')):
            raise ErroConsulta('Informe uma coluna de moeda distinta e o separador decimal.')
        m = _ident(moeda)
        if tipo in ('numerico', 'float'):
            expr = f'CASE WHEN isfinite({c}) THEN {c} END' if tipo == 'float' else c
            ausente = 'original IS NULL'
            invalido = 'original IS NOT NULL AND convertido IS NULL'
        elif tipo == 'texto':
            separador = '[.]' if decimal == '.' else ','
            padrao = f'^[+-]?[0-9]+({separador}[0-9]{{1,6}})?$'
            expr = f"CASE WHEN regexp_full_match(trim({c}), '{padrao}') THEN TRY_CAST(replace(trim({c}), ',', '.') AS DECIMAL(38,6)) END"
            ausente = "original IS NULL OR trim(original) = ''"
            invalido = "original IS NOT NULL AND trim(original) <> '' AND convertido IS NULL"
        else:
            raise ErroConsulta('O tipo da coluna não é compatível com soma por moeda.')
        return (f'WITH base AS (SELECT {m} AS moeda, {c} AS original, {expr} AS convertido FROM uploaded_data) '
                "SELECT moeda, SUM(convertido) FILTER (WHERE moeda IS NOT NULL AND trim(moeda) <> '') AS total, COUNT(*) AS registros, "
                'COUNT(convertido) AS valores_validos, '
                "COUNT(*) FILTER (WHERE convertido IS NOT NULL AND (moeda IS NULL OR trim(moeda) = '')) AS valores_validos_sem_moeda, "
                f'COUNT(*) FILTER (WHERE {ausente}) AS valores_ausentes, '
                f'COUNT(*) FILTER (WHERE {invalido}) AS valores_invalidos '
                ' , SUM(COUNT(*)) OVER () AS total_registros, '
                f'SUM(COUNT(*) FILTER (WHERE {ausente})) OVER () AS total_ausentes, '
                f'SUM(COUNT(*) FILTER (WHERE {invalido})) OVER () AS total_invalidos, '
                "SUM(COUNT(*) FILTER (WHERE convertido IS NOT NULL AND (moeda IS NULL OR trim(moeda) = ''))) OVER () AS total_validos_sem_moeda "
                'FROM base GROUP BY moeda ORDER BY moeda')
    if acao == 'contar_por_data':
        if tipo in ('datetime', 'data'):
            fuso = getattr(serie.dtype, 'tz', None)
            local = f"timezone('{str(fuso).replace(chr(39), chr(39) * 2)}', {c})" if fuso is not None else c
            expr = f'CAST({local} AS DATE)'
            ausente = 'original IS NULL'
            invalido = 'original IS NOT NULL AND convertido IS NULL'
        elif tipo == 'texto':
            expr = f"CASE WHEN regexp_full_match(trim({c}), '[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}') THEN TRY_CAST({c} AS DATE) END"
            ausente = "original IS NULL OR trim(original) = ''"
            invalido = "original IS NOT NULL AND trim(original) <> '' AND convertido IS NULL"
        else:
            raise ErroConsulta('O tipo da coluna não é compatível com contagem por data.')
        return (f'WITH base AS (SELECT {c} AS original, {expr} AS convertido FROM uploaded_data) '
                'SELECT convertido AS data, COUNT(*) AS registros, '
                f'COUNT(*) FILTER (WHERE {ausente}) AS valores_ausentes, '
                f'COUNT(*) FILTER (WHERE {invalido}) AS valores_invalidos '
                ' , SUM(COUNT(*)) OVER () AS total_registros, '
                f'SUM(COUNT(*) FILTER (WHERE {ausente})) OVER () AS total_ausentes, '
                f'SUM(COUNT(*) FILTER (WHERE {invalido})) OVER () AS total_invalidos '
                'FROM base GROUP BY convertido ORDER BY convertido')
    raise ErroConsulta('Operação de conversão não suportada.')


def validar_sql_simples(conn, sql, dados):
    """Aceita operações verificáveis, sem conversões implícitas em filtros."""
    try:
        doc = json.loads(conn.execute('SELECT json_serialize_sql(?)', [sql]).fetchone()[0])
        if doc.get('error') or len(doc['statements']) != 1:
            raise ValueError()
        node = doc['statements'][0]['node']
        tabela = node['from_table']
        if (node['type'] != 'SELECT_NODE' or tabela['type'] != 'BASE_TABLE'
                or tabela['table_name'].lower() != 'uploaded_data'
                or tabela.get('schema_name') or tabela.get('catalog_name')
                or node['cte_map']['map'] or node.get('having')
                or node.get('qualify') or node.get('sample') or tabela.get('sample')):
            raise ValueError()
        moedas = any(str(c).strip().lower() in NOMES_MOEDA for c in dados.columns)
        def coluna(expr):
            nomes = expr.get('column_names', [])
            return expr.get('class') == 'COLUMN_REF' and len(nomes) == 1
        def filtro(expr):
            if expr.get('class') == 'CONJUNCTION' and expr.get('type') in ('CONJUNCTION_AND', 'CONJUNCTION_OR'):
                filhos = expr.get('children', [])
                return bool(filhos) and all(filtro(filho) for filho in filhos)
            if expr.get('class') == 'OPERATOR' and expr.get('type') in ('OPERATOR_IS_NULL', 'OPERATOR_IS_NOT_NULL'):
                filhos = expr.get('children', [])
                return len(filhos) == 1 and coluna(filhos[0])
            if expr.get('class') != 'COMPARISON' or expr.get('type') not in ('COMPARE_EQUAL', 'COMPARE_NOTEQUAL'):
                return False
            left, right = expr.get('left', {}), expr.get('right', {})
            if not coluna(left):
                left, right = right, left
            if not coluna(left) or right.get('class') != 'CONSTANT' or right.get('literal', {}).get('kind') != 'STRING':
                return False
            nome = left['column_names'][0]
            if list(dados.columns).count(nome) != 1 or not is_string_dtype(dados[nome].dtype):
                return False
            return all(isinstance(valor, str) for valor in dados[nome].dropna())
        if node.get('where_clause') and not filtro(node['where_clause']):
            raise ValueError()
        def expressao(expr, agregado=True):
            if coluna(expr):
                return True
            if expr.get('class') == 'STAR':
                return not (expr.get('exclude_list') or expr.get('replace_list') or expr.get('expr') or expr.get('columns'))
            if agregado and expr.get('class') == 'FUNCTION':
                nome = expr.get('function_name', '').lower()
                args = expr.get('arguments', [])
                # DuckDB representa COUNT(*) como count_star sem argumentos.
                if nome == 'count_star':
                    return not args and not expr.get('filter') and not expr.get('distinct')
                if nome not in ('sum', 'avg', 'min', 'max', 'count') or expr.get('filter') or (expr.get('distinct') and nome != 'count') or len(args) != 1:
                    return False
                arg = args[0]['expression']
                if nome == 'count' and arg.get('class') == 'STAR':
                    return True
                if not coluna(arg):
                    return False
                if nome in ('sum', 'avg'):
                    if list(dados.columns).count(arg['column_names'][0]) != 1:
                        return False
                    serie = dados[arg['column_names'][0]]
                    return not moedas and is_numeric_dtype(serie.dtype) and not is_bool_dtype(serie.dtype)
                return True
            return False
        if not all(expressao(x) for x in node['select_list']):
            raise ValueError()
        if not all(coluna(x) for x in node['group_expressions']):
            raise ValueError()
        for mod in node['modifiers']:
            if mod['type'] == 'DISTINCT_MODIFIER' and not mod.get('distinct_on_targets'):
                continue
            if mod['type'] == 'LIMIT_MODIFIER':
                limite = mod.get('limit', {})
                literal = limite.get('literal', {})
                if (mod.get('offset') is None and mod.get('limit_type') == 'ROW_COUNT'
                        and limite.get('class') == 'CONSTANT' and literal.get('kind') == 'INTEGER'
                        and 0 <= int(literal.get('text', '-1')) <= 1000):
                    continue
            if mod['type'] != 'ORDER_MODIFIER' or not all(coluna(x['expression']) for x in mod['orders']):
                raise ValueError()
    except Exception as exc:
        raise ErroConsulta('Consulta fora do conjunto verificável. Use uma operação suportada ou esclareça a pergunta.', 'politica') from exc
