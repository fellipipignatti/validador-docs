from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
import io

app = FastAPI(title="Document Validator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


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
        data = resp.json()
        return data["content"][0]["text"]


@app.post("/extract")
async def extract_from_text(text: str = Form(...), filename: str = Form("")):
    """Recebe texto extraído do documento e pede à IA para identificar nomes e valores."""
    prompt = f"""Você é um extrator de dados de documentos. Analise o texto abaixo e extraia TODOS os registros que contenham um NOME DE PESSOA e um VALOR MONETÁRIO.

Retorne APENAS um JSON válido, sem markdown, sem explicação, neste formato exato:
[{{"nome":"Nome Completo da Pessoa","valor":"R$ 0,00"}}]

Regras:
- Extraia todos os pares nome+valor que encontrar
- Preserve o nome exatamente como aparece no documento
- Preserve o valor com sua formatação original
- Se não encontrar nenhum registro, retorne []
- Retorne APENAS o JSON, nada mais

Texto do documento ({filename}):
{text[:8000]}"""

    result = await call_claude(prompt)
    result = result.replace("```json", "").replace("```", "").strip()
    try:
        import json
        parsed = json.loads(result)
        return JSONResponse(content={"records": parsed})
    except Exception:
        raise HTTPException(status_code=422, detail="IA retornou formato inesperado.")


@app.post("/chat")
async def chat(question: str = Form(...), context: str = Form("")):
    """Chat livre sobre os dados processados."""
    prompt = f"{context}\nPergunta: {question}\nResponda em português de forma concisa."
    result = await call_claude(prompt)
    return JSONResponse(content={"answer": result})


@app.get("/health")
async def health():
    return {"status": "ok", "key_configured": bool(ANTHROPIC_API_KEY)}
