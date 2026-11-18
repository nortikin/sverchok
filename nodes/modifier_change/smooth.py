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
from bpy.props import IntProperty, FloatProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.dependencies import numba
from sverchok.utils.mesh.smooth import smooth_vertices
from sverchok.utils.nodes_mixins.sockets_config import ModifierNode


class SvSmoothNode(ModifierNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Smooth vertices
    Tooltip: Smooth the mesh by flattering the angles between the faces/edges.
    """
    bl_idname = 'SvSmoothNode'
    bl_label = 'Smooth Vertices'
    bl_icon = 'MOD_SMOOTH'


    def update_mode(self, context):
        self.inputs['ClipDist'].hide_safe = self.laplacian
        self.inputs['BorderFactor'].hide_safe = not self.laplacian
        updateNode(self, context)

    laplacian: BoolProperty(
        name="Laplacian Smooth", description="Use Laplacian smoothing",
        default=False, update=update_mode)

    use_numba: BoolProperty(
        name="Use Numba", description="Accelerate smoothing when Numba is installed",
        default=True, update=updateNode)

    output_numpy_vertices: BoolProperty(
        name="Vertices", description="Output vertex coordinates as NumPy arrays",
        default=False, update=updateNode)

    output_numpy_edges: BoolProperty(
        name="Edges", description="Output edge indices as NumPy arrays",
        default=False, update=updateNode)

    iterations: IntProperty(
        name="Iterations", min=1, max=1000, default=1, update=updateNode, description="Number of smoothing operation iterations")

    factor: FloatProperty(
        name="Factor", description="Smoothing factor (0 - no smoothing)", min=0.0, default=0.5, update=updateNode)

    border_factor: FloatProperty(
        name="Border factor", description="Smoothing factor in border",
        min=0.0, default=0.5, update=updateNode)

    mirror_clip_x: BoolProperty(
        name="Clip X", description="set vertices close to the X axis before the operation to 0",
        default=False, update=updateNode)

    mirror_clip_y: BoolProperty(
        name="Clip Y", description="set vertices close to the Y axis before the operation to 0",
        default=False, update=updateNode)

    mirror_clip_z: BoolProperty(
        name="Clip Z", description="set vertices close to the Z axis before the operation to 0",
        default=False, update=updateNode)

    clip_dist: FloatProperty(
        name="Clip threshold", description="Clipping threshold (for 'Clip X/Y/Z' procedure)",
        min=0.0, default=0.0001, update=updateNode)

    use_x: BoolProperty(
        name="X", description="smooth vertices along X axis",
        default=True, update=updateNode)

    use_y: BoolProperty(
        name="Y", description="smooth vertices along Y axis",
        default=True, update=updateNode)

    use_z: BoolProperty(
        name="Z", description="smooth vertices along Z axis",
        default=True, update=updateNode)

    preserve_volume: BoolProperty(
        name="Preserve volume", description="Apply volume preservation after smooth",
        default=True, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'VertMask')

        self.inputs.new('SvStringsSocket', 'Iterations').prop_name = "iterations"
        self.inputs.new('SvStringsSocket', 'ClipDist').prop_name = "clip_dist"
        self.inputs.new('SvStringsSocket', 'Factor').prop_name = "factor"
        self.inputs.new('SvStringsSocket', 'BorderFactor').prop_name = "border_factor"

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')

        self.update_mode(context)

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "use_x", toggle=True)
        row.prop(self, "use_y", toggle=True)
        row.prop(self, "use_z", toggle=True)

        col.prop(self, "laplacian", toggle=True)

        if self.laplacian:
            col.prop(self, "preserve_volume", toggle=True)
        else:
            row = col.row(align=True)
            row.prop(self, "mirror_clip_x", toggle=True)
            row.prop(self, "mirror_clip_y", toggle=True)
            row.prop(self, "mirror_clip_z", toggle=True)

    def draw_buttons_ext(self, context, layout):
        row = layout.row()
        row.enabled = numba is not None
        row.prop(self, "use_numba")
        if numba is None:
            layout.label(text="Numba is not installed")
        layout.label(text="Output NumPy")
        row = layout.row(align=True)
        row.prop(self, "output_numpy_vertices", toggle=True)
        row.prop(self, "output_numpy_edges", toggle=True)

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get(deepcopy=False)
        edges_s = self.inputs['Edges'].sv_get(default=[[]], deepcopy=False)
        faces_s = self.inputs['Faces'].sv_get(default=[[]], deepcopy=False)
        masks_s = self.inputs['VertMask'].sv_get(default=[[1]], deepcopy=False)
        iterations_s = self.inputs['Iterations'].sv_get(deepcopy=False)[0]
        if not self.laplacian:
            clip_dist_s = self.inputs['ClipDist'].sv_get(deepcopy=False)[0]
        else:
            clip_dist_s = [0.0]
        factor_s = self.inputs['Factor'].sv_get(deepcopy=False)[0]
        if self.laplacian:
            border_factor_s = self.inputs['BorderFactor'].sv_get(deepcopy=False)[0]
        else:
            border_factor_s = [0.0]

        result_vertices = []
        result_edges = []
        result_faces = []

        axes = (self.use_x, self.use_y, self.use_z)
        clip = (self.mirror_clip_x, self.mirror_clip_y, self.mirror_clip_z)
        output_vertices = self.outputs['Vertices'].is_linked
        output_edges = self.outputs['Edges'].is_linked
        output_faces = self.outputs['Faces'].is_linked
        meshes = match_long_repeat([vertices_s, edges_s, faces_s, masks_s, clip_dist_s, factor_s, border_factor_s, iterations_s])
        for vertices, edges, faces, masks, clip_dist, factor, border_factor, iterations in zip(*meshes):
            new_vertices, new_edges, new_faces = smooth_vertices(
                vertices, edges, faces, masks, axes, clip, clip_dist, factor,
                iterations, use_numba=self.use_numba,
                laplacian=self.laplacian, border_factor=border_factor,
                preserve_volume=self.preserve_volume,
                output_vertices=output_vertices,
                output_edges=output_edges,
                output_faces=output_faces,
                numpy_vertices=self.output_numpy_vertices,
                numpy_edges=self.output_numpy_edges)
            result_vertices.append(new_vertices)
            result_edges.append(new_edges)
            result_faces.append(new_faces)

        for name, result in zip(('Vertices', 'Edges', 'Faces'),
                                (result_vertices, result_edges, result_faces)):
            if self.outputs[name].is_linked:
                self.outputs[name].sv_set(result)

def register():
    bpy.utils.register_class(SvSmoothNode)


def unregister():
    bpy.utils.unregister_class(SvSmoothNode)
