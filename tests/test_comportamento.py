from contextlib import nullcontext
from io import BytesIO
from pathlib import Path
import runpy
import types
import unittest
from unittest.mock import patch

import duckdb  # Mantém o módulo nativo carregado entre execuções simuladas.
import pandas as pd
from dataagent.modelo import ErroModelo
from dataagent.resposta import Resposta
from dataagent.sql import ErroConsulta

ROOT = Path(__file__).resolve().parents[1]


class StopApp(Exception):
    pass


class Upload:
    def __init__(self, name, content):
        self.name = name
        self.content = content

    def getvalue(self):
        return self.content


class FakeStreamlit:
    def __init__(self, upload, *, options=None, submitted=False):
        self.upload = upload
        self.options = options or {}
        self.submitted = submitted
        self.frames = []
        self.warnings = []
        self.errors = []
        self.captions = []
        self.expanders = []
        self.textos = []
        self.consultas = []

    def set_page_config(self, **kwargs): pass
    def title(self, *args, **kwargs): pass
    def write(self, *args, **kwargs): pass
    def info(self, *args, **kwargs): pass
    def subheader(self, *args, **kwargs): pass
    def code(self, valor, **kwargs): self.consultas.append(valor)
    def text(self, valor, **kwargs): self.textos.append(valor)
    def caption(self, value): self.captions.append(value)
    def warning(self, value): self.warnings.append(value)
    def error(self, value): self.errors.append(value)
    def dataframe(self, value, **kwargs): self.frames.append(value.copy())
    def file_uploader(self, *args, **kwargs): return self.upload
    def expander(self, label, **kwargs):
        self.expanders.append((label, kwargs.get('expanded', False)))
        return nullcontext()
    def form(self, *args, **kwargs): return nullcontext()
    def spinner(self, *args, **kwargs): return nullcontext()
    def selectbox(self, label, choices): return self.options.get(label, choices[0])
    def text_area(self, *args, **kwargs): return 'Qual o total de vendas por produto?'
    def form_submit_button(self, *args, **kwargs): return self.submitted
    def stop(self): raise StopApp()


class FakeClient:
    def __init__(self, **kwargs): pass

    def chat(self, **kwargs):
        if 'linhas' in kwargs['format']['properties']:
            return types.SimpleNamespace(message=types.SimpleNamespace(content='{"linhas": [0]}'))
        content = '{"sql": "SELECT produto, SUM(vendas) AS total FROM uploaded_data GROUP BY produto ORDER BY produto", "explicacao": "Total por produto"}'
        return types.SimpleNamespace(message=types.SimpleNamespace(content=content))


def run_app(upload, **kwargs):
    st = FakeStreamlit(upload, **kwargs)
    with patch.dict('sys.modules', {'streamlit': st, 'ollama': types.SimpleNamespace(Client=FakeClient)}):
        try:
            runpy.run_path(str(ROOT / 'app_local.py'), run_name='__main__')
        except StopApp:
            pass
    return st


class LoadingBehaviorTests(unittest.TestCase):
    def test_example_csv_and_query(self):
        st = run_app(Upload('exemplo.csv', (ROOT / 'exemplo.csv').read_bytes()),
                     options={'Separador': ';', 'Separador decimal': ','}, submitted=True)
        self.assertEqual([], st.errors)
        self.assertEqual(3, len(st.frames[0]))
        self.assertEqual(['produto', 'vendas', 'quantidade'], list(st.frames[1]['Coluna']))
        self.assertIn(('Perfil e qualidade dos dados', False), st.expanders)
        self.assertTrue(any('Ollama local recebe' in caption for caption in st.captions))
        self.assertEqual({'Café': 220.50, 'Chá': 80.0},
                         dict(zip(st.frames[2]['produto'], st.frames[2]['total'])))
        self.assertTrue(any('Café' in texto and '220.5' in texto for texto in st.textos))

    def test_xlsx_loads_first_sheet(self):
        content = BytesIO()
        with pd.ExcelWriter(content, engine='openpyxl') as writer:
            pd.DataFrame({'produto': ['Café'], 'vendas': [12.5]}).to_excel(writer, index=False, sheet_name='Primeira')
            pd.DataFrame({'outro': [99]}).to_excel(writer, index=False, sheet_name='Segunda')
        st = run_app(Upload('dados.xlsx', content.getvalue()))
        self.assertEqual([], st.errors)
        self.assertEqual(['produto', 'vendas'], list(st.frames[0].columns))
        self.assertEqual('Café', st.frames[0].iloc[0]['produto'])

    def test_falha_de_interpretacao_preserva_tabela_e_sql(self):
        with patch('dataagent.resposta.ClienteOllama', side_effect=ErroModelo('falha')):
            st = run_app(Upload('exemplo.csv', (ROOT / 'exemplo.csv').read_bytes()),
                         options={'Separador': ';', 'Separador decimal': ','}, submitted=True)
        self.assertEqual(2, len(st.frames[2]))
        self.assertIn('SELECT produto', st.consultas[0])
        self.assertTrue(any('Não foi possível interpretar' in aviso for aviso in st.warnings))

    def test_exibe_erro_especifico_para_limite_de_memoria(self):
        with patch('dataagent.analise.analisar', side_effect=ErroConsulta('detalhes', 'recursos')):
            st = run_app(Upload('exemplo.csv', (ROOT / 'exemplo.csv').read_bytes()),
                         options={'Separador': ';', 'Separador decimal': ','}, submitted=True)
        self.assertEqual(['A consulta excedeu o limite de memória do DuckDB.'], st.errors)

    def test_interface_informa_interpretacao_parcial(self):
        with patch('dataagent.resposta.responder', return_value=Resposta(texto='Linhas selecionadas', parcial=True)):
            st = run_app(Upload('exemplo.csv', (ROOT / 'exemplo.csv').read_bytes()),
                         options={'Separador': ';', 'Separador decimal': ','}, submitted=True)
        self.assertTrue(any('apenas parte do resultado' in texto for texto in st.captions))
        self.assertIn('Linhas selecionadas', st.textos)

    def test_header_only_csv_warns(self):
        st = run_app(Upload('vazio.csv', b'produto;vendas\n'), options={'Separador': ';'})
        self.assertEqual(['O arquivo não contém linhas de dados para analisar.'], st.warnings)
        self.assertEqual([], st.frames)

    def test_empty_csv_reports_read_error(self):
        st = run_app(Upload('vazio.csv', b''), options={'Separador': ';'})
        self.assertTrue(st.errors[0].startswith('Não foi possível ler o arquivo:'))
        self.assertEqual([], st.frames)

    def test_invalid_excel_reports_read_error(self):
        st = run_app(Upload('invalido.xlsx', b'nao e uma planilha'))
        self.assertTrue(st.errors[0].startswith('Não foi possível ler o arquivo:'))
        self.assertEqual([], st.frames)

    def test_invalid_csv_encoding_reports_read_error(self):
        st = run_app(Upload('invalido.csv', b'coluna\n\xff\n'), options={'Separador': ';'})
        self.assertTrue(st.errors[0].startswith('Não foi possível ler o arquivo:'))
        self.assertEqual([], st.frames)


if __name__ == '__main__':
    unittest.main()
