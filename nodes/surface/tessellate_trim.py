
import numpy as np

import bpy
from bpy.props import EnumProperty, IntProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.geom_2d.merge_mesh import crop_mesh_delaunay
from sverchok.utils.sv_mesh_utils import mesh_join

from sverchok.utils.curve import SvCurve
from sverchok.utils.surface import SvSurface

# This node requires delaunay_cdt function, which is available
# since Blender 2.81 only. So the node will not be available in
# Blender 2.80.

class SvTessellateTrimSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Tessellate Trim Surface
    Tooltip: Tessellate a surface with trimming curve
    """
    bl_idname = 'SvExTessellateTrimSurfaceNode'
    bl_label = 'Tessellate & Trim Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_TRIM_TESSELLATE'

    axes = [
        ('XY', "X Y", "XOY plane", 0),
        ('YZ', "Y Z", "YOZ plane", 1),
        ('XZ', "X Z", "XOZ plane", 2)
    ]

    orientation : EnumProperty(
            name = "Curve orientation",
            items = axes,
            default = 'XY',
            update = updateNode)

    samples_u : IntProperty(
            name = "Samples U",
            default = 25, min = 3,
            update = updateNode)

    samples_v : IntProperty(
            name = "Samples V",
            default = 25, min = 3,
            update = updateNode)

    samples_t : IntProperty(
            name = "Curve Samples",
            default = 100, min = 3,
            update = updateNode)

    mode_items = [('inner', 'Inner', 'Fit mesh', 'SELECT_INTERSECT', 0),
                  ('outer', 'Outer', 'Make hole', 'SELECT_SUBTRACT', 1)]

    crop_mode: bpy.props.EnumProperty(
        items=mode_items,
        default = 'inner',
        name='Mode of cropping mesh',
        update=updateNode,
        description='Switch between creating holes and fitting mesh into another mesh')

    accuracy: bpy.props.IntProperty(
        name='Accuracy', update=updateNode, default=5, min=3, max=12,
        description='Some errors of the node can be fixed by changing this value')

    def draw_buttons(self, context, layout):
        if crop_mesh_delaunay:
            layout.label(text="Curve plane:")
            layout.prop(self, "orientation", expand=True)
            layout.prop(self, 'crop_mode', expand=True)
        else:
            layout.label("Unsupported Blender version")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvCurveSocket', "TrimCurve")
        self.inputs.new('SvStringsSocket', "SamplesU").prop_name = 'samples_u'
        self.inputs.new('SvStringsSocket', "SamplesV").prop_name = 'samples_v'
        self.inputs.new('SvStringsSocket', "CurveSamples").prop_name = 'samples_t'
        self.outputs.new('SvVerticesSocket', "Vertices")
        #self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def make_grid(self, surface, samples_u, samples_v):
        u_min = surface.get_u_min()
        u_max = surface.get_u_max()
        v_min = surface.get_v_min()
        v_max = surface.get_v_max()
        us = np.linspace(u_min, u_max, num=samples_u)
        vs = np.linspace(v_min, v_max, num=samples_v)
        us, vs = np.meshgrid(us, vs)
        us = us.flatten()
        vs = vs.flatten()
        return [(u, v, 0.0) for u, v in zip(us, vs)]

    def make_edges_xy(self, samples_u, samples_v):
        edges = []
        for row in range(samples_v):
            e_row = [(i + samples_u * row, (i+1) + samples_u * row) for i in range(samples_u-1)]
            edges.extend(e_row)
            if row < samples_v - 1:
                e_col = [(i + samples_u * row, i + samples_u * (row+1)) for i in range(samples_u)]
                edges.extend(e_col)
        return edges

    def make_faces_xy(self, samples_u, samples_v):
        faces = []
        for row in range(samples_v - 1):
            for col in range(samples_u - 1):
                i = row * samples_u + col
                face = (i, i+samples_u, i+samples_u+1, i+1)
                faces.append(face)
        return faces

    def make_curves(self, curves, samples_t):
        all_verts = []
        all_edges = []
        all_faces = []
        for curve in curves:
            t_min, t_max = curve.get_u_bounds()
            ts = np.linspace(t_min, t_max, num=samples_t)
            verts = curve.evaluate_array(ts).tolist()
            n = len(ts)
            edges = [[i, i + 1] for i in range(n - 1)]
            edges.append([n-1, 0])
            faces = [list(range(n))]
            all_verts.append(verts)
            all_edges.append(edges)
            all_faces.append(faces)
        verts, edges, faces = mesh_join(all_verts, all_edges, all_faces)
        return verts, edges, faces

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        if not crop_mesh_delaunay:
            raise Exception("Unsupported Blender version!")

        surfaces_s = self.inputs['Surface'].sv_get()
        curves_s = self.inputs['TrimCurve'].sv_get()
        samples_u_s = self.inputs['SamplesU'].sv_get()
        samples_v_s = self.inputs['SamplesV'].sv_get()
        samples_t_s = self.inputs['CurveSamples'].sv_get()

        surfaces_s = ensure_nesting_level(surfaces_s, 2, data_types=(SvSurface,))
        curves_s = ensure_nesting_level(curves_s, 3, data_types=(SvCurve,))
        samples_u_s = ensure_nesting_level(samples_u_s, 2)
        samples_v_s = ensure_nesting_level(samples_v_s, 2)
        samples_t_s = ensure_nesting_level(samples_t_s, 2)

        verts_out = []
        faces_out = []
        inputs = zip_long_repeat(surfaces_s, curves_s, samples_u_s, samples_v_s, samples_t_s)
        for surfaces, curves_i, samples_u_i, samples_v_i, samples_t_i in inputs:
            objects = zip_long_repeat(surfaces, curves_i, samples_u_i, samples_v_i, samples_t_i)
            for surface, curves, samples_u, samples_v, samples_t in objects:

                crop_verts, crop_edges, crop_faces = self.make_curves(curves, samples_t)
                grid_verts = self.make_grid(surface, samples_u, samples_v)
                #grid_edges = self.make_edges_xy(samples_u, samples_v)
                grid_faces = self.make_faces_xy(samples_u, samples_v)

                epsilon = 1.0 / 10**self.accuracy
                xy_verts, new_faces, _ = crop_mesh_delaunay(grid_verts, grid_faces, crop_verts, crop_faces, self.crop_mode, epsilon)

                us = np.array([vert[0] for vert in xy_verts])
                vs = np.array([vert[1] for vert in xy_verts])
                new_verts = surface.evaluate_array(us, vs).tolist()

                verts_out.append(new_verts)
                faces_out.append(new_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Faces'].sv_set(faces_out)

def register():
    bpy.utils.register_class(SvTessellateTrimSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvTessellateTrimSurfaceNode)

