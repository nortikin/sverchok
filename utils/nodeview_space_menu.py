# -*- coding: utf-8 -*-
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

''' borrows heavily from insights provided by Dynamic Space Bar! '''

import bpy
from bpy.props import (
    StringProperty,
)

'''
        # layout.menu("INFO_MT_mesh_add", text="Add Mesh",
        #             icon='OUTLINER_OB_MESH')

        # layout.operator_menu_enum("object.metaball_add", "type",
        #                           icon='OUTLINER_OB_META')
        # layout.operator("object.text_add", text="Add Text",
        #                 icon='OUTLINER_OB_FONT')
'''


def layout_draw_categories(layout, node_details):
    add_n_grab = 'node.sverchok_addngrab'
    add_node = layout.operator
    for node_info in node_details:
        num_items = len(node_info)
        if num_items == 3:
            bl_idname, shortname, icon = node_info
            add_node(add_n_grab, text=shortname, icon=icon).node_name = bl_idname
        elif num_items == 2:
            bl_idname, shortname = node_info
            add_node(add_n_grab, text=shortname).node_name = bl_idname
        else:
            continue


class SvNodeAddnGrab(bpy.types.Operator):
    ''' ops to add and grab '''

    bl_idname = "node.sverchok_addngrab"
    bl_label = "Sverchok Node AddnGrab"
    bl_options = {'REGISTER', 'UNDO'}

    node_name = StringProperty(default='')

    def execute(self, context):

        # something wrong with transform still, some context?
        bpy.ops.node.add_node(type=self.node_name, use_transform=True)

        # this is equivalent non ops code..
        # tree_name = context.space_data.node_tree.name
        # ng = bpy.data.node_groups[tree_name]
        # n = ng.nodes.new(self.node_name)
        # n.select = True

        print('adding -- {}'.format(self.node_name))
        return {'FINISHED'}


class NODEVIEW_MT_Dynamic_Menu(bpy.types.Menu):
    bl_label = "Sverchok Nodes"

    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        return (tree_type == 'SverchCustomTreeType')

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        # bpy.ops.node.add_search(use_transform=True)
        # layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
        s = layout.operator("node.add_search", text="Search", icon='VIEWZOOM')
        s.use_transform = True

        layout.separator()
        layout.menu("NODEVIEW_MT_AddGenerators", icon='OBJECT_DATAMODE')
        layout.menu("NODEVIEW_MT_AddTransforms", icon='MANIPUL')
        layout.menu("NODEVIEW_MT_AddAnalyzers", icon='BORDERMOVE')
        layout.menu("NODEVIEW_MT_AddModifiers", icon='MODIFIER')
        layout.separator()
        layout.menu("NODEVIEW_MT_AddNumber")
        layout.menu("NODEVIEW_MT_AddVector")
        layout.menu("NODEVIEW_MT_AddMatrix")
        layout.menu("NODEVIEW_MT_AddConditionals")
        layout.menu("NODEVIEW_MT_AddListOps")
        layout.separator()
        layout.menu("NODEVIEW_MT_AddBasicViz")
        layout.menu("NODEVIEW_MT_AddBasicData")
        layout.menu("NODEVIEW_MT_AddBasicDebug")
        layout.separator()
        layout.menu("NODEVIEW_MT_AddBetas", icon='OUTLINER_DATA_POSE')
        layout.menu("NODEVIEW_MT_AddAlphas", icon='ERROR')


class NODEVIEW_MT_AddGenerators(bpy.types.Menu):
    bl_label = "Add Generators"

    def draw(self, context):
        layout = self.layout

        # not sure if we need this or something else...
        layout.operator_context = 'INVOKE_REGION_WIN'

        # this can be in a for loop
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ["LineNode",            "Line",                  "GRIP"],
            ["PlaneNode",           "Plane",           "MESH_PLANE"],
            ["SvBoxNode",           "Box",              "MESH_CUBE"],
            ["SvCircleNode",        "Circle",         "MESH_CIRCLE"],
            ["CylinderNode",        "Cylinder",     "MESH_CYLINDER"],
            ["SphereNode",          "Sphere",       "MESH_UVSPHERE"],
            ['BasicSplineNode',     "2pt Spline",  "CURVE_BEZCURVE"],
            ["svBasicArcNode",      "3pt Arc",        "SPHERECURVE"]
        ]
        layout_draw_categories(layout, node_details)
        layout.menu("NODEVIEW_MT_AddGeneratorsExt", icon='PLUGIN')


class NODEVIEW_MT_AddGeneratorsExt(bpy.types.Menu):
    bl_label = "Extended generators"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ["SvBoxRoundedNode",    "Rounded Box"],
            ["HilbertNode",         "Hilbert"],
            ["Hilbert3dNode",       "Hilbert3d"],
            ["HilbertImageNode",    "Hilbert image"],
            ["ImageNode",           "Image",                "FILE_IMAGE"],
            ["SvFormulaShapeNode",  "Formula shape",               "IPO"],
            ["SvProfileNode",       "ProfileParametric"],
            ["SvScriptNode",        "Scripted Node",     "SCRIPTPLUGINS"]
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddTransforms(bpy.types.Menu):
    bl_label = "Transforms (Vec, Mat)"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ["SvRotationNode",      "Rotation",    "MAN_ROT"],
            ["SvScaleNode",         "Scale",       "MAN_SCALE"],
            ["VectorMoveNode",      "Vector Move", "MAN_TRANS"],
            ["SvMirrorNode",        "Mirror",      "MOD_MIRROR"],
            ["SvMatrixEulerNode",   "Matrix Euler"],
            ["MatrixShearNode",     "Matrix Shear"],
            ["MatrixApplyNode",     "Matrix Apply"],
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddModifiers(bpy.types.Menu):
    bl_label = "Modifiers (Make, Change)"

    def draw(self, context):
        layout = self.layout
        layout.menu("NODEVIEW_MT_AddModifierChange")
        layout.menu("NODEVIEW_MT_AddModifierMake")


class NODEVIEW_MT_AddListOps(bpy.types.Menu):
    bl_label = "List operations"

    def draw(self, context):
        layout = self.layout
        layout.menu("NODEVIEW_MT_AddListmain")
        layout.menu("NODEVIEW_MT_AddListstruct")

        node_details = [
            ['MaskListNode', 'List Mask (out)'],
            ['SvMaskJoinNode', 'List Mask Join (in)'],
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddBetas(bpy.types.Menu):
    bl_label = "Beta Nodes"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            # for testing convenience,
            ["ViewerNode2",         "Viewer draw MK2", 'RETOPO'],
            ["SvOffsetNode",        "Offset"],
            ["SvEmptyOutNode",      "Empty out", "OUTLINER_OB_EMPTY"],
            # need to be completely reviewed
            ["SvListDecomposeNode", "List Decompose"],
            # should be removed...
            ["SvReRouteNode",       "Reroute Point"],
            ["SvInstancerNode",     "mesh instancer"],
            ["SvWafelNode",         "Wafel"],
            ["SvVertexGroupNode",   "Vertex group"],
            ["SvRayCastNode",       "Raycast"]
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddAlphas(bpy.types.Menu):
    bl_label = "Alpha Nodes"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ["SvObjRemoteNode",       "Scene Objects"],
            ["SvImageComponentsNode", "Image Decompose",  "GROUP_VCOL"],
            ["SvJoinTrianglesNode",   "Join Triangles"],
            ["EvalKnievalNode",       "Eval Knieval",   'FORCE_VORTEX']
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddAnalyzers(bpy.types.Menu):
    bl_label = "Analyzers"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ["SvBBoxNode",          "Bounding box"],
            ["SvVolumeNode",        "Volume"],
            ["AreaNode",            "Area"],
            ["DistancePPNode",      "Distance"],
            ["CentersPolsNode",     "Centers Polygons"],
            ["VectorNormalNode",    "Vertex Normal"],
            # proximity anaylyses.
            ["SvKDTreeNode",        "KDT Closest Verts"],
            ["SvKDTreeEdgesNode",   "KDT Closest Edges"]
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddBasicViz(bpy.types.Menu):
    bl_label = "Basic Viz"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ['ViewerNode', 'Viewer draw'],
            ['ViewerNode_text', 'Viewer text'],
            ['IndexViewerNode', 'Viewer INDX'],
            ['Sv3DviewPropsNode', '3dview Props'],
            ['BmeshViewerNode', 'Viewer BMesh'],
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddBasicData(bpy.types.Menu):
    bl_label = "Basic Data"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ['ObjectsNode', 'Objects in'],
            ['SvTextInNode', 'Text in'],
            ['SvTextOutNode', 'Text out'],
            ['WifiInNode', 'Wifi in'],
            ['WifiOutNode', 'Wifi out'],
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddBasicDebug(bpy.types.Menu):
    bl_label = "Basic Debug"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ['SvFrameInfoNode', 'Frame info'],
            ['NoteNode', 'Note'],
            ['GTextNode', 'GText'],
            ['SvDebugPrintNode', 'Debug print'],
            ['SvStethoscopeNode', 'Stethoscope'],
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddListmain(bpy.types.Menu):
    bl_label = "List main"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ['ListJoinNode', 'List Join'],
            ['ZipNode', 'List Zip'],
            ['ListLevelsNode', 'List Del Levels'],
            ['ListLengthNode', 'List Length'],
            ['ListSumNode', 'List Sum'],
            ['ListMatchNode', 'List Match'],
            ['ListFuncNode', 'List Math'],
            ['ConverterNode', 'SocketConvert'],
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddListstruct(bpy.types.Menu):
    bl_label = "List struct"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ['ShiftNode', 'List Shift'],
            ['ListRepeaterNode', 'List Repeater'],
            ['ListSliceNode', 'List Slice'],
            ['SvListSplitNode', 'List Split'],
            ['ListFLNode', 'List First&Last'],
            ['ListItem2Node', 'List Item'],
            ['ListReverseNode', 'List Reverse'],
            ['ListShuffleNode', 'List Shuffle'],
            ['ListSortNode', 'List Sort'],
            ['ListFlipNode', 'List Flip'],
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddNumber(bpy.types.Menu):
    bl_label = "Number"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ['GenListRangeIntNode', 'Range Int'],
            ['SvGenFloatRange', 'Range Float'],
            ['SvListInputNode', 'List Input'],
            ['RandomNode', 'Random', 'RNDCURVE'],
            ['FloatNode', 'Float'],
            ['IntegerNode', 'Int'],
            ['Float2IntNode', 'Float 2 Int'],
            ['Formula2Node', 'Formula'],
            ['ScalarMathNode', 'Math'],
            ['SvMapRangeNode', 'Map Range'],
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddVector(bpy.types.Menu):
    bl_label = "Vector"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ['RandomVectorNode', 'Random Vector', 'RNDCURVE'],
            ['GenVectorsNode', 'Vector in'],
            ['VectorsOutNode', 'Vector out'],
            ['VectorMathNode', 'Vector Math'],
            ['VectorDropNode', 'Vector Drop'],
            ['VertsDelDoublesNode', 'Vector X Doubles'],
            ['EvaluateLineNode', 'Vector Evaluate'],
            ['SvInterpolationNode', 'Vector Interpolation'],
            ['SvVertSortNode', 'Vector Sort', 'SORTSIZE'],
            ['SvNoiseNode', 'Vector Noise', 'FORCE_TURBULENCE'],
            ['svAxisInputNode', 'Vector X | Y | Z', 'MANIPUL'],
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddMatrix(bpy.types.Menu):
    bl_label = "Matrix"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ['MatrixGenNode', 'Matrix in'],
            ['MatrixOutNode', 'Matrix out'],
            ['SvMatrixValueIn', 'Matrix Input'],
            ['MatrixDeformNode', 'Matrix Deform'],
            ['MatrixInterpolationNode', 'Matrix Interpolation'],
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddModifierChange(bpy.types.Menu):
    bl_label = "Modifier Change"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ['PolygonBoomNode', 'Polygon Boom'],
            ['Pols2EdgsNode', 'Polygons to Edges'],
            ['SvMeshJoinNode', 'Mesh Join'],
            ['SvRemoveDoublesNode', 'Remove Doubles'],
            ['SvDeleteLooseNode', 'Delete Loose'],
            ['SvSeparateMeshNode', 'Separate Loose Parts'],
            ['SvVertMaskNode', 'Mask Vertices'],
            ['SvFillsHoleNode', 'Fill Holes'],
            ['SvIntersectEdgesNode', 'Intersect Edges'],
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddModifierMake(bpy.types.Menu):
    bl_label = "Modifier Make"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ['LineConnectNode', 'UV Connection'],
            ['AdaptivePolsNode', 'Adaptive Polygons'],
            ['SvAdaptiveEdgeNode', 'Adaptive Edges'],
            ['CrossSectionNode', 'Cross Section'],
            ['SvBisectNode', 'Bisect'],
            ['SvSolidifyNode', 'Solidify'],
            ['SvWireframeNode', 'Wireframe'],
            ['DelaunayTriangulation2DNode', 'Delaunay 2D '],
            ['Voronoi2DNode', 'Voronoi 2D'],
            ['SvConvexHullNode', 'Convex Hull'],
            ['SvLatheNode', 'Lathe', 'MOD_SCREW'],
        ]
        layout_draw_categories(layout, node_details)


class NODEVIEW_MT_AddConditionals(bpy.types.Menu):
    bl_label = "Conditionals"

    def draw(self, context):
        layout = self.layout
        node_details = [
            # bl_idname, shortname, <icon> (optional)
            ['SvLogicNode', 'Logic'],
            ['SvSwitchNode', 'Switch'],
            ['SvNeuroElman1LNode', 'Neuro'],
        ]
        layout_draw_categories(layout, node_details)


classes = [
    SvNodeAddnGrab,
    NODEVIEW_MT_Dynamic_Menu,
    NODEVIEW_MT_AddGenerators,
    NODEVIEW_MT_AddGeneratorsExt,
    NODEVIEW_MT_AddTransforms,
    NODEVIEW_MT_AddModifiers,
    NODEVIEW_MT_AddAnalyzers,
    NODEVIEW_MT_AddBasicViz,
    NODEVIEW_MT_AddBasicData,
    NODEVIEW_MT_AddBasicDebug,
    NODEVIEW_MT_AddListmain,
    NODEVIEW_MT_AddListstruct,
    NODEVIEW_MT_AddNumber,
    NODEVIEW_MT_AddVector,
    NODEVIEW_MT_AddMatrix,
    NODEVIEW_MT_AddListOps,
    NODEVIEW_MT_AddModifierChange,
    NODEVIEW_MT_AddModifierMake,
    NODEVIEW_MT_AddConditionals,
    NODEVIEW_MT_AddBetas,
    NODEVIEW_MT_AddAlphas,
]


def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi = km.keymap_items.new('wm.call_menu', 'SPACE', 'PRESS')
        kmi.properties.name = "NODEVIEW_MT_Dynamic_Menu"


def unregister():
    for class_name in classes:
        bpy.utils.unregister_class(class_name)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Node Editor']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu':
                if kmi.properties.name == "NODEVIEW_MT_Dynamic_Menu":
                    km.keymap_items.remove(kmi)
                    break
