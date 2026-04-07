from typing import TypedDict, List

class AgentState(TypedDict):
    rascunho_atual: str
    comentarios_metodologia: List[str]
    comentarios_revisao: List[str]
    status_aprovacao: bool
    
# 1. Adicione 'referencias' ao seu Estado atual
class GraphState(TypedDict):
    texto_original: str
    texto_revisado: str
    explicacao: str
    referencias: List[str] # <--- Nova linha na memória do grafo