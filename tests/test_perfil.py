import unittest

import pandas as pd

from dataagent.perfil import MAX_COLUNAS, MAX_LINHAS, MAX_NOME, gerar_perfil


class PerfilTests(unittest.TestCase):
    def test_tipos_ausencias_e_resumos(self):
        dados = pd.DataFrame({
            'valor': pd.Series([1.0, None, 3.0]),
            'indicador': pd.Series([True, False, None], dtype='boolean'),
            'data': pd.to_datetime(['2026-01-01', None, '2026-01-03']),
            'texto': pd.Series(['casa', None, ''], dtype='string'),
        })
        original = dados.copy(deep=True)
        perfil = gerar_perfil(dados)
        colunas = {c['Coluna']: c for c in perfil.colunas}
        self.assertEqual((3, 4), (perfil.linhas_analisadas, perfil.colunas_analisadas))
        self.assertEqual((1, 2), (colunas['texto']['Ausentes'], colunas['texto']['Não ausentes']))
        self.assertEqual('float64', colunas['valor']['Tipo'])
        self.assertIn('1.0', colunas['valor']['Resumo'])
        self.assertIn('3.0', colunas['valor']['Resumo'])
        self.assertIn('Verdadeiro: 1; falso: 1', colunas['indicador']['Resumo'])
        self.assertIn('2026-01-01', colunas['data']['Resumo'])
        pd.testing.assert_frame_equal(dados, original)

    def test_indicios_ambiguos_sem_converter_nem_expor_textos(self):
        dados = pd.DataFrame({'misto': pd.Series(['001', '2,50', '31/12/2025', '2025-99-99', 'casa', None], dtype='string')})
        perfil = gerar_perfil(dados)
        coluna = perfil.colunas[0]
        self.assertIn('2 possível(is) número(s)', coluna['Indícios'])
        self.assertIn('2 possível(is) data(s)', coluna['Indícios'])
        self.assertEqual('', coluna['Resumo'])
        self.assertNotIn('001', str(perfil))
        self.assertNotIn('31/12/2025', str(perfil))
        self.assertEqual('001', dados.iloc[0, 0])

    def test_limites_amostra_nomes_e_colunas_duplicadas(self):
        dados = pd.DataFrame([[None] * (MAX_COLUNAS + 1)] * (MAX_LINHAS + 1), columns=['x' * 150] * (MAX_COLUNAS + 1))
        dados.iloc[MAX_LINHAS, 0] = 'fim'
        perfil = gerar_perfil(dados)
        self.assertEqual(MAX_LINHAS, perfil.linhas_analisadas)
        self.assertEqual(MAX_COLUNAS, perfil.colunas_analisadas)
        self.assertEqual(MAX_LINHAS + 1, perfil.linhas_totais)
        self.assertEqual(MAX_COLUNAS + 1, perfil.colunas_totais)
        self.assertEqual(MAX_LINHAS, perfil.colunas[0]['Ausentes'])
        self.assertEqual(MAX_NOME + 1, len(perfil.colunas[0]['Coluna']))

    def test_texto_longo_nao_classificado_e_objetos_mistos(self):
        dados = pd.DataFrame({'misto': pd.Series(['9' * 101, 42, '2024-01-01'], dtype=object)})
        coluna = gerar_perfil(dados).colunas[0]
        self.assertNotIn('número', coluna['Indícios'])
        self.assertIn('data', coluna['Indícios'])


if __name__ == '__main__':
    unittest.main()
