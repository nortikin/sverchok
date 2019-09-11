# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from sverchok.menu import node_add_operators
from sverchok.utils import get_node_class_reference

short_menu = {
    "input": "SvNumberNode SvGenFloatRange GenListRangeIntNode SvRndNumGen GenVectorsNode SvHomogenousVectorField SvListInputNode".split(),
    "gen primitive": "SvLineNodeMK3 SvPlaneNodeMK2 SvCircleNode SvBoxNode SvSphere SvCylinderNodeMK2 SvRegularSolid".split(),
    "gen complex": "SvRoundedCube BasicSplineNode svBasicArcNode SvTorusNode SvProfileNodeMK2".split(), 
    "effect": "SvInsetSpecial SvApplyNoise SvApplyRandom SvSmooth".split(),
    "topology": "SvSeparate SvUVConnection SvMergeMesh SvCSGBooleanNodeMK2".split(),
    "list manipulation": "SvListStruct SvListModifierNode ListFuncNode SvListDecomposeNode ZipNode ListLevelsNode".split(),
    "scripting": "SvScriptNodeLite SvSNFunctorB SvExecNodeMod".split(),
    "analyze": "SvPointInside SvBBoxNode SvVolumeNode SvAreaNode DistancePPNode SvDistancePointLineNode SvDistancePointPlaneNode SvDistancetLineLineNode".split(),
    "output": "SvVDExperimental SvBmeshViewerNodeV28 SvCurveViewerNodeV28 SvPolylineViewerNodeV28 --- SvStethoscopeNodeMK2 SvIDXViewer28".split()
}


class SvPopulateLiteMenu(bpy.types.Operator):
    bl_label = "Populate Lite Menu"
    bl_idname = "node.sv_populate_lite_menu"

    def execute(self, context):
        menu_headers = context.space_data.node_tree.sv_lite_menu_headers
        menu_headers.clear()
        for k in short_menu.keys():
            item = menu_headers.add()
            item.heading = k
        return {'FINISHED'}


class SvLiteMenuItems(bpy.types.PropertyGroup):
    heading: bpy.props.StringProperty(name="heading to show", default="")


class NODEVIEW_MT_SvLiteSubmenu(bpy.types.Menu):
    bl_label = "Sv Nodes submenu"

    def draw(self, context):
        layout = self.layout
        for item in short_menu[context.sv_menu_key.heading]:
            if item == "---":
                layout.row().separator()
                continue
            
            node_add_operator = node_add_operators.get(item.lower())
            if node_add_operator:

                node_ref = get_node_class_reference(item)

                if not node_ref:
                    print('000000', item, 'not found')

                layout.operator(node_add_operator.bl_idname, text=node_ref.bl_label)
            else:
                layout.row().label(text=item)



class NODEVIEW_MT_SvLiteMenu(bpy.types.Menu):
    bl_label = "Sv Nodes"

    def draw(self, context):
        layout = self.layout
        for item in context.space_data.node_tree.sv_lite_menu_headers:
            row = layout.row()
            row.context_pointer_set("sv_menu_key", item)
            row.menu("NODEVIEW_MT_SvLiteSubmenu", text=item.heading)

def register():
    bpy.utils.register_class(SvPopulateLiteMenu)
    bpy.utils.register_class(SvLiteMenuItems)
    bpy.types.NodeTree.sv_lite_menu_headers = bpy.props.CollectionProperty(type=SvLiteMenuItems)
    bpy.utils.register_class(NODEVIEW_MT_SvLiteSubmenu) 
    bpy.utils.register_class(NODEVIEW_MT_SvLiteMenu)

def unregister():
    bpy.utils.unregister_class(NODEVIEW_MT_SvLiteSubmenu)
    bpy.utils.unregister_class(NODEVIEW_MT_SvLiteMenu)
    bpy.utils.unregister_class(SvLiteMenuItems)
    bpy.utils.unregister_class(SvPopulateLiteMenu)
    del bpy.types.NodeTree.sv_lite_menu_headers
