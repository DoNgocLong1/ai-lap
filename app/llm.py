import os
from typing import TypedDict

from anthropic import AsyncAnthropic
from dotenv import load_dotenv

from app.schemas import TicketOut

load_dotenv()
client = AsyncAnthropic()
MODEL = os.getenv("LLM_MODEL", "claude-haiku-5-5")

SYSTEM_PROMPT = """Bạn là hệ thống phân loại ticket phần mềm.
Đọc ticket và trả về DUY NHẤT một object JSON. Không viết văn bản khác. Không dùng markdown.
JSON có các trường:
- category: một trong "bug", "feature_request", "question"
- severity: một trong "low", "medium", "high", "critical"
- module: tên module bị ảnh hưởng; dùng "unknown" nếu ticket không nêu
- summary: tóm tắt ticket trong 1 câu tiếng Việt"""


class ClassifyRequest(TypedDict):
    model: str
    system_prompt: str
    max_tokens: int
    messages: list[dict]


def parse_llm_output(text: str) -> TicketOut:
    text = text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return TicketOut.model_validate_json(text)


def build_request(content: str):
    return ClassifyRequest(
        model=MODEL,
        max_tokens=300,
        system_prompt=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )


async def classify_ticket(content: str) -> TicketOut:
    message = await client.messages.create(
        ClassifyRequest(
            model=MODEL,
            max_tokens=300,
            system_prompt=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        ),
    )
    return parse_llm_output(message.content[0].text)
