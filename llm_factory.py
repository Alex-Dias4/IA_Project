import psutil
from langchain_ollama import ChatOllama

def get_llm_model() -> ChatOllama:
    # Obtém a memória RAM total em Gigabytes
    ram_total_gb = psutil.virtual_memory().total / (1024 ** 3)
    
    # Acima de 16GB (Lab da faculdade)
    if ram_total_gb > 16:
        print(f"[Config] Memória: {ram_total_gb:.1f}GB. Carregando Llama 3...")
        return ChatOllama(model="llama3")
    
    # Até 16GB (Notebook atual)
    else:
        print(f"[Config] Memória: {ram_total_gb:.1f}GB. Carregando phi3:mini...")
        return ChatOllama(model="phi3:mini")