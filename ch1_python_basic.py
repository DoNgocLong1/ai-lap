import asyncio
import json
from pathlib import Path

name: str = "ai-lab"

print(f"1. Project {name}")

tickets = [
    {"id": 1, "title": "Lỗi login", "category": "bug"},
    {"id": 2, "title": "Thêm nút Excel", "category": "feature"},
    {"id": 3, "title": "Login chậm", "category": "bug"},
]

bugs = [item["title"] for item in tickets if item["category"] == "bug"]

print(f"2.Bugs: {bugs}")


def count_by(items: list[dict], key: str = "category") -> dict[str, int]:
    results: dict[str, int] = {}
    for item in items:
        if key in item:
            results[item[key]] = results.get(item[key], 0) + 1
    return results


print(f"3.Đếm: {count_by(tickets)}")


try:
    tickets[0]["priority"]
except KeyError as e:
    print(f"4. thiếu trường: {e}")

Path("out").mkdir(exist_ok=True)
Path("out/tickets.json").write_text(
    json.dumps(tickets, ensure_ascii=False, indent=2), encoding="utf-8"
)
data = json.loads(Path("out/tickets.json").read_text(encoding="utf-8"))

print(f"5. Đoc lại {len(data)} tickets")


async def fake_call(i: int) -> str:
    await asyncio.sleep(1)
    return f"Kết quả {i}"


async def main():
    results = await asyncio.gather(*(fake_call(i) for i in range(10)))
    print(f"6. lặp lại 3 lần gọi, tổng 1s: {results}")


asyncio.run(main())


def titles_with(items: list[dict], word: str) -> list[str]:
    list_data: list[str] = []
    for item in items:
        if word.lower() in str(item["title"]).lower():
            list_data.append(item["title"])
    return list_data


print(f"7. Lấy với title {titles_with(tickets, 'login')}")


def show_errors(items: list[dict]):
    for index, item in enumerate(items):
        print(f"Lỗi # {index + 1}: {item['title'] or ''}")


print("8. Danh sách lỗi: ")
show_errors(data)
