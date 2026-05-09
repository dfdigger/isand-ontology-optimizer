import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set, List, Optional


@dataclass
class OntologyGraph:
    level_by_id: Dict[int, int] = field(default_factory=dict)
    name_by_id: Dict[int, str] = field(default_factory=dict)
    children_by_id: Dict[int, Set[int]] = field(default_factory=dict)
    parents_by_id: Dict[int, Set[int]] = field(default_factory=dict)
    roots: Set[int] = field(default_factory=set)


    # Конструктор из CSV
    @classmethod
    def from_csv(
        cls,
        factors_path: str | Path,
        edges_path: str | Path,
        roots_path: Optional[str | Path] = None,
        variants_path: Optional[str | Path] = None,
    ) -> "OntologyGraph":
        graph = cls()

        # 1) factors.csv: id,level (level=1 - руты)
        with open(factors_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                node_id = int(row["id"])
                level = int(row["level"])
                graph.level_by_id[node_id] = level
                graph.children_by_id.setdefault(node_id, set())
                graph.parents_by_id.setdefault(node_id, set())

        # 2) factor_name_variants.csv: factor_id,variant
        if variants_path:
            with open(variants_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    node_id = int(row["factor_id"])
                    variant = row["variant"].strip()
                    if node_id not in graph.name_by_id and variant:
                        graph.name_by_id[node_id] = variant

        # fallback имя, если варианта нет
        for node_id in graph.level_by_id:
            graph.name_by_id.setdefault(node_id, f"factor_{node_id}")

        # 3) factor_graph_edges.csv: predecessor_id -> successor_id
        with open(edges_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                parent = int(row["predecessor_id"])
                child = int(row["successor_id"])

                # даже если в factors не было, добавляем узел с level=-1
                if parent not in graph.level_by_id:
                    graph.level_by_id[parent] = -1
                    graph.name_by_id.setdefault(parent, f"factor_{parent}")
                if child not in graph.level_by_id:
                    graph.level_by_id[child] = -1
                    graph.name_by_id.setdefault(child, f"factor_{child}")

                graph.children_by_id.setdefault(parent, set()).add(child)
                graph.parents_by_id.setdefault(child, set()).add(parent)
                graph.children_by_id.setdefault(child, set())
                graph.parents_by_id.setdefault(parent, set())

        # 4) factor_graph_roots.csv: root_id
        if roots_path:
            with open(roots_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    graph.roots.add(int(row["root_id"]))

        # если roots не заданы/пусты, выведем по структуре
        if not graph.roots:
            graph.roots = {
                node_id for node_id, parents in graph.parents_by_id.items() if len(parents) == 0
            }

        return graph


    def nodes(self) -> Set[int]:
        return set(self.level_by_id.keys())

    def children(self, node_id: int) -> Set[int]:
        return self.children_by_id.get(node_id, set())

    def parents(self, node_id: int) -> Set[int]:
        return self.parents_by_id.get(node_id, set())

    def is_leaf(self, node_id: int) -> bool:
        return len(self.children(node_id)) == 0

    def leaves(self) -> Set[int]:
        return {node_id for node_id in self.nodes() if self.is_leaf(node_id)}

    def has_multiple_parents(self, node_id: int) -> bool:
        return len(self.parents(node_id)) > 1

    def multi_parent_nodes(self) -> Dict[int, int]:
        return {
            node_id: len(self.parents(node_id))
            for node_id in self.nodes()
            if self.has_multiple_parents(node_id)
        }    


    # Валидация графа
    def detect_cycle(self) -> bool:
        """
        Проверка на циклы, классический dfs с цветами: 0=white,1=gray,2=black.
        """
        color: Dict[int, int] = {n: 0 for n in self.nodes()}

        def dfs(u: int) -> bool:
            color[u] = 1
            for v in self.children(u):
                if color[v] == 1:
                    return True
                if color[v] == 0 and dfs(v):
                    return True
            color[u] = 2
            return False

        for n in self.nodes():
            if color[n] == 0 and dfs(n):
                return True
        return False

    def validation_report(self) -> dict:
        all_nodes = self.nodes()
        multi = self.multi_parent_nodes()

        nodes_without_level = [n for n, lvl in self.level_by_id.items() if lvl == -1]
        nodes_without_name = [n for n in all_nodes if not self.name_by_id.get(n)]

        return {
            "n_nodes": len(all_nodes),
            "n_edges": sum(len(ch) for ch in self.children_by_id.values()),
            "n_roots": len(self.roots),
            "n_leaves": len(self.leaves()),
            "has_cycle": self.detect_cycle(),
            "n_multi_parent_nodes": len(multi),
            "top_multi_parent_nodes": sorted(
                multi.items(), key=lambda x: (-x[1], x[0])
            )[:20],
            "nodes_without_level": nodes_without_level[:20],
            "nodes_without_name": nodes_without_name[:20],
        }