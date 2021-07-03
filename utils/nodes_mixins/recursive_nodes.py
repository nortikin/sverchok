# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from bpy.props import EnumProperty
from mathutils import Matrix
from bpy.props import BoolProperty, IntVectorProperty
from sverchok.utils.sv_itertools import process_matched
from sverchok.core.socket_data import sentinel
from sverchok.data_structure import (updateNode,
                                    list_match_func, numpy_list_match_modes,
                                    ensure_nesting_level, ensure_min_nesting)
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata

DEFAULT_TYPES = {
    'NONE': sentinel,
    'EMPTY_LIST': [[]],
    'MATRIX': [Matrix()],
    'MASK': [[True]]
    }
def one_item_list(data):
    if len(data) == 1:
        return data[0]
    lens = list(map(len, data))
    if any([l > 1 for l in lens]):
        return data
    return [d[0] for d in data]

def create_bms(params):
    bmesh_list = []
    for p in zip(*params):
        if len(params) == 2:
            if len(p[1][0]) == 2:
                bmesh_list.append(bmesh_from_pydata(verts=p[0], edges=p[1]))

            else:
                bmesh_list.append(bmesh_from_pydata(verts=p[0], faces=p[1]))
        else:

            bmesh_list.append(bmesh_from_pydata(*p))
    return bmesh_list
class SvRecursiveNode():
    '''
    This mixin is used to vectorize any node.
    In the init function some socket properties have to be defined in order to work properly
    They can also be defined in the pre_setup function that will be called before getting the input data

    for every input socket(s):
        if socket is mandatory:
            s.is_mandatory = True (Default value is False)
        the desired nesting level
            s.nesting_level =
                3 for vectors lists (Default for Vertices Socket)
                2 for number lists (Default)
                1 for single item

        the socket default mode
            s.default_mode =
                'NONE' to leave empty
                'EMPTY_LIST' for [[]] (Default)
                'MATRIX' for Matrix()
                'MASK' for [[True]]
        if pre_processing desired:
            s.pre_processing =
                'ONE_ITEM' for values like the number of subdivision (one value per object).
                           It will match one value per object independently if the list is [[1,2]] or [[1],[2]]
                           In case of more complex inputs no preprocessing will be made
                'NONE' not doing any preprocessing. (Default)

    from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
    ...
    class SvAwesomeNode(bpy.types.Node, SverchCustomTreeNode, SvRecursiveNode):
    ...
    def sv_init(self, context):
        p1 = self.inputs.new('SvVerticesSocket', "Param1")
        p1.is_mandatory = True
        p1.nesting_level = 3
        p1.default_mode = 'NONE'
        p2 = self.inputs.new('SvStringsSocket', "Param2")
        p2.nesting_level = 3
        self.outputs.new('SvStringsSocket', "Res1")
        self.outputs.new('SvStringsSocket', "Res2")

    def pre_setup(self):
        if self.option == 'SOME_OPTION':
            self.inputs[0].nesting_level = 2

    def process_data(self, params):
        param1, param2 = params
        res1, res2 = awesome_func(param1)
        return res1, res2

    This mixing also adds the list_match property to let the user choose among repeat_last, cycle and match short and so on
    to add this property to the layout:
        def draw_buttons_ext(self, context, layout):
            layout.prop(self, 'list_match')

        def rclick_menu(self, context, layout):
            layout.prop_menu_enum(self, "list_match", text="List Match")

    in case of needing to generate bmesh geometry you can

        set self.build_bmesh = True
        define base sockets indices (verts, edges and faces) or (verts, edg_pol) in self.bmesh_inputs

        then process_data will receive a list with bmesh mesh as first item
            def process_data(self, params)
                bmesh_list, other_param1, other_param2 = params

        creating the bmesh_list before matching improves performance a lot, but if
        you are modifiying the bm in your function do it over a copy  -> bm.copy()


    '''
    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    build_bmesh = False
    bmesh_inputs = [0, 1, 2]

    def update_params_to_bmesh(self, params, input_nesting):
        bms = process_matched([p for i, p in enumerate(params) if i in self.bmesh_inputs],
                              create_bms,
                              self.list_match,
                              [3 for n in self.bmesh_inputs],
                              1)
        params = [bms, *[p for i, p in enumerate(params) if i not in self.bmesh_inputs]]
        input_nesting = [1, *[n for i, n in enumerate(input_nesting) if i not in self.bmesh_inputs]]
        return params, input_nesting

    def pre_setup(self):
        '''
        function to be overridden in the node in case something has to change
        before getting input data
        '''
        # pass

    def process(self):

        self.pre_setup()

        if not all([s.is_linked for s in self.inputs if s.is_mandatory]):
            return

        if not any([s.is_linked for s in self.outputs]):
            return

        params = []
        input_nesting = []
        for s in self.inputs:
            input_nesting.append(s.nesting_level)
            default = DEFAULT_TYPES[s.default_mode]
            if s.pre_processing == 'ONE_ITEM':
                p = one_item_list(ensure_min_nesting(s.sv_get(deepcopy=False, default=default), 2))
            else:
                p = ensure_min_nesting(s.sv_get(deepcopy=False, default=default), s.nesting_level)

            params.append(p)

        one_output = len(self.outputs) == 1

        if self.build_bmesh:
            params, input_nesting = self.update_params_to_bmesh(params, input_nesting)

        result = process_matched(params, self.process_data, self.list_match, input_nesting, len(self.outputs))

        if one_output:
            self.outputs[0].sv_set(result)
        else:
            for s, r in zip(self.outputs, result):
                if s.is_linked:
                    s.sv_set(r)
