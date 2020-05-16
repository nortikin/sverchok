
import numpy as np
import random

import bpy
from bpy.props import EnumProperty, IntProperty, BoolProperty, FloatProperty
from mathutils.kdtree import KDTree

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.surface import SvSurface
from sverchok.utils.field.scalar import SvScalarField

def random_point(min_x, max_x, min_y, max_y):
    x = random.uniform(min_x, max_x)
    y = random.uniform(min_y, max_y)
    return x,y

def check_all(v_new, vs_old, min_r):
    kdt = KDTree(len(vs_old))
    for i, v in enumerate(vs_old):
        kdt.insert(v, i)
    kdt.balance()
    nearest, idx, dist = kdt.find(v_new)
    if dist is None:
        return True
    return (dist >= min_r)

#     for v_old in vs_old:
#         distance = np.linalg.norm(v_new - v_old)
#         if distance < min_r:
#             return False
#    return True

BATCH_SIZE = 100
MAX_ITERATIONS = 1000

class SvPopulateSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Populate Surface
    Tooltip: Generate random points on the surface
    """
    bl_idname = 'SvPopulateSurfaceNode'
    bl_label = 'Populate Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FIELD_RANDOM_PROBE'

    threshold : FloatProperty(
            name = "Threshold",
            default = 0.5,
            update = updateNode)

    field_min : FloatProperty(
            name = "Field Minimum",
            default = 0.0,
            update = updateNode)

    field_max : FloatProperty(
            name = "Field Maximum",
            default = 1.0,
            update = updateNode)

    seed: IntProperty(default=0, name='Seed', update=updateNode)

    count : IntProperty(
            name = "Count",
            default = 50,
            min = 1,
            update = updateNode)

    @throttled
    def update_sockets(self, context):
        self.inputs['FieldMin'].hide_safe = self.proportional != True
        self.inputs['FieldMax'].hide_safe = self.proportional != True

    proportional : BoolProperty(
            name = "Proportional",
            default = False,
            update = update_sockets)

    min_r : FloatProperty(
            name = "Min Distance",
            default = 0.5,
            min = 0,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "proportional", toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvScalarFieldSocket', "Field")
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'count'
        self.inputs.new('SvStringsSocket', "MinDistance").prop_name = 'min_r'
        self.inputs.new('SvStringsSocket', "Threshold").prop_name = 'threshold'
        self.inputs.new('SvStringsSocket', "FieldMin").prop_name = 'field_min'
        self.inputs.new('SvStringsSocket', "FieldMax").prop_name = 'field_max'
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvVerticesSocket', "UVPoints")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        fields_s = self.inputs['Field'].sv_get(default=[[None]])
        count_s = self.inputs['Count'].sv_get()
        threshold_s = self.inputs['Threshold'].sv_get()
        field_min_s = self.inputs['FieldMin'].sv_get()
        field_max_s = self.inputs['FieldMax'].sv_get()
        min_r_s = self.inputs['MinDistance'].sv_get()
        seed_s = self.inputs['Seed'].sv_get()

        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
        has_field = self.inputs['Field'].is_linked
        if has_field:
            fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))

        verts_out = []
        uv_out = []

        parameters = zip_long_repeat(surface_s, fields_s, count_s, threshold_s, field_min_s, field_max_s, min_r_s, seed_s)
        for surfaces, fields, counts, thresholds, field_mins, field_maxs, min_rs, seeds in parameters:
            objects = zip_long_repeat(surfaces, fields, counts, thresholds, field_mins, field_maxs, min_rs, seeds)
            for surface, field, count, threshold, field_min, field_max, min_r, seed in objects:
                u_min, u_max = surface.get_u_min(), surface.get_u_max()
                v_min, v_max = surface.get_v_min(), surface.get_v_max()

                if seed == 0:
                    seed = 12345
                random.seed(seed)
                done = 0
                new_verts = []
                new_uv = []
                iterations = 0

                while done < count:
                    iterations += 1
                    if iterations > MAX_ITERATIONS:
                        self.error("Maximum number of iterations (%s) reached, stop.", MAX_ITERATIONS)
                        break
                    batch_us = []
                    batch_vs = []
                    left = count - done
                    max_size = min(BATCH_SIZE, left)
                    for i in range(max_size):
                        u = random.uniform(u_min, u_max)
                        v = random.uniform(v_min, v_max)
                        batch_us.append(u)
                        batch_vs.append(v)
                    batch_us = np.array(batch_us)
                    batch_vs = np.array(batch_vs)
                    batch_ws = np.zeros_like(batch_us)
                    batch_uvs = np.stack((batch_us, batch_vs, batch_ws)).T

                    batch_verts = surface.evaluate_array(batch_us, batch_vs)
                    batch_xs = batch_verts[:,0]
                    batch_ys = batch_verts[:,1]
                    batch_zs = batch_verts[:,2]

                    if field is not None:
                        values = field.evaluate_grid(batch_xs, batch_ys, batch_zs)

                        good_idxs = values >= threshold
                        if not self.proportional:
                            candidates = batch_verts[good_idxs]
                            candidate_uvs = batch_uvs[good_idxs]
                        else:
                            candidates = []
                            candidate_uvs = []
                            for uv, vert, value in zip(batch_uvs[good_idxs].tolist(), batch_verts[good_idxs].tolist(), values[good_idxs].tolist()):
                                probe = random.uniform(field_min, field_max)
                                if probe <= value:
                                    candidates.append(vert)
                                    candidate_uvs.append(uv)
                            candidates = np.array(candidates)
                            candidate_uvs = np.array(candidate_uvs)
                    else:
                        candidates = batch_verts
                        candidate_uvs = batch_uvs

                    if len(candidates) > 0:
                        good_verts = []
                        good_uvs = []
                        for candidate_uv, candidate in zip(candidate_uvs, candidates):
                            if min_r == 0 or check_all(candidate, new_verts + good_verts, min_r):
                                good_verts.append(candidate)
                                good_uvs.append(candidate_uv)
                                done += 1
                        new_verts.extend(good_verts)
                        new_uv.extend(good_uvs)

                verts_out.append(new_verts)
                uv_out.append(new_uv)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['UVPoints'].sv_set(uv_out)

def register():
    bpy.utils.register_class(SvPopulateSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvPopulateSurfaceNode)

