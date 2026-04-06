from typing import TypedDict, List

class AgentState(TypedDict):
    rascunho_atual: str
    comentarios_metodologia: List[str]
    comentarios_revisao: List[str]
    status_aprovacao: bool