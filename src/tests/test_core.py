"""
Сравнение NaiveCounter и UniqueCounter на маленьких ручных графах
"""

import sys
import unittest
from pathlib import Path

# для корректного импорта
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from core import NaiveCounter
from core import OntologyGraph
from core import UniqueCounter


def _chain_graph() -> OntologyGraph:
    """1 -> 2 -> 3"""
    g = OntologyGraph()
    for nid in (1, 2, 3):
        g.level_by_id[nid] = nid
        g.name_by_id[nid] = f"n{nid}"
    g.children_by_id = {1: {2}, 2: {3}, 3: set()}
    g.parents_by_id = {1: set(), 2: {1}, 3: {2}}
    g.roots = {1}
    return g


def _triangle_graph() -> OntologyGraph:
    """Корень 1 и два листа 2, 3"""
    g = OntologyGraph()
    for nid in (1, 2, 3):
        g.level_by_id[nid] = 1
        g.name_by_id[nid] = f"n{nid}"
    g.children_by_id = {1: {2, 3}, 2: set(), 3: set()}
    g.parents_by_id = {1: set(), 2: {1}, 3: {1}}
    g.roots = {1}
    return g


def _diamond_graph() -> OntologyGraph:
    """
      1
     / \\
    2   3
     \\ /
      4
    """
    g = OntologyGraph()
    for nid in (1, 2, 3, 4):
        g.level_by_id[nid] = 1
        g.name_by_id[nid] = f"n{nid}"
    g.children_by_id = {1: {2, 3}, 2: {4}, 3: {4}, 4: set()}
    g.parents_by_id = {1: set(), 2: {1}, 3: {1}, 4: {2, 3}}
    g.roots = {1}
    return g


def _naive_all(g: OntologyGraph) -> dict[int, float]:
    c = NaiveCounter(g)
    return c.count_for_all_nodes()


def _unique_all(g: OntologyGraph) -> dict[int, float]:
    c = UniqueCounter(g)
    return c.count_for_all_nodes()


class TestNaiveVsUnique(unittest.TestCase):
    def test_chain_counts_match(self) -> None:
        g = _chain_graph()
        naive = _naive_all(g)
        unique = _unique_all(g)
        for nid in g.nodes():
            self.assertEqual(naive[nid], unique[nid], msg=f"node {nid}")

    def test_triangle_counts_match(self) -> None:
        g = _triangle_graph()
        naive = _naive_all(g)
        unique = _unique_all(g)
        for nid in g.nodes():
            self.assertEqual(naive[nid], unique[nid], msg=f"node {nid}")

    def test_diamond_root_naive_doubles_unique(self) -> None:
        g = _diamond_graph()
        naive = NaiveCounter(g).count_for_node(1)
        unique = UniqueCounter(g).count_for_node(1)
        self.assertEqual(naive, 2.0)
        self.assertEqual(unique, 1.0)

    def test_diamond_inner_nodes_agree(self) -> None:
        g = _diamond_graph()
        for nid in (2, 3, 4):
            n = NaiveCounter(g).count_for_node(nid)
            u = UniqueCounter(g).count_for_node(nid)
            self.assertEqual(n, u, msg=f"node {nid}")

    def test_count_for_all_nodes_same_keys(self) -> None:
        g = _diamond_graph()
        naive_keys = set(_naive_all(g).keys())
        unique_keys = set(_unique_all(g).keys())
        self.assertEqual(naive_keys, unique_keys)
        self.assertEqual(naive_keys, g.nodes())

    def test_unique_with_weight_matches_manual(self) -> None:
        g = _diamond_graph()
        weights = {4: 10.0}

        def w(term_id: int) -> float:
            return weights.get(term_id, 1.0)

        total = UniqueCounter(g).count_for_node(1, term_weight=w)
        self.assertEqual(total, 10.0)

    def test_naive_with_weight_diamond_doubles_unique(self) -> None:
        g = _diamond_graph()
        weights = {4: 10.0}

        def w(term_id: int) -> float:
            return weights.get(term_id, 1.0)

        naive = NaiveCounter(g).count_for_node(1, term_weight=w)
        unique = UniqueCounter(g).count_for_node(1, term_weight=w)
        self.assertEqual(naive, 20.0)
        self.assertEqual(unique, 10.0)


if __name__ == "__main__":
    unittest.main()