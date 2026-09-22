import json
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import Iterator

API = "https://tok.wikipedia.org/w/api.php"
UA = "tp-indexing/1.0 (+https://github.com/nymwa-works/tp-indexing)"
OUTPUT = Path(__file__).parent.parent / "data" / "titles.json"
PARAMS = {
    "action": "query",  # データを読むアクション
    "list": "allpages",  # 全ページを列挙
    "apnamespace": "0",  # 通常の記事 (0) が対象
    "aplimit": "500",  # 1回のリクエストで 500 件取得する。
    "format": "json",  # json で取得する。
    "formatversion": "2",  # 最新のフォーマット (2) を使用する。
    "apfilterredir": "nonredirects",  # リダイレクトを除外
}


class Page(BaseModel):
    """MediaWiki API の allpages で得られるページ"""

    title: str


class Query(BaseModel):
    """MediaWiki API の query"""

    allpages: list[Page] = []


class ApiError(BaseModel):
    """MediaWiki API のエラー"""

    code: str
    info: str


class AllPages(BaseModel):
    """MediaWiki API の allpages のレスポンス"""

    query: Query = Field(default_factory=Query)
    error: ApiError | None = None
    continue_: dict[str, str] = Field(default_factory=dict, alias="continue")
    # continue は予約語で、構文解析に失敗するため、continue_ とする必要がある。


def main() -> None:
    """トキポナ版 Wikipedia から記事名の一覧を取得する。"""
    with httpx.Client(
        headers={"User-Agent": UA, "Accept": "application/json"},
        timeout=60,
        follow_redirects=True,
    ) as client:
        titles = list(fetch_titles(client))
    _ = OUTPUT.write_text(
        json.dumps(titles, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def fetch_titles(client: httpx.Client) -> Iterator[str]:
    """MediaWiki API の allpages で記事名を順に取り出す。"""
    continue_: dict[str, str] = {}
    while True:
        pages = fetch_pages(client, PARAMS | continue_)
        yield from (page.title for page in pages.query.allpages)

        # 続きがなければ終了する。
        if not pages.continue_:
            return
        continue_ = pages.continue_


def fetch_pages(client: httpx.Client, params: dict[str, str]) -> AllPages:
    """1回分のリクエストを送り、検証したレスポンスを返す。"""
    response = client.get(API, params=params)
    _ = response.raise_for_status()
    pages = AllPages.model_validate_json(response.content)
    if pages.error:
        msg = f"{pages.error.code}: {pages.error.info}"
        raise RuntimeError(msg)
    return pages


if __name__ == "__main__":
    main()
