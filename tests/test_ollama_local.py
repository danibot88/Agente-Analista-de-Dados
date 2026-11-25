"""Teste opcional com Ollama real e dados sintéticos em memória."""
import os
import unittest

from dataagent.analise import analisar
from dataagent.leitura import ler_arquivo
from dataagent.sql import ExecutorSQL


@unittest.skipUnless(os.environ.get('DATAAGENT_TESTE_OLLAMA') == '1', 'Teste local opcional com Ollama real')
class OllamaLocalTests(unittest.TestCase):
    def test_contagens_e_sql_executado(self):
        conteudo = b'id,currency\n1,EUR\n2,BRL\n3,EUR\n4,USD\n5,BRL\n'
        dados = ler_arquivo(conteudo, 'sintetico.csv', {'sep': ','})

        for pergunta, esperado, precisa_filtro in [
            ('Quantas linhas tem a tabela?', 5, False),
            ("Quantos registros têm currency igual a 'EUR'?", 2, True),
        ]:
            executadas = []

            class ExecutorMonitorado(ExecutorSQL):
                def executar(self, query, preservar_decimal=False):
                    resposta = super().executar(query, preservar_decimal=preservar_decimal)
                    executadas.append((query, resposta.copy()))
                    return resposta

            with self.subTest(pergunta=pergunta):
                resultado = analisar(dados, pergunta, executor_factory=ExecutorMonitorado)
                self.assertIsNotNone(resultado.dados, resultado.aviso)
                self.assertEqual((1, 1), resultado.dados.shape)
                self.assertEqual(esperado, int(resultado.dados.iloc[0, 0]))
                self.assertTrue(executadas)
                self.assertEqual(executadas[-1][0], resultado.sql)
                self.assertEqual(esperado, int(executadas[-1][1].iloc[0, 0]))
                if precisa_filtro:
                    self.assertIn('WHERE', resultado.sql.upper())
                    self.assertIn('currency', resultado.sql.lower())
                    self.assertIn("'EUR'", resultado.sql.upper())


if __name__ == '__main__':
    unittest.main()
