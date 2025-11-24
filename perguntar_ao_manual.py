import pgvector
import psycopg2
import requests
import sys
import json
import pgvector.psycopg2

db_name = 'detrannormas'
db_user = 'postgres'
db_pass = 'psswrd'
db_host = '172.30.151.166'
db_port = '5432'

ollama_chat_model = "qwen2.5:1.5b"
ollama_embed_model = "nomic-embed-text:latest"
ollama_base_url = f"http://{db_host}:11434"
ollama_api_embed = f"{ollama_base_url}/api/embeddings"
ollama_api_chat = f"{ollama_base_url}/api/chat"

def conectadb():
    """conexão com o Postgre SQL"""
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port,
        )
        print(conn)
        return conn
    except psycopg2.Error as e:
        print(f"Erro de Conexão com o Banco: {e}")
        return None
    
def embedtext(text):  
    try:  
        resposta = requests.post(  
            ollama_api_embed,  
            json={"model": ollama_embed_model, "prompt": text}    
        )  
        resposta.raise_for_status()  
        return resposta.json()['embedding']  
    except requests.RequestException as e:  
        print(f"Erro ao vetorizar: {e}")  
        return None
    
def encontrarregras(conn, pergunta_vetor, top_k = 10):
    cursor = conn.cursor()
    """Busca as regras mais similares no banco. top_k=10 aumenta a precisão."""
    query = """
    SELECT descricao_regra, exemplo, padrao_sintaxe 
    FROM regras_nomenclatura
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
    """
    cursor.execute(query, (list(pergunta_vetor), top_k))
    return cursor.fetchall()

def perguntaollama(pergunta, contexto):
    """Envia o contexto e a pergunta com resposta em TEMPO REAL (Streaming)."""
    contexto_str = "\n".join(

        f"- Regra: {regra} | Exemplo: {exemplo} | Padrão: {sintaxe}" 
        for regra, exemplo, sintaxe in contexto
    )
    print(f"\n[DEBUG - O QUE O BANCO ENCONTROU]:\n{contexto_str}\n")
    print("#"*10)

    print(" Resposta da ia:")
    print("#"*10)

    prompt_completo = f"""Você é um assistente especialista no manual do DETRAN-PE.
Use o contexto abaixo para responder a pergunta de forma direta e técnica.
Contexto:
{contexto_str}

Pergunta: {pergunta}
Resposta:"""
    try:
        resposta = requests.post(
            ollama_api_chat,
            json={
                "model": ollama_chat_model,
                "messages": [
                    {"role": "system", "content": "Você é um assistente útil e técnico."},
                    {"role": "user", "content": prompt_completo}
                ],
                "stream": True
            },
            stream=True
        )
        resposta.raise_for_status()
        resposta_completa = ""

        for line in resposta.iter_lines():
            if line:
                try:
                    json_data = json.loads(line.decode('utf-8'))
                    if 'message' in json_data:
                        content = json_data['message']['content']

                        print(content, end='', flush=True) 
                        resposta_completa += content

                except ValueError:
                    pass
        print("\n") 
        return resposta_completa
    except Exception as e:
        return f"\n Erro técnico: {e}"

def main():
    if len(sys.argv) < 2:
        print('Uso correto: python perguntar_ao_manual.py "Sua pergunta entre aspas"')
        return
    pergunta = sys.argv[1]

    print(f" Analisando pergunta: '{pergunta}'")

    conn = conectadb()
    if not conn: return

    vetor = embedtext(pergunta)
    if not vetor: return

    contexto = encontrarregras(conn, vetor)
    if not contexto:
        print(" Nenhuma regra relevante encontrada no banco.")

        return
    print(f"Regras recuperadas: {len(contexto)}")

    perguntaollama(pergunta, contexto)
    conn.close()
if __name__ == "__main__":

    main()
