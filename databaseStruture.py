import os
from dotenv import load_dotenv
import psycopg2
from pgvector.psycopg2 import register_vector
import requests
from langchain_community.embeddings import HuggingFaceEmbeddings
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import time

# Força o carregamento do .env
load_dotenv(override=True)

# Inicialização do Gerador de Vetores (Rodando 100% Local e sem limites)
print("[Sistema] Carregando motor de Embeddings local...")

gerador_vetores = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-base",
    model_kwargs={'device': 'cpu'}, # Força o uso do seu processador
    encode_kwargs={'normalize_embeddings': True} # Melhora a precisão da busca
)

def conectar_local():
    """Conexão de fallback para uso em casa"""
    db_url = os.environ.get("DATABASE_URL_LOCAL")
    conn = psycopg2.connect(db_url)
    register_vector(conn)
    return conn

def processar_pdf_e_salvar(arquivo_upload):
    """Lê o PDF, cria o Documento Pai e insere os Blocos Filhos no Supabase"""
    ambiente = os.getenv("AMBIENTE", "producao")
    print(f"[{ambiente.upper()}] Estruturando PDF relacional: {arquivo_upload.name}...")
    
    # 1. Extrai o texto do PDF
    leitor = PdfReader(arquivo_upload)
    texto_completo = ""
    for pagina in leitor.pages:
        texto_extraido = pagina.extract_text()
        if texto_extraido:
            texto_completo += texto_extraido + "\n"
            
    # 2. Corta o texto em blocos de 1000 caracteres
    divisor = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    blocos = divisor.split_text(texto_completo)
    
    if ambiente == "producao":
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        headers_pai = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation" 
        }
        
        # --- A) CRIA O DOCUMENTO PAI ---
        url_docs = f"{supabase_url}/rest/v1/documentos"
        dados_doc = {"titulo": arquivo_upload.name, "autores": "Base de Conhecimento RAG"}
        res_doc = requests.post(url_docs, headers=headers_pai, json=dados_doc)
        
        if res_doc.status_code not in (200, 201):
            print(f"[ERRO API] Falha ao criar documento pai: {res_doc.text}")
            return
            
        doc_id = res_doc.json()[0]["id"] 
        
        # --- B) CRIA OS BLOCOS FILHOS ---
        url_blocos = f"{supabase_url}/rest/v1/blocos_vetores"
        headers_filhos = headers_pai.copy()
        headers_filhos["Prefer"] = "return=minimal" 
        
        sessao_supabase = requests.Session()

        for bloco in blocos:
            vetor = gerador_vetores.embed_query(bloco)
            dados_bloco = {
                "documento_id": doc_id,  
                "texto_bloco": bloco,
                "embedding": vetor
            }
            # Substitua requests.post por sessao_supabase.post
            resposta = sessao_supabase.post(url_blocos, headers=headers_filhos, json=dados_bloco)
            
            # Um respiro de apenas 0.2 segundos (bem mais rápido que o 1s de antes)
            time.sleep(0.2)
            
        print("[API] Documento Pai e Blocos Filhos indexados com sucesso!")

def buscar_artigos_similares(texto_busca, limite=5):
    import os
    import requests
    
    # Prepara as variáveis de conexão exclusivas para a busca
    url_rpc = f"{os.environ.get('SUPABASE_URL')}/rest/v1/rpc/match_blocos"
    headers_rpc = {
        "apikey": os.environ.get("SUPABASE_KEY"),
        "Authorization": f"Bearer {os.environ.get('SUPABASE_KEY')}",
        "Content-Type": "application/json"
    }
    
    # O SEGREDO DO MODELO E5: Adicionar 'query: ' antes do texto
    texto_formatado = f"query: {texto_busca}"
    
    vetor_busca = gerador_vetores.embed_query(texto_formatado)
    
    dados = {
        "query_embedding": vetor_busca,
        "match_threshold": 0.1, 
        "match_count": limite
    }
    
    try:
        resposta = requests.post(url_rpc, headers=headers_rpc, json=dados)
        resposta.raise_for_status()
        return resposta.json()
    except Exception as e:
        print(f"[ERRO RAG] Falha ao buscar no Supabase: {e}")
        return []