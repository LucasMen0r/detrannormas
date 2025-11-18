# Projeto RAG - Manual DETRAN-PE (Consulta Local com IA)

![Status](https://img.shields.io/badge/status-Prova%20de%20Conceito%20(PoC)-green)

Este é um sistema de **RAG (Retrieval-Augmented Generation)** desenvolvido para permitir consultas em linguagem natural ao "Manual de Padrão de Nomenclatura de Banco de Dados" do DETRAN-PE.

O projeto foi desenhado para rodar **100% offline** em ambientes corporativos restritos, utilizando modelos de IA locais (via Ollama) e um banco de dados vetorial (PostgreSQL + pgvector) para garantir total privacidade e performance sem depender de APIs externas.

## 🚀 Funcionalidades Principais

* **Consulta em Linguagem Natural:** Pergunte coisas como "Qual o padrão para chaves estrangeiras?" em vez de ler o PDF.
* **100% Offline:** Nenhuma informação (nem as perguntas, nem os dados do manual) sai da rede local.
* **RAG (Geração Aumentada por Recuperação):** O sistema primeiro busca os trechos mais relevantes do manual no banco vetorial e *depois* usa a IA para gerar uma resposta baseada nesses trechos, evitando alucinações.
* **Contornorno de Firewall:** Inclui métodos de instalação de modelos (GGUF) que funcionam mesmo em redes com inspeção SSL/TLS.

---

## 🛠️ Stack de Tecnologia

* **Linguagem:** Python 3.10+
* **Servidor de IA:** Ollama
* **Modelos de IA:**
    * **Vetorização (Embedding):** `nomic-embed-text`
    * **Geração de Resposta (Chat):** `qwen2.5:1.5b` (Otimizado para CPU)
* **Banco de Dados:** PostgreSQL 16
* **Extensão Vetorial:** `pgvector`

---

## ⚙️ Guia de Instalação e Configuração

Este guia assume a instalação em um ambiente **WSL2 (Ubuntu)** dentro de uma rede corporativa restrita.

### 1. Pré-requisitos

* WSL2 (Windows Subsystem for Linux)
* Git
* Servidor PostgreSQL 16 instalado no WSL
* Ollama instalado no WSL

### 2. Configuração do Banco de Dados (PostgreSQL)

O método mais rápido é **restaurar o backup completo**, que já contém todas as tabelas, regras e os vetores calculados.

```bash
# 1. Crie o usuário (use a senha '12345' ou atualize os scripts)
sudo -u postgres createuser -P ollama_trainer

# 2. Crie o banco de dados vazio
sudo -u postgres createdb detrannormas -O ollama_trainer

# 3. (Dentro do psql) Ative a extensão OBRIGATÓRIA
sudo -u postgres psql -d detrannormas -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 4. Restaure o backup completo (MUITO IMPORTANTE)
# Isso carrega as regras E os vetores, pulando a indexação.
psql -h localhost -U ollama_trainer -d detrannormas <setup_inicial.sql
```
*(Se preferir criar as tabelas do zero, use o `setup_inicial.sql` e depois rode o `indexar_banco.py`)*

### 3. Configuração do Ollama (Método Offline)

Em redes restritas, o `ollama pull` falha. Use este método manual (GGUF) para instalar os modelos:

1.  **Baixe os Modelos no Windows** (use o navegador, que confia no firewall):
    * **Nomic (Vetor):** [Baixar nomic-embed-text-v1.5.Q4_K_M.gguf](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/nomic-embed-text-v1.5.Q4_K_M.gguf?download=true)
    * **Qwen (Chat):** [Baixar qwen2.5-1.5b-instruct-q4_k_m.gguf](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf?download=true)

2.  **Mova os arquivos para o WSL** (substitua `SEU_USUARIO`):
    ```bash
    cp /mnt/c/Users/SEU_USUARIO/Downloads/nomic-embed-text-v1.5.Q4_K_M.gguf ./nomic.gguf
    cp /mnt/c/Users/SEU_USUARIO/Downloads/qwen2.5-1.5b-instruct-q4_k_m.gguf ./qwen.gguf
    ```

3.  **Crie os modelos no Ollama (Offline):**
    ```bash
    # Criar Nomic
    echo "FROM ./nomic.gguf" > Modelfile_Nomic
    ollama create nomic-embed-text -f Modelfile_Nomic

    # Criar Qwen
    echo "FROM ./qwen.gguf" > Modelfile_Qwen
    ollama create qwen2.5:1.5b -f Modelfile_Qwen
    ```

### 4. Configuração do Ambiente Python

1.  **Clone o repositório:**
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO]
    cd [NOME_DO_REPOSITORIO]
    ```

2.  **Crie e ative o ambiente virtual:**
    ```bash
    python3 -m venv testedbdetran
    source testedbdetran/bin/activate
    ```

3.  **Instale as dependências (Modo Anti-Firewall):**
    *Se o `pip install` normal falhar por SSL, use o comando "teimoso":*
    ```bash
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
    ```

---

## 🚀 Como Usar o Sistema

O sistema exige **dois terminais** rodando simultaneamente.

### Terminal 1: Servidor de IA (Ollama)

Este terminal deve ficar aberto o tempo todo, servindo os modelos de IA.

```bash
ollama serve
```
*(Se o `ollama pull` falhar, você pode precisar iniciar com `OLLAMA_SKIP_TLS_VERIFY=true ollama serve`)*

### Terminal 2: Aplicação Python

Use este terminal para fazer as perguntas.

```bash
# 1. Ative o ambiente (se ainda não estiver)
source testedbdetran/bin/activate

# 2. Faça sua pergunta!
python3 perguntar_ao_manual.py "Como eu nomeio uma chave estrangeira?"
```

#### Exemplo de Pergunta:
```bash
python3 perguntar_ao_manual.py "Qual o padrão dos objetos z?"
```

#### (Opcional) Re-indexar o Banco
Se você alterar as regras no `setup_inicial.sql` e quiser recalcular os vetores:
```bash
python3 indexar_banco.py
```

---

## 📂 Estrutura do Projeto

```
.
├── .gitignore             # Ignora arquivos de ambiente (ex: /testedbdetran)
├── README.md              # Este arquivo
├── requirements.txt       # Bibliotecas Python (psycopg2, requests, pgvector)
├──
├── banco_completo.sql     # 🌟 BACKUP PRINCIPAL (Tabelas + Regras + Vetores)
├── setup_inicial.sql      # Script "limpo" para criar o schema e inserir regras (sem vetores)
└── perguntar_ao_manual.py   # Script principal para fazer perguntas ao RAG
```
