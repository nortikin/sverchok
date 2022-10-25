
import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.surface.core import SvSurface
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    from FreeCAD import Part
    try:
        import Part as PartModule
    except ImportError:
        PartModule = Part

    from sverchok.utils.solid import to_solid


class SvCompoundSolidNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Compound Solid
    Tooltip: Make Compound Solid object out of Solids, Curves and Surfaces
    """
    bl_idname = 'SvCompoundSolidNode'
    bl_label = 'Compound Solid'
    bl_icon = 'STICKY_UVS_LOC'
    sv_category = "Solid Outputs"
    sv_dependencies = {'FreeCAD'}

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solids")
        self.inputs.new('SvCurveSocket', "Curves")
        self.inputs.new('SvSurfaceSocket', "Surfaces")
        self.outputs.new('SvSolidSocket', "Compound")

    def process(self):
        if not self.outputs['Compound'].is_linked:
            return
        if not any(sock.is_linked for sock in self.inputs):
            return

        solids_s = self.inputs['Solids'].sv_get(default=[[None]])
        curves_s = self.inputs['Curves'].sv_get(default=[[None]])
        surfaces_s = self.inputs['Surfaces'].sv_get(default=[[None]])

        if self.inputs['Solids'].is_linked:
            solids_s = ensure_nesting_level(solids_s, 2, data_types=(PartModule.Shape,))
            solids_level = get_data_nesting_level(solids_s, data_types=(PartModule.Shape,))
        else:
            solids_level = 2
        if self.inputs['Curves'].is_linked:
            curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
            curves_level = get_data_nesting_level(curves_s, data_types=(SvCurve,))
        else:
            curves_level = 2
        if self.inputs['Surfaces'].is_linked:
            surfaces_s = ensure_nesting_level(surfaces_s, 2, data_types=(SvSurface,))
            surfaces_level = get_data_nesting_level(surfaces_s, data_types=(SvSurface,))
        else:
            surfaces_level = 2

        max_level = max(solids_level, curves_level, surfaces_level)
        compounds_out = []
        for solids, curves, surfaces in zip_long_repeat(solids_s, curves_s, surfaces_s):
            shapes = solids + curves + surfaces
            shapes = [to_solid(s) for s in shapes if s is not None]
            compound = PartModule.Compound(shapes)
            compounds_out.append(compound)

        self.outputs['Compound'].sv_set(compounds_out)


def register():
    bpy.utils.register_class(SvCompoundSolidNode)


def unregister():
    bpy.utils.unregister_class(SvCompoundSolidNode)
