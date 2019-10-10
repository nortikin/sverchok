
import unittest

from sverchok.utils.logging import error
from sverchok.utils.testing import *
from sverchok.data_structure import *

class DataStructureTests(SverchokTestCase):
    def test_match_long_repeat(self):
        inputs = [[1,2,3,4,5], [10,11]]
        output = match_long_repeat(inputs)
        expected_output = [[1,2,3,4,5], [10,11,11,11,11]]
        self.assertEquals(output, expected_output)

    def test_match_long_cycle(self):
        inputs = [[1,2,3,4,5] ,[10,11]]
        output = match_long_cycle(inputs)
        expected_output = [[1,2,3,4,5] ,[10,11,10,11,10]]
        self.assertEquals(output, expected_output)

    def test_full_list_1(self):
        data = [1,2,3]
        fullList(data, 7)
        self.assertEquals(data, [1, 2, 3, 3, 3, 3, 3])
        
    def test_full_list_2(self):
        data = [[1], [2], [3]]
        fullList(data, 7)
        self.assertEquals(data, [[1], [2], [3], [3], [3], [3], [3]])
        
    def test_full_list_deep_copy(self):
        data = [[3], [2], [1]]
        fullList_deep_copy(data, 7)
        self.assertEquals(data, [[3], [2], [1], [1], [1], [1], [1]])    

    def test_get_data_nesting_level_1(self):
        self.subtest_assert_equals(get_data_nesting_level(1), 0)
        self.subtest_assert_equals(get_data_nesting_level([]), 1)
        self.subtest_assert_equals(get_data_nesting_level([1]), 1)
        self.subtest_assert_equals(get_data_nesting_level([[(1,2,3)]]), 3)

    def test_get_data_nesting_level_2(self):
        with self.assertRaises(TypeError):
            data = [dict(), 3]
            level = get_data_nesting_level(data)
            error("get_data_nesting_level() returned %s", level)

    def test_ensure_nesting_level_1(self):
        self.subtest_assert_equals(ensure_nesting_level(17, 0), 17)
        self.subtest_assert_equals(ensure_nesting_level(17, 1), [17])
        self.subtest_assert_equals(ensure_nesting_level([17], 1), [17])
        self.subtest_assert_equals(ensure_nesting_level([17], 2), [[17]])
        self.subtest_assert_equals(ensure_nesting_level([(1,2,3)], 3), [[(1,2,3)]])

    def test_ensure_nesting_level_2(self):
        with self.assertRaises(TypeError):
            data = [[[17]]]
            result = ensure_nesting_level(data, 1)
            error("ensure_nesting_level() returned %s", result)
     
    def test_transpose_list(self):
        self.subtest_assert_equals(transpose_list([[1,2], [3,4]]), [[1,3], [2, 4]])

    def test_rotate_list_1(self):
        input = [1, 2, 3]
        expected_output = [2, 3, 1]
        output = rotate_list(input)
        self.assertEquals(output, expected_output)

    def test_rotate_list_2(self):
        input = [1, 2, 3]
        expected_output = [3, 1, 2]
        output = rotate_list(input, 2)
        self.assertEquals(output, expected_output)

    def test_describe_data_shape(self):
        self.subtest_assert_equals(describe_data_shape(None), 'Level 0: NoneType')
        self.subtest_assert_equals(describe_data_shape(1), 'Level 0: int')
        self.subtest_assert_equals(describe_data_shape([]), 'Level 1: list [0]')
        self.subtest_assert_equals(describe_data_shape([1]), 'Level 1: list [1] of int')
        self.subtest_assert_equals(describe_data_shape([[(1,2,3)]]), 'Level 3: list [1] of list [1] of tuple [3] of int')

class CalcMaskTests(SverchokTestCase):
    def test_calc_mask_1(self):
        subset = [1]
        set = [1, 2, 3]
        mask = calc_mask(subset, set, level=0)
        expected = [True, False, False]
        self.assertEquals(mask, expected)

    def test_calc_mask_2(self):
        subset = [1]
        set = [1, 2, 3]
        mask = calc_mask(subset, set, negate=True)
        expected = [False, True, True]
        self.assertEquals(mask, expected)

    def test_calc_mask_3(self):
        subset = [[1, 2], [3, 4]]
        set = [[1, 2], [3, 4], [5, 6]]
        mask = calc_mask(subset, set, level=0)
        expected = [True, True, False]
        self.assertEquals(mask, expected)

    def test_calc_mask_4(self):
        subset = [[1, 2], [3, 4]]
        set = [[1, 2], [3, 4], [5, 6]]
        mask = calc_mask(subset, set, level=1)
        expected = [[True, True], [True, True], [False, False]]
        self.assertEquals(mask, expected)

    def test_calc_mask_5(self):
        subset = [[1], [5,6]]
        set = [[1, 2, 3], [7, 8, 9]]
        mask = calc_mask(subset, set, level=0)
        expected = [False, False]
        self.assertEquals(mask, expected)

    def test_calc_mask_6(self):
        subset = [[1], [5,6]]
        set = [[1, 2, 3], [7, 8, 9]]
        mask = calc_mask(subset, set, level=1)
        expected = [[True, False, False], [False, False, False]]
        self.assertEquals(mask, expected)

    def test_calc_mask_7(self):
        subset = [[1, 2], [3, 4]]
        set = [[2, 1], [5, 6]]
        mask = calc_mask(subset, set, ignore_order=True)
        expected = [True, False]
        self.assertEquals(mask, expected)

