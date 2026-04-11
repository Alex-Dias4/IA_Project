from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState
# Importe o novo nó aqui
from nodes import no_metodologico, no_revisor, no_bibliotecario, no_humano, roteador_de_aprovacao

def compilar_grafo():
    builder = StateGraph(AgentState)

    builder.add_node("metodologia", no_metodologico)
    builder.add_node("revisor", no_revisor)
    builder.add_node("bibliotecario", no_bibliotecario) # <--- Nó adicionado
    builder.add_node("humano", no_humano)

    # Nova rota com o bibliotecário no meio
    builder.add_edge(START, "metodologia")
    builder.add_edge("metodologia", "revisor")
    builder.add_edge("revisor", "bibliotecario")  # Revisor passa pro Bibliotecário
    builder.add_edge("bibliotecario", "humano")   # Bibliotecário entrega pro Humano aprovar
    
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
    # config = {"configurable": {"thread_id": "teste_loop_infinito_02"}} # Mudei o ID pra resetar a memória do teste
    
    # texto_teste = "Eu decidi criar um app pra ajudar os alunos a estudar, pq eu acho que vai ser daora e vai resolver o problema de notas baixas."

    # # Adicionando 'referencias' no input inicial
    # estado_input = {
    #     "rascunho_atual": texto_teste,
    #     "comentarios_metodologia": [],
    #     "comentarios_revisao": [],
    #     "referencias": [], # <--- Iniciando vazio
    #     "status_aprovacao": False
    # }

    # print("\n--- INICIANDO FLUXO DE REVISÃO MULTIAGENTE ---")
    
    # while True:
    #     for evento in grafo.stream(estado_input, config):
    #         pass 

    #     estado_salvo = grafo.get_state(config)
        
    #     if not estado_salvo.next:
    #         print("\n--- RESULTADO FINAL ---")
    #         print(f"Texto Final Aprovado: {estado_salvo.values['rascunho_atual']}")
    #         break

    #     valores = estado_salvo.values
    #     print("\n--- FEEDBACK DOS AGENTES ---")
        
    #     # O try/except garante que não vai dar erro se a lista estiver vazia no primeiro ciclo
    #     try: print(f"[Orientador Metodológico]:\n{valores['comentarios_metodologia'][-1]}\n")
    #     except: pass
        
    #     try: print(f"[Corretor ABNT/Gramática]:\n{valores['comentarios_revisao'][-1]}\n")
    #     except: pass
        
    #     print("[Agente Bibliotecário - Sugestões de Leitura]:")
    #     for ref in valores.get('referencias', []):
    #         print(ref)
    #     print("\n")
        
    #     print("--- AÇÃO DO USUÁRIO ---")
    #     novo_texto = input("Digite a nova versão corrigida (ou ENTER para manter): ")
    #     aprovado = input("O texto atingiu a qualidade desejada? Aprovar e finalizar? (s/n): ").strip().lower() == 's'
        
    #     estado_input = {"status_aprovacao": aprovado}
    #     if novo_texto:
    #         estado_input["rascunho_atual"] = novo_texto

    #     print("\n--- RETOMANDO FLUXO ---")

if __name__ == "__main__":
    main()