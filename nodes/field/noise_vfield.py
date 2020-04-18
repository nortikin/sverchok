
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
from sverchok.utils.modules.eval_formula import get_variables, safe_eval
from sverchok.utils.logging import info, exception
from sverchok.utils.sv_noise_utils import noise_options, PERLIN_ORIGINAL

from sverchok.utils.field.vector import SvNoiseVectorField

avail_noise = [(t[0], t[0].title(), t[0].title(), '', t[1]) for t in noise_options]

class SvNoiseVectorFieldNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Noise Vector Field
    Tooltip: Noise Vector Field
    """
    bl_idname = 'SvExNoiseVectorFieldNode'
    bl_label = 'Noise Vector Field'
    bl_icon = 'OUTLINER_OB_FORCE_FIELD'

    noise_type: EnumProperty(
        items=avail_noise,
        default=PERLIN_ORIGINAL,
        description="Noise type",
        update=updateNode)

    seed: IntProperty(default=0, name='Seed', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.outputs.new('SvVectorFieldSocket', 'Noise')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'noise_type', text="Type")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        seeds_s = self.inputs['Seed'].sv_get()

        fields_out = []
        for seed in seeds_s:
            if isinstance(seed, (list, int)):
                seed = seed[0]

            if seed == 0:
                seed = 12345
            field = SvNoiseVectorField(self.noise_type, seed)
            fields_out.append(field)

        self.outputs['Noise'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvNoiseVectorFieldNode)

def unregister():
    bpy.utils.unregister_class(SvNoiseVectorFieldNode)

