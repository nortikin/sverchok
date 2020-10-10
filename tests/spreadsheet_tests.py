
from collections import defaultdict

from sverchok.utils.testing import *
from sverchok.utils.modules.spreadsheet import *
from sverchok.utils.topo import stable_topo_sort

class SpreadsheetTests(SverchokTestCase):
    def test_references_1(self):
        string = "Cube.Width + 2*Circle.Radius - delta"
        result = get_references(string, {'Cube', 'Circle'})
        expected = dict(Cube = {'Width'}, Circle = {'Radius'})
        self.assertEquals(result, expected)

    def test_references_2(self):
        string = "Cube.Width + 2*Circle.Radius - delta"
        result = get_references(string, {'Cube', 'Circle'}, {'Width'})
        expected = dict(Cube = {'Width'})
        self.assertEquals(result, expected)

    def test_topo_sort_1(self):
        items = ["Cube.Width", "Circle.Radius", "Cylinder.Height"]
        edges = [[0, 2], [2,1]]
        result = stable_topo_sort(items, edges)
        expected = ["Cube.Width", "Cylinder.Height", "Circle.Radius"]
        self.assertEquals(result, expected)

    def test_get_deps_1(self):
        src_dict = defaultdict(dict)
        src_dict['Cube']['Width'] = "2 * Circle.Radius"
        src_dict['Circle']['Radius'] = "Cylinder.Height - delta"

        items, addresses, edges = get_dependencies(src_dict, ['Cube', 'Circle', 'Cylinder'], ['Width', 'Radius'])
        exp_items = ['2 * Circle.Radius', 'Cylinder.Height - delta']
        exp_addresses = [('Cube', 'Width'), ('Circle', 'Radius')]
        exp_edges = [(1, 0)]

        self.assertEquals(items, exp_items)
        self.assertEquals(addresses, exp_addresses)
        self.assertEquals(edges, exp_edges)

    def test_get_deps_2(self):
        src_dict = defaultdict(dict)
        src_dict['Cube']['Width'] = "2 * Circle.Radius"
        src_dict['Circle']['Radius'] = "Cylinder.Height - delta"
        src_dict['Cylinder']['Height'] = 1.0

        items, addresses, edges = get_dependencies(src_dict, ['Cube', 'Circle', 'Cylinder'], ['Width', 'Radius', 'Height'])
        exp_items = ['2 * Circle.Radius', 'Cylinder.Height - delta', 1.0]
        exp_addresses = [('Cube', 'Width'), ('Circle', 'Radius'), ('Cylinder', 'Height')]
        exp_edges = [(1, 0), (2,1)]

        self.assertEquals(items, exp_items)
        self.assertEquals(addresses, exp_addresses)
        self.assertEquals(edges, exp_edges)

    def test_get_deps_3(self):
        src_dict = defaultdict(dict)
        src_dict['Cube']['Width'] = "2 * Circle.Radius + 0.5*Cylinder.Height"
        src_dict['Circle']['Radius'] = "Cylinder.Height - delta"
        src_dict['Cylinder']['Height'] = 1.0

        items, addresses, edges = get_dependencies(src_dict, ['Cube', 'Circle', 'Cylinder'], ['Width', 'Radius', 'Height'])
        exp_items = ['2 * Circle.Radius + 0.5*Cylinder.Height', 'Cylinder.Height - delta', 1.0]
        exp_addresses = [('Cube', 'Width'), ('Circle', 'Radius'), ('Cylinder', 'Height')]
        exp_edges = [(1, 0), (2,0), (2,1)]

        self.assertEquals(items, exp_items)
        self.assertEquals(addresses, exp_addresses)
        self.assertEquals(edges, exp_edges)

    def test_sort_deps_1(self):
        src_dict = defaultdict(dict)
        src_dict['Cube']['Width'] = "2 * Circle.Radius + 0.5*Cylinder.Height"
        src_dict['Circle']['Radius'] = "Cylinder.Height - delta"
        src_dict['Cylinder']['Height'] = 1.0

        addresses = topo_sort_dependencies(src_dict, ['Cube', 'Circle', 'Cylinder'], ['Width', 'Radius', 'Height'])
        exp_addresses = [('Cylinder', 'Height'), ('Circle', 'Radius'), ('Cube', 'Width')]

        self.assertEquals(addresses, exp_addresses)

    def test_eval_spreadsheet_1(self):
        src_dict = defaultdict(dict)
        src_dict['Cube']['Width'] = "2 * Circle.Radius + 0.5*Cylinder.Height"
        src_dict['Circle']['Radius'] = "Cylinder.Height - delta"
        src_dict['Cylinder']['Height'] = '1.0'

        variables = dict(delta=0.1)
        result = eval_spreadsheet(src_dict, ['Cube', 'Circle', 'Cylinder'], ['Width', 'Radius', 'Height'], variables)
        expected = {'Cube': {'Width': 2.3}, 'Circle': {'Radius': 0.9}, 'Cylinder': {'Height': 1.0}}

        self.assertEquals(result, expected)

    def test_eval_spreadsheet_2(self):
        src_dict = defaultdict(dict)
        src_dict['Cube']['Width'] = "2 * Circle.Radius + 0.5*Cylinder.Height"
        src_dict['Circle']['Radius'] = "Cylinder.Height - delta"
        src_dict['Cylinder']['Height'] = '1.0 + Box.Fillet'
        src_dict['Box']['Fillet'] = 0.2

        variables = dict(delta=0.1)
        result = eval_spreadsheet(src_dict, ['Cube', 'Circle', 'Cylinder', 'Box'], ['Width', 'Radius', 'Height'], variables)
        expected = {'Cube': {'Width': 2.8}, 'Circle': {'Radius': 1.0999999999999999}, 'Cylinder': {'Height': 1.2}, 'Box': {'Fillet': 0.2}}

        self.assertEquals(result, expected)

