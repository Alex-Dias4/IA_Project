from langgraph.graph import StateGraph, START, END

# Importa o estado e os nossos nós inteligentes da nova arquitetura
from state import AgentState
from nodes import (
    no_meta_supervisor,
    no_metodologico,
    no_revisor,
    no_bibliotecario,
    no_humano
)

# 1. Inicializa o Grafo
grafo = StateGraph(AgentState)

# 2. Adiciona os nós (Os Atores)
grafo.add_node("meta_supervisor", no_meta_supervisor)
grafo.add_node("avaliar_metodologia", no_metodologico)
grafo.add_node("corrigir_escrita", no_revisor)
grafo.add_node("buscar_referencias", no_bibliotecario)
grafo.add_node("aguardar_humano", no_humano)

# 3. Função de Roteamento Dinâmico
def decidir_proximo_passo(state: AgentState):
    """Lê a decisão tomada pelo Meta-Supervisor no estado"""
    return state.get("proxima_rota", "aguardar_humano")

# 4. Desenhando as Arestas (O Caminho)
# O fluxo SEMPRE começa pelo Maestro
grafo.add_edge(START, "meta_supervisor")

# O Maestro distribui as tarefas com base na sua decisão lógica
grafo.add_conditional_edges(
    "meta_supervisor",
    decidir_proximo_passo,
    {
        "avaliar_metodologia": "avaliar_metodologia",
        "corrigir_escrita": "corrigir_escrita",
        "buscar_referencias": "buscar_referencias",
        "aguardar_humano": "aguardar_humano",
        "finalizar": END
    }
)

# Os professores devolvem o texto para o Maestro após trabalharem
grafo.add_edge("avaliar_metodologia", "meta_supervisor")
grafo.add_edge("corrigir_escrita", "meta_supervisor")
grafo.add_edge("buscar_referencias", "meta_supervisor")

# A rodada termina quando aguarda o humano
grafo.add_edge("aguardar_humano", END)

# 5. Compila a obra-prima direto na variável
app_grafo = grafo.compile()