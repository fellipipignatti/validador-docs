from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import httpx, os, json
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# Caminho absoluto do index.html (mesmo diretório do main.py)
BASE_DIR = Path(__file__).parent
INDEX_PATH = BASE_DIR / "index.html"


async def call_claude(prompt: str) -> str:
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY não configurada no servidor.")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


@app.get("/", response_class=HTMLResponse)
async def index():
    if not INDEX_PATH.exists():
        raise HTTPException(status_code=404, detail=f"index.html não encontrado em {INDEX_PATH}")
    return HTMLResponse(content=INDEX_PATH.read_text(encoding="utf-8"))


@app.post("/extract")
async def extract(text: str = Form(...), filename: str = Form("")):
    prompt = f"""Analise o texto e extraia TODOS os pares de NOME DE PESSOA e VALOR MONETÁRIO.
Retorne APENAS JSON válido, sem markdown, sem explicação:
[{{"nome":"Nome da Pessoa","valor":"R$ 0,00"}}]
Se não encontrar nenhum, retorne [].

Texto ({filename}):
{text[:8000]}"""
    result = await call_claude(prompt)
    result = result.replace("```json", "").replace("```", "").strip()
    try:
        return JSONResponse({"records": json.loads(result)})
    except Exception:
        raise HTTPException(status_code=422, detail="Formato inválido retornado pela IA.")


@app.post("/chat")
async def chat(question: str = Form(...), context: str = Form("")):
    prompt = f"{context}\nPergunta: {question}\nResponda em português de forma concisa."
    return JSONResponse({"answer": await call_claude(prompt)})


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "key_configured": bool(ANTHROPIC_API_KEY),
        "index_found": INDEX_PATH.exists(),
        "index_path": str(INDEX_PATH),
    }
