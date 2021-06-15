from functools import wraps
from typing import List, Tuple

import numpy as np

from mathutils import Matrix

from sverchok.data_structure import levels_of_list_or_np


SvVerts = List[Tuple[float, float, float]]
SvEdges = List[Tuple[int, int]]
SvPolys = List[List[int]]


def vectorize(func=None, *, match_mode="REPEAT"):
    """
    If there is function which takes some values
    with this decorator it's possible to call the function by passing list of values of any shape
    Take care of properly annotating of decorated function
    Use Tuple[] in return annotation only if you want the decorator splits the return values into different lists

    ++ Example ++

    from sverchok.utils import vectorize

    def main_node_logic(*, prop_a: List[float], prop_b: Matrix, mode_a: str) -> Tuple[list, list]:
        ...
        return data1, data2

    class MyNode:
        ...
        def process(self):
            input_a = self.inputs[0].sv_get(default=None)
            input_b = self.inputs[1].sv_get(default=None)

            main_node_logic = vectorize(main_node_logic, match_mode=self.match_mode)
            out1, out2 = main_node_logic(input_a, input_b, mode_a = self.mode_a)

            self.outputs[0].sv_set(out1)
            self.outputs[1].sv_set(out2)
    """

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
                annotation = func.__annotations__.get(key)
                nesting_level = _get_nesting_level(annotation) if annotation else 0
                walkers.append(DataWalker(data, output_nesting=nesting_level, mode=match_mode, data_name=key))

        # this is corner case, it can't be handled via walk data iterator
        if all([w.what_is_next() == DataWalker.VALUE for w in walkers]):
            return func(*args, **kwargs)

        out_number = _get_output_number(func)

        # handle case when return value of decorated function is simple one value
        if out_number == 1:
            out_list = []
            for match_args, result in walk_data(walkers, [out_list]):
                match_args, match_kwargs = match_args[:len(args)], match_args[len(args):]
                match_kwargs = {n: d for n, d in zip(kwargs, match_kwargs)}
                func_out = func(*match_args, **match_kwargs)
                if not is_empty_out(func_out):
                    result[0].append(func_out)
            return out_list

        # the case when return value is tuple of multiple values
        else:
            out_lists = [[] for _ in range(out_number)]
            for match_args, result in walk_data(walkers, out_lists):
                match_args, match_kwargs = match_args[:len(args)], match_args[len(args):]
                match_kwargs = {n: d for n, d in zip(kwargs, match_kwargs)}
                func_out = func(*match_args, **match_kwargs)
                [r.append(out) for r, out in zip(result, func_out) if not is_empty_out(out)]
            return out_lists

    def is_empty_out(value):
        if value is None:
            return True
        try:
            return not bool(len(value))
        except TypeError:
            return False

    return wrap


def devectorize(func=None, *, match_mode="REPEAT"):
    """It takes list of values of arbitrary shape, flatten it
    and call the decorated function once with flattened data
    This needs for functions (nodes) which breaks vectorization"""

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
                annotation = func.__annotations__.get(key)
                nesting_level = _get_nesting_level(annotation) if annotation else 0
                walkers.append(DataWalker(data, output_nesting=nesting_level - 1, mode=match_mode, data_name=key))

        flat_data = {key: [] for key in kwargs}
        for match_args, _ in walk_data(walkers, []):
            match_args, match_kwargs = match_args[:len(args)], match_args[len(args):]
            [container.append(data) for container, data in zip(flat_data.values(), match_kwargs)]

        return func(**flat_data)

    return wrap


def _get_nesting_level(annotation) -> int:
    """It measures how many nested types the annotation has
    simple annotations like string, float have 0 level
    list without arguments gives 1 level
    List[list] such thing returns 2 level"""
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
    """Returns number of arguments returning by given function
    the function should have returning annotation with Tuple value - Tuple[list, list]"""
    annotation = function.__annotations__.get('return')
    if annotation:
        if hasattr(annotation, '__origin__') and annotation.__origin__ == tuple:
            if hasattr(annotation, '__args__'):
                return len(annotation.__args__)
    return 1


def _what_is_next_catch(func):
    """It's exclusively for using in DataWalker class for optimization performance"""

    @wraps(func)
    def what_is_next_catcher(self):
        next_val_id = id(self._stack[-1])
        if next_val_id not in self._catch:
            # this should not conflict with float, string, integer and other values
            self._catch[next_val_id] = func(self)
        return self._catch[next_val_id]

    return what_is_next_catcher


class DataWalker:
    """This class allows walk over a list of arbitrary shape like over a tree data structure
    Input data can be a value or list
    the list can include values and / or other lists
    the value itself can be just a number, list of numbers, list of list of numbers etc.
    values should be consistent and should not include other values
    for example inside list of vertices there should be other lists of vertices or any thing else
    there is no way of handling such data structure efficiently"""

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
                return list(data) + [data[-1]] * (match_len - len(data))  # todo deepcopy ??
            # todo add other modes

    def __repr__(self):
        return f"<DataWalker {self._name if self._name else 'data'}: {self._stack}>"


class EmptyDataWalker:
    """Use this (instead of DataWalker) if a channel does not has any data
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
    """Generates tree from nested lists with step up/down interface"""
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


def walk_data(walkers: List[DataWalker], out_list: List[list]) -> Tuple[list, List[list]]:
    """It walks over data in given walkers in proper order
    match data between each other if necessary
    and gives output containers where to put result of handled data"""
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
