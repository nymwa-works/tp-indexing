import json
import re
from pathlib import Path

from tokipona import load_vocabulary

DATA = Path(__file__).parent.parent / "data"
TITLES = DATA / "titles.json"
OUTPUT = DATA / "known_names.json"

NAME = re.compile(r"\b[A-Z][a-z]+\b")
WORD = re.compile(r"(?:[jklmnpstw]?[aeiou]n?)+")
BANNED = ("ji", "ti", "wu", "wo", "nn", "nm")


def main() -> None:
    """トキポナ版 Wikipedia の記事名から、既知の固有名を抽出する。"""
    titles: list[str] = json.loads(TITLES.read_text(encoding="utf-8"))
    names = extract_names(titles, frozenset(load_vocabulary()))
    _ = OUTPUT.write_text(
        json.dumps(sorted(names), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def extract_names(titles: list[str], vocabulary: frozenset[str]) -> set[str]:
    """記事名からトキポナの音韻に沿った名前を抽出する。"""
    return {
        name
        for title in titles
        for name in NAME.findall(title)
        if is_name(name, vocabulary)
    }


def is_name(name: str, vocabulary: frozenset[str]) -> bool:
    """語彙 (pu, ku suli) になく、トキポナの音韻に沿った名前か確かめる。"""
    word = name.lower()
    return (
        word not in vocabulary
        and bool(WORD.fullmatch(word))
        and not any(pattern in word for pattern in BANNED)
    )


if __name__ == "__main__":
    main()
