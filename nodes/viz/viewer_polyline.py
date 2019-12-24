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
from bpy.props import (BoolProperty, StringProperty, FloatProperty, IntProperty)

from sverchok.utils.sv_obj_helper import SvObjHelper
from sverchok.utils.geom import multiply_vectors
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect, fullList, updateNode


def set_bevel_object(node, cu, obj_index):
    # use bevel object if provided
    bevel_objs = node.inputs['bevel object'].sv_get(default=[])
    if bevel_objs:
        obj_ref = bevel_objs[obj_index] if obj_index < len(bevel_objs) else bevel_objs[-1]
        if obj_ref.type == 'CURVE':
            cu.bevel_object = obj_ref
            cu.use_fill_caps = node.caps
    else:
        cu.bevel_object = None
        cu.use_fill_caps = False    


# -- POLYLINE --
def live_curve(obj_index, node, verts, radii, twist):

    obj, cu = node.get_obj_curve(obj_index)

    obj.show_wire = node.show_wire
    cu.bevel_depth = node.depth
    cu.bevel_resolution = node.resolution
    cu.dimensions = node.curve_dimensions
    if cu.dimensions == '2D':
        cu.fill_mode = 'FRONT'
    else:
        cu.fill_mode = 'FULL'

    set_bevel_object(node, cu, obj_index)

    kind = ["POLY", "NURBS"][bool(node.bspline)]

    if node.selected_mode == 'Multi':
        verts = [verts]
        radii = [radii]
        twist = [twist]

    for idx, (VERTS, RADII, TWIST) in enumerate(zip(verts, radii, twist)):

        full_flat = []
        for v in VERTS:
            full_flat.extend([v[0], v[1], v[2], 1.0])

        polyline = cu.splines.new(kind)
        polyline.points.add(len(VERTS)-1)
        polyline.points.foreach_set('co', full_flat)

        if RADII:
            if len(VERTS) < len(RADII):
                RADII = RADII[:len(VERTS)]
            elif len(VERTS) > len(RADII):
                fullList(RADII, len(VERTS))
            polyline.points.foreach_set('radius', RADII)

        if TWIST:
            if len(VERTS) < len(TWIST):
                TWIST = TWIST[:len(VERTS)]
            elif len(VERTS) > len(TWIST):
                fullList(TWIST, len(VERTS))
            polyline.points.foreach_set('tilt', TWIST)
            
        if node.close:
            cu.splines[idx].use_cyclic_u = True

        if node.bspline:
            polyline.order_u = len(polyline.points)-1

        polyline.use_smooth = node.use_smooth

    return obj

def make_curve_geometry(obj_index, node, verts, matrix, radii, twist):
    sv_object = live_curve(obj_index, node, verts, radii, twist)
    sv_object.hide_select = False
    node.set_auto_uv(sv_object)
    node.push_custom_matrix_if_present(sv_object, matrix)
    return sv_object


class SvPolylineViewerNodeV28(bpy.types.Node, SverchCustomTreeNode, SvObjHelper):

    bl_idname = 'SvPolylineViewerNodeV28'
    bl_label = 'Polyline Viewer'
    bl_icon = 'MOD_CURVE'
    sv_icon = 'SV_POLYLINE_VIEWER'

    mode_options = [(k, k, '', i) for i, k in enumerate(["Multi", "Single"])]
    selected_mode: bpy.props.EnumProperty(
        items=mode_options,
        description="offers joined of unique curves",
        default="Multi", update=updateNode
    )

    dimension_modes = [(k, k, '', i) for i, k in enumerate(["3D", "2D"])]
    
    curve_dimensions: bpy.props.EnumProperty(
        items=dimension_modes, update=updateNode,
        description="2D or 3D curves", default="3D"
    )

    depth: FloatProperty(min=0.0, default=0.2, update=updateNode)
    resolution: IntProperty(min=0, default=3, update=updateNode)
    bspline: BoolProperty(default=False, update=updateNode)
    close: BoolProperty(default=False, update=updateNode)

    radii: FloatProperty(min=0, default=0.2, update=updateNode)
    twist: FloatProperty(default=0.0, update=updateNode)
    caps: BoolProperty(update=updateNode)
    use_auto_uv: BoolProperty(name="auto uv", update=updateNode)

    data_kind: StringProperty(default='CURVE')

    def sv_init(self, context):
        self.sv_init_helper_basedata_name()

        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvMatrixSocket', 'matrix')
        self.inputs.new('SvStringsSocket', 'radii').prop_name = 'radii'
        self.inputs.new('SvStringsSocket', 'twist').prop_name = 'twist'
        self.inputs.new('SvObjectSocket', 'bevel object')
        self.outputs.new('SvObjectSocket', "object")


    def draw_buttons(self, context, layout):

        self.draw_live_and_outliner(context, layout)
        self.draw_object_buttons(context, layout)

        layout.row().prop(self, 'curve_dimensions', expand=True)

        col = layout.column()
        if self.curve_dimensions == '3D':
            r1 = col.row(align=True)
            r1.prop(self, 'depth', text='radius')
            r1.prop(self, 'resolution', text='subdiv')
        row = col.row(align=True)
        row.prop(self, 'bspline', text='bspline', toggle=True)
        row.prop(self, 'close', text='close', toggle=True)
        if self.inputs['bevel object'].sv_get(default=[]):
            row.prop(self, 'caps', text='caps', toggle=True)
        row = col.row(align=True)
        row.prop(self, 'show_wire', text='wire', toggle=True)
        row.prop(self, 'use_smooth', text='smooth', toggle=True)
        row.separator()
        row.prop(self, 'selected_mode', expand=True)


    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        self.draw_ext_object_buttons(context, layout)
        row = layout.row()
        row.prop(self, "use_auto_uv", text="Use UV for mapping")


    def get_geometry_from_sockets(self, has_matrices):
        
        def get(socket_name):
            data = self.inputs[socket_name].sv_get(default=[])
            return dataCorrect(data)

        mverts = get('vertices')
        mradii = self.inputs['radii'].sv_get(deepcopy=True)
        mtwist = self.inputs['twist'].sv_get(deepcopy=True)
        mmtrix = get('matrix')

        # extend all non empty lists to longest of these
        maxlen = max(len(mverts), len(mmtrix))
        if has_matrices:
            fullList(mverts, maxlen)
            fullList(mmtrix, maxlen)

        if mradii:
            fullList(mradii, maxlen)
        if mtwist:
            fullList(mtwist, maxlen)

        return mverts, mradii, mtwist, mmtrix


    def process(self):
        if not self.activate:
            return

        if not self.inputs['vertices'].is_linked:
            return

        has_matrices = self.inputs['matrix'].is_linked
        mverts, mradii, mtwist, mmatrices = self.get_geometry_from_sockets(has_matrices)

        with self.sv_throttle_tree_update():
            out_objects = []
            for obj_index, Verts in enumerate(mverts):
                if not Verts:
                    continue

                matrix = mmatrices[obj_index] if has_matrices else []

                if self.selected_mode == 'Multi':
                    curve_args = obj_index, self, Verts, matrix, mradii[obj_index], mtwist[obj_index]
                    new_obj = make_curve_geometry(*curve_args)
                    out_objects.append(new_obj)
                else:
                    if matrix:
                        mverts = [multiply_vectors(*mv) for mv in zip(mmatrices, mverts)]
                    new_obj = make_curve_geometry(0, self, mverts, [], mradii, mtwist)
                    out_objects.append(new_obj)
                    break

            last_index = len(mverts) - 1
            self.remove_non_updated_objects(last_index)
            self.set_corresponding_materials()

            self.outputs['object'].sv_set(out_objects)


    def set_auto_uv(self, obj):
        """
        this will change the state of the object.prop if it does not match the new desired state
        """
        if obj.data.use_uv_as_generated != self.use_auto_uv:
            obj.data.use_uv_as_generated = self.use_auto_uv


def register():
    bpy.utils.register_class(SvPolylineViewerNodeV28)


def unregister():
    bpy.utils.unregister_class(SvPolylineViewerNodeV28)
