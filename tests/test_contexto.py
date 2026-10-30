import json
import unittest
from decimal import Decimal
from datetime import date, datetime
from io import BytesIO

import pandas as pd

from dataagent.analise import analisar
from dataagent.modelo import ErroModelo, ClienteOllama
from dataagent.leitura import ler_arquivo
from dataagent.politica import confirma_operacao_sem_filtro
from dataagent.sql import ErroConsulta, ExecutorSQL


class Modelo:
    def __init__(self, plano):
        self.plano = plano
        self.mensagens = None

    def gerar_sql(self, mensagens):
        self.mensagens = mensagens
        raw = json.dumps(self.plano)
        return raw, self.plano.get('sql', ''), self.plano.get('explicacao', '')


class ContextoTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            'id': ['a', 'a', 'b', 'c', 'd', 'e'],
            'moeda': ['BRL', 'BRL', 'USD', 'USD', 'USD', None],
            'valor': ['10.50', '2.50', '9.00', 'invalido', None, '5.00'],
            'data': ['2025-01-01', '2025-01-01', '2025-02-02', '2025-99-99', None, '2025-01-01'],
        })

    def test_contagem_de_linhas_e_agrupamento_com_count_asterisco(self):
        modelo = Modelo({'sql': 'SELECT COUNT(*) AS total FROM uploaded_data', 'explicacao': ''})
        total = analisar(self.df, 'Quantas linhas?', modelo)
        self.assertEqual(6, total.dados.iloc[0]['total'])
        self.assertIn('Perfil limitado', modelo.mensagens[1]['content'])
        self.assertNotIn('invalido', modelo.mensagens[1]['content'])
        grupos = analisar(self.df, 'Contar por moeda', Modelo({'sql': 'SELECT moeda, COUNT(*) AS total FROM uploaded_data GROUP BY moeda ORDER BY total DESC', 'explicacao': ''}))
        self.assertEqual(6, grupos.dados['total'].sum())

    def test_conversao_sem_filtro_recusa_perguntas_filtradas_ou_ambiguas(self):
        plano = {'acao': 'somar_por_moeda', 'coluna': 'valor', 'moeda': 'moeda', 'decimal': '.', 'sql': '', 'explicacao': ''}
        perguntas = [
            'Some valor por moeda apenas para BRL',
            'Some valor por moeda excluindo BRL',
            'Somar por moeda',
            'somar "valor" por "moeda" decimal "." em todas as linhas, exceto BRL',
        ]
        for pergunta in perguntas:
            consultas = []
            class ExecutorMonitorado(ExecutorSQL):
                def executar(self, query, preservar_decimal=False):
                    consultas.append(query)
                    return super().executar(query, preservar_decimal=preservar_decimal)
            with self.subTest(pergunta=pergunta):
                resultado = analisar(self.df, pergunta, Modelo(plano), executor_factory=ExecutorMonitorado)
                self.assertIn('Operação recusada', resultado.aviso)
                self.assertIsNone(resultado.dados)
                self.assertEqual('', resultado.sql)
                self.assertEqual([], consultas)

    def test_conversao_data_com_filtro_e_plano_contraditorio_sao_recusados(self):
        plano = {'acao': 'contar_por_data', 'coluna': 'data', 'sql': '', 'explicacao': ''}
        for pergunta, mudanca in [('Contar por data apenas em 2025', {}), ('contar por data "data" em todas as linhas, exceto 2025', {'filtro': '2025'})]:
            with self.subTest(pergunta=pergunta, mudanca=mudanca):
                resultado = analisar(self.df, pergunta, Modelo({**plano, **mudanca}))
                self.assertIn('Operação recusada', resultado.aviso)
                self.assertIsNone(resultado.dados)
        comando = 'contar por data "data" em todas as linhas'
        self.assertFalse(confirma_operacao_sem_filtro(comando, {**plano, 'filtro': '2025'}))
        self.assertFalse(confirma_operacao_sem_filtro(comando, {**plano, 'sql': 'SELECT 1'}))
        self.assertFalse(confirma_operacao_sem_filtro(comando, {**plano, 'coluna': 'outra'}))
        modelo = Modelo({**plano, 'filtro': '2025'})
        resultado = analisar(self.df, comando, modelo)
        self.assertIsNotNone(resultado.dados)
        self.assertIsNone(modelo.mensagens)

    def test_comando_estruturado_respeita_nome_com_aspas(self):
        dados = pd.DataFrame({'va"lor': ['1.25'], 'moeda': ['BRL']})
        comando = 'somar "va\\"lor" por "moeda" decimal "." em todas as linhas'
        resultado = analisar(dados, comando)
        self.assertEqual(Decimal('1.250000'), resultado.dados.iloc[0]['total'])

    def test_count_com_filtro_e_sql_multiplo_permanecem_bloqueados(self):
        for sql in ['SELECT COUNT(*) FILTER (WHERE id = \'a\') FROM uploaded_data', 'SELECT COUNT(*) FROM uploaded_data; SELECT 1']:
            with self.subTest(sql=sql), self.assertRaises(ErroConsulta):
                analisar(self.df, 'Pergunta', Modelo({'sql': sql, 'explicacao': ''}))

    def test_contagem_com_filtro_textual_preserva_consulta_e_duplicados(self):
        sql = "SELECT COUNT(*) AS total FROM uploaded_data WHERE moeda = 'BRL'"
        resultado = analisar(self.df, 'Quantos BRL?', Modelo({'sql': sql, 'explicacao': ''}))
        self.assertEqual(2, resultado.dados.iloc[0]['total'])
        self.assertEqual(sql, resultado.sql)

    def test_filtros_sem_conversao_e_distinct(self):
        sql = 'SELECT COUNT(DISTINCT moeda) AS total FROM uploaded_data WHERE moeda IS NOT NULL'
        resultado = analisar(self.df, 'Quantas moedas distintas?', Modelo({'sql': sql, 'explicacao': ''}))
        self.assertEqual(2, resultado.dados.iloc[0]['total'])
        self.assertEqual(sql, resultado.sql)
        sql = 'SELECT DISTINCT moeda FROM uploaded_data ORDER BY moeda LIMIT 2'
        resultado = analisar(self.df, 'Duas moedas distintas', Modelo({'sql': sql, 'explicacao': ''}))
        self.assertEqual(2, len(resultado.dados))
        self.assertEqual(sql, resultado.sql)

    def test_filtro_nao_autoriza_coercao_ou_funcoes(self):
        for sql in ["SELECT COUNT(*) FROM uploaded_data WHERE valor = 10", "SELECT COUNT(*) FROM uploaded_data WHERE CAST(valor AS DOUBLE) = 10", "SELECT COUNT(*) FROM uploaded_data WHERE lower(moeda) = 'brl'", 'SELECT * FROM uploaded_data LIMIT 1001']:
            with self.subTest(sql=sql), self.assertRaises(ErroConsulta):
                analisar(self.df, 'Pergunta', Modelo({'sql': sql, 'explicacao': ''}))
        dados_mistos = pd.DataFrame({'coluna': pd.Series(['1', 1], dtype=object)})
        with self.assertRaises(ErroConsulta):
            analisar(dados_mistos, 'Pergunta', Modelo({'sql': "SELECT COUNT(*) FROM uploaded_data WHERE coluna = '1'", 'explicacao': ''}))

    def test_conversao_separa_moedas_conta_invalidos_e_preserva_repetidos(self):
        modelo = Modelo({'acao': 'somar_por_moeda', 'coluna': 'valor', 'moeda': 'moeda', 'decimal': '.', 'sql': '', 'explicacao': ''})
        resultado = analisar(self.df, 'somar "valor" por "moeda" decimal "." em todas as linhas', modelo)
        grupos = resultado.dados.set_index('moeda')
        self.assertEqual(Decimal('13.000000'), grupos.loc['BRL', 'total'])
        self.assertIsInstance(grupos.loc['BRL', 'total'], Decimal)
        self.assertEqual(2, grupos.loc['BRL', 'registros'])
        self.assertEqual(9.0, float(grupos.loc['USD', 'total']))
        self.assertEqual(1, grupos.loc['USD', 'valores_invalidos'])
        self.assertEqual(1, grupos.loc['USD', 'valores_ausentes'])
        self.assertEqual(1, int(resultado.dados['moeda'].isna().sum()))
        desconhecida = resultado.dados[resultado.dados['moeda'].isna()].iloc[0]
        self.assertTrue(pd.isna(desconhecida['total']))
        self.assertEqual(1, desconhecida['valores_validos_sem_moeda'])
        self.assertIn('sem moeda, fora das somas: 1', resultado.limitacoes)
        self.assertIn('inválidos: 1', resultado.limitacoes)
        self.assertIn('identificadores repetidos', resultado.limitacoes)
        self.assertIsNone(modelo.mensagens)

    def test_conversao_data_informa_invalidos_e_ausentes(self):
        resultado = analisar(self.df, 'contar por data "data" em todas as linhas', Modelo({'acao': 'contar_por_data', 'coluna': 'data', 'sql': '', 'explicacao': ''}))
        nao_convertidos = resultado.dados[resultado.dados['data'].isna()].iloc[0]
        self.assertEqual(1, nao_convertidos['valores_invalidos'])
        self.assertEqual(1, nao_convertidos['valores_ausentes'])
        self.assertEqual(6, resultado.dados['registros'].sum())

    def test_soma_moeda_com_numeros_tipados_e_ausentes(self):
        dados = pd.DataFrame({'moeda': ['BRL', 'BRL', 'USD', None],
                              'valor': pd.Series([100, None, 30, 7], dtype='Int64')})
        original = dados.copy(deep=True)
        resultado = analisar(dados, 'somar "valor" por "moeda" decimal "," em todas as linhas')
        grupos = resultado.dados.set_index('moeda')
        self.assertEqual(100, grupos.loc['BRL', 'total'])
        self.assertEqual(1, grupos.loc['BRL', 'valores_ausentes'])
        self.assertEqual(0, grupos.loc['BRL', 'valores_invalidos'])
        self.assertEqual(30, grupos.loc['USD', 'total'])
        self.assertEqual(1, resultado.dados.iloc[0]['total_validos_sem_moeda'])
        self.assertIn('sem aplicar o separador decimal', resultado.limitacoes)
        pd.testing.assert_frame_equal(dados, original)

    def test_soma_moeda_float_sem_arredondar_e_infinito_invalido(self):
        dados = pd.DataFrame({'moeda': ['BRL'] * 4, 'valor': [1.123456789, None, float('inf'), float('-inf')]})
        original = dados.copy(deep=True)
        resultado = analisar(dados, 'somar "valor" por "moeda" decimal "." em todas as linhas')
        linha = resultado.dados.iloc[0]
        self.assertAlmostEqual(1.123456789, linha['total'], places=9)
        self.assertEqual(1, linha['valores_ausentes'])
        self.assertEqual(2, linha['valores_invalidos'])
        self.assertIn('ponto flutuante', resultado.limitacoes)
        pd.testing.assert_frame_equal(dados, original)

    def test_soma_decimal_nativo_preserva_precisao(self):
        dados = pd.DataFrame({'moeda': ['BRL'] * 3,
                              'valor': pd.Series([Decimal('1.123456789'), None, Decimal('2.000000001')], dtype=object)})
        original = dados.copy(deep=True)
        resultado = analisar(dados, 'somar "valor" por "moeda" decimal "." em todas as linhas')
        self.assertEqual(Decimal('3.123456790'), resultado.dados.iloc[0]['total'])
        self.assertEqual(1, resultado.dados.iloc[0]['valores_ausentes'])
        pd.testing.assert_frame_equal(dados, original)

    def test_contagem_de_datetime_por_dia_e_ausentes(self):
        dados = pd.DataFrame({'data': pd.to_datetime(['2025-01-01 10:30', '2025-01-01 23:59', None])})
        original = dados.copy(deep=True)
        resultado = analisar(dados, 'contar por data "data" em todas as linhas')
        encontrados = resultado.dados.dropna(subset=['data'])
        self.assertEqual(date(2025, 1, 1), encontrados.iloc[0]['data'])
        self.assertEqual(2, encontrados.iloc[0]['registros'])
        self.assertEqual(1, resultado.dados['valores_ausentes'].sum())
        self.assertEqual(0, resultado.dados['valores_invalidos'].sum())
        self.assertIn('horário é desconsiderado', resultado.limitacoes)
        pd.testing.assert_frame_equal(dados, original)

    def test_data_nativa_e_datetime_com_fuso_preservam_dia_local(self):
        datas = pd.DataFrame({'data': pd.Series([date(2025, 1, 1), None], dtype=object)})
        resultado = analisar(datas, 'contar por data "data" em todas as linhas')
        self.assertEqual(date(2025, 1, 1), resultado.dados.dropna(subset=['data']).iloc[0]['data'])
        self.assertEqual(1, resultado.dados['valores_ausentes'].sum())
        objetos = pd.DataFrame({'data': pd.Series([datetime(2025, 1, 1, 18), None], dtype=object)})
        resultado = analisar(objetos, 'contar por data "data" em todas as linhas')
        self.assertEqual(date(2025, 1, 1), resultado.dados.dropna(subset=['data']).iloc[0]['data'])
        self.assertEqual(1, resultado.dados['valores_ausentes'].sum())
        dados = pd.DataFrame({'data': pd.to_datetime(['2025-01-01 23:30', None]).tz_localize('America/Sao_Paulo')})
        original = dados.copy(deep=True)
        resultado = analisar(dados, 'contar por data "data" em todas as linhas')
        self.assertEqual(date(2025, 1, 1), resultado.dados.dropna(subset=['data']).iloc[0]['data'])
        self.assertIn('America/Sao_Paulo', resultado.limitacoes)
        pd.testing.assert_frame_equal(dados, original)

    def test_dados_tipados_mantem_recusa_de_filtro(self):
        casos = [
            (pd.DataFrame({'moeda': ['BRL'], 'valor': [3.0]}), 'somar valor por moeda apenas para BRL',
             {'acao': 'somar_por_moeda', 'coluna': 'valor', 'moeda': 'moeda', 'decimal': '.', 'sql': '', 'explicacao': ''}),
            (pd.DataFrame({'data': pd.to_datetime(['2025-01-01'])}), 'contar por data somente em 2025',
             {'acao': 'contar_por_data', 'coluna': 'data', 'sql': '', 'explicacao': ''}),
        ]
        for dados, pergunta, plano in casos:
            with self.subTest(pergunta=pergunta):
                resultado = analisar(dados, pergunta, Modelo(plano))
                self.assertIsNone(resultado.dados)
                self.assertIn('Operação recusada', resultado.aviso)

    def test_leitura_excel_e_planos_com_numeros_e_datas(self):
        arquivo = BytesIO()
        tabela = pd.DataFrame({'moeda': ['BRL', 'BRL', 'USD'], 'valor': [10.5, None, 2.0],
                               'data': pd.to_datetime(['2025-01-01 14:30', None, '2025-01-02 00:00'])})
        tabela.to_excel(arquivo, index=False, engine='openpyxl')
        dados = ler_arquivo(arquivo.getvalue(), 'dados.xlsx')
        original = dados.copy(deep=True)
        soma = analisar(dados, 'somar "valor" por "moeda" decimal "." em todas as linhas')
        self.assertEqual(10.5, soma.dados.set_index('moeda').loc['BRL', 'total'])
        self.assertEqual(1, soma.dados['valores_ausentes'].sum())
        datas = analisar(dados, 'contar por data "data" em todas as linhas')
        self.assertEqual(1, datas.dados['valores_ausentes'].sum())
        self.assertEqual(3, datas.dados['registros'].sum())
        pd.testing.assert_frame_equal(dados, original)

    def test_bloqueia_conversao_sql_arbitraria_e_soma_moedas(self):
        for sql in ['SELECT SUM(TRY_CAST(valor AS DOUBLE)) FROM uploaded_data', 'SELECT SUM(id) FROM uploaded_data', 'SELECT * FROM uploaded_data WHERE CAST(valor AS DOUBLE) > 0']:
            with self.subTest(sql=sql), self.assertRaises(ErroConsulta):
                analisar(self.df, 'Pergunta', Modelo({'sql': sql, 'explicacao': ''}))
        numeros = pd.DataFrame({'currency': ['USD', 'BRL'], 'value': [1.0, 2.0]})
        with self.assertRaises(ErroConsulta):
            analisar(numeros, 'Somar', Modelo({'sql': 'SELECT SUM(value) FROM uploaded_data', 'explicacao': ''}))

    def test_formato_ambiguo_fica_invalidado(self):
        modelo = Modelo({'acao': 'somar_por_moeda', 'coluna': 'valor', 'moeda': 'moeda', 'decimal': ',', 'sql': '', 'explicacao': ''})
        resultado = analisar(pd.DataFrame({'valor': ['1,50', '1.50'], 'moeda': ['BRL', 'BRL']}), 'somar "valor" por "moeda" decimal "," em todas as linhas', modelo)
        linha = resultado.dados.iloc[0]
        self.assertEqual(1.5, float(linha['total']))
        self.assertEqual(1, linha['valores_invalidos'])

    def test_contagens_globais_permanecem_visiveis_com_grupos_truncados(self):
        dados = pd.DataFrame({'moeda': [f'M{i:04d}' for i in range(1001)], 'valor': ['1'] * 1000 + ['erro']})
        modelo = Modelo({'acao': 'somar_por_moeda', 'coluna': 'valor', 'moeda': 'moeda', 'decimal': '.', 'sql': '', 'explicacao': ''})
        resultado = analisar(dados, 'somar "valor" por "moeda" decimal "." em todas as linhas', modelo)
        self.assertTrue(resultado.truncado)
        self.assertEqual(1000, len(resultado.dados))
        self.assertIn('Total de registros: 1001', resultado.limitacoes)
        self.assertIn('inválidos: 1', resultado.limitacoes)

    def test_impossibilidade_e_plano_invalido(self):
        resultado = analisar(self.df, 'Qual moeda?', Modelo({'acao': 'impossivel', 'sql': '', 'explicacao': 'Informe a moeda.'}))
        self.assertEqual('Informe a moeda.', resultado.aviso)
        with self.assertRaises(ErroConsulta):
            analisar(self.df, 'somar "valor" por "ausente" decimal "." em todas as linhas', Modelo({'acao': 'somar_por_moeda', 'coluna': 'valor', 'moeda': 'ausente', 'decimal': '.', 'sql': '', 'explicacao': ''}))


if __name__ == '__main__':
    unittest.main()
