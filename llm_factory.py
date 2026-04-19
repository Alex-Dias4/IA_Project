import os
import psutil
import requests
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq

def verificar_modelo_ollama(nome_modelo="llama3"):
    """
    Faz um 'ping' silencioso na porta 11434 para ver se o Ollama está ligado
    e verifica se o modelo exigido já foi baixado.
    """
    try:
        # Tenta bater na porta local do Ollama. Timeout curtinho para não travar o site.
        resposta = requests.get("http://localhost:11434/api/tags", timeout=2)
        
        if resposta.status_code == 200:
            modelos = resposta.json().get("models", [])
            # Varre a lista de modelos instalados
            for m in modelos:
                # Checa se é exatamente "llama3" ou alguma variação como "llama3:latest"
                if m.get("name") == nome_modelo or m.get("name").startswith(f"{nome_modelo}:"):
                    return True
        return False
    except requests.exceptions.RequestException:
        # Se der erro de conexão, significa que o app do Ollama está fechado
        return False

def get_llm_model():
    # Obtém a memória RAM total em Gigabytes
    ram_total_gb = psutil.virtual_memory().total / (1024 ** 3)
    
    # 1. TENTA RODAR LOCALMENTE SE TIVER RAM SUFICIENTE
    if ram_total_gb > 16:
        print(f"[Config] Memória: {ram_total_gb:.1f}GB. Verificando disponibilidade do Ollama...")
        
        if verificar_modelo_ollama("llama3"):
            print("[Config] Ollama e Llama 3 detectados! Carregando processamento local...")
            return ChatOllama(model="llama3")
        else:
            print("[Config] Ollama desligado ou modelo ausente. Fazendo fallback para a nuvem...")
    
    # 2. SE TEM POUCA RAM (OU SE O OLLAMA FALHOU ACIMA), VAI PARA A GROQ
    else:
        print(f"[Config] Memória: {ram_total_gb:.1f}GB. Direcionando processamento para a nuvem...")
        
    print("[Config] Conectando à API da Groq (LPU)...")
    chave_groq = os.environ.get("GROQ_API_KEY")
    
    if not chave_groq:
        raise ValueError("Erro fatal: GROQ_API_KEY não encontrada no arquivo .env!")
        
    return ChatGroq(
        model="llama-3.1-8b-instant", # <-- Atualizado para o modelo novo e suportado!
        temperature=0.1,        
        api_key=chave_groq
    )