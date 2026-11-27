# 03. Python / FastAPI

## Pydantic model

### Pydantic model là gì

**Pydantic model** là một class kế thừa `pydantic.BaseModel`.
- Khai báo các trường bằng **type hint**.
- Pydantic **kiểm tra dữ liệu khi chạy** dựa trên type hint đó, và **báo lỗi khi dữ liệu sai**.

Đây là điểm khác chính so với `TypedDict` và `@dataclass`: hai cách đó **không** kiểm tra dữ liệu khi chạy.

```python
from typing import Literal

from pydantic import BaseModel, Field


class TicketIn(BaseModel):
    content: str = Field(min_length=1, description="Nội dung ticket tiếng Việt")


class TicketOut(BaseModel):
    category: Literal["bug", "feature_request", "question"]
    severity: Literal["low", "medium", "high", "critical"]
    module: str
    summary: str
```

### Tên gọi khác

| Tên gọi | Lý do |
|---|---|
| **Pydantic model** | Tên chính thức, vì class kế thừa `BaseModel`. |
| **Schema** | Mô tả **hình dạng dữ liệu**: có những trường nào, kiểu gì, ràng buộc gì. Vì vậy file đặt tên là `schemas.py`. |
| **DTO** (Data Transfer Object) | Đối tượng chỉ dùng để **chuyển dữ liệu**, không chứa logic nghiệp vụ. |
| **Request model / Response model** | Tên gọi trong FastAPI, theo vai trò của class. |

Quy ước đặt tên hậu tố `In` / `Out` (hoặc `Create` / `Read`, `Request` / `Response`) phân biệt **dữ liệu đi vào** và **dữ liệu đi ra**. Hai loại này thường có các trường khác nhau.

### Pydantic làm được gì

#### 1. Validate (kiểm tra dữ liệu)

```python
TicketOut(category="bug", severity="high", module="payment", summary="x")  # ✅

TicketOut(category="loi", severity="high", module="payment", summary="x")
# ❌ ValidationError: category
#    Input should be 'bug', 'feature_request' or 'question' [input_value='loi']

TicketOut(category="bug", severity="high")
# ❌ ValidationError: module — Field required; summary — Field required
```

#### 2. Parse JSON thành object

```python
t = TicketOut.model_validate_json(
    '{"category":"bug","severity":"high","module":"auth","summary":"x"}'
)
t.category  # "bug" (truy cập bằng dấu chấm)
```

Dữ liệu từ bên ngoài **không đáng tin**, ví dụ:
- output của LLM;
- request từ client;
- file JSON.

Pydantic chặn dữ liệu sai **ngay tại điểm dữ liệu đi vào hệ thống**.

#### 3. Tự chuyển kiểu (coercion)

```python
class Item(BaseModel):
    id: int


Item(id="5").id  # 5 (chuỗi "5" được chuyển thành int)
Item(id="abc")   # ❌ ValidationError
```

Muốn kiểm tra nghiêm ngặt, **không** tự chuyển kiểu: dùng `model_config = ConfigDict(strict=True)`.

#### 4. Xuất dữ liệu (serialize)

```python
t.model_dump()       # → dict
t.model_dump_json()  # → chuỗi JSON
```

#### 5. Tạo JSON Schema

```python
TicketOut.model_json_schema()
# {"properties": {"category": {"enum": ["bug", ...]}, ...}, "required": [...]}
```

- FastAPI dùng schema này để tạo trang `/docs`.
- Thư viện `mcp` dùng schema này để mô tả tool.

#### 6. Ràng buộc chi tiết bằng `Field`

```python
class TicketIn(BaseModel):
    content: str = Field(min_length=1, max_length=5000, description="Nội dung ticket tiếng Việt")
    priority: int = Field(default=3, ge=1, le=5)  # 1 ≤ priority ≤ 5
```

### Các method hay dùng

| Method | Tác dụng |
|---|---|
| `Model(**data)` / `Model.model_validate(dict)` | Tạo object từ dữ liệu và validate |
| `Model.model_validate_json(str)` | Parse chuỗi JSON rồi validate |
| `obj.model_dump()` | Chuyển object thành `dict` |
| `obj.model_dump_json()` | Chuyển object thành chuỗi JSON |
| `Model.model_json_schema()` | Lấy JSON Schema |
| `obj.model_copy(update={...})` | Tạo bản sao, thay đổi một số trường |

### Ví dụ từng method

Dữ liệu mẫu cho các ví dụ:

```python
from app.schemas import TicketOut

data = {"category": "bug", "severity": "high", "module": "payment", "summary": "Lỗi thanh toán Visa"}
```

#### 1. `Model(**data)`: tạo object từ dict

```python
t1 = TicketOut(**data)
# TicketOut(category='bug', severity='high', module='payment', summary='Lỗi thanh toán Visa')
```

`**data` tách dict thành keyword argument. Tương đương `TicketOut(category="bug", severity="high", ...)`.

#### 2. `Model.model_validate(dict)`: tạo object từ dict (khuyên dùng)

```python
t2 = TicketOut.model_validate(data)
t1 == t2  # True
```

- Kết quả giống `Model(**data)`.
- Nên dùng khi dữ liệu là dict từ bên ngoài (ví dụ kết quả của `json.loads`), vì vẫn chạy đúng khi tên khóa không phải tên hợp lệ trong Python.

#### 3. `Model.model_validate_json(str)`: parse chuỗi JSON

Dùng trong `parse_llm_output()` của dự án.

```python
raw = '{"category":"question","severity":"low","module":"auth","summary":"Hỏi reset mật khẩu"}'
t3 = TicketOut.model_validate_json(raw)
# TicketOut(category='question', severity='low', module='auth', summary='Hỏi reset mật khẩu')
```

Khi dữ liệu sai, Pydantic **liệt kê tất cả lỗi trong một lần**:

```python
from pydantic import ValidationError

try:
    TicketOut.model_validate_json('{"category":"loi"}')
except ValidationError as e:
    e.error_count()                     # 4
    [err["loc"] for err in e.errors()]  # [('category',), ('severity',), ('module',), ('summary',)]
```

Nhanh hơn `json.loads(raw)` rồi `model_validate(...)`, vì parse và validate trong một bước.

#### 4. `obj.model_dump()`: object thành dict

```python
t1.model_dump()
# {'category': 'bug', 'severity': 'high', 'module': 'payment', 'summary': 'Lỗi thanh toán Visa'}

t1.model_dump(include={"category", "severity"})  # chỉ lấy một số trường
# {'category': 'bug', 'severity': 'high'}

t1.model_dump(exclude={"summary"})  # bỏ một số trường
```

Ví dụ áp dụng: `save_ticket` có thể viết `{"id": ..., "content": ..., **ticket.model_dump()}` thay vì liệt kê từng trường.

#### 5. `obj.model_dump_json()`: object thành chuỗi JSON

```python
t1.model_dump_json()
# {"category":"bug","severity":"high","module":"payment","summary":"Lỗi thanh toán Visa"}

t1.model_dump_json(indent=2)
# {
#   "category": "bug",
#   ...
# }
```

Tiếng Việt được giữ nguyên, không bị chuyển thành `ỗ`. **Không** cần `ensure_ascii=False` như `json.dumps`.

#### 6. `Model.model_json_schema()`: lấy JSON Schema

```python
TicketOut.model_json_schema()
```

```json
{
  "title": "TicketOut",
  "type": "object",
  "properties": {
    "category": {"enum": ["bug", "feature_request", "question"], "title": "Category", "type": "string"},
    "severity": {"enum": ["low", "medium", "high", "critical"], "title": "Severity", "type": "string"},
    "module":   {"title": "Module", "type": "string"},
    "summary":  {"title": "Summary", "type": "string"}
  },
  "required": ["category", "severity", "module", "summary"]
}
```

Dùng ở đâu:
- FastAPI: trang `/docs`.
- MCP: output schema của tool.
- Prompt: đưa schema vào prompt để LLM biết chính xác định dạng cần trả về.

#### 7. `obj.model_copy(update={...})`: tạo bản sao có thay đổi

```python
t4 = t1.model_copy(update={"severity": "critical"})
t4.severity  # 'critical'
t1.severity  # 'high' (object gốc không đổi)
```

> **Cảnh báo:** `model_copy(update=...)` **không validate** giá trị mới. `update={"severity": "abc"}` vẫn chạy, không báo lỗi.
> Cần validate thì dùng: `TicketOut.model_validate({**t1.model_dump(), "severity": "abc"})`.

#### Tóm tắt luồng dữ liệu

```
chuỗi JSON ──model_validate_json──▶ object ──model_dump_json──▶ chuỗi JSON
   dict    ──model_validate──────▶ object ──model_dump───────▶   dict
```

### So sánh với `TypedDict` và `@dataclass`

| | `TypedDict` | `@dataclass` | **Pydantic `BaseModel`** |
|---|---|---|---|
| Kiểu thật khi chạy | `dict` | object | object |
| Truy cập | `x["field"]` | `x.field` | `x.field` |
| Validate khi chạy | ❌ | ❌ (chỉ báo khi thiếu tham số) | ✅ |
| Tự chuyển kiểu | ❌ | ❌ | ✅ |
| Parse JSON / xuất JSON | Dùng thư viện `json` có sẵn | Phải tự viết | ✅ Có sẵn |
| Tạo JSON Schema | ❌ | ❌ | ✅ |
| Cần cài thêm thư viện | Không | Không | Cần `pydantic` |
| Nên dùng cho | Dict truyền vào API bằng `**` | Dữ liệu nội bộ do code tự tạo | **Dữ liệu từ bên ngoài** |

### Áp dụng trong dự án ai-lab

**`TicketIn`** là **request model**: dữ liệu client gửi lên `POST /classify`.
- FastAPI tự validate.
- `content` rỗng (vi phạm `min_length=1`): client nhận lỗi **422**, code của endpoint **không** chạy.

**`TicketOut`** là **response model**, được dùng ở 3 nơi:

| Nơi dùng | Tác dụng |
|---|---|
| `response_model=TicketOut` trong `app/main.py` | FastAPI kiểm tra và lọc response trước khi trả về. |
| `parse_llm_output()` trong `app/classifier.py` | Validate JSON do LLM trả về. Sai enum: ném `ValidationError`, `main.py` đổi thành lỗi **502**. |
| Kiểu trả về của tool MCP | Thư viện `mcp` tạo output schema cho tool. |

**`ClassifyRequest`** dùng `@dataclass`, **không** dùng Pydantic, vì dữ liệu do code tự tạo nên không cần validate.
