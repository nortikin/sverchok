# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, StringProperty, BoolProperty, EnumProperty, IntProperty

from sverchok.core.socket_data import SvNoDataError
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, ensure_nesting_level, zip_long_repeat, throttle_and_update_node, get_data_nesting_level
from sverchok.utils.geom import center
from sverchok.utils.voronoi import voronoi_bounded, Bounds

class SvLloyd2dNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Lloyd 2D
    Tooltip: Redistribute 2D points uniformly by use of Lloyd's algorithms
    """
    bl_idname = 'SvLloyd2dNode'
    bl_label = 'Lloyd 2D'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    clip: FloatProperty(
        name='clip', description='Clipping Distance',
        default=1.0, min=0, update=updateNode)

    bound_modes = [
            ('BOX', 'Bounding Box', "Bounding Box", 0),
            ('CIRCLE', 'Circle', "Circle", 1)
        ]

    bound_mode: EnumProperty(
        name = 'Bounds Mode',
        description = "Bounding mode",
        items = bound_modes,
        default = 'BOX',
        update = updateNode)

    iterations : IntProperty(
        name = "Iterations",
        description = "Number of Lloyd algorithm iterations",
        min = 0,
        default = 3,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', 'Iterations').prop_name = 'iterations'
        self.outputs.new('SvVerticesSocket', "Vertices")

    def draw_buttons(self, context, layout):
        layout.prop(self, "bound_mode")
        layout.prop(self, "clip", text="Clipping")

    def lloyd2d(self, verts, n_iterations):
        bounds = Bounds.new(self.bound_mode)
        bounds.init_from_sites(verts)

        def invert_points(pts):
            result = []
            for pt in pts:
                pt2d = x0,y0 = (pt[0], pt[1])
                if bounds.contains(pt2d):
                    x1,y1,z1 = bounds.project(pt)
                    x2 = x0 + 2*(x1-x0)
                    y2 = y0 + 2*(y1-y0)
                    out_pt = (x2, y2, z1)
                    result.append(out_pt)
            return result
        
        def iteration(pts):
            n = len(pts)
            all_pts = pts + invert_points(pts)
            voronoi_verts, _, voronoi_faces = voronoi_bounded(all_pts,
                        bound_mode = self.bound_mode,
                        clip = self.clip,
                        draw_bounds = True,
                        draw_hangs = True,
                        make_faces = True,
                        ordered_faces = True,
                        max_sides = 10)
            centers = []
            for face in voronoi_faces[:n]:
                face_verts = [voronoi_verts[i] for i in face]
                new_pt = center(face_verts)
                centers.append(new_pt)
            return centers

        def restrict(pts):
            return [bounds.restrict(pt) for pt in pts]

        points = restrict(verts)
        for i in range(n_iterations):
            points = iteration(points)
            points = restrict(points)
        return points

    def process(self):

        if not self.outputs['Vertices'].is_linked:
            return

        verts_in = self.inputs['Vertices'].sv_get()
        iterations_in = self.inputs['Iterations'].sv_get()

        input_level = get_data_nesting_level(verts_in)
        verts_in = ensure_nesting_level(verts_in, 4)
        iterations_in = ensure_nesting_level(iterations_in, 2)

        nested_output = input_level > 3

        verts_out = []
        for params in zip_long_repeat(verts_in, iterations_in):
            new_verts = []
            for verts, iterations in zip_long_repeat(*params):
                iter_verts = self.lloyd2d(verts, iterations)
                new_verts.append(iter_verts)
            if nested_output:
                verts_out.append(new_verts)
            else:
                verts_out.extend(new_verts)

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvLloyd2dNode)

def unregister():
    bpy.utils.unregister_class(SvLloyd2dNode)

