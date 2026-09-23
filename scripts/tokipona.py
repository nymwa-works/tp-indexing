"""トキポナに関する共有モジュール"""

import json
from pathlib import Path

VOCABULARY = Path(__file__).parent.parent / "data" / "vocabulary.json"

CONSONANTS = "jklmnpstw"
VOWELS = "aeiou"
BANNED = ("ji", "ti", "wo", "wu")

FIRST_CONSONANTS = "jklmnpst"
FIRST_VOWELS = "aeou"
SECONDS = tuple(
    consonant + vowel
    for consonant in CONSONANTS
    for vowel in VOWELS
    if consonant + vowel not in BANNED
)
"""第2音節に使える CV の組"""

BOOKS = ("pu", "ku suli")
"""トキポナの語彙として採用する出典書籍の一覧"""


def load_vocabulary() -> tuple[str, ...]:
    """採用する語を辞書順に読み込む。"""
    books: dict[str, list[str]] = json.loads(
        VOCABULARY.read_text(encoding="utf-8"),
    )
    return tuple(sorted({word for book in BOOKS for word in books[book]}))
