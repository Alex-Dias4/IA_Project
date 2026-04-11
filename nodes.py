from state import AgentState
from llm_factory import get_llm_model
# Importamos a função de busca do nosso banco atualizado
from databaseStruture import buscar_artigos_similares

ia = get_llm_model()

def no_metodologico(state: AgentState):
    print("\n[Node: Metodológico] Avaliando estrutura e coerência...")
    prompt = f"""
    Você é um orientador metodológico. Analise o texto: {state['rascunho_atual']}
    Aponte falhas na estrutura lógica, como falta de clareza no problema de pesquisa ou nos objetivos.
    Seja breve e direto.
    """
    resposta = ia.invoke(prompt)
    novos_comentarios = state.get("comentarios_metodologia", []) + [resposta.content]
    
    return {"comentarios_metodologia": novos_comentarios}

def no_revisor(state: AgentState):
    print("\n[Node: Revisor] Avaliando linguagem acadêmica...")
    prompt = f"""
    Você é um corretor rigoroso. Analise o texto: {state['rascunho_atual']}
    Aponte erros de ortografia, uso incorreto da primeira pessoa e problemas de coesão.
    Seja breve e direto.
    """
    resposta = ia.invoke(prompt)
    novos_comentarios = state.get("comentarios_revisao", []) + [resposta.content]
    
    return {"comentarios_revisao": novos_comentarios}

def no_bibliotecario(state: AgentState):
    print("\n--- [AGENTE BIBLIOTECÁRIO] Buscando embasamento teórico... ---")
    
    texto_base = state.get("rascunho_atual", "")
    resultados = buscar_artigos_similares(texto_base, limite=5)
    
    artigos_unicos = {} 
    
    if resultados and isinstance(resultados, list) and len(resultados) > 0 and "titulo" in resultados[0]:
        for art in resultados:
            titulo = art['titulo']
            if titulo not in artigos_unicos:
                artigos_unicos[titulo] = f"📚 {titulo} - {art.get('autores', 'Autor Desconhecido')}"
                
        referencias_formatadas = list(artigos_unicos.values())
    else:
        referencias_formatadas = ["Nenhuma conexão semântica forte foi encontrada na base de dados."]
        
    return {"referencias": referencias_formatadas}

def no_humano(state: AgentState):
    print("\n[Node: Humano] Aguardando interação...")
    return {"status_aprovacao": True}

def roteador_de_aprovacao(state: AgentState) -> str:
    if state.get("status_aprovacao") == True:
        return "finalizar"
    else:
        return "continuar_revisao"