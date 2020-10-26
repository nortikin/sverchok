# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from itertools import count
from typing import Generator, List


class Tree(ABC):
    @property
    @abstractmethod
    def nodes(self): ...

    @property
    def input_nodes(self) -> List[Node]:
        return [node for node in self.nodes.values() if node.is_input]

    @property
    def output_nodes(self) -> List[Node]:
        return [node for node in self.nodes.values() if node.is_output]

    @staticmethod
    def bfs_walk(nodes: List[Node], direction: str = 'FORWARD') -> Generator[Node]:
        """Forward walk from the current node, it will visit all next nodes"""
        # https://en.wikipedia.org/wiki/Breadth-first_search
        waiting_nodes = deque(nodes)
        discovered = set(nodes)

        safe_counter = count()
        max_node_number = 20000
        while waiting_nodes:
            node = waiting_nodes.popleft()
            yield node
            for next_node in (node.next_nodes if direction == 'FORWARD' else node.last_nodes):
                if next_node not in discovered:
                    waiting_nodes.append(next_node)
                    discovered.add(next_node)

            if next(safe_counter) > max_node_number:
                raise RecursionError(f'The tree has either more then={max_node_number} nodes '
                                     f'or most likely it is circular')

    @staticmethod
    def dfs_walk(nodes: List[Node], direction: str = 'FORWARD') -> Generator[Node]:
        # https://en.wikipedia.org/wiki/Depth-first_search
        stack = nodes
        visited = set()

        safe_counter = count()
        max_node_number = 20000
        while stack:
            current_node = stack.pop()
            yield current_node
            visited.add(current_node)
            for next_node in current_node.next_nodes if direction == 'FORWARD' else current_node.last_nodes:
                if next_node not in visited:
                    stack.append(next_node)

            if next(safe_counter) > max_node_number:
                raise RecursionError(f'The tree has either more then={max_node_number} nodes '
                                     f'or most likely it is circular')

    @staticmethod
    def sorted_walk(to_nodes: List[Node]) -> Generator[Node]:
        stack = to_nodes
        discovered = set(to_nodes)  # gray color
        visited = set()  # black color

        safe_counter = count()
        max_node_number = 20000
        while stack:
            node = stack[-1]
            next_visited = []
            for next_node in node.last_nodes:
                next_visited.append(True if next_node in visited else False)
                if next_node not in discovered and next_node not in visited:
                    stack.append(next_node)
                    visited.add(next_node)
            if not next_visited or all(next_visited):
                stack.pop()
                yield node
                visited.add(node)

            if next(safe_counter) > max_node_number:
                raise RecursionError(f'The tree has either more then={max_node_number} nodes '
                                     f'or most likely it is circular')


class Node(ABC):
    @property
    @abstractmethod
    def next_nodes(self) -> List[Node]: ...

    @property
    @abstractmethod
    def last_nodes(self) -> List[Node]: ...

    @property
    def is_input(self) -> bool:
        return not bool(self.last_nodes)

    @property
    def is_output(self):
        return not bool(self.next_nodes)

    def bfs_walk(self, direction: str = 'FORWARD') -> Generator[Node]:
        yield from Tree.bfs_walk([self], direction)

    def dfs_walk(self, direction: str = 'FORWARD') -> Generator[Node]:
        yield from Tree.dfs_walk([self], direction)
