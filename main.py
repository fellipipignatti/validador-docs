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

BASE_DIR = Path(__file__).parent
INDEX_PATH = BASE_DIR / "index.html"


async def call_claude(prompt: str, max_tokens: int = 4000) -> str:
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY não configurada no servidor.")
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": max_tokens,
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
    """
    Extrai todos os nomes próprios do documento e qualquer valor
    monetário associado a eles. Retorna lista de ocorrências brutas
    (a agregação/soma é feita no frontend).
    """
    prompt = f"""Você é um extrator de dados de documentos brasileiros.

Analise o texto abaixo e extraia TODOS os NOMES PRÓPRIOS DE PESSOAS que aparecem.
Para cada nome, extraia também qualquer VALOR MONETÁRIO diretamente associado a ele (salário, pagamento, reembolso, etc.).
Se um nome aparecer sem valor associado, use null para o valor.
Se um nome aparecer múltiplas vezes com valores diferentes, liste cada ocorrência separadamente.

Retorne APENAS JSON válido, sem markdown, sem explicação, neste formato:
[{{"nome":"Nome Completo","valor":"R$ 0,00"}}]

Regras importantes:
- Extraia APENAS nomes de pessoas físicas reais (não empresas, não cargos, não lugares)
- Preserve o nome exatamente como aparece no documento
- Se não houver valor associado ao nome, omita o campo valor ou use null
- Se não encontrar nenhum nome, retorne []
- Retorne APENAS o JSON

Texto do documento ({filename}):
{text[:12000]}"""

    result = await call_claude(prompt)
    result = result.replace("```json", "").replace("```", "").strip()
    try:
        records = json.loads(result)
        # Garante campo origem em cada registro
        for r in records:
            r["origem"] = filename
            if "valor" not in r:
                r["valor"] = None
        return JSONResponse({"records": records})
    except Exception:
        raise HTTPException(status_code=422, detail="Formato inválido retornado pela IA.")


@app.post("/chat")
async def chat(question: str = Form(...), context: str = Form("")):
    prompt = f"{context}\nPergunta: {question}\nResponda em português de forma concisa."
    return JSONResponse({"answer": await call_claude(prompt, max_tokens=600)})


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "key_configured": bool(ANTHROPIC_API_KEY),
        "index_found": INDEX_PATH.exists(),
    }
