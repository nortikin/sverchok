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
    add_dummy('SvSolidBooleanNode', 'Solid Boolean', 'FreeCAD')
else:
    from sverchok.utils.solid import SvGeneralFuse, SvBoolResult

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

    @throttled
    def update_mode(self, context):
        self.inputs['Solid A'].hide_safe = self.nest_objs
        self.inputs['Solid B'].hide_safe = self.nest_objs
        self.inputs['Solids'].hide_safe = not self.nest_objs
        self.outputs['EdgesMask'].hide_safe = not self.generate_masks
        self.outputs['EdgeSources'].hide_safe = not self.generate_masks
        self.outputs['FacesMask'].hide_safe = not self.generate_masks
        self.outputs['FaceSources'].hide_safe = not self.generate_masks

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

    generate_masks : BoolProperty(
        name = "Generate Masks",
        description = "Calculate masks so it will be possible to know which edges / faces are new",
        default = False,
        update = update_mode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "selected_mode", toggle=True)
        layout.prop(self, 'generate_masks', toggle=True)
        layout.prop(self, "nest_objs", toggle=True)
        if self.selected_mode == 'UNION':
            layout.prop(self, "refine_solid")

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid A")
        self.inputs.new('SvSolidSocket', "Solid B")
        self.inputs.new('SvSolidSocket', "Solids")

        self.outputs.new('SvSolidSocket', "Solid")
        self.outputs.new('SvStringsSocket', "EdgesMask")
        self.outputs.new('SvStringsSocket', "EdgeSources")
        self.outputs.new('SvStringsSocket', "FacesMask")
        self.outputs.new('SvStringsSocket', "FaceSources")

        self.update_mode(context)

    def make_solid(self, solids):
        if self.generate_masks:
            return self.make_solid_general(solids)
        else:
            solid = self.make_solid_simple(solids)
            return SvBoolResult(solid)

    def make_solid_simple(self, solids):
        base = solids[0].copy()
        rest = solids[1:]
        if self.selected_mode == 'UNION':
            solid = base.fuse(rest)
        elif self.selected_mode == 'ITX':
            solid = base.common(rest)
        elif self.selected_mode == 'DIFF':
            solid = base.cut(rest)
        else:
            raise Exception("Unknown mode")
        do_refine = self.refine_solid and self.selected_mode in {'UNION'}
        if do_refine:
            solid = solid.removeSplitter()
        return solid

    def make_solid_general(self, solids):
        do_refine = self.refine_solid and self.selected_mode in {'UNION'}

        for i in range(len(solids)):
            if not isinstance(solids[i], Part.Solid):
                solids[i] = Part.makeSolid(solids[i])

        fused = SvGeneralFuse(solids)
        if self.selected_mode == 'UNION':
            solid = fused.get_union_all(refine=do_refine)
        elif self.selected_mode == 'ITX':
            solid = fused.get_intersect_all(refine=do_refine)
        elif self.selected_mode == 'DIFF':
            solid = fused.get_clean_part_by_idx(0, refine=do_refine)
        else:
            raise Exception("Unknown mode")

        edge_mask = []
        edge_map = []
        face_mask = []
        face_map = []

        if solid is not None:
            for edge in solid.Edges:
                srcs = fused.get_edge_source_idxs(edge)
                edge_map.append(list(srcs))
                is_new = len(srcs) > 1
                edge_mask.append(is_new)

            for face in solid.Faces:
                srcs = fused.get_face_source_idxs(face)
                face_map.append(list(srcs))
                is_new = len(srcs) > 1
                face_mask.append(is_new)

        return SvBoolResult(solid, edge_mask, edge_map, face_mask, face_map)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids_out = []
        edge_masks_out = []
        edge_srcs_out = []
        face_masks_out = []
        face_srcs_out = []
        if self.nest_objs:
            solids_in = self.inputs['Solids'].sv_get()
            #level = get_data_nesting_level(solids_in, data_types=(Part.Shape,))
            solids_in = ensure_nesting_level(solids_in, 2, data_types=(Part.Shape,))

            for solids in solids_in:
                result = self.make_solid(solids)
                solids_out.append(result.solid)
                edge_masks_out.append(result.edge_mask)
                edge_srcs_out.append(result.edge_map)
                face_masks_out.append(result.face_mask)
                face_srcs_out.append(result.face_map)

        else:
            solids_a_in = self.inputs['Solid A'].sv_get()
            solids_b_in = self.inputs['Solid B'].sv_get()
            level_a = get_data_nesting_level(solids_a_in, data_types=(Part.Shape,))
            level_b = get_data_nesting_level(solids_b_in, data_types=(Part.Shape,))
            solids_a_in = ensure_nesting_level(solids_a_in, 2, data_types=(Part.Shape,))
            solids_b_in = ensure_nesting_level(solids_b_in, 2, data_types=(Part.Shape,))
            level = max(level_a, level_b)

            for params in zip_long_repeat(solids_a_in, solids_b_in):
                new_solids = []
                new_edge_masks = []
                new_edge_srcs = []
                new_face_masks = []
                new_face_srcs = []
                for solid_a, solid_b in zip_long_repeat(*params):
                    result = self.make_solid([solid_a, solid_b])
                    new_solids.append(result.solid)
                    new_edge_masks.append(result.edge_mask)
                    new_edge_srcs.append(result.edge_map)
                    new_face_masks.append(result.face_mask)
                    new_face_srcs.append(result.face_map)
                if level == 1:
                    solids_out.extend(new_solids)
                    edge_masks_out.extend(new_edge_masks)
                    edge_srcs_out.extend(new_edge_srcs)
                    face_masks_out.extend(new_face_masks)
                    face_srcs_out.extend(new_face_srcs)
                else:
                    solids_out.append(new_solids)
                    edge_masks_out.append(new_edge_masks)
                    edge_srcs_out.append(new_edge_srcs)
                    face_masks_out.append(new_face_masks)
                    face_srcs_out.append(new_face_srcs)

        self.outputs['Solid'].sv_set(solids_out)
        if 'EdgesMask' in self.outputs:
            self.outputs['EdgesMask'].sv_set(edge_masks_out)
        if 'EdgeSources' in self.outputs:
            self.outputs['EdgeSources'].sv_set(edge_srcs_out)
        if 'FacesMask' in self.outputs:
            self.outputs['FacesMask'].sv_set(face_masks_out)
        if 'FaceSources' in self.outputs:
            self.outputs['FaceSources'].sv_set(face_srcs_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidBooleanNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidBooleanNode)
