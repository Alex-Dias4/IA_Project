import streamlit as st
from main import app_grafo
from databaseStruture import processar_pdf_e_salvar

# Configuração da página para usar a tela toda
st.set_page_config(page_title="Banca IA - Orientador", layout="wide")

st.title("🎓 Orientador Acadêmico IA")
st.markdown("Envie seus PDFs de referência e receba feedback estruturado e iterativo do seu trabalho.")

# ==========================================
# 1. BARRA LATERAL (INGESTÃO RAG)
# ==========================================
with st.sidebar:
    st.header("📚 Base de Conhecimento")
    arquivo_pdf = st.file_uploader("Injetar novo artigo (PDF)", type=["pdf"])
    if st.button("➕ Injetar no Banco de Dados"):
        if arquivo_pdf:
            with st.spinner("Processando e indexando no Supabase..."):
                processar_pdf_e_salvar(arquivo_pdf)
            st.success("Documento indexado com sucesso!")
        else:
            st.error("Selecione um arquivo PDF primeiro.")

# ==========================================
# 2. GERENCIAMENTO DE ESTADO (MEMÓRIA)
# ==========================================
if "estado_grafo" not in st.session_state:
    st.session_state.estado_grafo = {
        "rascunho_atual": "",
        "passos_executados": [],
        "comentarios_escrita": [],
        "comentarios_banca": [],
        "referencias_rag": [],
        "proxima_rota": "",
        "status_aprovacao": False
    }

# ==========================================
# 3. ÁREA DE TEXTO E EXECUÇÃO
# ==========================================
rascunho = st.text_area("Cole seu rascunho aqui para avaliação:", height=200)

if st.button("🚀 Iniciar Análise da Banca"):
    if rascunho.strip():
        # Prepara o estado para uma nova rodada
        st.session_state.estado_grafo["rascunho_atual"] = rascunho
        st.session_state.estado_grafo["passos_executados"] = []
        st.session_state.estado_grafo["comentarios_escrita"] = []
        st.session_state.estado_grafo["comentarios_banca"] = []
        st.session_state.estado_grafo["referencias_rag"] = []
        
        with st.spinner("O Meta-Supervisor está coordenando a análise na nuvem (Groq)..."):
            for evento in app_grafo.stream(st.session_state.estado_grafo, {"recursion_limit": 15}):
                for nome_agente, estado_retornado in evento.items():
                    # BLINDAGEM: Só tenta atualizar a memória se o retorno for um dicionário válido
                    if estado_retornado and isinstance(estado_retornado, dict):
                        for chave, valor in estado_retornado.items():
                            st.session_state.estado_grafo[chave] = valor
    else:
        st.warning("Por favor, cole um texto antes de iniciar a análise.")

# ==========================================
# 4. EXIBIÇÃO VISUAL DO FEEDBACK
# ==========================================
estado = st.session_state.estado_grafo

if estado.get("comentarios_banca") or estado.get("comentarios_escrita"):
    st.divider()
    st.subheader("📋 Relatório da Banca")
    
    col1, col2 = st.columns(2)
    
    # --- COLUNA 1: METODOLOGIA ---
    with col1:
        st.markdown("### 👨‍🏫 Orientação Metodológica")
        for bloco in estado["comentarios_banca"]:
            if isinstance(bloco, list): 
                for item in bloco:
                    if isinstance(item, dict):
                        trecho = str(item.get("trecho", "Geral"))
                        titulo = f"📍 {trecho[:60]}..." if len(trecho) > 60 else f"📍 {trecho}"
                        
                        with st.expander(titulo):
                            st.warning(f"**Diagnóstico:** {item.get('comentario', 'Sem comentário')}")
                            st.success(f"**Sugestão de Melhoria:** {item.get('sugestao', 'Sem sugestão')}")

    # --- COLUNA 2: REVISOR ---
    with col2:
        st.markdown("### ✍️ Correção ABNT e Estilo")
        for bloco in estado["comentarios_escrita"]:
            if isinstance(bloco, list):
                for item in bloco:
                    if isinstance(item, dict):
                        trecho = str(item.get("trecho", "Geral"))
                        titulo = f"🔍 {trecho[:60]}..." if len(trecho) > 60 else f"🔍 {trecho}"
                        
                        with st.expander(titulo):
                            st.info(f"**Erro/Regra:** {item.get('comentario', 'Sem comentário')}")
                            st.success(f"**Como reescrever:** {item.get('sugestao', 'Sem sugestão')}")

    # --- SESSÃO INFERIOR: BIBLIOTECÁRIO ---
    st.divider()
    st.markdown("### 📚 Recomendações de Leitura (Base de Dados)")
    if estado.get("referencias_rag"):
        for ref in estado["referencias_rag"]:
            st.markdown(ref)
    else:
        st.markdown("*O Agente Bibliotecário não encontrou referências estritamente ligadas a este trecho.*")