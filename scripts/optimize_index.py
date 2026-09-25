import itertools
import json
from pathlib import Path

from ortools.sat.python import cp_model
from rapidfuzz.distance import Levenshtein
from tokipona import load_vocabulary

DATA = Path(__file__).parent.parent / "data"
CANDIDATES = DATA / "index_candidates.json"
OUTPUT = DATA / "index.json"

WORKERS = 8
"""CP-SAT の並列実行数"""

NAME_LENGTH = 4
"""名前の長さ"""


def main() -> None:
    """候補の中から、索引に使う固有名を決める。"""
    names = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    words = load_vocabulary()
    exclusive_groups = groups_sharing_two_places(names)
    similar_groups = groups_sharing_one_place(names)
    model = cp_model.CpModel()

    # --- 変数 ---
    # 1. それぞれの名前を採用するかしないかの二値変数
    flags = {name: model.new_bool_var(name) for name in names}
    # 2. ある位置で1文字が共通する名前の中から選ばれた名前の数を表す整数変数
    counts = [model.new_int_var(0, len(group), "") for group in similar_groups]
    # 3. ある位置で1文字が共通する名前の中から選ばれたペアの数を表す整数変数
    pairs = [
        model.new_int_var(0, len(group) * (len(group) - 1) // 2, "")
        for group in similar_groups
    ]

    # --- 制約 ---
    for group in exclusive_groups:
        # 1. 同じ位置で2文字が共通する名前は同時に存在できない。
        _ = model.add_at_most_one(flags[name] for name in group)
    for group, count, pair in zip(similar_groups, counts, pairs, strict=True):
        # group: ある位置で1文字が共通する名前のグループ (make, milo, ... 等)
        # 2. count には、group の中から選ばれた名前の数が入る。
        _ = model.add(count == sum(flags[name] for name in group))
        # 3. count が決まると、pair も自動的に決まる。
        #    CP-SAT では二次式は記述できないため、対応表を制約として渡す。
        _ = model.add_allowed_assignments(
            [count, pair],
            [(k, k * (k - 1) // 2) for k in range(len(group) + 1)],
        )

    # --- 目的関数 ---
    model.maximize(
        sum(farness(name, words) * flag for name, flag in flags.items())
        - sum(pairs)
    )

    # --- 実行 ---
    solver = solve(model)
    selected = [
        name for name, flag in flags.items() if solver.boolean_value(flag)
    ]
    selected.sort()
    write_result(selected)


def groups_sharing_two_places(names: list[str]) -> list[list[str]]:
    """2つの位置の字が共通する名前をまとめたグループをすべて返す。"""
    return [
        [name for name in names if (name[first], name[second]) == letters]
        for first, second in itertools.combinations(range(NAME_LENGTH), 2)
        for letters in {(name[first], name[second]) for name in names}
    ]


def groups_sharing_one_place(names: list[str]) -> list[list[str]]:
    """1つの位置の字が共通する名前をまとめたグループをすべて返す。"""
    return [
        [name for name in names if name[place] == letter]
        for place in range(NAME_LENGTH)
        for letter in {name[place] for name in names}
    ]


def farness(name: str, words: tuple[str, ...]) -> int:
    """その名前とすべての語との編集距離の合計を返す。"""
    return sum(Levenshtein.distance(name, word) for word in words)


def solve(model: cp_model.CpModel) -> cp_model.CpSolver:
    """モデルを受け取り最適解を持つ solver を返す。"""
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = WORKERS
    status = solver.solve(model)
    if status != cp_model.OPTIMAL:
        msg = f"最適解が見つからない: {solver.status_name(status)}"
        raise RuntimeError(msg)
    return solver


def write_result(names: list[str]) -> None:
    """決まった固有名を JSON で書き出す。"""
    names = [name.capitalize() for name in names]
    text = json.dumps(names, ensure_ascii=False, indent=2) + "\n"
    _ = OUTPUT.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
