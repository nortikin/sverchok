# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat as mlr, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvSolidBooleanNode', 'Solid Boolean', 'FreeCAD')
else:
    import Part

class SvSolidBooleanNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Union, Diff, Intersect
    Tooltip: Perform Boolean Operations on Solids
    """
    bl_idname = 'SvSolidBooleanNode'
    bl_label = 'Solid Boolean'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SOLID_BOOLEAN'
    solid_catergory = "Operators"

    precision: FloatProperty(
        name="Length",
        default=0.1,
        precision=4,
        update=updateNode)

    mode_options = [
        ("ITX", "Intersect", "", 0),
        ("UNION", "Union", "", 1),
        ("DIFF", "Difference", "", 2)
        ]

    selected_mode: EnumProperty(
        name='Operation',
        items=mode_options,
        description="basic booleans using solids",
        default="ITX",
        update=updateNode)

    def update_mode(self, context):
        self.inputs['Solid A'].hide_safe = self.nest_objs
        self.inputs['Solid B'].hide_safe = self.nest_objs
        self.inputs['Solids'].hide_safe = not self.nest_objs
        updateNode(self, context)

    nest_objs: BoolProperty(
        name="Accumulate nested",
        description="bool first two solids, then applies rest to result one by one",
        default=False,
        update=update_mode)

    refine_solid: BoolProperty(
        name="Refine Solid",
        description="Removes redundant edges (may slow the process)",
        default=True,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "selected_mode", toggle=True)
        layout.prop(self, "nest_objs", toggle=True)
        if self.selected_mode == 'UNION':
            layout.prop(self, "refine_solid")

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid A")
        self.inputs.new('SvSolidSocket', "Solid B")
        self.inputs.new('SvSolidSocket', "Solids")
        self.inputs['Solids'].hide_safe = True

        self.outputs.new('SvSolidSocket', "Solid")

    def make_solid(self, solids):
        do_refine = self.refine_solid and self.selected_mode in {'UNION'}
        base = solids[0].copy()
        rest = solids[1:]
        if self.selected_mode == 'UNION':
            solid = base.fuse(rest)
        elif sel.selected_mode == 'ITX':
            solid = base.common(rest)
        elif self.selected_mode == 'DIFF':
            solid = base.cut(rest)
        else:
            raise Exception("Unknown mode")
        if do_refine:
            solid = solid.removeSplitter()
        return solid

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids_out = []
        if self.nest_objs:
            solids_in = self.inputs['Solids'].sv_get()
            #level = get_data_nesting_level(solids_in, data_types=(Part.Shape,))
            solids_in = ensure_nesting_level(solids_in, 2, data_types=(Part.Shape,))

            for solids in solids_in:
                solid = self.make_solid(solids)
                solids_out.append(solid)

            self.outputs['Solid'].sv_set(solids_out)

        else:
            solids_a_in = self.inputs['Solid A'].sv_get()
            solids_b_in = self.inputs['Solid B'].sv_get()
            level_a = get_data_nesting_level(solids_a_in, data_types=(Part.Shape,))
            level_b = get_data_nesting_level(solids_b_in, data_types=(Part.Shape,))
            solids_a_in = ensure_nesting_level(solids_a_in, 2, data_types=(Part.Shape,))
            solids_b_in = ensure_nesting_level(solids_b_in, 2, data_types=(Part.Shape,))
            level = max(level_a, level_b)

            solids_out = []
            for params in zip_long_repeat(solids_a_in, solids_b_in):
                new_solids = []
                for solid_a, solid_b in zip_long_repeat(*params):
                    solid = self.make_solid([solid_a, solid_b])
                    new_solids.append(solid)
                if level == 1:
                    solids_out.extend(new_solids)
                else:
                    solids_out.append(new_solids)

            self.outputs['Solid'].sv_set(solids_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidBooleanNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidBooleanNode)
