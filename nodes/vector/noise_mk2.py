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
from bpy.props import EnumProperty, IntProperty, BoolProperty
from mathutils import noise

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode
from sverchok.utils.sv_noise_utils import noise_options, PERLIN_ORIGINAL, noise_numpy_types
import numpy as np


def numpy_noise(vecs, out, out_mode, seed, noise_function, smooth, output_numpy):
    if out_mode == 'VECTOR':
        obj = np.array(vecs)
        r_noise = np.stack((
            noise_function(obj, seed, smooth),
            noise_function(obj, seed + 1, smooth),
            noise_function(obj, seed + 2, smooth)
            )).T
        out.append((2 * r_noise - 1) if output_numpy else (2 * r_noise - 1).tolist())
    else:
        if output_numpy:
            out.append(noise_function(np.array(vecs), seed, smooth))
        else:
            out.append(noise_function(np.array(vecs), seed, smooth).tolist())

def mathulis_noise(vecs, out, out_mode, noise_type, noise_function, output_numpy):
    if out_mode == 'VECTOR':
        if output_numpy:
            out.append(np.array([noise_function(v, noise_basis=noise_type)[:] for v in vecs]))
        else:
            out.append([noise_function(v, noise_basis=noise_type)[:] for v in vecs])
    else:
        vecs = np.array([noise_function(v, noise_basis=noise_type)[:] for v in vecs])
        vecs -= [0, 0, 1]
        noise_output = np.linalg.norm(vecs, axis=1)*0.5
        out.append(noise_output if output_numpy else noise_output.tolist())


avail_noise = [(t[0], t[0].title().replace('_', ' '), t[0].title(), '', t[1]) for t in noise_options]

for idx, new_type in enumerate(noise_numpy_types.keys()):
    avail_noise.append((new_type, new_type.title().replace('_', ' '), new_type.title(), '', 100 + idx))


class SvNoiseNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Vector Noise
    Tooltip: Affect input verts with a noise function.

    A short description for reader of node code
    """

    bl_idname = 'SvNoiseNodeMK2'
    bl_label = 'Vector Noise'
    bl_icon = 'FORCE_TURBULENCE'
    sv_icon = 'SV_VECTOR_NOISE'

    @throttled
    def changeMode(self, context):
        outputs = self.outputs
        if self.out_mode == 'SCALAR':
            if 'Noise S' not in outputs:
                outputs[0].replace_socket('SvStringsSocket', 'Noise S')
                return
        if self.out_mode == 'VECTOR':
            if 'Noise V' not in outputs:
                outputs[0].replace_socket('SvVerticesSocket', 'Noise V')
                return

    out_modes = [
        ('SCALAR', 'Scalar', 'Scalar output', '', 1),
        ('VECTOR', 'Vector', 'Vector output', '', 2)]

    out_mode: EnumProperty(
        items=out_modes,
        default='VECTOR',
        description='Output type',
        update=changeMode)

    noise_type: EnumProperty(
        items=avail_noise,
        default=PERLIN_ORIGINAL,
        description="Noise type",
        update=updateNode)

    seed: IntProperty(default=0, name='Seed', update=updateNode)

    smooth: BoolProperty(
        name='Smooth',
        description='Smooth noise',
        default=True, update=updateNode)

    interpolate: BoolProperty(
        name='Interpolate',
        description='Interpolate gradients',
        default=True, update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.outputs.new('SvVerticesSocket', 'Noise V')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'out_mode', expand=True)
        layout.prop(self, 'noise_type', text="Type")
        if self.noise_type in noise_numpy_types.keys():
            row = layout.row(align=True)
            row.prop(self, 'smooth', toggle=True)
            row.prop(self, 'interpolate', toggle=True)


    def draw_buttons_ext(self, ctx, layout):
        self.draw_buttons(ctx, layout)
        layout.prop(self, "output_numpy", toggle=False)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "out_mode")
        layout.prop_menu_enum(self, "noise_type")
        if self.noise_type in noise_numpy_types.keys():
            layout.prop(self, 'smooth', toggle=True)
            layout.prop(self, 'interpolate', toggle=True)
        layout.prop(self, "output_numpy", toggle=True)

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        if not (outputs[0].is_linked and inputs[0].is_linked):
            return

        out = []
        verts = inputs['Vertices'].sv_get(deepcopy=False)
        seeds = inputs['Seed'].sv_get()[0]

        max_len = max(map(len, (seeds, verts)))
        noise_type = self.noise_type

        out_mode = self.out_mode
        output_numpy = self.output_numpy

        if noise_type in noise_numpy_types.keys():

            noise_function = noise_numpy_types[noise_type][self.interpolate]
            smooth = self.smooth
            for i in range(max_len):
                seed = seeds[min(i, len(seeds)-1)]
                obj_id = min(i, len(verts)-1)
                numpy_noise(verts[obj_id], out, out_mode, seed, noise_function, smooth, output_numpy)

        else:

            noise_function = noise.noise_vector

            for i in range(max_len):
                seed = seeds[min(i, len(seeds)-1)]
                obj_id = min(i, len(verts)-1)
                # 0 unsets the seed and generates unreproducable output based on system time
                seed_val = int(round(seed)) or 140230
                noise.seed_set(seed_val)
                mathulis_noise(verts[obj_id], out, out_mode, noise_type, noise_function, output_numpy)

        outputs[0].sv_set(out)


    def draw_label(self):
        if self.hide:
            if not self.inputs['Seed'].is_linked:
                seed = ' + ({0})'.format(str(int(self.seed)))
            else:
                seed = ' + seed(s)'
            return self.noise_type.title() + seed
        else:
            return self.label or self.name

classes = [SvNoiseNodeMK2]
register, unregister = bpy.utils.register_classes_factory(classes)
