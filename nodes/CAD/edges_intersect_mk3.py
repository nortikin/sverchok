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
from copy import copy

import bpy
from mathutils import Vector
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.geom_2d.intersections import intersect_sv_edges
from sverchok.utils.intersect_edges import intersect_edges_3d_np, intersect_edges_2d, remove_doubles_from_edgenet, intersect_edges_2d_np, intersect_edges_2d_np_big

try:
    from mathutils.geometry import delaunay_2d_cdt as bl_intersect
except ImportError:
    bl_intersect = None

modeItems = [("2D", "2D", "", 0), ("3D", "3D", "", 1)]

''' helpers '''

class SvIntersectEdgesNodeMK3(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'SvIntersectEdgesNodeMK3'
    bl_label = 'Intersect Edges'
    sv_icon = 'SV_XALL'

    mode_items_2d = [("Alg_1", "Alg_1", "", 0),
                     ("Sweep_line", "Sweep line", "", 1),
                     ("Blender", "Blender", "", 2),
                     ("Np", "Np", "", 3)]

    mode: bpy.props.EnumProperty(items=modeItems, default="3D", update=updateNode)
    rm_switch: bpy.props.BoolProperty(update=updateNode)
    rm_doubles: bpy.props.FloatProperty(min=0.0, default=0.0001, step=0.1, update=updateNode)
    epsilon: bpy.props.IntProperty(min=3, default=5, update=updateNode)
    alg_mode_2d: bpy.props.EnumProperty(items=mode_items_2d, default="Alg_1", update=updateNode)
    only_touching: bpy.props.BoolProperty(
        name='Include "On touch"',
        description='consider a valid intersection when one end of the edge lays on another edge. Generates double points so if active "remove doubles" switch is recommended',
        update=updateNode)
    big_data_limit: bpy.props.IntProperty(
        name='Big data limit',
        description='Number of incoming edges where the node will switch to a slower-but-safer implementation of the algorithm',
        min=0, default=8000)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts_in')
        self.inputs.new('SvStringsSocket', 'Edges_in')

        self.outputs.new('SvVerticesSocket', 'Verts_out')
        self.outputs.new('SvStringsSocket', 'Edges_out')

    def draw_buttons(self, context, layout):
        row = layout.column(align=True)
        row.row(align=True).prop(self, "mode", expand=True)
        if self.mode == "2D":
            row.row(align=True).prop(self, "alg_mode_2d", expand=True)
            if self.alg_mode_2d == 'Blender' and not bl_intersect:
                row.label(text="For 2.81+ only", icon='ERROR')
        if self.mode == '3D' or (self.mode == "2D" and self.alg_mode_2d in ['Np']):
            layout.prop(self, 'only_touching')
        if self.mode == "3D" or self.mode == "2D" and self.alg_mode_2d in ['Alg_1', 'Np']:
            r = layout.row(align=True)
            r1 = r.split(factor=0.32)
            r1.prop(self, 'rm_switch', text='doubles', toggle=True)
            r2 = r1.split()
            r2.enabled = self.rm_switch
            r2.prop(self, 'rm_doubles', text='delta')

    def draw_buttons_ext(self, context, layout):
        # layout.prop(self, 'epsilon')
        if self.mode == '2D' and self.alg_mode_2d == 'Alg_1':
            layout.prop(self, 'big_data_limit')
        else:
            layout.prop(self, 'epsilon')

    def process(self):

        inputs = self.inputs
        outputs = self.outputs
        try:
            verts_in = inputs['Verts_in'].sv_get(deepcopy=False)
            edges_in = inputs['Edges_in'].sv_get(deepcopy=False)
            linked = outputs['Verts_out'].is_linked
        except (IndexError, KeyError) as e:
            return

        if self.mode == "2D" and self.alg_mode_2d == "Blender" and not bl_intersect:
            return
        verts_out, edges_out = [], []
        for vs, eds in zip(verts_in, edges_in):
            if self.mode == "3D":
                v_out, ed_out = intersect_edges_3d_np(vs, eds, 1 / 10 ** self.epsilon, only_touching=self.only_touching)

            elif self.alg_mode_2d == "Alg_1":
                v_out, ed_out = intersect_edges_2d(copy(vs), eds, 1 / 10 ** self.epsilon)
            elif self.alg_mode_2d == "Np":
                if len(eds) > self.big_data_limit:
                    v_out, ed_out = intersect_edges_2d_np_big(vs, eds, 1 / 10 ** self.epsilon, only_touching=self.only_touching)
                else:
                    v_out, ed_out = intersect_edges_2d_np(vs, eds, 1 / 10 ** self.epsilon, only_touching=self.only_touching)
            elif self.alg_mode_2d == "Sweep_line":
                v_out, ed_out = intersect_sv_edges(vs, eds, self.epsilon)
            else:
                v_out, ed_out, _, _, _, _ = bl_intersect([Vector(co[:2]) for co in vs], eds, [], 2,
                                                         1 / 10 ** self.epsilon)
                v_out = [v.to_3d()[:] for v in v_out]

            # post processing step to remove doubles
            if self.rm_switch and (self.mode == "3D" or self.alg_mode_2d in ['Alg_1', 'Np']):
                v_out, ed_out = remove_doubles_from_edgenet(v_out, ed_out, self.rm_doubles)

            verts_out.append(v_out)
            edges_out.append(ed_out)
        outputs['Verts_out'].sv_set(verts_out)
        outputs['Edges_out'].sv_set(edges_out)



def register():
    bpy.utils.register_class(SvIntersectEdgesNodeMK3)

def unregister():
    bpy.utils.unregister_class(SvIntersectEdgesNodeMK3)
