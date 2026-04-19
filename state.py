from typing import TypedDict, List, Any

class AgentState(TypedDict):
    rascunho_atual: str
    passos_executados: List[str]
    comentarios_escrita: List[Any]
    comentarios_banca: List[Any]
    referencias_rag: List[str]
    proxima_rota: str
    status_aprovacao: bool