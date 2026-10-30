"""Teste opcional com Ollama real e arquivo local, somente leitura."""
import hashlib
import os
from pathlib import Path
import unittest

from dataagent.analise import analisar
from dataagent.leitura import ler_arquivo
from dataagent.sql import ExecutorSQL


@unittest.skipUnless(os.environ.get('DATAAGENT_TESTE_OLLAMA') == '1', 'Teste local opcional com Ollama real')
class OllamaLocalTests(unittest.TestCase):
    def test_contagens_e_sql_executado(self):
        caminho = Path(__file__).resolve().parents[1] / 'dados_locais' / 'playstation_sales_dirty_13500.csv'
        conteudo = caminho.read_bytes()
        hash_inicial = hashlib.sha256(conteudo).digest()
        self.addCleanup(lambda: self.assertEqual(hash_inicial, hashlib.sha256(caminho.read_bytes()).digest()))
        dados = ler_arquivo(conteudo, caminho.name, {'sep': None, 'encoding': 'utf-8-sig', 'decimal': '.'})
        self.assertEqual(13500, len(dados))
        self.assertEqual(2950, int(dados['currency'].eq('EUR').sum()))

        for pergunta, esperado, precisa_filtro in [
            ('Quantas linhas tem a tabela?', 13500, False),
            ("Quantos registros têm currency igual a 'EUR'?", 2950, True),
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
                print(f'Pergunta: {pergunta}; resultado: {esperado}; SQL executado: {resultado.sql}', flush=True)


if __name__ == '__main__':
    unittest.main()
