from functools import wraps
from typing import List, Tuple

import numpy as np

from mathutils import Matrix

from sverchok.data_structure import levels_of_list_or_np


SvVerts = List[Tuple[float, float, float]]
SvEdges = List[Tuple[int, int]]
SvPolys = List[List[int]]


def vectorize(func=None, *, match_mode="REPEAT"):

    # this condition only works when used via "@" syntax
    if func is None:
        return lambda f: vectorize(f, match_mode=match_mode)

    @wraps(func)
    def wrap(*args, **kwargs):

        # it's better not to use positional arguments for backward compatibility
        # in this case a function can get new arguments
        if args:
            raise TypeError(f'Vectorized function {func.__name__} should not have positional arguments')

        walkers = []
        for key, data in zip(kwargs, kwargs.values()):
            if data is None or data == []:
                walkers.append(EmptyDataWalker(data, key))
            else:
                annotation = func.__annotations__[key]
                walkers.append(
                    DataWalker(data, output_nesting=_get_nesting_level(annotation), mode=match_mode, data_name=key))

        # this is corner case, it can't be handled via walk data iterator
        if all([w.what_is_next() == DataWalker.VALUE for w in walkers]):
            return func(*args, **kwargs)

        out_lists = [[] for _ in range(_get_output_number(func))]
        for match_args, result in walk_data(walkers, out_lists):
            match_args, match_kwargs = match_args[:len(args)], match_args[len(args):]
            match_kwargs = {n: d for n, d in zip(kwargs, match_kwargs)}
            func_out = func(*match_args, **match_kwargs)
            [r.append(out) for r, out in zip(result, func_out) if out is not None and len(out)]
        return out_lists

    return wrap


def devectorize(func=None, *, match_mode="REPEAT"):

    # this condition only works when used via "@" syntax
    if func is None:
        return lambda f: vectorize(f, match_mode=match_mode)

    @wraps(func)
    def wrap(*args, **kwargs):

        # it's better not to use positional arguments for backward compatibility
        # in this case a function can get new arguments
        if args:
            raise TypeError(f'Vectorized function {func.__name__} should not have positional arguments')

        walkers = []
        for key, data in zip(kwargs, kwargs.values()):
            if data is None or data == []:
                walkers.append(EmptyDataWalker(data, key))
            else:
                annotation = func.__annotations__[key]
                walkers.append(
                    DataWalker(data, output_nesting=_get_nesting_level(annotation) - 1, mode=match_mode, data_name=key))

        flat_data = {key: [] for key in kwargs}
        for match_args, _ in walk_data(walkers, []):
            match_args, match_kwargs = match_args[:len(args)], match_args[len(args):]
            [container.append(data) for container, data in zip(flat_data.values(), match_kwargs)]

        return func(**flat_data)

    return wrap


def _get_nesting_level(annotation):
    if not hasattr(annotation, '__origin__'):
        if annotation in [list, tuple]:
            return 1
        elif annotation in [float, int, bool, Matrix, str]:
            return 0

    elif annotation.__origin__ is list:
        return 1 + _get_nesting_level(annotation.__args__[0])
    elif annotation.__origin__ is tuple:
        # not sure how this should act if arguments of the tuple have different level of nesting
        return 1 + max([_get_nesting_level(arg) for arg in annotation.__args__])

    raise NotImplementedError(f'Given annotation: {annotation} is not supported yet')


def _get_output_number(function):
    annotation = function.__annotations__.get('return')
    if annotation:  # todo if only tuple
        if hasattr(annotation, '__args__'):
            return len(annotation.__args__)
    return 1


def _what_is_next_catch(func):

    @wraps(func)
    def what_is_next_catcher(self):
        next_val_id = id(self._stack[-1])
        if next_val_id not in self._catch:
            # this should not conflict with float, string, integer and other values
            self._catch[next_val_id] = func(self)
        return self._catch[next_val_id]

    return what_is_next_catcher


class DataWalker:
    """Input data can be a value or list
    the list should include either values or other lists but not both simultaneously
    because there is no way of handling such data structure efficiently
    the value itself can be just a number, list of numbers, list of list of numbers etc."""

    # match modes
    SHORT, CYCLE, REPEAT, XREF, XREF2 = "SHORT", "CYCLE", "REPEAT", "XREF", "XREF2"

    # node types
    VALUE, END, SUB_TREE = "VALUE", "END", "SUB_TREE"

    EXIT_VALUE = type('ExitValue', (), {'__repr__': lambda s: "<ExitValue>"})()

    def __init__(self, data, output_nesting=0, mode=REPEAT, data_name=None):
        self.match_mode = mode

        self._stack = [data]
        self._output_nesting = output_nesting
        self._name = data_name

        self._catch = dict()  # for optimization

    def step_down_matching(self, match_len, match_mode):
        # todo protection from little nesting
        if self.what_is_next() == DataWalker.SUB_TREE:
            current_node = self._stack.pop()
        elif self.what_is_next() == DataWalker.VALUE:
            current_node = [self._stack.pop()]
        else:
            raise RuntimeError(f'Step down is impossible current position is: {self._stack[-1]}')

        self._stack.append(DataWalker.EXIT_VALUE)
        self._stack.extend(list(reversed(self._match_values(current_node, match_len, match_mode))))

    def step_up(self):
        if self.what_is_next() != DataWalker.END:
            raise RuntimeError(f'There are still values to read: {self._stack}')
        self._stack.pop()

    def pop_next_value(self):
        return self._stack.pop()

    # this method is used most extensively
    @_what_is_next_catch
    def what_is_next(self):
        if self._stack[-1] is DataWalker.EXIT_VALUE:
            return DataWalker.END
        if isinstance(self._stack[-1], (list, tuple, np.ndarray)):
            nesting = levels_of_list_or_np(self._stack[-1])
        else:
            nesting = 0
        if nesting == self._output_nesting:
            return DataWalker.VALUE
        else:  # todo add the case when next element has too less nested levels
            return DataWalker.SUB_TREE

    @property
    def next_values_number(self):
        try:
            if self.what_is_next() == DataWalker.VALUE:
                return 1
            last = self._stack[-1]
            return len(last)
        except (IndexError, TypeError):
            return 0

    @property
    def is_exhausted(self):
        return not bool(self._stack)

    @staticmethod
    def _match_values(data, match_len, match_mode):
        if len(data) > match_len:
            return data[:match_len]
        elif len(data) == match_len:
            return data
        else:
            if match_mode == DataWalker.REPEAT:
                return data + [data[-1]] * (match_len - len(data))  # todo deepcopy ??
            # todo add other modes

    def __repr__(self):
        return f"<DataWalker {self._name if self._name else 'data'}: {self._stack}>"


class EmptyDataWalker:
    """Use this if a channel does not has any data
    It is needed not to overcomplicate logic of DataWalker"""

    def __init__(self, data=None, data_name=None):
        self._data = data
        self._name = data_name

    def step_down_matching(self, *_, **__):
        pass

    def step_up(self):
        pass

    def pop_next_value(self):
        return self._data

    def what_is_next(self):
        return DataWalker.VALUE

    @property
    def next_values_number(self):
        return 0

    @property
    def is_exhausted(self):
        return True

    def __repr__(self):
        return f"<EmptyDataWalker {self._name if self._name else 'data'}: {self._data}>"


class ListTreeGenerator:
    def __init__(self, root_list):
        self.data = root_list
        self._stack = [root_list]

    def step_down(self):
        new_node = []
        self._stack.append(new_node)

    def step_up(self):
        last_node = self._stack.pop()
        if last_node and self._stack:
            current_node = self._stack[-1]
            current_node.append(last_node)

    @property
    def current_list(self):
        return self._stack[-1]

    def __repr__(self):
        return f'<TreeGen data: {self.data}>'


def walk_data(walkers: List[DataWalker], out_list: List[list]):
    match_mode = DataWalker.REPEAT  # todo should be determined by modes of input walkers
    result_data = [ListTreeGenerator(l) for l in out_list]

    # first step is always step down because walkers create extra wrapping list (for the algorithm simplicity)
    max_value_len = max(w.next_values_number for w in walkers)
    [w.step_down_matching(max_value_len, match_mode) for w in walkers]

    while any(not w.is_exhausted for w in walkers):
        if all(w.what_is_next() == DataWalker.VALUE for w in walkers):
            yield [w.pop_next_value() for w in walkers], [t.current_list for t in result_data]
        elif any(w.what_is_next() == DataWalker.END for w in walkers):
            [w.step_up() for w in walkers]
            [t.step_up() for t in result_data]
        elif any(w.what_is_next() == DataWalker.SUB_TREE for w in walkers):
            max_value_len = max(w.next_values_number for w in walkers)
            [w.step_down_matching(max_value_len, match_mode) for w in walkers]
            [t.step_down() for t in result_data]


if __name__ == '__main__':
    wa = DataWalker(1)
    wb = DataWalker([1, 2, 3])

    walker = flat_walk_data(wa, wb)
    assert [v for v in walker] == [[1, 1], [1, 2], [1, 3]]

    wa = DataWalker([[1, 2], 3])
    wb = DataWalker([1, [2, 3], 4])

    walker = flat_walk_data(wa, wb)
    assert [v for v in walker] == [[1, 1], [2, 1], [3, 2], [3, 3], [3, 4]]

    wa = DataWalker([[1, 2], [3, 4, 5]])
    wb = DataWalker([1, [2, 3], 4])

    walker = flat_walk_data(wa, wb)
    assert [v for v in walker] == [[1, 1], [2, 1], [3, 2], [4, 3], [5, 3], [3, 4], [4, 4], [5, 4]]

    wa = DataWalker(1)
    wb = DataWalker([1, 2, 3])

    out = []
    walker = walk_data(wa, wb, out_list=out)
    [l.append((a, b)) for (a, b), l in walker]
    assert out == [(1, 1), (1, 2), (1, 3)]

    wa = DataWalker([[1, 2], 3])
    wb = DataWalker([1, [2, 3], 4])

    out = []
    walker = walk_data(wa, wb, out_list=out)
    [l.append((a, b)) for (a, b), l in walker]
    assert out == [[(1, 1), (2, 1)], [(3, 2), (3, 3)], (3, 4)]

    wa = DataWalker([[1, 2], [3, 4, 5]])
    wb = DataWalker([1, [2, 3], 4])

    out = []
    walker = walk_data(wa, wb, out_list=out)
    [l.append((a, b)) for (a, b), l in walker]
    assert out == [[(1, 1), (2, 1)], [(3, 2), (4, 3), (5, 3)], [(3, 4), (4, 4), (5, 4)]]

    def math(a: float, b: float, *, mode='SUM'):
        if mode == 'SUM':
            return a + b
        elif mode == 'MUL':
            return a * b

    a_values = [[1, 2], [3, 4, 5]]
    b_values = [1, [2, 3], 4]

    math1 = vectorize(math, match_mode="REPEAT")
    assert math1(a_values, b_values, mode='SUM') == [[2, 3], [5, 7, 8], [7, 8, 9]]

    a_values = 10
    b_values = [1, [2, 3], 4]

    math2 = vectorize(math, match_mode="REPEAT")
    assert math2(a_values, b_values, mode='SUM') == [11, [12, 13], 14]
