from fastapi import FastAPI

from app.schemas import TicketIn, TicketOut

app = FastAPI(title="Ticket Classifier")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/classify", response_model=TicketOut)
def classify(ticket: TicketIn):
    # Tạm thời trả kết quả cố định. Bước sau sẽ gọi Claude ở đây.
    return TicketOut(
        category="bug",
        severity="medium",
        module="unknown",
        summary=ticket.content[:50],
    )
