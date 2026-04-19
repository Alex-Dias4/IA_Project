import json
from pydantic import BaseModel, Field
from typing import Literal, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from state import AgentState
from llm_factory import get_llm_model
from databaseStruture import buscar_artigos_similares

ia = get_llm_model()

# ==========================================
# 1. MODELOS DE DADOS
# ==========================================
class RotaDecisao(BaseModel):
    proximo_passo: Literal["avaliar_metodologia", "corrigir_escrita", "buscar_referencias", "aguardar_humano", "finalizar"] = Field(
        description="O próximo agente que deve atuar no rascunho."
    )

class ComentarioAvaliacao(BaseModel):
    trecho: str = Field(description="Trecho do texto original com problema")
    comentario: str = Field(description="Diagnóstico direto do erro")
    sugestao: str = Field(description="Sugestão prática de melhoria")

class ListaComentarios(BaseModel):
    avaliacoes: List[ComentarioAvaliacao]

# ==========================================
# 2. O META-SUPERVISOR (MAESTRO)
# ==========================================
def no_meta_supervisor(state: AgentState):
    print("\n👑 [META-SUPERVISOR] Analisando o estado do projeto...")
    
    if state.get("status_aprovacao") == True:
        return {"proxima_rota": "finalizar"}
        
    passos_executados = state.get("passos_executados", [])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Você é o roteador do sistema.
        - Se 'avaliar_metodologia' não está no histórico, escolha: avaliar_metodologia
        - Se 'corrigir_escrita' não está no histórico, escolha: corrigir_escrita
        - Se 'buscar_referencias' não está no histórico, escolha: buscar_referencias
        - Se todos os 3 já estão no histórico, escolha: aguardar_humano"""),
        ("user", "Histórico atual: {passos}")
    ])
    
    roteador = prompt | ia.with_structured_output(RotaDecisao)
    
    try:
        decisao = roteador.invoke({"passos": passos_executados})
        rota = decisao.proximo_passo
    except Exception as e:
        print(f"[Aviso] Falha de Rota: {e}")
        rota = "aguardar_humano"
        
    print(f"   ↳ Roteando para -> {rota}")
    return {"proxima_rota": rota}

# ==========================================
# 3. AGENTES ESPECIALISTAS
# ==========================================
def no_metodologico(state: AgentState):
    print("\n👨‍🏫 [Banca Metodológica] Analisando argumentação...")
    
    # Adicionamos o Parser
    parser = PydanticOutputParser(pydantic_object=ListaComentarios)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Você é um orientador metodológico rigoroso.
        Analise o texto e aponte falhas na argumentação, estrutura e lógica.
        
        {format_instructions}"""),
        ("user", "Texto: {rascunho}")
    ])
    
    chain = prompt | ia | parser
    
    try:
        # Injetamos as instruções de formatação no invoke
        resposta = chain.invoke({
            "rascunho": state.get("rascunho_atual", ""),
            "format_instructions": parser.get_format_instructions()
        })
        feedback = [avaliacao.model_dump() for avaliacao in resposta.avaliacoes]
    except Exception as e:
        print(f"[ERRO METODOLÓGICO REAL] {e}")
        feedback = [{"trecho": "Erro", "comentario": "Falha na extração.", "sugestao": "Tente de novo"}]
        
    return {
        "comentarios_banca": state.get("comentarios_banca", []) + [feedback], 
        "passos_executados": state.get("passos_executados", []) + ["avaliar_metodologia"]
    }

def no_revisor(state: AgentState):
    print("\n✍️  [Corretor ABNT] Revisando gramática e estilo...")
    
    parser = PydanticOutputParser(pydantic_object=ListaComentarios)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Você é um corretor de normas ABNT.
        Procure por verbos em primeira pessoa e erros de estilo.
        
        {format_instructions}"""),
        ("user", "Texto: {rascunho}")
    ])
    
    chain = prompt | ia | parser
    
    try:
        resposta = chain.invoke({
            "rascunho": state.get("rascunho_atual", ""),
            "format_instructions": parser.get_format_instructions()
        })
        feedback = [avaliacao.model_dump() for avaliacao in resposta.avaliacoes]
    except Exception as e:
        print(f"[ERRO REVISOR REAL] {e}")
        feedback = [{"trecho": "Erro", "comentario": "Falha na extração.", "sugestao": "Tente de novo"}]
        
    return {
        "comentarios_escrita": state.get("comentarios_escrita", []) + [feedback], 
        "passos_executados": state.get("passos_executados", []) + ["corrigir_escrita"]
    }

def no_bibliotecario(state: AgentState):
    print("\n📚 [Bibliotecário RAG] Buscando conexões no banco vetorial...")
    
    rascunho = state.get("rascunho_atual", "")
    texto_para_busca = rascunho[:1000] if len(rascunho) > 1000 else rascunho
    
    resultados = buscar_artigos_similares(texto_para_busca, limite=5)
    artigos_unicos = {}
    
    if resultados and isinstance(resultados, list) and len(resultados) > 0 and "titulo" in resultados[0]:
        for art in resultados:
            titulo = art['titulo']
            if titulo not in artigos_unicos:
                artigos_unicos[titulo] = f"📄 {titulo} - {art.get('autores', 'Autor Desconhecido')}"
        referencias = list(artigos_unicos.values())
    else:
        referencias = ["Nenhuma conexão semântica direta encontrada. Verifique se você já injetou artigos na base de dados."]
        
    return {
        "referencias_rag": state.get("referencias_rag", []) + referencias, 
        "passos_executados": state.get("passos_executados", []) + ["buscar_referencias"]
    }

def no_humano(state: AgentState):
    print("\n🧑‍💻 [Pausa Humana] Aguardando decisão do usuário...")
    return {"passos_executados": []}