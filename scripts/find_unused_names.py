import json
from pathlib import Path

from tokipona import FIRSTS, SECONDS

DATA = Path(__file__).parent.parent / "data"
KNOWN_NAMES = DATA / "known_names.json"
OUTPUT = DATA / "unused_names.json"


def main() -> None:
    """作れる名前のうち、まだ誰にも使われていないものを集める。"""
    known = load_known_names()
    names = [name for name in build_names() if name not in known]
    _ = OUTPUT.write_text(
        json.dumps(names, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_names() -> list[str]:
    """第一・二音節で子音が重複しない CVCV の形の名前をすべて生成する。"""
    return [
        first + second
        for first in FIRSTS
        for second in SECONDS
        if first[0] != second[0]
    ]


def load_known_names() -> frozenset[str]:
    """既知の固有名をすべて小文字にして読み込む。"""
    names: list[str] = json.loads(KNOWN_NAMES.read_text(encoding="utf-8"))
    return frozenset(name.lower() for name in names)


if __name__ == "__main__":
    main()
