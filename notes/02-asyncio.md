# 02. asyncio

## asyncio là gì

`asyncio` là thư viện có sẵn trong Python. Nó cho phép chạy **nhiều việc phải chờ cùng một lúc trên một luồng**.

"Việc phải chờ" là việc I/O, ví dụ:
- gọi API;
- đọc dữ liệu qua mạng;
- truy vấn database.

Cách hoạt động: khi một việc phải chờ (`await`), Python **tạm dừng việc đó và chạy việc khác**. Python không đứng yên chờ. Bộ phận điều phối việc chuyển qua lại gọi là **event loop**.

```
Chạy tuần tự:   [gọi 1 ──1s──][gọi 2 ──1s──][gọi 3 ──1s──]   = 3s
Dùng asyncio:   [gọi 1 ──1s──]
                [gọi 2 ──1s──]                               = 1s
                [gọi 3 ──1s──]
```

Ví dụ (trong `ch1_python_basic.py`): gọi `fake_call` 3 lần, mỗi lần chờ 1s, tổng thời gian chỉ khoảng 1s.

```python
import asyncio


async def fake_call(i: int) -> str:
    await asyncio.sleep(1)
    return f"Kết quả {i}"


async def main():
    results = await asyncio.gather(*(fake_call(i) for i in range(3)))
    print(results)  # ['Kết quả 0', 'Kết quả 1', 'Kết quả 2']


asyncio.run(main())
```

## 3 khái niệm cơ bản

| Khái niệm | Ý nghĩa |
|---|---|
| `async def f()` | Khai báo **coroutine function**. Gọi `f()` **chưa chạy** code, chỉ tạo ra một coroutine object. |
| `await x` | Chạy `x` và chờ kết quả. Trong lúc chờ, event loop chạy việc khác. Chỉ dùng được bên trong `async def`. |
| event loop | Bộ điều phối các coroutine. `asyncio.run(...)` tạo ra event loop. |

## Lưu ý quan trọng

- `asyncio` chỉ giúp nhanh hơn với **việc chờ I/O**. Việc tính toán nặng (CPU) **không** nhanh hơn.
- **Không** gọi hàm chặn bên trong `async def`. Hàm chặn làm **đứng toàn bộ event loop**.

| Hàm chặn (không dùng trong `async def`) | Dùng thay bằng |
|---|---|
| `time.sleep(1)` | `await asyncio.sleep(1)` |
| `requests.get(url)` | `httpx.AsyncClient`, hoặc `await asyncio.to_thread(requests.get, url)` |
| `Anthropic()` (client sync) | `AsyncAnthropic()` |

## Các hàm hay dùng

### 1. `asyncio.run(coro)`: điểm khởi động

- Tạo event loop, chạy coroutine đến khi xong, rồi đóng event loop.
- Thường **chỉ gọi một lần**, ở cấp ngoài cùng của chương trình.

```python
asyncio.run(main())
```

### 2. `asyncio.sleep(s)`: chờ mà không chặn

- Là phiên bản async của `time.sleep`.
- Dùng để giả lập độ trễ khi test, hoặc chờ giữa các lần retry.

```python
await asyncio.sleep(1)
```

### 3. `asyncio.gather(*coros)`: chạy song song, lấy tất cả kết quả

- Kết quả trả về **đúng thứ tự** truyền vào.
- Mặc định: nếu một việc lỗi, lỗi được ném ra ngay.
- Với `return_exceptions=True`: lỗi được trả về như một phần tử trong danh sách kết quả.

```python
results = await asyncio.gather(*(fake_call(i) for i in range(3)))
results = await asyncio.gather(*coros, return_exceptions=True)
```

### 4. `asyncio.create_task(coro)`: chạy ngay, lấy kết quả sau

```python
task = asyncio.create_task(fake_call(1))  # bắt đầu chạy nền
...                                       # làm việc khác
result = await task                       # lấy kết quả khi cần
```

### 5. `asyncio.TaskGroup()`: cách mới, an toàn hơn `gather`

- Có từ Python 3.11.
- Nếu một task lỗi, các task còn lại **tự động bị hủy**.

```python
async with asyncio.TaskGroup() as tg:
    t1 = tg.create_task(fake_call(1))
    t2 = tg.create_task(fake_call(2))
print(t1.result(), t2.result())
```

### 6. `asyncio.timeout(s)` và `asyncio.wait_for(coro, s)`: giới hạn thời gian

- Quá thời gian thì ném `TimeoutError`.
- `asyncio.timeout` có từ Python 3.11. `wait_for` là cách cũ.

```python
async with asyncio.timeout(5):
    r = await fake_call(1)

r = await asyncio.wait_for(fake_call(1), timeout=5)
```

### 7. `asyncio.Semaphore(n)`: giới hạn số việc chạy cùng lúc

- Hay dùng khi gọi API LLM, để không vượt quá rate limit.

```python
sem = asyncio.Semaphore(5)


async def limited(i):
    async with sem:  # tối đa 5 lời gọi chạy cùng lúc
        return await fake_call(i)


results = await asyncio.gather(*(limited(i) for i in range(100)))
```

### 8. `asyncio.as_completed(coros)`: xử lý việc nào xong trước

- Kết quả trả về theo **thứ tự hoàn thành**, không theo thứ tự gọi.

```python
for coro in asyncio.as_completed([fake_call(i) for i in range(3)]):
    print(await coro)
```

### 9. `asyncio.to_thread(func, *args)`: chạy hàm đồng bộ mà không chặn loop

- Hàm đồng bộ (sync) được chạy trong một thread riêng.

```python
data = await asyncio.to_thread(requests.get, url)
```

## Bảng tóm tắt

| Hàm | Dùng khi |
|---|---|
| `asyncio.run` | Khởi động chương trình async |
| `asyncio.sleep` | Chờ mà không chặn |
| `asyncio.gather` | Chạy nhiều việc song song, lấy tất cả kết quả |
| `asyncio.create_task` | Chạy nền, lấy kết quả sau |
| `asyncio.TaskGroup` | Chạy song song, tự hủy khi có lỗi |
| `asyncio.timeout` / `wait_for` | Giới hạn thời gian |
| `asyncio.Semaphore` | Giới hạn số việc chạy cùng lúc |
| `asyncio.as_completed` | Xử lý việc xong trước |
| `asyncio.to_thread` | Chạy hàm sync mà không chặn loop |

## So sánh với event loop của JavaScript

Về ý tưởng thì giống: cả hai chạy trên **một luồng** và nhường quyền chạy ở `await`. Nhưng cách vận hành khác nhau ở một số điểm quan trọng.

### Giống nhau

- Chạy trên một luồng. Các việc tự nhường nhau ở `await`, không bị ngắt giữa chừng như khi dùng thread.
- Phù hợp với việc chờ I/O: gọi API, mạng, file.
- Code chạy lâu hoặc chặn **làm đứng cả loop**.
- Cú pháp `async` / `await` gần như giống nhau.

### Khác nhau

| | JavaScript | Python asyncio |
|---|---|---|
| Event loop | **Luôn chạy sẵn**, có trong runtime (trình duyệt, Node) | **Phải tự khởi động** bằng `asyncio.run(...)` |
| Gọi hàm async | **Chạy ngay** đến `await` đầu tiên, trả về Promise | **Chưa chạy gì**, chỉ tạo coroutine object |
| Quên `await` | Promise vẫn chạy ngầm | Code **không chạy**, Python báo `RuntimeWarning: coroutine was never awaited` |
| Hàng đợi | Có 2 loại: microtask (Promise) và macrotask (setTimeout, I/O) | Một hàng đợi "ready" chung |
| Hủy việc đang chạy | Promise không hủy được, phải dùng `AbortController` | `task.cancel()` ném `CancelledError` vào task |
| Thư viện mặc định | Hầu hết API I/O đã là async (`fetch`, `fs.promises`) | Nhiều thư viện vẫn là sync (`requests`, `open`), dễ chặn loop |

### Điểm khác quan trọng nhất: chạy ngay hay chưa chạy

```js
// JavaScript
async function f() { console.log("chạy f"); }
f(); // in "chạy f" ngay, dù không có await
```

```python
# Python
async def f():
    print("chạy f")

f()                       # KHÔNG in gì, chỉ có cảnh báo "never awaited"
await f()                 # bây giờ mới chạy
asyncio.create_task(f())  # hoặc đưa vào loop để chạy nền, giống JS
```

Hệ quả:
- **JS:** gọi nhiều hàm async liên tiếp là chúng đã chạy song song.
- **Python:** phải gom coroutine lại bằng `gather` hoặc `create_task` thì mới chạy song song.

### Bảng tương đương

| JavaScript | Python asyncio |
|---|---|
| `Promise` | `Task` / `Future` |
| `Promise.all([...])` | `asyncio.gather(...)` |
| `Promise.allSettled([...])` | `asyncio.gather(..., return_exceptions=True)` |
| `Promise.race([...])` | `asyncio.wait(..., return_when=asyncio.FIRST_COMPLETED)` |
| `await new Promise(r => setTimeout(r, 1000))` | `await asyncio.sleep(1)` |
| `setTimeout(fn, 1000)` | `loop.call_later(1, fn)` |
| `queueMicrotask(fn)` | `loop.call_soon(fn)` (gần tương đương) |
| Worker threads | `asyncio.to_thread(...)` |

> **Cách nhớ:** event loop của JS luôn chạy sẵn và hàm async chạy ngay khi gọi. Event loop của Python phải tự khởi động, và coroutine chỉ chạy khi được `await` hoặc đưa vào loop.

## Liên hệ với dự án ai-lab

- `app/llm.py` dùng `AsyncAnthropic`, nên phải `await client.messages.create(...)`.
- Trong FastAPI (`app/main.py`), endpoint `async def` chạy trên event loop do FastAPI quản lý. **Không** gọi `asyncio.run` trong endpoint, chỉ cần `await`.
- Phân loại nhiều ticket cùng lúc: kết hợp `gather` với `Semaphore`.

```python
async def classify_many(contents: list[str]) -> list[TicketOut]:
    sem = asyncio.Semaphore(5)

    async def one(c: str) -> TicketOut:
        async with sem:
            return await classify_ticket(c)

    return await asyncio.gather(*(one(c) for c in contents))
```
