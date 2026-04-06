import psycopg2
from pgvector.psycopg2 import register_vector
from langchain_ollama import OllamaEmbeddings

# 1. Inicializa o gerador de embeddings local
gerador_vetores = OllamaEmbeddings(model="nomic-embed-text")

def conectar_banco():
    # Substitua 'sua_nova_senha' pela senha que você criou
    conn = psycopg2.connect(
        dbname="IA_Project", 
        user="postgres", 
        password="072485", 
        host="localhost", 
        port="5432"
    )
    # Ensina o psycopg2 a lidar com o tipo 'vector' do pgvector
    register_vector(conn)
    return conn

def inicializar_tabela():
    conn = conectar_banco()
    cur = conn.cursor()
    
    # Cria a tabela caso ela não exista
    cur.execute("""
        CREATE TABLE IF NOT EXISTS exemplos_revisao (
            id SERIAL PRIMARY KEY,
            categoria VARCHAR(50) NOT NULL,
            texto_ruim TEXT NOT NULL,
            texto_corrigido TEXT NOT NULL,
            explicacao TEXT,
            embedding vector(768)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("[DB] Tabela 'exemplos_revisao' verificada/criada com sucesso.")

def inserir_exemplo(categoria: str, texto_ruim: str, texto_corrigido: str, explicacao: str):
    print(f"[Embedding] Gerando vetor para a categoria: {categoria}...")
    
    # O vetor é gerado baseado no texto ruim, pois é ele que o aluno vai digitar e precisamos dar o 'match'
    vetor = gerador_vetores.embed_query(texto_ruim)
    
    conn = conectar_banco()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO exemplos_revisao (categoria, texto_ruim, texto_corrigido, explicacao, embedding)
        VALUES (%s, %s, %s, %s, %s)
    """, (categoria, texto_ruim, texto_corrigido, explicacao, vetor))
    
    conn.commit()
    cur.close()
    conn.close()
    print("[DB] Exemplo inserido com sucesso!")

if __name__ == "__main__":
    # Teste de execução: Cria a tabela e insere o nosso primeiro antipadrão
    inicializar_tabela()
    
    inserir_exemplo(
        categoria="Primeira Pessoa",
        texto_ruim="Eu decidi criar um app pra ajudar os alunos a estudar, pq eu acho que vai ser daora.",
        texto_corrigido="O presente projeto propõe o desenvolvimento de um aplicativo com o intuito de auxiliar no processo de aprendizagem dos discentes.",
        explicacao="Em textos acadêmicos, deve-se evitar o uso da primeira pessoa do singular e gírias. Prefira a voz passiva e vocabulário formal."
    )