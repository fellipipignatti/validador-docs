# Validador de Documentos com IA

Chatbot que lê PDFs e Excels, extrai **nome** e **valor** via Claude AI,
e cruza com sua base de dados para preencher o **departamento**.

---

## Pré-requisitos

- Python 3.9+
- Conta Anthropic com API Key → https://console.anthropic.com

---

## Instalação (2 minutos)

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar sua API Key
# Windows:
set ANTHROPIC_API_KEY=sk-ant-SUA_CHAVE_AQUI

# Mac/Linux:
export ANTHROPIC_API_KEY=sk-ant-SUA_CHAVE_AQUI

# 3. Subir o servidor
uvicorn main:app --reload --port 8000
```

O servidor estará em: http://localhost:8000

---

## Uso

1. Abra o arquivo `index.html` no navegador (duplo clique)
2. A URL do backend já vem preenchida como `http://localhost:8000`
3. Clique em **"Carregar base de exemplo"** ou suba seu CSV/Excel com colunas `nome` e `departamento`
4. Envie um PDF ou Excel — a IA extrai os dados automaticamente
5. Veja a tabela com validação e departamento preenchido
6. Exporte em CSV se quiser

---

## Formato da base de dados

Seu CSV ou Excel deve ter pelo menos estas colunas:

| nome               | departamento      |
|--------------------|-------------------|
| Ana Paula Ferreira | Recursos Humanos  |
| Carlos Souza       | Financeiro        |

Colunas extras (cargo, matrícula, etc.) são ignoradas.

---

## Como funciona a validação

| Tipo      | Descrição                                              |
|-----------|--------------------------------------------------------|
| `exato`   | Nome idêntico ao banco (ignorando acentos/maiúsculas)  |
| `parcial` | 2+ palavras do nome batem com o banco                  |
| `não encontrado` | Nenhuma correspondência encontrada             |

---

## Deploy online (opcional)

Para publicar e compartilhar o link com outras pessoas:

**Railway (grátis):**
```bash
# Instale o CLI do Railway
npm install -g @railway/cli
railway login
railway init
railway up
```
Depois configure a variável de ambiente `ANTHROPIC_API_KEY` no painel do Railway.
Atualize a URL do backend no `index.html` para a URL gerada pelo Railway.

---

## Estrutura dos arquivos

```
/
├── main.py          ← backend FastAPI (proxy da Claude API)
├── requirements.txt ← dependências Python
├── index.html       ← frontend completo (abrir no navegador)
└── README.md        ← este arquivo
```
