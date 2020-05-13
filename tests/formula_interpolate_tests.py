
import unittest
from os.path import basename, splitext, dirname, join, exists
from os import walk
from glob import glob

import sverchok
from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info, error
from sverchok.nodes.number.formula_interpolate import ControlPoint, split_points

class DocumentationTests(SverchokTestCase):
    def test_empty(self):
        points = []
        result = split_points(points)
        expected_result = []
        self.assertEquals(result, expected_result)

    def test_single(self):
        points = [ControlPoint(1, 2, False)]
        result = split_points(points)
        expected_result = [points]
        self.assertEquals(result, expected_result)

    def test_two_smooth(self):
        points = [ControlPoint(1, 2, False), ControlPoint(2, 3, False)]
        result = split_points(points)
        expected_result = [points]
        self.assertEquals(result, expected_result)

    def test_two_sharp(self):
        points = [ControlPoint(1, 2, True), ControlPoint(2, 3, True)]
        result = split_points(points)
        expected_result = [points]
        self.assertEquals(result, expected_result)

    def test_two_mixed_1(self):
        points = [ControlPoint(1, 2, True), ControlPoint(2, 3, False)]
        result = split_points(points)
        expected_result = [points]
        self.assertEquals(result, expected_result)

    def test_two_mixed_2(self):
        points = [ControlPoint(1, 2, False), ControlPoint(2, 3, True)]
        result = split_points(points)
        expected_result = [points]
        self.assertEquals(result, expected_result)

    def test_three(self):
        points = [ControlPoint(1, 2, False), ControlPoint(2, 3, False), ControlPoint(3, 1, False)]
        result = split_points(points)
        expected_result = [points]
        self.assertEquals(result, expected_result)

    def test_one_sharp(self):
        points = [ControlPoint(1, 2, False), ControlPoint(2, 3, True), ControlPoint(3, 1, False)]
        result = split_points(points)
        expected_result = [
                [ControlPoint(1, 2, False), ControlPoint(2, 3, True)],
                [ControlPoint(2, 3, True), ControlPoint(3, 1, False)]
            ]
        self.assertEquals(result, expected_result)

    def test_two_sharp_1(self):
        points = [ControlPoint(1, 2, False), ControlPoint(2, 3, True), ControlPoint(3, 1, True), ControlPoint(4, 2, False)]
        result = split_points(points)
        expected_result = [
                [ControlPoint(1, 2, False), ControlPoint(2, 3, True)],
                [ControlPoint(2, 3, True), ControlPoint(3, 1, True)],
                [ControlPoint(3, 1, True), ControlPoint(4, 2, False)]
            ]
        self.assertEquals(result, expected_result)

    def test_two_sharp_2(self):
        points = [ControlPoint(1, 2, False), ControlPoint(2, 3, True), ControlPoint(3, 1, False), ControlPoint(4, 2, True), ControlPoint(5, 1, False)]
        result = split_points(points)
        expected_result = [
                [ControlPoint(1, 2, False), ControlPoint(2, 3, True)],
                [ControlPoint(2, 3, True), ControlPoint(3, 1, False), ControlPoint(4, 2, True)],
                [ControlPoint(4, 2, True), ControlPoint(5, 1, False)]
            ]
        self.assertEquals(result, expected_result)

