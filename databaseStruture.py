import os
import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
from langchain_community.embeddings import OllamaEmbeddings

# Carrega as variáveis do .env
load_dotenv()

gerador_vetores = OllamaEmbeddings(model="nomic-embed-text")

def conectar_banco():
    ambiente = os.getenv("AMBIENTE", "local")
    
    if ambiente == "producao":
        db_url = os.getenv("DATABASE_URL_PROD")
        print("[DB] Conectando ao Supabase (Nuvem)...")
    else:
        db_url = os.getenv("DATABASE_URL_LOCAL")
        print("[DB] Conectando ao banco LOCAL...")
        
    conn = psycopg2.connect(db_url)
    register_vector(conn)
    return conn


>>>>>>> 883a9a1 (iniciando versão com datbase online)
def inicializar_tabela():
    conn = conectar_banco()
    cur = conn.cursor()
    
    # 1. Tabela de Usuários
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nome VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Catálogo Global de Artigos (Índice de RAG para o Agente Bibliotecário)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS artigos_globais (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            titulo VARCHAR(255) NOT NULL,
            autores VARCHAR(255) NOT NULL,
            ano INT,
            doi VARCHAR(100),
            resumo_conceitual TEXT NOT NULL,
            tags VARCHAR(150),
            embedding vector(768),
            adicionado_por UUID REFERENCES usuarios(id) ON DELETE SET NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. Workspace Privado (Rascunhos e Documentos em andamento do aluno)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documentos_privados (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
            titulo_projeto VARCHAR(255),
            conteudo_texto TEXT NOT NULL,
            embedding_conteudo vector(768), 
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 4. Tabela de Exemplos de Revisão (Few-Shot Prompting Dinâmico)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS exemplos_revisao (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            categoria VARCHAR(50) NOT NULL,
            texto_ruim TEXT NOT NULL,
            texto_corrigido TEXT NOT NULL,
            explicacao TEXT,
            embedding vector(768)
        );
    """)

    # 5. Índices HNSW para otimização de busca vetorial
    cur.execute("CREATE INDEX IF NOT EXISTS idx_artigos_embedding ON artigos_globais USING hnsw (embedding vector_l2_ops);")
    
    # CORREÇÃO AQUI: Alterado de 'embedding' para 'embedding_conteudo'
    cur.execute("CREATE INDEX IF NOT EXISTS idx_doc_priv_embedding ON documentos_privados USING hnsw (embedding_conteudo vector_l2_ops);")
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_exemplos_embedding ON exemplos_revisao USING hnsw (embedding vector_l2_ops);")

    conn.commit()
    cur.close()
    conn.close()
    print("[DB] Estrutura global, privada e índices vetoriais criados com sucesso.")

if __name__ == "__main__":
    inicializar_tabela()