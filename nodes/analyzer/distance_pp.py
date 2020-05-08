# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import BoolProperty, EnumProperty
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (
    Matrix_location, Vector_generate,
    updateNode, list_match_func, list_match_modes
)

class DistancePPNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Distance Point to Point '''
    bl_idname = 'DistancePPNode'
    bl_label = 'Distance'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DISTANCE'

    Cross_dist: BoolProperty(
        name='Cross_dist',
        description='Calculate distance beteen each point of the first list with all points of second list DANGEROUS! It can be very heavy',
        default=False,
        update=updateNode)

    list_match_global: EnumProperty(
        name="Match Global",
        description="Behavior on different list lengths, multiple objects level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    list_match_local: EnumProperty(
        name="Match Local",
        description="Behavior on different list lengths, object level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'vertices1')
        self.inputs.new('SvMatrixSocket', 'matrix1')
        self.inputs.new('SvVerticesSocket', 'vertices2')
        self.inputs.new('SvMatrixSocket', 'matrix2')
        self.outputs.new('SvStringsSocket', 'distances')

    def draw_buttons(self, context, layout):
        layout.prop(self, "Cross_dist", text="CrossOver")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "Cross_dist", text="CrossOver")
        layout.separator()
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", text="Global Match", expand=False)
        layout.prop(self, "list_match_local", text="Local Match", expand=False)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Local")

    def process(self):
        if not self.outputs['distances'].is_linked:
            return
        inputs = self.inputs
        if inputs['vertices1'].is_linked and inputs['vertices2'].is_linked:
            prop1_ = self.inputs['vertices1'].sv_get()
            prop1 = Vector_generate(prop1_)
            if inputs['matrix1'].is_linked:
                m = inputs['matrix1'].sv_get(deepcopy=False, default=[Matrix()])
                verts, matrix = list_match_func[self.list_match_global]([prop1, m])
                prop1 = [[mx @ v for v in vs] for mx, vs in zip(matrix, verts)]

            prop2_ = self.inputs['vertices2'].sv_get()
            prop2 = Vector_generate(prop2_)
            if inputs['matrix2'].is_linked:
                m = inputs['matrix2'].sv_get(deepcopy=False, default=[Matrix()])
                verts, matrix = list_match_func[self.list_match_global]([prop2, m])
                prop2 = [[mx @ v for v in vs] for mx, vs in zip(matrix, verts)]

        elif inputs['matrix1'].is_linked and inputs['matrix2'].is_linked:
            propa = self.inputs['matrix1'].sv_get()
            prop1 = Matrix_location(propa)
            propb = self.inputs['matrix2'].sv_get()
            prop2 = Matrix_location(propb)
        else:
            prop1, prop2 = [], []

        if prop1 and prop2:
            if self.Cross_dist:
                output = self.calcM(prop1, prop2)
            else:
                output = self.calc_vectors_distance(prop1, prop2)
            self.outputs['distances'].sv_set(output)
        else:
            self.outputs['distances'].sv_set([])

    def calc_vectors_distance(self, list1, list2):
        distances = []
        list_a, list_b = list_match_func[self.list_match_global]([list1, list2])
        for _l_a, _l_b in zip(list_a, list_b):
            values = []
            l_a, l_b = list_match_func[self.list_match_local]([_l_a, _l_b])
            for v, v1 in zip(l_a, l_b):
                values.append((v-v1).length)
            distances.append(values)
        return distances

    def calcM(self, list1, list2):
        ll1, ll2 = len(list1[0]), len(list2[0])
        if ll1 > ll2:
            short = list2
            long = list1
        else:
            short = list1
            long = list2
        dists = []
        for obsh in short:
            obshdis = []
            for vers in obsh:
                for obln in long:
                    oblndis = []
                    for verl in obln:
                        oblndis.append(self.distance(vers, verl))
                    obshdis.append(oblndis)
            dists.append(obshdis)

        return dists[0]

    def distance(self, x, y):
        vec = Vector((x[0] - y[0], x[1] - y[1], x[2] - y[2]))
        return vec.length


def register():
    bpy.utils.register_class(DistancePPNode)


def unregister():
    bpy.utils.unregister_class(DistancePPNode)
