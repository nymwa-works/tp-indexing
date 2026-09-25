import itertools
import json
import operator
from pathlib import Path

from ortools.sat.python import cp_model
from rapidfuzz.distance import Levenshtein
from tokipona import CONSONANTS, load_vocabulary

DATA = Path(__file__).parent.parent / "data"
CANDIDATES = DATA / "index_candidates.json"
KNOWN_NAMES = DATA / "known_names.json"
OUTPUT = DATA / "index.json"
OUTPUT_SCORE = DATA / "scored_index.json"

WORKERS = 8
"""CP-SAT の並列実行数"""

NAME_LENGTH = 4
"""名前の長さ"""

MAX_PER_CONSONANT = 3
"""各音節の子音について、同じ子音を持つ名前の最大数"""


def main() -> None:
    """候補の中から、索引に使う固有名を決める。"""
    words = load_vocabulary()
    names: list[str] = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    known_names = tuple(
        x.lower() for x in json.loads(KNOWN_NAMES.read_text(encoding="utf-8"))
    )
    model = cp_model.CpModel()

    # --- 変数 ---
    # それぞれの名前を採用するかしないかの二値変数
    flags = {name: model.new_bool_var(name) for name in names}

    # --- 制約 ---
    # 同じ位置で2文字が共通する名前は同時に存在できない。
    for group in groups_sharing_two_places(names):
        _ = model.add_at_most_one(flags[name] for name in group)
    # 各音節の子音について、同じ子音を持つ名前の最大数を制限する。
    for c in CONSONANTS:
        for p in [0, 2]:
            same = (f for n, f in flags.items() if n[p] == c)
            _ = model.add(sum(same) <= MAX_PER_CONSONANT)

    # --- 目的関数 ---
    model.maximize(sum(farness(n, words) * f for n, f in flags.items()))

    # --- 実行 ---
    solver = solve(model)
    selected = [
        (n.capitalize(), [neighbors(n, known_names, d) for d in range(1, 4)])
        for n, f in flags.items()
        if solver.boolean_value(f)
    ]
    selected.sort(key=operator.itemgetter(1))

    # --- 出力 ---
    text = (
        json.dumps([n for n, _ in selected], ensure_ascii=False, indent=2)
        + "\n"
    )
    scored = json.dumps(selected, ensure_ascii=False, indent=2) + "\n"
    _ = OUTPUT.write_text(text, encoding="utf-8")
    _ = OUTPUT_SCORE.write_text(scored, encoding="utf-8")


def groups_sharing_two_places(names: list[str]) -> list[list[str]]:
    """2つの位置の字が共通する名前をまとめたグループをすべて返す。"""
    return [
        [name for name in names if (name[first], name[second]) == letters]
        for first, second in itertools.combinations(range(NAME_LENGTH), 2)
        for letters in {(name[first], name[second]) for name in names}
    ]


def farness(name: str, words: tuple[str, ...]) -> int:
    """その名前とすべての語との編集距離の合計を返す。"""
    return sum(Levenshtein.distance(name, word) for word in words)


def neighbors(name: str, words: tuple[str, ...], distance: int) -> int:
    """その名前との編集距離が distance の語の数を返す。"""
    return sum(Levenshtein.distance(name, word) == distance for word in words)


def solve(model: cp_model.CpModel) -> cp_model.CpSolver:
    """モデルを受け取り最適解を持つ solver を返す。"""
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = WORKERS
    status = solver.solve(model)
    if status != cp_model.OPTIMAL:
        msg = f"最適解が見つからない: {solver.status_name(status)}"
        raise RuntimeError(msg)
    return solver


if __name__ == "__main__":
    main()
