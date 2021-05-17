from typing import Tuple, List

from sverchok.utils.testing import SverchokTestCase

from sverchok.utils.vectorize import DataWalker, walk_data, vectorize


class VectorizeTest(SverchokTestCase):
    def test_parameters_matching(self):

        wa = DataWalker(1)
        wb = DataWalker([1, 2, 3])
        walker = walk_data([wa, wb], [[]])
        self.assertEqual([v for v, _ in walker], [[1, 1], [1, 2], [1, 3]])

        wa = DataWalker([[1, 2], 3])
        wb = DataWalker([1, [2, 3], 4])
        walker = walk_data([wa, wb], [[]])
        self.assertEqual([v for v, _ in walker], [[1, 1], [2, 1], [3, 2], [3, 3], [3, 4]])

        wa = DataWalker([[1, 2], [3, 4, 5]])
        wb = DataWalker([1, [2, 3], 4])
        walker = walk_data([wa, wb], [[]])
        self.assertEqual([v for v, _ in walker], [[1, 1], [2, 1], [3, 2], [4, 3], [5, 3], [3, 4], [4, 4], [5, 4]])

        wa = DataWalker(1)
        wb = DataWalker([1, 2, 3])
        out = []
        walker = walk_data([wa, wb], [out])
        [l[0].append((a, b)) for (a, b), l in walker]
        self.assertEqual(out, [(1, 1), (1, 2), (1, 3)])

        wa = DataWalker([[1, 2], 3])
        wb = DataWalker([1, [2, 3], 4])
        out = []
        walker = walk_data([wa, wb], [out])
        [l[0].append((a, b)) for (a, b), l in walker]
        self.assertEqual(out, [[(1, 1), (2, 1)], [(3, 2), (3, 3)], (3, 4)])

        wa = DataWalker([[1, 2], [3, 4, 5]])
        wb = DataWalker([1, [2, 3], 4])
        out = []
        walker = walk_data([wa, wb], [out])
        [l[0].append((a, b)) for (a, b), l in walker]
        self.assertEqual(out, [[(1, 1), (2, 1)], [(3, 2), (4, 3), (5, 3)], [(3, 4), (4, 4), (5, 4)]])

    def test_decorator(self):

        def math(*, a: float, b: float, mode='SUM'):
            if mode == 'SUM':
                return a + b
            elif mode == 'MUL':
                return a * b

        a_values = [[1, 2], [3, 4, 5]]
        b_values = [1, [2, 3], 4]
        math1 = vectorize(math, match_mode="REPEAT")
        self.assertEqual(math1(a=a_values, b=b_values, mode='SUM'), [[2, 3], [5, 7, 8], [7, 8, 9]])

        a_values = 10
        b_values = [1, [2, 3], 4]
        math2 = vectorize(math, match_mode="REPEAT")
        self.assertEqual(math2(a=a_values, b=b_values, mode='SUM'), [11, [12, 13], 14])

        def some_list_statistic(*, a: list, b: list) -> Tuple[list, list]:
            a_grater_b = [_a > _b for _a, _b in zip(a, b)]
            a_in_b = [_a in b for _a in a]
            return a_grater_b, a_in_b

        a_values = [[1, 3, 7, 3, 7, 1], [[1, 2], [3, 4]]]
        b_values = [[5, 7, 3, 4, 6, 7], [[2, 3], [4, 5]]]
        some_list_statistic1 = vectorize(some_list_statistic, match_mode='REPEAT')
        a_grater_b, a_in_b = some_list_statistic1(a=a_values, b=b_values)
        self.assertEqual(a_grater_b, [[False, False, True, False, True, False], [[False, False], [False, False]]])
        self.assertEqual(a_in_b, [[False, True, True, True, True, False], [[False, True], [False, True]]])

        def zeros(*, length: int) -> list:
            return [0 for _ in range(length)]

        lengths = [4, [[3], 1], 5]
        zeros1 = vectorize(zeros, match_mode='REPEAT')
        self.assertEqual(zeros1(length=lengths), [[0, 0, 0, 0], [[[0, 0, 0]], [0]], [0, 0, 0, 0, 0]])

        def vector(*, length) -> List[int]:
            return list(range(length))

        vector1 = vectorize(vector, match_mode='REPEAT')
        self.assertEqual(vector1(length=lengths), [[0, 1, 2, 3], [[[0, 1, 2]], [0]], [0, 1, 2, 3, 4]])


if __name__ == '__main__':
    import unittest
    unittest.main(exit=False)
