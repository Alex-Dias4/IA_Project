import os
from dotenv import load_dotenv
import psycopg2
from pgvector.psycopg2 import register_vector
import requests
from langchain_ollama import OllamaEmbeddings
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Força o carregamento das variáveis do .env
load_dotenv(override=True)

# Inicializa o gerador de embeddings local
gerador_vetores = OllamaEmbeddings(model="nomic-embed-text")

def conectar_local():
    """Conecta ao PostgreSQL local via psycopg2 (Porta 5432)"""
    db_url = os.environ.get("DATABASE_URL_LOCAL")
    conn = psycopg2.connect(db_url)
    register_vector(conn)
    return conn

def inserir_exemplo(categoria: str, texto_ruim: str, texto_corrigido: str, explicacao: str):
    """Insere o dado escolhendo a rota (Local ou Online via API REST Direta)"""
    ambiente = os.getenv("AMBIENTE", "local")
    
    print(f"[{ambiente.upper()}] Gerando vetor para a categoria: {categoria}...")
    vetor = gerador_vetores.embed_query(texto_ruim)
    
    if ambiente == "producao":
        # === ROTA 1: ONLINE (VIA REQUESTS HTTP - ZERO DEPENDÊNCIAS C++) ===
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        # A URL aponta direto para a tabela "exemplos_revisao"
        endpoint = f"{supabase_url}/rest/v1/exemplos_revisao"
        
        # Cabeçalhos de autenticação do Supabase
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        # O pacote de dados
        dados = {
            "categoria": categoria,
            "texto_ruim": texto_ruim,
            "texto_corrigido": texto_corrigido,
            "explicacao": explicacao,
            "embedding": vetor
        }
        
        # Dispara para a internet
        resposta = requests.post(endpoint, headers=headers, json=dados)
        
        if resposta.status_code in (200, 201):
            print("[API] Inserção online no Supabase concluída com sucesso!")
        else:
            print(f"[Erro API] Falha ao inserir: {resposta.text}")
            
    else:
        # === ROTA 2: LOCAL (VIA SQL DIRETO) ===
        conn = conectar_local()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO exemplos_revisao (categoria, texto_ruim, texto_corrigido, explicacao, embedding)
            VALUES (%s, %s, %s, %s, %s)
        """, (categoria, texto_ruim, texto_corrigido, explicacao, vetor))
        conn.commit()
        cur.close()
        conn.close()
        print("[DB Local] Inserção no Postgres local concluída com sucesso via SQL!")
    
def inserir_artigo_global(titulo: str, autores: str, resumo: str):
    """Insere um artigo de referência no catálogo global"""
    ambiente = os.getenv("AMBIENTE", "local")
    print(f"[{ambiente.upper()}] Gerando vetor para o artigo: {titulo}...")
    vetor = gerador_vetores.embed_query(resumo)
    
    if ambiente == "producao":
        url = f"{os.environ.get('SUPABASE_URL')}/rest/v1/artigos_globais"
        headers = {
            "apikey": os.environ.get("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.environ.get('SUPABASE_KEY')}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        dados = {"titulo": titulo, "autores": autores, "resumo_conceitual": resumo, "embedding": vetor}
        requests.post(url, headers=headers, json=dados)
        print("[API] Artigo global inserido com sucesso!")
    else:
        conn = conectar_local()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO artigos_globais (titulo, autores, resumo_conceitual, embedding)
            VALUES (%s, %s, %s, %s)
        """, (titulo, autores, resumo, vetor))
        conn.commit()
        cur.close()
        conn.close()

def buscar_artigos_similares(texto_aluno: str, limite: int = 2):
    """Busca os artigos com maior proximidade semântica ao texto do aluno"""
    ambiente = os.getenv("AMBIENTE", "local")
    vetor_busca = gerador_vetores.embed_query(texto_aluno)
    
    if ambiente == "producao":
        # Chama a função SQL (RPC) que criamos no painel do Supabase
        url = f"{os.environ.get('SUPABASE_URL')}/rest/v1/rpc/match_artigos"
        headers = {
            "apikey": os.environ.get("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.environ.get('SUPABASE_KEY')}",
            "Content-Type": "application/json"
        }
        dados = {
            "query_embedding": vetor_busca,
            "match_threshold": 0.1, # Traz artigos com pelo menos 30% de aderência ao texto
            "match_count": limite
        }
        resposta = requests.post(url, headers=headers, json=dados)
        return resposta.json() # Retorna uma lista de dicionários com os artigos encontrados
    else:
        conn = conectar_local()
        cur = conn.cursor()
        cur.execute("""
            SELECT titulo, autores, resumo_conceitual 
            FROM artigos_globais 
            ORDER BY embedding <-> %s::vector 
            LIMIT %s
        """, (vetor_busca, limite))
        resultados = cur.fetchall()
        cur.close()
        conn.close()
        # Formata o retorno local para ficar igual ao retorno da nuvem
        return [{"titulo": r[0], "autores": r[1], "resumo_conceitual": r[2]} for r in resultados]
    
def processar_pdf_e_salvar(arquivo_upload):
    """Lê um PDF, salva o documento Pai e depois insere os blocos Filhos no Supabase"""
    ambiente = os.getenv("AMBIENTE", "producao")
    print(f"[{ambiente.upper()}] Estruturando PDF relacional: {arquivo_upload.name}...")
    
    # 1. Extrai o texto
    leitor = PdfReader(arquivo_upload)
    texto_completo = ""
    for pagina in leitor.pages:
        texto_extraido = pagina.extract_text()
        if texto_extraido:
            texto_completo += texto_extraido + "\n"
            
    # 2. Corta o texto
    divisor = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    blocos = divisor.split_text(texto_completo)
    
    if ambiente == "producao":
        import requests
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        # Cabeçalho exigindo que o Supabase DEVOLVA os dados após inserir (para pegarmos o ID)
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
            
        # Pega o ID (UUID) que o Supabase acabou de gerar para este PDF
        doc_id = res_doc.json()[0]["id"] 
        
        # --- B) CRIA OS BLOCOS FILHOS ---
        url_blocos = f"{supabase_url}/rest/v1/blocos_vetores"
        headers_filhos = headers_pai.copy()
        headers_filhos["Prefer"] = "return=minimal" # Não precisa devolver os blocos, só salvar
        
        for i, bloco in enumerate(blocos):
            vetor = gerador_vetores.embed_query(bloco)
            dados_bloco = {
                "documento_id": doc_id,  # A Chave Estrangeira ligando o bloco ao PDF!
                "texto_bloco": bloco,
                "embedding": vetor
            }
            requests.post(url_blocos, headers=headers_filhos, json=dados_bloco)
            
        print("[API] Documento Pai e Blocos Filhos indexados com sucesso!")
        
    else:
        # Lógica de conexão local (Postgres)
        conn = conectar_local()
        cur = conn.cursor()
        
        # Insere Pai e retorna ID
        cur.execute("""
            INSERT INTO documentos (titulo, autores) VALUES (%s, %s) RETURNING id
        """, (arquivo_upload.name, "Base de Conhecimento RAG"))
        doc_id = cur.fetchone()[0]
        
        # Insere Filhos
        for bloco in blocos:
            vetor = gerador_vetores.embed_query(bloco)
            cur.execute("""
                INSERT INTO blocos_vetores (documento_id, texto_bloco, embedding)
                VALUES (%s, %s, %s)
            """, (doc_id, bloco, vetor))
            
        conn.commit()
        cur.close()
        conn.close()
        print("[DB Local] Documento Pai e Blocos Filhos indexados com sucesso!")
    
if __name__ == "__main__":
    # Inserindo um artigo real para teste
    inserir_artigo_global(
        titulo="Arquitetura de Microsserviços no Ensino Público",
        autores="Silva, M.; Pereira, J.",
        resumo="Este estudo analisa a transição de sistemas monolíticos para microsserviços em instituições federais, destacando a melhoria no tempo de resposta das APIs educacionais e a escalabilidade no registro de alunos."
    )
    
    # Simulando o Agente buscando algo baseado no texto do aluno
    rascunho_aluno = "A gente quer melhorar o sistema da escola separando tudo em pequenos serviços pra ficar mais rápido."
    print("\n[Agente Bibliotecário] Buscando referências...")
    artigos = buscar_artigos_similares(rascunho_aluno)
    
    for art in artigos:
        print(f"-> Referência Sugerida: {art['titulo']} ({art['autores']})")