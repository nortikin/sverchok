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
    from sverchok.utils.solid import SvGeneralFuse, SvBoolResult

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

    set_modes = [
            ('EQ', "Exact", "Index sets are specified exactly", 0),
            ('SUB', "Subsets", "Index sets are specified by their subsets", 1)
        ]
    
    set_mode : EnumProperty(
        name = "Sets mode",
        items = set_modes,
        default = 'EQ',
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text='Specify:')
        layout.prop(self, 'set_mode', text='')
        layout.prop(self, 'merge_result')
        if self.merge_result:
            layout.prop(self, "refine_solid")

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solids")
        self.inputs.new('SvStringsSocket', "Include")
        self.inputs.new('SvStringsSocket', "Exclude")
        self.outputs.new('SvSolidSocket', "Solid")
        self.outputs.new('SvStringsSocket', "SolidSources")
        self.outputs.new('SvStringsSocket', "EdgesMask")
        self.outputs.new('SvStringsSocket', "EdgeSources")
        self.outputs.new('SvStringsSocket', "FacesMask")
        self.outputs.new('SvStringsSocket', "FaceSources")

    def _check_subset(self, subset, srcs):
        if self.set_mode == 'EQ':
            return set(subset) == srcs
        else:
            return set(subset).issubset(srcs)

    def _process(self, solids, include_idxs, exclude_idxs):
        fused = SvGeneralFuse(solids)
        good = []
        for part in fused.get_all_parts():
            src_idxs = fused.get_part_source_idxs(part)

            if include_idxs is not None:
                include = False
                for idxs in include_idxs:
                    if self._check_subset(idxs, src_idxs):
                        include = True
                        break
            else:
                include = True

            exclude = False
            if exclude_idxs is not None:
                for idxs in exclude_idxs:
                    if self._check_subset(idxs, src_idxs):
                        exclude = True
                        break

            if include and not exclude:
                good.append(part)

        if self.merge_result:
            if not good:
                solid_result = None
            elif len(good) == 1:
                solid_result = good[0]
            else:
                solid = good[0].fuse(good[1:])
                if self.refine_solid:
                    solid = solid.removeSplitter()
                solid_result = solid
        else:
            solid_result = good

        # wrap for generalization
        if self.merge_result:
            result_solid_list = [solid_result]
        else:
            result_solid_list = solid_result

        result = SvBoolResult(solid_result)

        for part in good:
            solid_map = []
            srcs = fused.get_part_source_idxs(part)
            solid_map.append(list(srcs))
            result.solid_map.append(solid_map)

        for solid in result_solid_list:
            if solid is None:
                continue

            edge_mask = []
            edge_map = []
            face_mask = []
            face_map = []

            for edge in solid.Edges:
                srcs = fused.get_edge_source_idxs(edge)
                edge_map.append(list(srcs))
                is_new = len(srcs) > 1
                edge_mask.append(is_new)

            result.edge_map.append(edge_map)
            result.edge_mask.append(edge_mask)

            for face in solid.Faces:
                srcs = fused.get_face_source_idxs(face)
                face_map.append(list(srcs))
                is_new = len(srcs) > 1
                face_mask.append(is_new)

            result.face_map.append(face_map)
            result.face_mask.append(face_mask)

        # unwrap if we've wrapped earlier
        if self.merge_result:
            # we actually have only one item in result_solid_list
            result.edge_map = result.edge_map[0]
            result.edge_mask = result.edge_mask[0]
            result.face_map = result.face_map[0]
            result.face_mask = result.face_mask[0]

            # merged body has all sources from all it's parts
            solid_map_set = set()
            for part_maps in result.solid_map:
                for part_map in part_maps:
                    solid_map_set.update(set(part_map))
            result.solid_map = list(solid_map_set)

        return result

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids_in = self.inputs['Solids'].sv_get()
        input_level = get_data_nesting_level(solids_in, data_types=(Part.Shape,))
        solids_in = ensure_nesting_level(solids_in, 2, data_types=(Part.Shape,))
        include_in = self.inputs['Include'].sv_get(default=[None])
        if self.inputs['Include'].is_linked:
            include_in = ensure_nesting_level(include_in, 3)
        exclude_in = self.inputs['Exclude'].sv_get(default=[None])
        if self.inputs['Exclude'].is_linked:
            exclude_in = ensure_nesting_level(exclude_in, 3)

        solids_out = []
        solid_srcs_out = []
        edge_masks_out = []
        edge_srcs_out = []
        face_masks_out = []
        face_srcs_out = []

        if self.merge_result:
            out_level = 1
        else:
            out_level = input_level

        print(f"Merge {self.merge_result}, in_level {input_level} => out {out_level}")

        for solids, include_idxs, exclude_idxs in zip_long_repeat(solids_in, include_in, exclude_in):
            result = self._process(solids, include_idxs, exclude_idxs)
            if out_level == 1:
                if self.merge_result:
                    solids_out.append(result.solid)
                else:
                    solids_out.extend(result.solid)
                solid_srcs_out.extend(result.solid_map)
                edge_masks_out.extend(result.edge_mask)
                edge_srcs_out.extend(result.edge_map)
                face_masks_out.extend(result.face_mask)
                face_srcs_out.extend(result.face_map)
            else:
                solids_out.append(result.solid)
                solid_srcs_out.append(result.solid_map)
                edge_masks_out.append(result.edge_mask)
                edge_srcs_out.append(result.edge_map)
                face_masks_out.append(result.face_mask)
                face_srcs_out.append(result.face_map)

        self.outputs['Solid'].sv_set(solids_out)
        self.outputs['SolidSources'].sv_set(solid_srcs_out)
        self.outputs['EdgesMask'].sv_set(edge_masks_out)
        self.outputs['EdgeSources'].sv_set(edge_srcs_out)
        self.outputs['FacesMask'].sv_set(face_masks_out)
        self.outputs['FaceSources'].sv_set(face_srcs_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidGeneralFuseNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidGeneralFuseNode)

