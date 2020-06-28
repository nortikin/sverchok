
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import bpy
    from bpy.props import BoolProperty, FloatProperty, StringProperty, EnumProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode, match_long_repeat as mlr
    import FreeCAD as F
    import Part
    from FreeCAD import Base

    class SvSolidBooleanNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Union, Diff, Intersect
        Tooltip: Perform Boolean Operations on Solids
        """
        bl_idname = 'SvSolidBooleanNode'
        bl_label = 'Solid Boolean'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'


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

        def draw_buttons(self, context, layout):
            layout.prop(self, "selected_mode", toggle=True)
            layout.prop(self, "nest_objs", toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid A")
            self.inputs.new('SvSolidSocket', "Solid B")
            self.inputs.new('SvSolidSocket', "Solids")
            self.inputs['Solids'].hide_safe = True


            self.outputs.new('SvSolidSocket', "Solid")



        def single_union(self):
            solids_a = self.inputs[0].sv_get()
            solids_b = self.inputs[1].sv_get()
            solids = []
            for solid_a, solid_b in zip(*mlr([solids_a, solids_b])):
                solids.append(solid_a.fuse(solid_b))
            self.outputs[0].sv_set(solids)

        def multi_union(self):
            solids = self.inputs[2].sv_get()
            base = solids[0].copy()
            for s in solids[1:]:
                base = base.fuse(s)

            self.outputs[0].sv_set([base])
        def single_intersect(self):
            solids_a = self.inputs[0].sv_get()
            solids_b = self.inputs[1].sv_get()
            solids = []
            for solid_a, solid_b in zip(*mlr([solids_a, solids_b])):
                solids.append(solid_a.common(solid_b))
            self.outputs[0].sv_set(solids)

        def multi_intersect(self):
            solids = self.inputs[2].sv_get()
            base = solids[0].copy()
            for s in solids[1:]:
                base = base.common(s)
        def single_difference(self):
            solids_a = self.inputs[0].sv_get()
            solids_b = self.inputs[1].sv_get()
            solids = []
            for solid_a, solid_b in zip(*mlr([solids_a, solids_b])):
                solids.append(solid_a.cut(solid_b))
            self.outputs[0].sv_set(solids)

        def multi_difference(self):
            solids = self.inputs[2].sv_get()
            base = solids[0].copy()
            for s in solids[1:]:
                base = base.cut(s)

            self.outputs[0].sv_set([base])

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            if self.selected_mode == 'UNION':
                if self.nest_objs:
                    self.multi_union()
                else:
                    self.single_union()
            elif self.selected_mode == 'ITX':
                if self.nest_objs:
                    self.multi_intersect()
                else:
                    self.single_intersect()
            else:
                if self.nest_objs:
                    self.multi_difference()
                else:
                    self.single_difference()


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidBooleanNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidBooleanNode)
