
import random
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils.kdtree import KDTree

import sverchok
<<<<<<< HEAD
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, throttle_and_update_node
=======
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.field.scalar import SvScalarField
>>>>>>> "Field random probe" mk2.

BATCH_SIZE = 50
MAX_ITERATIONS = 1000

def _check_all(v_new, vs_old, min_r):
    kdt = KDTree(len(vs_old))
    for i, v in enumerate(vs_old):
        kdt.insert(v, i)
    kdt.balance()
    nearest, idx, dist = kdt.find(v_new)
    if dist is None:
        return True
    return (dist >= min_r)

class SvFieldRandomProbeMk2Node(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Scalar Field Random Probe
    Tooltip: Generate random points according to scalar field
    """
    bl_idname = 'SvFieldRandomProbeMk2Node'
    bl_label = 'Field Random Probe'
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

    min_r : FloatProperty(
            name = "Min.Distance",
            description = "Minimum distance between generated points; set to 0 to disable the check",
            default = 0.0,
            min = 0.0,
            update = updateNode)

    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['FieldMin'].hide_safe = self.proportional != True
        self.inputs['FieldMax'].hide_safe = self.proportional != True

    proportional : BoolProperty(
            name = "Proportional",
            default = False,
            update = update_sockets)

    def draw_buttons(self, context, layout):
        layout.prop(self, "proportional", toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "Field")
        self.inputs.new('SvVerticesSocket', "Bounds")
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'count'
        self.inputs.new('SvStringsSocket', "MinDistance").prop_name = 'min_r'
        self.inputs.new('SvStringsSocket', "Threshold").prop_name = 'threshold'
        self.inputs.new('SvStringsSocket', "FieldMin").prop_name = 'field_min'
        self.inputs.new('SvStringsSocket', "FieldMax").prop_name = 'field_max'
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.update_sockets(context)

    def get_bounds(self, vertices):
        vs = np.array(vertices)
        min = vs.min(axis=0)
        max = vs.max(axis=0)
        return min.tolist(), max.tolist()

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        fields_s = self.inputs['Field'].sv_get()
        vertices_s = self.inputs['Bounds'].sv_get()
        count_s = self.inputs['Count'].sv_get()
        min_r_s = self.inputs['MinDistance'].sv_get()
        threshold_s = self.inputs['Threshold'].sv_get()
        field_min_s = self.inputs['FieldMin'].sv_get()
        field_max_s = self.inputs['FieldMax'].sv_get()
        seed_s = self.inputs['Seed'].sv_get()

        fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))
        vertices_s = ensure_nesting_level(vertices_s, 4)
        count_s = ensure_nesting_level(count_s, 2)
        min_r_s = ensure_nesting_level(min_r_s, 2)
        threshold_s = ensure_nesting_level(threshold_s, 2)
        field_min_s = ensure_nesting_level(field_min_s, 2)
        field_max_s = ensure_nesting_level(field_max_s, 2)
        seed_s = ensure_nesting_level(seed_s, 2)

        verts_out = []
        inputs = zip_long_repeat(fields_s, vertices_s, threshold_s, field_min_s, field_max_s, count_s, min_r_s, seed_s)
        for objects in inputs:
            for field, vertices, threshold, field_min, field_max, count, min_r, seed in zip_long_repeat(*objects):

                random.seed(seed)

                b1, b2 = self.get_bounds(vertices)
                x_min, y_min, z_min = b1
                x_max, y_max, z_max = b2

                done = 0
                new_verts = []
                iterations = 0
                while done < count:
                    iterations += 1
                    if iterations > MAX_ITERATIONS:
                        self.error("Maximum number of iterations (%s) reached, stop.", MAX_ITERATIONS)
                        break
                    batch_xs = []
                    batch_ys = []
                    batch_zs = []
                    batch = []
                    left = count - done
                    max_size = min(BATCH_SIZE, left)
                    for i in range(max_size):
                        x = random.uniform(x_min, x_max)
                        y = random.uniform(y_min, y_max)
                        z = random.uniform(z_min, z_max)
                        batch_xs.append(x)
                        batch_ys.append(y)
                        batch_zs.append(z)
                        batch.append((x, y, z))
                    batch_xs = np.array(batch_xs)#[np.newaxis][np.newaxis]
                    batch_ys = np.array(batch_ys)#[np.newaxis][np.newaxis]
                    batch_zs = np.array(batch_zs)#[np.newaxis][np.newaxis]
                    batch = np.array(batch)

                    values = field.evaluate_grid(batch_xs, batch_ys, batch_zs)
                    #values = values[0][0]
                    good_idxs = values >= threshold
                    if not self.proportional:
                        candidates = batch[good_idxs].tolist()
                    else:
                        candidates = []
                        for vert, value in zip(batch[good_idxs].tolist(), values[good_idxs].tolist()):
                            probe = random.uniform(field_min, field_max)
                            if probe <= value:
                                candidates.append(vert)

                    if min_r == 0:
                        good_verts = candidates
                    else:
                        good_verts = []
                        for candidate in candidates:
                            if _check_all(candidate, new_verts + good_verts, min_r):
                                good_verts.append(candidate)

                    new_verts.extend(good_verts)
                    done += len(good_verts)

                verts_out.append(new_verts)

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvFieldRandomProbeMk2Node)

def unregister():
    bpy.utils.unregister_class(SvFieldRandomProbeMk2Node)

