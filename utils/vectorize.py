from functools import wraps
from itertools import chain


def vectorize(func=None, *, match_mode="REPEAT"):

    # this condition only works when used via "@" syntax
    if func is None:
        return lambda f: vectorize(f, match_mode=match_mode)

    @wraps(func)
    def wrap(*args, **kwargs):
        walkers = []
        for data in chain(args, kwargs.values()):
            # todo handle nesting levels and input match_modes format
            walkers.append(DataWalker(data, mode=match_mode))
        out = []
        for match_args, result in walk_data(*walkers, out_list=out):
            match_args, match_kwargs = match_args[:len(args)], match_args[len(args):]
            match_kwargs = {n: d for n, d in zip(kwargs, match_kwargs)}
            result.append(func(*match_args, **match_kwargs))
        return out

    return wrap


def levelsOflist(lst):  # todo to remove
    """calc list nesting only in countainment level integer"""
    level = 1
    for n in lst:
        if n and isinstance(n, (list, tuple)):
            level += levelsOflist(n)
        return level
    return 0


class DataWalker:
    # match modes
    SHORT, CYCLE, REPEAT, XREF, XREF2 = "SHORT", "CYCLE", "REPEAT", "XREF", "XREF2"

    # node types
    VALUE, END, SUB_TREE = "VALUE", "END", "SUB_TREE"

    EXIT_VALUE = type('ExitValue', (), {'__repr__': lambda s: "<ExitValue>"})()

    def __init__(self, data, output_nesting=0, mode=REPEAT):
        self.match_mode = mode

        self._stack = [data]
        self._output_nesting = output_nesting

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

    def what_is_next(self):
        if self._stack[-1] is DataWalker.EXIT_VALUE:
            return DataWalker.END
        if isinstance(self._stack[-1], (list, tuple)):  # todo add numpy arrays or more general solution?
            nesting = levelsOflist(self._stack[-1])
        else:
            nesting = 0
        if nesting == self._output_nesting:
            return DataWalker.VALUE
        else:  # todo add the case when next element has too less nested levels
            return DataWalker.SUB_TREE

    @property
    def next_values_number(self):
        try:
            last = self._stack[-1]
            return 0 if isinstance(last, str) else len(last)  # todo other types??
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
        return f"<DataWalker data: {self._stack}>"


class ListTreeGenerator:
    def __init__(self, root_list):
        self.data = root_list
        self._stack = [root_list]

    def step_down(self):
        current_node = self._stack[-1]
        new_node = []
        current_node.append(new_node)
        self._stack.append(new_node)

    def step_up(self):
        self._stack.pop()

    @property
    def current_list(self):
        return self._stack[-1]

    def __repr__(self):
        return f'<TreeGen data: {self.data}>'


def walk_data(*walkers, out_list):
    match_mode = DataWalker.REPEAT  # todo should be determined by modes of input walkers
    result_data = ListTreeGenerator(out_list)

    # first step is always step down because walkers create extra wrapping list (for the algorithm simplicity)
    max_value_len = max(w.next_values_number for w in walkers)
    [w.step_down_matching(max_value_len, match_mode) for w in walkers]

    while any(not w.is_exhausted for w in walkers):
        if any(w.what_is_next() == DataWalker.END for w in walkers):
            [w.step_up() for w in walkers]
            result_data.step_up()
        elif any(w.what_is_next() == DataWalker.SUB_TREE for w in walkers):
            max_value_len = max(w.next_values_number for w in walkers)
            [w.step_down_matching(max_value_len, match_mode) for w in walkers]
            result_data.step_down()
        else:
            yield [w.pop_next_value() for w in walkers], result_data.current_list


def flat_walk_data(*walkers):
    match_mode = DataWalker.REPEAT  # todo should be determined by modes of input walkers

    # first step is always step down because walkers create extra wrapping list
    max_value_len = max(w.next_values_number for w in walkers)
    [w.step_down_matching(max_value_len, match_mode) for w in walkers]

    while any(not w.is_exhausted for w in walkers):
        if any(w.what_is_next() == DataWalker.END for w in walkers):
            [w.step_up() for w in walkers]
        elif any(w.what_is_next() == DataWalker.SUB_TREE for w in walkers):
            max_value_len = max(w.next_values_number for w in walkers)
            [w.step_down_matching(max_value_len, match_mode) for w in walkers]
        else:
            yield [w.pop_next_value() for w in walkers]


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
