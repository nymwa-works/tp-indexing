import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import Iterator

API = "https://tok.wikipedia.org/w/api.php"
UA = "tp-indexing/1.0 (+https://github.com/nymwa-works/tp-indexing)"
OUTPUT = Path(__file__).parent.parent / "data" / "titles.json"


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

    query: Query | None = None
    error: ApiError | None = None
    continue_: dict[str, str] = Field(default_factory=dict, alias="continue")
    # continue は予約語で、構文解析に失敗するため、continue_ とする必要がある。


def main() -> None:
    """トキポナ版 Wikipedia から記事名の一覧を取得する。"""
    with new_client() as client:
        titles = list(fetch_titles(client))
    _ = OUTPUT.write_text(
        json.dumps(titles, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def new_client(timeout: float = 60) -> httpx.Client:
    """ページをまたいで接続を使い回すためのクライアントを作る。"""
    return httpx.Client(
        headers={"User-Agent": UA, "Accept": "application/json"},
        timeout=timeout,
        follow_redirects=True,
    )


def fetch_titles(
    client: httpx.Client,
    limit: int = 500,
    wait: float = 1.0,
) -> Iterator[str]:
    """MediaWiki API の allpages で記事名を順に取り出す。"""
    params = build_params(limit)
    while True:
        # GET リクエストを送信してレスポンスを取得する。
        response = AllPages.model_validate_json(get(client, params))

        # エラーが返ってきたら例外を投げる。
        if response.error:
            msg = f"{response.error.code}: {response.error.info}"
            raise RuntimeError(msg)

        # クエリが存在していたら、タイトルを返す。
        if response.query:
            yield from (page.title for page in response.query.allpages)

        # 続きがなければ終了する。
        if not response.continue_:
            return

        # これまで取得した分を params に記録する。
        params.update(response.continue_)

        # 次のリクエストまで少し待つ。
        time.sleep(wait)


def build_params(limit: int = 500) -> dict[str, str]:
    """Allpages 用のパラメータを構築する。"""
    return {
        "action": "query",  # データを読むアクション
        "list": "allpages",  # 全ページを列挙
        "apnamespace": "0",  # 通常の記事 (0) が対象
        "aplimit": str(limit),  # 1回のリクエストで limit 件取得する。
        "format": "json",  # json で取得する。
        "formatversion": "2",  # 最新のフォーマット (2) を使用する。
        "apfilterredir": "nonredirects",  # リダイレクトを除外
    }


def get(client: httpx.Client, params: dict[str, str]) -> bytes:
    """GET して本文を返す。"""
    response = client.get(API, params=params)
    _ = response.raise_for_status()
    return response.content


if __name__ == "__main__":
    main()
