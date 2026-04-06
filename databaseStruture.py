import os
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_ollama import OllamaEmbeddings

# Força o carregamento do .env
load_dotenv(override=True)

# Inicializa o gerador de embeddings local
gerador_vetores = OllamaEmbeddings(model="nomic-embed-text")

def conectar_supabase() -> Client:
    """Cria a conexão HTTPS com o Supabase usando as chaves da API"""
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("Chaves do Supabase não encontradas no arquivo .env")
        
    return create_client(url, key)

def inserir_exemplo(categoria: str, texto_ruim: str, texto_corrigido: str, explicacao: str):
    """Insere um exemplo de erro no banco convertido em vetor via API"""
    print(f"[API] Gerando vetor matemático para a categoria: {categoria}...")
    
    # 1. Converte o texto ruim em vetor usando o Nomic local
    vetor = gerador_vetores.embed_query(texto_ruim)
    
    # 2. Conecta ao Supabase
    supabase = conectar_supabase()
    
    # 3. Monta o pacote de dados (JSON)
    dados = {
        "categoria": categoria,
        "texto_ruim": texto_ruim,
        "texto_corrigido": texto_corrigido,
        "explicacao": explicacao,
        "embedding": vetor
    }
    
    # 4. Envia via requisição HTTPS (Porta 443 - Passa pelo firewall)
    resposta = supabase.table("exemplos_revisao").insert(dados).execute()
    
    print("[API] Inserção concluída com sucesso via web!")
    return resposta

if __name__ == "__main__":
    # Teste de execução enviando o primeiro exemplo
    inserir_exemplo(
        categoria="Primeira Pessoa",
        texto_ruim="Eu decidi criar um app pra ajudar os alunos a estudar, pq eu acho que vai ser daora.",
        texto_corrigido="O presente projeto propõe o desenvolvimento de um aplicativo com o intuito de auxiliar no processo de aprendizagem dos discentes.",
        explicacao="Em textos acadêmicos, deve-se evitar o uso da primeira pessoa do singular e gírias. Prefira a voz passiva e vocabulário formal."
    )