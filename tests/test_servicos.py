import json
import types
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from dataagent.analise import analisar
from dataagent.leitura import ErroLeitura, ler_arquivo
from dataagent.modelo import ClienteOllama, ErroModelo
from dataagent.sql import ErroConsulta, ExecutorSQL


class ModeloFalso:
    def __init__(self, respostas):
        self.respostas = iter(respostas)
        self.mensagens = []

    def gerar_sql(self, mensagens):
        self.mensagens.append(list(mensagens))
        resposta = next(self.respostas)
        if isinstance(resposta, Exception):
            raise resposta
        return json.dumps({'sql': resposta, 'explicacao': ''}), resposta, ''


class ServicosTests(unittest.TestCase):
    def setUp(self):
        self.dados = pd.DataFrame({'valor': [1, 2]})

    def test_leitura_erro_preserva_causa_sem_expor_conteudo(self):
        with self.assertRaises(ErroLeitura) as erro:
            ler_arquivo(b'\xff', 'dados.csv', {'encoding': 'utf-8'})
        self.assertIsNotNone(erro.exception.__cause__)
        self.assertNotIn('xff', str(erro.exception))

    def test_consulta_e_truncamento(self):
        modelo = ModeloFalso(['SELECT * FROM uploaded_data'])
        resultado = analisar(pd.DataFrame({'valor': range(1001)}), 'Listar', modelo)
        self.assertEqual(1000, len(resultado.dados))
        self.assertTrue(resultado.truncado)
        self.assertEqual('SELECT * FROM uploaded_data', resultado.sql)

    def test_sql_invalido_repetido_e_retentativa_bem_sucedida(self):
        modelo = ModeloFalso(['SELECT ausente FROM uploaded_data', 'SELECT SUM(valor) AS total FROM uploaded_data'])
        resultado = analisar(self.dados, 'Somar', modelo)
        self.assertEqual(3, resultado.dados.iloc[0]['total'])
        self.assertEqual(2, len(modelo.mensagens))
        self.assertNotIn('Binder Error', modelo.mensagens[1][-1]['content'])

    def test_modelo_corrige_apos_receber_motivo_de_referencia_sanitizado(self):
        class ModeloQueUsaMotivo:
            def __init__(self):
                self.chamadas = 0
                self.motivo = ''

            def gerar_sql(self, mensagens):
                self.chamadas += 1
                if self.chamadas == 1:
                    sql = 'SELECT coluna_inexistente FROM uploaded_data'
                else:
                    self.motivo = mensagens[-1]['content']
                    if 'refer\u00eancia ou express\u00e3o SQL' not in self.motivo:
                        raise AssertionError('Motivo util ausente na tentativa de correcao')
                    sql = 'SELECT SUM(valor) AS total FROM uploaded_data'
                return json.dumps({'sql': sql}), sql, ''

        modelo = ModeloQueUsaMotivo()
        resultado = analisar(self.dados, 'Somar', modelo)
        self.assertEqual(2, modelo.chamadas)
        self.assertEqual(3, resultado.dados.iloc[0]['total'])
        self.assertNotIn('coluna_inexistente', modelo.motivo)
        self.assertNotIn('Binder Error', modelo.motivo)

    def test_motivos_sao_categorias_fixas_sem_mensagem_bruta(self):
        import duckdb
        casos = [
            (duckdb.ParserException('segredo privado'), 'sintaxe'),
            (duckdb.BinderException('segredo privado'), 'referencia'),
            (duckdb.CatalogException('segredo privado'), 'referencia'),
            (duckdb.ConversionException('segredo privado'), 'conversao'),
            (RuntimeError('segredo privado'), 'execucao'),
        ]
        for falha, categoria in casos:
            conexao = MagicMock()
            conexao.extract_statements.side_effect = falha
            with self.subTest(categoria=categoria), patch('dataagent.sql.duckdb.connect', return_value=conexao):
                with ExecutorSQL(self.dados) as executor:
                    with self.assertRaises(ErroConsulta) as erro:
                        executor.executar('SELECT 1')
                self.assertEqual(categoria, erro.exception.categoria)
                self.assertNotIn('segredo privado', erro.exception.motivo_correcao)
                self.assertNotIn('segredo privado', str(erro.exception))

    def test_motivo_de_restricao_e_especifico(self):
        with ExecutorSQL(self.dados) as executor:
            with self.assertRaises(ErroConsulta) as erro:
                executor.executar('DELETE FROM uploaded_data')
        self.assertEqual('restricao', erro.exception.categoria)
        self.assertIn('\u00fanica instru\u00e7\u00e3o SELECT', erro.exception.motivo_correcao)

    def test_tres_falhas_de_consulta(self):
        modelo = ModeloFalso(['DELETE FROM uploaded_data'] * 3)
        with self.assertRaises(ErroConsulta):
            analisar(self.dados, 'Pergunta', modelo)
        self.assertEqual(3, len(modelo.mensagens))

    def test_sql_vazio_retorna_aviso(self):
        resultado = analisar(self.dados, 'Pergunta', ModeloFalso(['']))
        self.assertTrue(resultado.aviso)
        self.assertIsNone(resultado.dados)

    def test_parser_e_acesso_externo(self):
        with ExecutorSQL(self.dados) as executor:
            self.assertFalse(executor.conn.execute("SELECT current_setting('enable_external_access')").fetchone()[0])
            for sql in ['SELECT 1; SELECT 2', 'DELETE FROM uploaded_data', "SELECT * FROM read_csv('arquivo.csv')"]:
                with self.subTest(sql=sql), self.assertRaises(ErroConsulta):
                    executor.executar(sql)

    def test_conexao_fecha_em_sucesso_falha_modelo_e_falha_sql(self):
        for resposta in ['SELECT * FROM uploaded_data', ErroModelo('falha'), 'DELETE FROM uploaded_data']:
            conexao = MagicMock()
            conexao.extract_statements.return_value = []
            if resposta == 'SELECT * FROM uploaded_data':
                import duckdb
                conexao.extract_statements.return_value = [types.SimpleNamespace(type=duckdb.StatementType.SELECT)]
                conexao.execute.return_value.df.return_value = self.dados
            modelo = ModeloFalso([resposta] * 3)
            with self.subTest(resposta=str(resposta)), patch('dataagent.sql.duckdb.connect', return_value=conexao):
                if resposta == 'SELECT * FROM uploaded_data':
                    analisar(self.dados, 'Pergunta', modelo)
                else:
                    with self.assertRaises((ErroModelo, ErroConsulta)):
                        analisar(self.dados, 'Pergunta', modelo)
                conexao.close.assert_called_once()

    def test_conexao_fecha_se_registro_falhar(self):
        conexao = MagicMock()
        conexao.register.side_effect = RuntimeError('dado privado')
        with patch('dataagent.sql.duckdb.connect', return_value=conexao):
            with self.assertRaises(ErroConsulta) as erro:
                ExecutorSQL(self.dados)
        conexao.close.assert_called_once()
        self.assertNotIn('dado privado', str(erro.exception))

    def test_resposta_modelo_invalida_e_falha_de_comunicacao(self):
        cliente = ClienteOllama.__new__(ClienteOllama)
        cliente.cliente = MagicMock()
        for resposta in ['{invalido', '[]']:
            cliente.cliente.chat.return_value = types.SimpleNamespace(message=types.SimpleNamespace(content=resposta))
            with self.subTest(resposta=resposta), self.assertRaises(ErroModelo):
                cliente.gerar_sql([])
        cliente.cliente.chat.side_effect = RuntimeError('segredo')
        with self.assertRaises(ErroModelo) as erro:
            cliente.gerar_sql([])
        self.assertNotIn('segredo', str(erro.exception))


if __name__ == '__main__':
    unittest.main()
