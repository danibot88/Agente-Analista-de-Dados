"""Acesso ao Ollama e interpretação da resposta estruturada."""
import json


class ErroModelo(Exception):
    """O modelo não respondeu ou retornou uma resposta inválida."""


class ClienteOllama:
    def __init__(self):
        try:
            from ollama import Client
            self.cliente = Client(host='http://localhost:11434', trust_env=False, timeout=180)
        except Exception as exc:
            raise ErroModelo('Não foi possível iniciar o cliente Ollama.') from exc

    def gerar_sql(self, mensagens):
        schema = {
            'type': 'object',
            'properties': {'sql': {'type': 'string'}, 'explicacao': {'type': 'string'}, 'acao': {'type': 'string', 'enum': ['sql', 'somar_por_moeda', 'contar_por_data', 'impossivel']}, 'coluna': {'type': 'string'}, 'moeda': {'type': 'string'}, 'decimal': {'type': 'string'}},
            'required': ['sql', 'explicacao'],
        }
        try:
            response = self.cliente.chat(model='llama3.2:latest', messages=mensagens,
                                         format=schema, options={'temperature': 0})
            raw = response.message.content or '{}'
            result = json.loads(raw)
            if (not isinstance(result, dict)
                    or not isinstance(result.get('sql'), str)
                    or not isinstance(result.get('explicacao'), str)
                    or result.get('acao', 'sql') not in ('sql', 'somar_por_moeda', 'contar_por_data', 'impossivel')
                    or any(key in result and not isinstance(result[key], str) for key in ('coluna', 'moeda', 'decimal'))):
                raise ValueError('Resposta não é um objeto')
            query = str(result.get('sql', '')).strip().rstrip(';').strip()
            explanation = str(result.get('explicacao', ''))
            return raw, query, explanation
        except Exception as exc:
            raise ErroModelo('Não foi possível obter uma resposta válida do Ollama.') from exc
