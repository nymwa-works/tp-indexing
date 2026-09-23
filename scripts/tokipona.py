"""トキポナに関する共有モジュール"""

import json
from pathlib import Path

VOCABULARY = Path(__file__).parent.parent / "data" / "vocabulary.json"

CONSONANTS = "jklmnpstw"
VOWELS = "aeiou"
BANNED = ("ji", "ti", "wo", "wu")

SYLLABLES = tuple(
    consonant + vowel
    for consonant in CONSONANTS
    for vowel in VOWELS
    if consonant + vowel not in BANNED
)
"""トキポナで発音できる CV の音節"""

BOOKS = ("pu", "ku suli")
"""トキポナの語彙として採用する出典書籍の一覧"""


def load_vocabulary() -> tuple[str, ...]:
    """語彙を読み込む。"""
    books: dict[str, list[str]] = json.loads(
        VOCABULARY.read_text(encoding="utf-8"),
    )
    return tuple(sorted({word for book in BOOKS for word in books[book]}))


def load_syllables() -> tuple[str, ...]:
    """単体で語とみなされない音節の一覧を返す。"""
    words = frozenset(load_vocabulary())
    return tuple(syllable for syllable in SYLLABLES if syllable not in words)
