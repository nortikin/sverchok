
import numpy as np

import bpy
from bpy.props import EnumProperty, IntProperty, BoolProperty, FloatProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.geom_2d.merge_mesh import crop_mesh_delaunay

from sverchok.utils.curve import SvCurve
from sverchok.utils.surface import SvSurface
from sverchok.utils.adaptive_surface import adaptive_subdivide, MAXIMUM, GAUSS, MEAN

class SvAdaptiveTessellateNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Adaptive Tessellate Surface
    Tooltip: Adaptively tessellate surface
    """
    bl_idname = 'SvAdaptiveTessellateNode'
    bl_label = 'Adaptive Tessellate Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_ADAPTIVE_TESSELLATE'

    samples_u : IntProperty(
            name = "Samples U",
            default = 25, min = 3,
            update = updateNode)

    samples_v : IntProperty(
            name = "Samples V",
            default = 25, min = 3,
            update = updateNode)

    min_ppf : IntProperty(
            name = "Min per cell",
            description = "Minimum number of new points per rectangular grid cell",
            min = 0, default = 0,
            update = updateNode)

    max_ppf : IntProperty(
            name = "Max per cell",
            description = "Minimum number of new points per rectangular grid cell",
            min = 1, default = 5,
            update = updateNode)

    seed : IntProperty(
            name = "Seed",
            description = "Random Seed value",
            default = 0,
            update = updateNode)

    by_curvature : BoolProperty(
            name = "By Curvature",
            default = True,
            update = updateNode)

    by_area : BoolProperty(
            name = "By Area",
            default = False,
            update = updateNode)

    curvature_types = [
        (MAXIMUM, "Maximum", "Maximum principal curvature", 0),
        (GAUSS, "Gauss", "Gaussian curvature value", 1),
        (MEAN, "Mean", "Mean curvature value", 2)
    ]

    curvature_type : EnumProperty(
            name = "Curvature type",
            description = "Curvature value type to use",
            items = curvature_types,
            default = MAXIMUM,
            update = updateNode)
    
    curvature_clip : FloatProperty(
            name = "Clip Curvature",
            description = "Do not consider curvature values bigger than specified one; set to 0 to consider all curvature values",
            default = 100,
            min = 0,
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
        name="Trimming mode",
        update=updateNode,
        description='Switch between creating holes and fitting mesh into another mesh')

    accuracy: bpy.props.IntProperty(
        name='Trim Accuracy', update=updateNode, default=5, min=3, max=12,
        description='Some errors of the node can be fixed by changing this value')

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, 'by_curvature', toggle=True)
        row.prop(self, 'by_area', toggle=True)
        if self.by_curvature:
            layout.prop(self, 'curvature_type')
        layout.prop(self, 'crop_mode', expand=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        if self.by_curvature:
            layout.prop(self, 'curvature_clip')
        layout.prop(self, 'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvCurveSocket', "TrimCurve")
        self.inputs.new('SvStringsSocket', "SamplesU").prop_name = 'samples_u'
        self.inputs.new('SvStringsSocket', "SamplesV").prop_name = 'samples_v'
        self.inputs.new('SvStringsSocket', "SamplesT").prop_name = 'samples_t'
        self.inputs.new('SvStringsSocket', "MinPpf").prop_name = 'min_ppf'
        self.inputs.new('SvStringsSocket', "MaxPpf").prop_name = 'max_ppf'
        self.inputs.new('SvStringsSocket', "Seed").prop_name = 'seed'
        self.inputs.new('SvVerticesSocket', "AddUVPoints")
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvVerticesSocket', "UVPoints")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surfaces_s = self.inputs['Surface'].sv_get()
        curves_s = self.inputs['TrimCurve'].sv_get(default = [[None]])
        samples_u_s = self.inputs['SamplesU'].sv_get()
        samples_v_s = self.inputs['SamplesV'].sv_get()
        samples_t_s = self.inputs['SamplesT'].sv_get()
        min_ppf_s = self.inputs['MinPpf'].sv_get()
        max_ppf_s = self.inputs['MaxPpf'].sv_get()
        seed_s = self.inputs['Seed'].sv_get()
        add_points_s = self.inputs['AddUVPoints'].sv_get(default=[[]])

        surfaces_s = ensure_nesting_level(surfaces_s, 2, data_types=(SvSurface,))
        curves_s = ensure_nesting_level(curves_s, 2, data_types = (SvCurve,type(None)))
        samples_u_s = ensure_nesting_level(samples_u_s, 2)
        samples_v_s = ensure_nesting_level(samples_v_s, 2)
        samples_t_s = ensure_nesting_level(samples_t_s, 2)
        min_ppf_s = ensure_nesting_level(min_ppf_s, 2)
        max_ppf_s = ensure_nesting_level(max_ppf_s, 2)
        seed_s = ensure_nesting_level(seed_s, 2)
        add_points_s = ensure_nesting_level(add_points_s, 4)

        epsilon = 1.0 / 10**self.accuracy

        verts_out = []
        faces_out = []
        uv_out = []
        inputs = zip_long_repeat(surfaces_s, curves_s, samples_u_s, samples_v_s, samples_t_s, min_ppf_s, max_ppf_s, seed_s, add_points_s)
        for surfaces, curves, samples_u_i, samples_v_i, samples_t_i, min_ppf_i, max_ppf_i, seed_i, add_points_i in inputs:
            objects = zip_long_repeat(surfaces, curves, samples_u_i, samples_v_i, samples_t_i, min_ppf_i, max_ppf_i, seed_i, add_points_i)
            for surface, curve, samples_u, samples_v, samples_t, min_ppf, max_ppf, seed, add_points in objects:
                us, vs, new_faces = adaptive_subdivide(surface,
                                        samples_u, samples_v,
                                        trim_curve = curve,
                                        samples_t = samples_t,
                                        trim_mode = self.crop_mode,
                                        epsilon = epsilon,
                                        by_curvature = self.by_curvature,
                                        curvature_clip = self.curvature_clip,
                                        curvature_type = self.curvature_type,
                                        by_area = self.by_area,
                                        add_points = add_points,
                                        min_ppf = min_ppf, max_ppf = max_ppf, seed = seed)
                new_verts = surface.evaluate_array(us, vs).tolist()
                new_uv = [(u,v,0) for u, v in zip(us, vs)]
                uv_out.append(new_uv)
                verts_out.append(new_verts)
                faces_out.append(new_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Faces'].sv_set(faces_out)
        self.outputs['UVPoints'].sv_set(uv_out)

def register():
    bpy.utils.register_class(SvAdaptiveTessellateNode)

def unregister():
    bpy.utils.unregister_class(SvAdaptiveTessellateNode)

