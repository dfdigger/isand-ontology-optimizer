from dataclasses import dataclass, field
from typing import Callable, Dict, Set

from .ontology_graph import OntologyGraph

@dataclass
class UniqueCounter:
    """
    Уникальный подсчет терминов:
    для каждого узла сначала собирается множество уникальных leaf-терминов,
    это устраняет дубли из-за нескольких путей до одного и того же leaf
    """

    graph: OntologyGraph

    # сохраняем данные для нодов, чтобы не считать их заново
    memo_terms: Dict[int, Set[int]] = field(default_factory=dict)

    def terms_for_node(self, node_id: int) -> Set[int]:
        if node_id in self.memo_terms:
            return self.memo_terms[node_id]

        children = self.graph.children(node_id)
        if not children:
            self.memo_terms[node_id] = {node_id}
            return self.memo_terms[node_id]

        uniq_terms: Set[int] = set()
        for child_id in children:
            uniq_terms.update(self.terms_for_node(child_id))

        self.memo_terms[node_id] = uniq_terms
        return uniq_terms

    def count_for_node(
        self,
        node_id: int,
        term_weight: Callable[[int], float] | None = None,  # id -> weight
    ) -> float:
        """
        Если term_weight не задан, каждый термин имеет вес 1.
        Если term_weight задан, сумма считается по весам уникальных терминов
        """
        terms = self.terms_for_node(node_id)
        if term_weight is None:
            return float(len(terms))
        return float(sum(term_weight(term_id) for term_id in terms))

    def count_for_all_nodes(
        self,
        term_weight: Callable[[int], float] | None = None,
    ) -> Dict[int, float]:
        self.memo_terms.clear()
        return {
            node_id: self.count_for_node(node_id, term_weight=term_weight)
            for node_id in self.graph.nodes()
        }

    def reset_cache(self) -> None:
        self.memo_terms.clear()