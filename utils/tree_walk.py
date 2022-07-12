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
from typing import Generator, List, TypeVar, Generic, Callable, Iterable, Iterator

T = TypeVar('T')
NextFunc = Callable[[T], Iterable[T]]


def bfs_walk(nodes: Iterable[T], next_: NextFunc) -> Iterator[T]:
    """
    Walk from the current node, it will visit all next nodes
    First will be visited children nodes than children of children nodes etc.
    https://en.wikipedia.org/wiki/Breadth-first_search
    """
    waiting_nodes = deque(nodes)
    discovered = set(nodes)

    for i in range(20000):
        if not waiting_nodes:
            break
        n = waiting_nodes.popleft()
        yield n
        for next_node in next_(n):
            if next_node not in discovered:
                waiting_nodes.append(next_node)
                discovered.add(next_node)
    else:
        raise RecursionError(f'The tree has either more then={20000} nodes '
                             f'or most likely it is circular')


def recursion_dfs_walk(nodes: Iterable[T], next_: NextFunc, _count=None) -> Iterator[T]:
    if _count is None:
        _count = count(1)
    for node in nodes:
        yield node
        yield from recursion_dfs_walk(next_(node), next_, _count)
    if (i := next(_count)) and i > 20000:
        raise RecursionError(f'The tree has either more then={20000} nodes '
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
        """doesn't have nodes before"""
        return not bool(self.last_nodes)

    @property
    def is_output(self):
        """doesn't have nodes after"""
        return not bool(self.next_nodes)


NodeType = TypeVar('NodeType', bound=Node)


class Tree(ABC, Generic[NodeType]):
    @property
    @abstractmethod
    def nodes(self): ...  # something iterable

    @property
    def input_nodes(self) -> List[NodeType]:
        """Nodes which don't have nodes before"""
        return [node for node in self.nodes if node.is_input]

    @property
    def output_nodes(self) -> List[NodeType]:
        """Nodes which don't have nodes after"""
        return [node for node in self.nodes if node.is_output]

    @staticmethod
    def bfs_walk(nodes: List[NodeType], direction: str = 'FORWARD') -> Generator[NodeType]:
        """
        Walk from the current node, it will visit all next nodes in FORWARD of BACKWARD direction
        First will be visited children nodes than children of children nodes and etc
        """
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
    def dfs_walk(nodes: List[NodeType], direction: str = 'FORWARD') -> Generator[NodeType]:
        """
        Walk from the current node, it will visit all next nodes in FORWARD of BACKWARD direction
        First will be visited first child and its children then second child and etc
        """
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
    def sorted_walk(to_nodes: List[NodeType]) -> Generator[NodeType]:
        """
        If tree is 0--1--2--3 and node "3" is given the method will return nodes in next order [0, 1, 2, 3]
        """
        # https://en.wikipedia.org/wiki/Topological_sorting
        stack = []
        discovered = set()  # gray color
        visited = set()  # black color

        safe_counter = count()
        max_node_number = 20000

        for to_node in to_nodes:
            if to_node in visited:
                continue
            else:
                stack.append(to_node)
                discovered.add(to_node)

            while stack:
                node = stack[-1]
                next_undiscovered_node = None
                for next_node in node.last_nodes:
                    if next_node in discovered:
                        raise RecursionError(f'The tree is cycled')
                    if next_node not in visited:
                        next_undiscovered_node = next_node
                        break

                if next_undiscovered_node is not None:
                    stack.append(next_undiscovered_node)
                    discovered.add(next_undiscovered_node)
                else:
                    # last node in stack does not have next nodes or all of them are visited
                    stack.pop()
                    yield node
                    visited.add(node)
                    discovered.remove(node)

                if next(safe_counter) > max_node_number:
                    raise RuntimeError(f'The tree has either more then={max_node_number} nodes '
                                       f'or most likely it is circular')
