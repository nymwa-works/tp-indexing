import json
from pathlib import Path

from rapidfuzz.distance import Levenshtein
from tokipona import FIRSTS, SECONDS, load_vocabulary

DATA = Path(__file__).parent.parent / "data"
KNOWN_NAMES = DATA / "known_names.json"
OUTPUT = DATA / "index_candidates.json"

DISTANCE = 2  # 名前が語から離れていなければならない編集距離


def main() -> None:
    """索引に使える名前を集める。"""
    known = load_known_names()
    words = load_vocabulary()
    candidates = [
        name
        for name in build_names()
        if name not in known and nearest(name, words) >= DISTANCE
    ]
    _ = OUTPUT.write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_known_names() -> frozenset[str]:
    """既知の固有名をすべて小文字にして読み込む。"""
    names: list[str] = json.loads(KNOWN_NAMES.read_text(encoding="utf-8"))
    return frozenset(name.lower() for name in names)


def build_names() -> list[str]:
    """第一・二音節で子音が重複しない CVCV の形の名前をすべて生成する。"""
    return [
        first + second
        for first in FIRSTS
        for second in SECONDS
        if first[0] != second[0]
    ]


def nearest(name: str, words: tuple[str, ...]) -> int:
    """その名前に最も近い語との編集距離を返す。"""
    return min(Levenshtein.distance(name, word) for word in words)


if __name__ == "__main__":
    main()
