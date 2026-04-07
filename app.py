import streamlit as st
from main import compilar_grafo
from databaseStruture import processar_pdf_e_salvar

# Configuração da página (Tema claro/escuro automático)
st.set_page_config(page_title="Revisor Acadêmico IA", page_icon="🎓", layout="wide")

# ==========================================
# BARRA LATERAL (ESTILO NOTEBOOKLM)
# ==========================================
with st.sidebar:
    st.header("📚 Base de Conhecimento")
    st.markdown("Faça upload de PDFs para a IA usar como referência teórica (RAG).")
    
    arquivo_pdf = st.file_uploader("Anexar Documento", type=["pdf"])
    
    # Gerencia a lista de PDFs na memória do navegador
    if "pdfs_salvos" not in st.session_state:
        st.session_state.pdfs_salvos = []
        
    if arquivo_pdf:
        if st.button("➕ Injetar no Banco de Dados", use_container_width=True):
            with st.spinner("Vetorizando o PDF e enviando para a nuvem..."):
                processar_pdf_e_salvar(arquivo_pdf)
                if arquivo_pdf.name not in st.session_state.pdfs_salvos:
                    st.session_state.pdfs_salvos.append(arquivo_pdf.name)
                st.success("PDF indexado com sucesso!")
                
    st.divider()
    st.subheader("Fontes Ativas:")
    if st.session_state.pdfs_salvos:
        for pdf in st.session_state.pdfs_salvos:
            st.markdown(f"📄 `{pdf}`")
    else:
        st.caption("Nenhum documento anexado nesta sessão.")

# ==========================================
# ÁREA PRINCIPAL
# ==========================================
st.title("🎓 Assistente Multiagente Acadêmico")
st.markdown("Escreva ou cole seu rascunho. O **Orientador**, o **Revisor** e o **Bibliotecário** farão a análise conjunta.")

if "grafo" not in st.session_state:
    st.session_state.grafo = compilar_grafo()
    st.session_state.config = {"configurable": {"thread_id": "sessao_web_notebook"}}

texto_usuario = st.text_area("Seu Rascunho:", height=200, placeholder="Ex: O presente trabalho visa investigar...")

if st.button("🚀 Iniciar Análise da Banca", type="primary"):
    if not texto_usuario:
        st.warning("Insira algum texto antes de chamar os agentes.")
    else:
        with st.spinner("Os agentes estão debatendo o seu texto... Aguarde."):
            estado_input = {
                "rascunho_atual": texto_usuario,
                "comentarios_metodologia": [],
                "comentarios_revisao": [],
                "referencias": [],
                "status_aprovacao": False
            }
            
            for evento in st.session_state.grafo.stream(estado_input, st.session_state.config):
                pass
            
            estado_salvo = st.session_state.grafo.get_state(st.session_state.config)
            valores = estado_salvo.values
            
            st.toast("Análise finalizada!", icon="✅")
            
            # Cards de visualização (Container com bordas)
            col1, col2 = st.columns(2)
            
            with col1:
                with st.container(border=True):
                    st.subheader("👨‍🏫 Orientador Metodológico")
                    st.write(valores['comentarios_metodologia'][-1])
                    
            with col2:
                with st.container(border=True):
                    st.subheader("✍️ Corretor ABNT / Gramática")
                    st.write(valores['comentarios_revisao'][-1])
            
            # O bibliotecário ganha um bloco inteiro só para ele embaixo
            with st.container(border=True):
                st.subheader("📚 Agente Bibliotecário (RAG)")
                referencias = valores.get('referencias', [])
                if referencias and "Nenhum" not in referencias[0]:
                    for ref in referencias:
                        st.success(ref)
                else:
                    st.info("Nenhuma conexão semântica forte foi encontrada entre o seu texto e os PDFs da base.")