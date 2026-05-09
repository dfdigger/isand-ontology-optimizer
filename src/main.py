import sys
import unittest
from pathlib import Path
from pprint import pprint
from itertools import islice

# для корректного импорта
_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from core import NaiveCounter, OntologyGraph, UniqueCounter
from tests import test_core


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _data_raw() -> Path:
    return _repo_root() / "data" / "raw"


def run_unit_tests() -> None:
    """Прогон тестов из tests/test_core.py"""
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_core)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


def main() -> None:
    run_unit_tests()

    raw = _data_raw()
    graph = OntologyGraph.from_csv(
        factors_path=raw / "factors.csv",
        edges_path=raw / "factor_graph_edges.csv",
        roots_path=raw / "factor_graph_roots.csv",
        variants_path=raw / "factor_name_variants.csv",
    )

    print("\n=== validation_report ===")
    pprint(graph.validation_report())

    naive_counts = NaiveCounter(graph).count_for_all_nodes()
    unique_counts = UniqueCounter(graph).count_for_all_nodes()

    # вывод первых 40 узлов для примера
    short_naive_counts = dict(islice(naive_counts.items(), 40))
    short_unique_counts = dict(islice(unique_counts.items(), 40))

    print("\n=== naive: ===")
    pprint(short_naive_counts)

    print("\n=== unique: ===")
    pprint(short_unique_counts)

    differing = [
        (f"nid: {nid}", f"naive: {naive_counts[nid]}", f"unique: {unique_counts[nid]}")
        for nid in sorted(graph.nodes())
        if naive_counts[nid] != unique_counts[nid]
    ]
    print(f"\n=== узлы, где naive != unique: {len(differing)} ===")
    if differing:
        pprint(differing)


if __name__ == "__main__":
    main()
