import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from app.llm import classify_ticket
from app.schemas import TicketIn, TicketOut

app = FastAPI(title="Ticket Classifier")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/classify", response_model=TicketOut)
async def classify(ticket: TicketIn):
    try:
        return await classify_ticket(ticket.content)
    except ValidationError:
        raise HTTPException(status_code=502, detail="LLM trả về JSON sai schema")
    except anthropic.APIError as e:
        raise HTTPException(status_code=503, detail=f"Lỗi gọi LLM: {e.__class__.__name__}")
