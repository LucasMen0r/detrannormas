import psycopg2
import requests
import sys
import json
import pgvector.psycopg2  # Essencial para o vetor funcionar

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
DB_NAME = "detrannormas"      # Nome confirmado com 's'
DB_USER = "ollama_trainer"
DB_PASS = "password"             # A senha que definimos por último
DB_HOST = "localhost"
DB_PORT = "5432"

# --- CONFIGURAÇÃO DO OLLAMA ---
# Modelo leve e eficiente que definimos (Qwen 2.5 1.5B)
OLLAMA_CHAT_MODEL = "qwen2.5:1.5b"
OLLAMA_EMBED_MODEL = "nomic-embed-text"
OLLAMA_API_EMBED = "http://localhost:11434/api/embeddings"
OLLAMA_API_CHAT = "http://localhost:11434/api/chat"

def get_db_connection():
    """Conecta ao banco PostgreSQL."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.Error as e:
        print(f"❌ Erro de Conexão com o Banco: {e}")
        return None

def get_embedding(text):
    """Gera o vetor da pergunta usando o Ollama."""
    try:
        response = requests.post(
            OLLAMA_API_EMBED,
            json={"model": OLLAMA_EMBED_MODEL, "prompt": text}
        )
        response.raise_for_status()
        return response.json()['embedding']
    except Exception as e:
        print(f"❌ Erro ao vetorizar: {e}")
        return None

def find_relevant_rules(pergunta_vetor, conn, top_k=6):
    """Busca as regras mais similares no banco. top_k=6 aumenta a precisão."""
    cursor = conn.cursor()
    
    # O segredo do sucesso: %s::vector para forçar o tipo correto
    query = """
    SELECT descricao_regra, exemplo, padrao_sintaxe 
    FROM regras_nomenclatura
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
    """
    cursor.execute(query, (list(pergunta_vetor), top_k))
    return cursor.fetchall()

def ask_ollama(pergunta, contexto):
    """Envia o contexto e a pergunta com resposta em TEMPO REAL (Streaming)."""
    
    contexto_str = "\n".join(
        f"- Regra: {regra} | Exemplo: {exemplo or 'N/A'} | Padrão: {sintaxe or 'N/A'}" 
        for regra, exemplo, sintaxe in contexto
    )

    print(f"\n[DEBUG - O QUE O BANCO ENCONTROU]:\n{contexto_str}\n")
    print("="*50)
    print("🤖 RESPOSTA DA IA (Escrevendo...):")
    print("="*50)
    
    prompt_completo = f"""Você é um assistente especialista no manual do DETRAN-PE.
Use o contexto abaixo para responder a pergunta de forma direta e técnica.

Contexto:
{contexto_str}

Pergunta: {pergunta}

Resposta:"""

    try:
        # stream=True faz a resposta chegar letra por letra
        response = requests.post(
            OLLAMA_API_CHAT,
            json={
                "model": OLLAMA_CHAT_MODEL,
                "messages": [
                    {"role": "system", "content": "Você é um assistente útil e técnico."},
                    {"role": "user", "content": prompt_completo}
                ],
                "stream": True
            },
            stream=True
        )
        
        response.raise_for_status()
        
        resposta_completa = ""
        
        # Loop que imprime cada pedacinho assim que chega
        for line in response.iter_lines():
            if line:
                try:
                    json_data = json.loads(line.decode('utf-8'))
                    if 'message' in json_data:
                        content = json_data['message']['content']
                        # end='' impede de pular linha a cada letra
                        print(content, end='', flush=True) 
                        resposta_completa += content
                except ValueError:
                    pass
                    
        print("\n") # Pula linha no final para ficar bonito
        return resposta_completa

    except Exception as e:
        return f"\n❌ Erro técnico: {e}"

def main():
    if len(sys.argv) < 2:
        print('Uso correto: python3 perguntar_ao_manual.py "Sua pergunta entre aspas"')
        return

    pergunta = sys.argv[1]
    print(f"🔍 Analisando pergunta: '{pergunta}'...")

    conn = get_db_connection()
    if not conn: return

    # 1. Vetorizar
    vetor = get_embedding(pergunta)
    if not vetor: return

    # 2. Buscar (RAG)
    contexto = find_relevant_rules(vetor, conn)
    if not contexto:
        print("⚠️ Nenhuma regra relevante encontrada no banco.")
        return
    
    print(f"📚 Regras recuperadas: {len(contexto)}")

    # 3. Gerar Resposta
    ask_ollama(pergunta, contexto)
    
    conn.close()

if __name__ == "__main__":
    main()
