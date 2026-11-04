import types
import unittest
from unittest.mock import MagicMock

import pandas as pd

from dataagent.modelo import ClienteOllama, ErroModelo
from dataagent.resposta import MAX_COLUNAS, MAX_LINHAS, MAX_VALOR, responder


class Seletor:
    def __init__(self, indices=None, erro=None):
        self.indices = [0] if indices is None else indices
        self.erro = erro
        self.contexto = None

    def selecionar_linhas(self, contexto):
        self.contexto = contexto
        if self.erro:
            raise self.erro
        return self.indices


class RespostaTests(unittest.TestCase):
    def test_resposta_usa_apenas_celulas_executadas(self):
        cliente = Seletor([1])
        dados = pd.DataFrame({'produto': ['Café', 'Chá'], 'total': [220.5, 80.0]})
        resultado = responder('Quanto?', 'SELECT produto, total FROM uploaded_data', dados, cliente=cliente)
        self.assertIn('produto: Chá; total: 80.0', resultado.texto)
        self.assertNotIn('Café', resultado.texto)
        self.assertFalse(resultado.parcial)
        self.assertEqual(['Chá', '80.0'], cliente.contexto['linhas'][1])

    def test_resultado_vazio_nao_chama_modelo(self):
        cliente = Seletor(erro=AssertionError('não deve chamar'))
        resultado = responder('Pergunta', 'SELECT * FROM uploaded_data', pd.DataFrame({'a': []}), cliente=cliente)
        self.assertIn('não retornou linhas', resultado.texto)
        self.assertIsNone(cliente.contexto)

    def test_limites_e_truncamento_sao_informados(self):
        dados = pd.DataFrame([['x' * (MAX_VALOR + 1)] * (MAX_COLUNAS + 1)] * (MAX_LINHAS + 1))
        cliente = Seletor()
        resultado = responder('p' * 2001, 's' * 4001, dados, truncado=True, cliente=cliente)
        self.assertTrue(resultado.parcial)
        self.assertEqual(MAX_LINHAS, len(cliente.contexto['linhas']))
        self.assertEqual(MAX_COLUNAS, len(cliente.contexto['colunas']))
        self.assertEqual(MAX_VALOR + 1, len(cliente.contexto['linhas'][0][0]))
        self.assertEqual(2000, len(cliente.contexto['pergunta']))
        self.assertEqual(4000, len(cliente.contexto['sql']))
        self.assertTrue(cliente.contexto['parcial'])

    def test_falha_ou_indices_inventados_nao_geram_texto(self):
        dados = pd.DataFrame({'total': [5]})
        for cliente in [Seletor(erro=ErroModelo('segredo')), Seletor([7]), Seletor([True])]:
            with self.subTest(cliente=cliente):
                resultado = responder('Pergunta', 'SELECT 5', dados, cliente=cliente)
                self.assertTrue(resultado.aviso)
                self.assertEqual('', resultado.texto)
                self.assertNotIn('segredo', resultado.aviso)

    def test_cliente_ollama_valida_estrutura_e_indices(self):
        cliente = ClienteOllama.__new__(ClienteOllama)
        cliente.cliente = MagicMock()
        contexto = {'linhas': [['5']]}
        for raw in ['{}', '{"linhas": [1]}', '{"linhas": [true]}', '{"linhas": [0, 0]}']:
            cliente.cliente.chat.return_value = types.SimpleNamespace(message=types.SimpleNamespace(content=raw))
            with self.subTest(raw=raw), self.assertRaises(ErroModelo):
                cliente.selecionar_linhas(contexto)
        cliente.cliente.chat.return_value = types.SimpleNamespace(message=types.SimpleNamespace(content='{"linhas": [0]}'))
        self.assertEqual([0], cliente.selecionar_linhas(contexto))


if __name__ == '__main__':
    unittest.main()
