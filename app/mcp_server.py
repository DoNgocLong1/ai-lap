import json
from pathlib import Path
from typing import Literal

import anthropic
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import ValidationError

from app.classifier import (
    MODEL,
    ClassifyRequest,
    build_request,
    classify_ticket,
    parse_llm_output,
)
from app.schemas import TicketOut

mcp = MCPServer("ticket-tools")
DB_FILE = Path(__file__).parent.parent / "tickets.json"
MODULES = ["auth", "payment", "report", "notification", "admin"]


def _load() -> list[dict]:
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text(encoding="utf-8"))
    return []


@mcp.tool()
def list_modules() -> list[str]:
    """Danh sách module hợp lệ của hệ thống. Gọi trước khi phân loại ticket."""
    return MODULES


@mcp.tool()
async def classify(content: str) -> TicketOut:
    """Phân loại ticket bằng code classify_ticket() của dự án (gọi Claude API qua app/llm.py).
    Dùng tool này khi người dùng muốn test/kiểm tra code phân loại của dự án;
    trả về đúng kết quả code tạo ra, không tự sửa."""
    try:
        return await classify_ticket(content)
    except ValidationError as e:
        raise ToolError(f"LLM trả về JSON sai schema TicketOut: {e}")
    except anthropic.APIError as e:
        raise ToolError(
            f"Lỗi gọi Claude API (model={MODEL}): {e.__class__.__name__}: {e}"
        )
    except Exception as e:  # noqa: BLE001 - tool test cần hiện mọi lỗi
        raise ToolError(f"Lỗi không mong đợi: {e.__class__.__name__}: {e}")


@mcp.tool()
def get_classify_prompt(content: str) -> ClassifyRequest:
    """Bước 1 của cách test code phân loại KHÔNG cần API key (Claude đóng vai model).
    Trả về system prompt và user message mà classify_ticket() sẽ gửi cho model.
    Sau khi gọi: hãy trả lời ĐÚNG như một model nhận prompt này (chỉ output thô,
    không sửa cho đẹp, không giải thích), rồi đưa nguyên văn vào parse_classify_output."""
    return build_request(content)


@mcp.tool()
def parse_classify_output(raw_output: str) -> TicketOut:
    """Bước 2: chạy output thô của model qua parse_llm_output() của dự án
    (bỏ markdown + validate schema TicketOut). Trả về kết quả hoặc lỗi đúng như code tạo ra."""
    try:
        return parse_llm_output(raw_output)
    except ValidationError as e:
        raise ToolError(f"Output sai schema TicketOut: {e}")


@mcp.tool()
def save_ticket(
    content: str,
    category: Literal["bug", "feature_request", "question"],
    severity: Literal["low", "medium", "high", "critical"],
    module: str,
    summary: str,
) -> str:
    """Lưu một ticket đã được phân loại. module phải nằm trong list_modules hoặc là "unknown"."""
    if module not in MODULES and module != "unknown":
        raise ToolError(
            f"Module không hợp lệ: {module}. Hợp lệ: {MODULES} hoặc 'unknown'"
        )
    tickets = _load()
    tickets.append(
        {
            "id": len(tickets) + 1,
            "content": content,
            "category": category,
            "severity": severity,
            "module": module,
            "summary": summary,
        }
    )
    DB_FILE.write_text(
        json.dumps(tickets, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return f"Đã lưu ticket #{len(tickets)}"


@mcp.tool()
def search_tickets(keyword: str) -> list[dict]:
    """Tìm các ticket đã lưu có chứa từ khóa trong nội dung hoặc tóm tắt."""
    kw = keyword.lower()
    return [
        t for t in _load() if kw in t["content"].lower() or kw in t["summary"].lower()
    ]


if __name__ == "__main__":
    mcp.run()  # mặc định dùng stdio
