# 01. MCP hoạt động thế nào

## MCP là gì

**MCP (Model Context Protocol)** là một giao thức chuẩn. Nó cho phép một ứng dụng AI (gọi là **client**) dùng công cụ (gọi là **tool**) do một chương trình khác (gọi là **server**) cung cấp.

Trong dự án này:
- **Client**: Claude Code.
- **Server**: `app/mcp_server.py`, tên server là `ticket-tools`.

```
┌──────────────┐   JSON-RPC qua stdio    ┌────────────────────┐
│ Claude Code  │ ──────────────────────▶ │  app/mcp_server.py │
│  (client)    │ ◀────────────────────── │  (server)          │
└──────┬───────┘                         └─────────┬──────────┘
       │ đưa tên + mô tả + schema tool vào context  │ chạy code Python của dự án
       ▼                                            ▼
   Model Claude                              app/llm.py, schemas.py, tickets.json
```

## Một phiên làm việc có 5 bước

### Bước 1. Khởi động

Claude Code đọc cấu hình MCP. Dự án này đăng ký server trong `~/.claude.json`:

```json
{
  "type": "stdio",
  "command": "uv",
  "args": ["run", "--directory", "/home/longdn16/project/ai-lab", "python", "-m", "app.mcp_server"]
}
```

Claude Code chạy lệnh này thành một **tiến trình con**. Hai bên gửi tin nhắn **JSON-RPC** cho nhau qua `stdin` và `stdout`.

### Bước 2. Handshake

1. Client gửi `initialize`.
2. Client gửi `tools/list`.
3. Server trả về danh sách tool. Mỗi tool có 3 phần:
   - **Tên**: tên hàm Python, ví dụ `classify`.
   - **Mô tả**: lấy từ **docstring** của hàm.
   - **JSON Schema của tham số**: sinh tự động từ **type hint** của hàm.

Ví dụ, type hint `content: str` sinh ra schema:

```json
{"content": {"type": "string"}}
```

### Bước 3. Model đọc thông tin tool

Client đưa tên, mô tả và schema của tool vào context của model. Tên tool có dạng `mcp__<server>__<tool>`, ví dụ `mcp__ticket-tools__classify`.

Model dựa vào **docstring** để quyết định khi nào gọi tool nào.

> **Lưu ý:** docstring của tool có vai trò như một prompt cho model. Viết docstring rõ ràng thì model dùng tool đúng hơn.

### Bước 4. Gọi tool

1. Model quyết định dùng một tool.
2. Client gửi `tools/call` kèm `{name, arguments}`.
3. Server kiểm tra tham số theo schema.
4. Server chạy hàm Python.
5. Server chuyển giá trị trả về thành JSON và gửi lại cho client. Giá trị trả về có thể là Pydantic model, `dict` hoặc `list`.

### Bước 5. Báo lỗi

Nếu hàm ném `ToolError`, client nhận kết quả có `isError: true` kèm thông báo lỗi.

Model đọc được thông báo lỗi và có thể tự điều chỉnh. Ví dụ: `save_ticket` báo "Module không hợp lệ", model sửa module rồi gọi lại.

## Tóm tắt

Server MCP chỉ là các **hàm Python bình thường** được gắn decorator `@mcp.tool()`. Thư viện `mcp` làm các việc còn lại:
- xử lý giao thức JSON-RPC;
- sinh schema từ type hint;
- chuyển đổi dữ liệu sang JSON.

```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("ticket-tools")


@mcp.tool()
def list_modules() -> list[str]:
    """Danh sách module hợp lệ của hệ thống. Gọi trước khi phân loại ticket."""
    return ["auth", "payment", "report", "notification", "admin"]


if __name__ == "__main__":
    mcp.run()  # mặc định dùng stdio
```

## Type hint ảnh hưởng đến schema MCP

Python không kiểm tra type hint khi chạy. Nhưng thư viện `mcp` **đọc type hint** để sinh schema. Vì vậy trong MCP, type hint có tác dụng thật.

| Kiểu trả về | Schema MCP mô tả |
|---|---|
| `-> dict` | Chỉ ghi là một object, không nói có khóa nào. |
| `-> ClassifyRequest` (`TypedDict`) | Liệt kê từng khóa, kiểu của khóa, khóa bắt buộc. |
| `-> TicketOut` (Pydantic `BaseModel`) | Liệt kê từng trường; server còn validate dữ liệu trước khi trả về. |

## Lưu ý khi dùng

- Sau khi sửa code server, cần **khởi động lại server**: gõ `/mcp` trong Claude Code, chọn reconnect `ticket-tools`.
- Chạy tay `python -m app.mcp_server` trong terminal thì server chỉ đứng chờ, không in gì. Đây là bình thường, vì server giao tiếp qua stdio.
- Muốn thử tool trên giao diện web: chạy `uv run mcp dev app/mcp_server.py` để mở MCP Inspector (cần Node.js).
