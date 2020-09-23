# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, match_long_repeat as mlr, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvSolidGeneralFuseNode', 'Solid General Fuse', 'FreeCAD')
else:
    from sverchok.utils.solid import SvGeneralFuse

    import Part

class SvSolidGeneralFuseNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Union, Diff, Intersect
    Tooltip: Perform Boolean Operations on Solids
    """
    bl_idname = 'SvSolidGeneralFuseNode'
    bl_label = 'Solid General Fuse'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SOLID_BOOLEAN'
    solid_catergory = "Operators"

    refine_solid: BoolProperty(
        name="Refine Solid",
        description="Removes redundant edges (may slow the process)",
        default=True,
        update=updateNode)

    merge_result : BoolProperty(
        name = "Merge Result",
        default=True,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'merge_result')
        if self.merge_result:
            layout.prop(self, "refine_solid")

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solids")
        self.inputs.new('SvStringsSocket', "Include")
        self.inputs.new('SvStringsSocket', "Exclude")
        self.outputs.new('SvSolidSocket', "Solid")

    def make_solid(self, solids, include_idxs, exclude_idxs):
        fused = SvGeneralFuse(solids)
        good = []
        for part in fused.get_all_parts():
            src_idxs = fused.get_part_source_idxs(part)
            print("P", part, src_idxs)

            if include_idxs is not None:
                include = False
                for idxs in include_idxs:
                    if set(idxs) == src_idxs:
                        print(f"{idxs} in {src_idxs} => include")
                        include = True
                        break
            else:
                include = True

            exclude = False
            if exclude_idxs is not None:
                for idxs in exclude_idxs:
                    if set(idxs) == src_idxs:
                        exclude = True
                        break

            if include and not exclude:
                good.append(part)

        if self.merge_result:
            if not good:
                return []
            elif len(good) == 1:
                return good[0]
            else:
                solid = good[0].fuse(good[1:])
                if self.refine_solid:
                    solid = solid.removeSplitter()
                return solid
        else:
            return good

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids_in = self.inputs['Solids'].sv_get()
        level = get_data_nesting_level(solids_in, data_types=(Part.Shape,))
        solids_in = ensure_nesting_level(solids_in, 2, data_types=(Part.Shape,))
        include_in = self.inputs['Include'].sv_get(default=[None])
        if self.inputs['Include'].is_linked:
            include_in = ensure_nesting_level(include_in, 3)
        exclude_in = self.inputs['Exclude'].sv_get(default=[None])
        if self.inputs['Exclude'].is_linked:
            exclude_in = ensure_nesting_level(exclude_in, 3)

        solids_out = []
        for solids, include_idxs, exclude_idxs in zip_long_repeat(solids_in, include_in, exclude_in):
            new_solids = self.make_solid(solids, include_idxs, exclude_idxs)
            if level > 1 or self.merge_result:
                solids_out.append(new_solids)
            else:
                solids_out.extend(new_solids)

        self.outputs['Solid'].sv_set(solids_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidGeneralFuseNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidGeneralFuseNode)

