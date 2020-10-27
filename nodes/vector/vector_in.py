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
from bpy.props import FloatProperty, BoolProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, numpy_list_match_modes, numpy_list_match_func
from sverchok.utils.sv_itertools import recurse_f_level_control
from sverchok.utils.sv_itertools import sv_zip_longest
from numpy import array

class SvVectorFromCursor(bpy.types.Operator):
    "Vector from 3D Cursor"

    bl_idname = "node.sverchok_vector_from_cursor"
    bl_label = "Vector from 3D Cursor"
    bl_options = {'REGISTER'}

    nodename: StringProperty(name='nodename')
    treename: StringProperty(name='treename')

    def execute(self, context):
        cursor = bpy.context.scene.cursor.location

        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        node.x_, node.y_, node.z_ = tuple(cursor)

        return{'FINISHED'}

def python_pack_vecs(params, constant, matching_f):
    X_, Y_, Z_ = params
    output_numpy, _ = constant
    series_vec = []
    for vs in zip(X_, Y_, Z_):
        x, y, z = matching_f(vs)
        series_vec.append(array([x,y,z]).T if output_numpy else list(zip(x, y, z)))
    return series_vec

def numpy_pack_vecs(params, constant, matching_f):
    X_, Y_, Z_ = params
    output_numpy, match_mode = constant
    np_match = numpy_list_match_func[match_mode]
    series_vec = []
    for obj in zip(X_, Y_, Z_):
        np_obj = [array(p) for p in obj]
        x, y, z = np_match(np_obj)
        vecs = array([x,y,z]).T
        series_vec.append(vecs if output_numpy else vecs.tolist())
    return series_vec

class GenVectorsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Combine XYZ
    Tooltip:  Generate vectors from numbers list.
    """

    bl_idname = 'GenVectorsNode'
    bl_label = 'Vector in'
    sv_icon = 'SV_VECTOR_IN'

    x_: FloatProperty(name='X', description='X', default=0.0, precision=3, update=updateNode)
    y_: FloatProperty(name='Y', description='Y', default=0.0, precision=3, update=updateNode)
    z_: FloatProperty(name='Z', description='Z', default=0.0, precision=3, update=updateNode)


    show_3d_cursor_button: BoolProperty(name='show button', update=updateNode, default=False)
    implementation_modes = [
        ("NumPy", "NumPy", "NumPy", 0),
        ("Python", "Python", "Python", 1)]

    implementation: EnumProperty(
        name='Implementation', items=implementation_modes,
        description='Choose calculation method',
        default="Python", update=updateNode)
    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    correct_output_modes = [
        ('NONE', 'None', 'Leave at multi-object level (Advanced)', 0),
        ('FLAT', 'Flat Output', 'Flat to object level', 2),
    ]
    correct_output: EnumProperty(
        name="Simplify Output",
        description="Behavior on different list lengths, object level",
        items=correct_output_modes, default="FLAT",
        update=updateNode)
    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "X").prop_name = 'x_'
        self.inputs.new('SvStringsSocket', "Y").prop_name = 'y_'
        self.inputs.new('SvStringsSocket', "Z").prop_name = 'z_'
        self.width = 100
        self.outputs.new('SvVerticesSocket', "Vectors")

    def draw_buttons(self, context, layout):
        # unfortunately, the mere fact that this function is present, will inject vertical space
        # regardless of whether content is drawn.
        if not any(s.is_linked for s in self.inputs) and self.show_3d_cursor_button:
            row = layout.row()
            get_cursor = row.operator('node.sverchok_vector_from_cursor', text='3D Cursor')
            get_cursor.nodename = self.name
            get_cursor.treename = self.id_data.name

    def draw_buttons_ext(self, context, layout):
        layout.label(text="Implementation:")
        layout.prop(self, "implementation", expand=True)
        layout.prop(self, 'list_match')
        layout.prop(self, "output_numpy", toggle=False)
        layout.prop(self, 'correct_output')


    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "implementation", text="Implementation")
        layout.prop_menu_enum(self, 'list_match')
        layout.prop(self, 'output_numpy', toggle=True)
        layout.prop_menu_enum(self, 'correct_output')
        layout.prop(self, "show_3d_cursor_button", text="show 3d cursor button")
        if not any(s.is_linked for s in self.inputs):
            opname = 'node.sverchok_vector_from_cursor'
            get_cursor = layout.operator(opname, text='Vector from 3D Cursor', icon='PIVOT_CURSOR')
            get_cursor.nodename = self.name
            get_cursor.treename = self.id_data.name

    def process(self):

        if not self.outputs['Vectors'].is_linked:
            return

        params = [si.sv_get(default=[[]], deepcopy=False) for si in self.inputs]

        matching_f = list_match_func[self.list_match]
        desired_levels = [2, 2, 2]
        ops = [self.output_numpy, self.list_match]
        concatenate = 'APPEND' if self.correct_output == 'NONE' else "EXTEND"
        pack_func = numpy_pack_vecs if self.implementation == 'NumPy' else python_pack_vecs
        result = recurse_f_level_control(params, ops, pack_func, matching_f, desired_levels, concatenate=concatenate)

        self.outputs[0].sv_set(result)


def register():
    bpy.utils.register_class(GenVectorsNode)
    bpy.utils.register_class(SvVectorFromCursor)


def unregister():
    bpy.utils.unregister_class(GenVectorsNode)
    bpy.utils.unregister_class(SvVectorFromCursor)
