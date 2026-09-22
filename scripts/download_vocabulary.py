import json
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from collections.abc import Sequence

API = "https://api.linku.la/v2/words"
UA = "tp-indexing/1.0 (+https://github.com/nymwa-works/tp-indexing)"
OUTPUT = Path(__file__).parent.parent / "data" / "vocabulary.json"
BOOKS = ("pu", "ku suli", "ku lili", "none")


def main() -> None:
    """`lipu Linku` から単語一覧を取得する。"""
    data = parse(fetch())
    _ = OUTPUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def fetch(timeout: float = 60) -> dict[str, str]:
    """`lipu Linku` の単語一覧の API からデータを取得する。"""
    r = httpx.get(
        API,
        headers={"User-Agent": UA, "Accept": "application/json"},
        timeout=timeout,
        follow_redirects=True,
    )
    _ = r.raise_for_status()
    return {k: v["book"] for k, v in r.json().items()}


def parse(
    data: dict[str, str],
    books: Sequence[str] = BOOKS,
) -> dict[str, list[str]]:
    """単語一覧を出典の書籍ごとに分類し、それぞれをソートして返す。"""
    return {
        book: sorted(key for key, value in data.items() if value == book)
        for book in books
    }


if __name__ == "__main__":
    main()
