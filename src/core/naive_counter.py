from dataclasses import dataclass, field
from typing import Callable, Dict

from .ontology_graph import OntologyGraph


@dataclass
class NaiveCounter:
    """
    Наивный подсчёт: сумма по детям.
    Один и тот же лист суммируется столько раз, сколько различных путей к нему
    из текущего узла
    """

    graph: OntologyGraph

    # сохраняем данные для нодов, чтобы не считать их заново
    memo: Dict[int, float] = field(default_factory=dict)

    def count_for_node(
        self,
        node_id: int,
        term_weight: Callable[[int], float] | None = None,  # id -> weight
    ) -> float:
        if node_id in self.memo:
            return self.memo[node_id]

        children = self.graph.children(node_id)
        if not children:
            leaf_value = 1.0 if term_weight is None else float(term_weight(node_id))
            self.memo[node_id] = leaf_value
            return leaf_value

        total = 0.0
        for child_id in children:
            total += self.count_for_node(child_id, term_weight)

        self.memo[node_id] = total
        return total

    def count_for_all_nodes(
        self,
        term_weight: Callable[[int], float] | None = None,
    ) -> Dict[int, float]:
        self.memo.clear()
        return {
            node_id: self.count_for_node(node_id, term_weight=term_weight)
            for node_id in self.graph.nodes()
        }

    def reset_cache(self) -> None:
        self.memo.clear()
