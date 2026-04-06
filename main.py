from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState
from nodes import no_metodologico, no_revisor, no_humano, roteador_de_aprovacao

def compilar_grafo():
    builder = StateGraph(AgentState)

    builder.add_node("metodologia", no_metodologico)
    builder.add_node("revisor", no_revisor)
    builder.add_node("humano", no_humano)

    builder.add_edge(START, "metodologia")
    builder.add_edge("metodologia", "revisor")
    builder.add_edge("revisor", "humano")
    
    builder.add_conditional_edges(
        "humano", 
        roteador_de_aprovacao,
        {
            "finalizar": END,             
            "continuar_revisao": "metodologia" 
        }
    )

    memory = MemorySaver()
    return builder.compile(
        checkpointer=memory,
        interrupt_before=["humano"]
    )

def main():
    grafo = compilar_grafo()
    config = {"configurable": {"thread_id": "teste_loop_infinito_01"}}
    
    texto_teste = "Eu decidi criar um app pra ajudar os alunos a estudar, pq eu acho que vai ser daora e vai resolver o problema de notas baixas."

    # Usamos estado_input para injetar dados no grafo a cada ciclo
    estado_input = {
        "rascunho_atual": texto_teste,
        "comentarios_metodologia": [],
        "comentarios_revisao": [],
        "status_aprovacao": False
    }

    print("\n--- INICIANDO FLUXO DE REVISÃO MULTIAGENTE ---")
    
    # O loop mantém o script vivo para infinitas revisões
    while True:
        # Executa até a próxima interrupção ou até o END
        for evento in grafo.stream(estado_input, config):
            pass 

        # Captura o estado do momento em que o grafo pausou
        estado_salvo = grafo.get_state(config)
        
        # Se não houver um "next" (próximo nó), significa que o fluxo acabou
        if not estado_salvo.next:
            print("\n--- RESULTADO FINAL ---")
            print(f"Texto Final Aprovado: {estado_salvo.values['rascunho_atual']}")
            break

        # Se houver um "next", o fluxo pausou aguardando o humano
        valores = estado_salvo.values
        print("\n--- FEEDBACK DOS AGENTES ---")
        print(f"[Orientador Metodológico]:\n{valores['comentarios_metodologia'][-1]}\n")
        print(f"[Corretor ABNT/Gramática]:\n{valores['comentarios_revisao'][-1]}\n")
        
        print("--- AÇÃO DO USUÁRIO ---")
        novo_texto = input("Digite a nova versão corrigida (ou ENTER para manter): ")
        aprovado = input("O texto atingiu a qualidade desejada? Aprovar e finalizar? (s/n): ").strip().lower() == 's'
        
        # Prepara o input para o próximo ciclo
        estado_input = {"status_aprovacao": aprovado}
        if novo_texto:
            estado_input["rascunho_atual"] = novo_texto

        print("\n--- RETOMANDO FLUXO ---")

if __name__ == "__main__":
    main()