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

import bpy
from bpy.props import StringProperty, BoolProperty, FloatVectorProperty
from bpy.types import NodeTree, NodeSocket, NodeSocketStandard
from nodeitems_utils import NodeCategory, NodeItem

import data_structure
from data_structure import (SvGetSocketInfo, SvGetSocket,
                            SvSetSocket,  updateNode)
from core.update_system import (build_update_list, sverchok_update,
                                get_update_lists)
from core import upgrade_nodes


class SvColors(bpy.types.PropertyGroup):
    """ Class for colors CollectionProperty """
    color = FloatVectorProperty(
        name="svcolor", description="sverchok color",
        default=(0.055, 0.312, 0.5), min=0, max=1,
        step=1, precision=3, subtype='COLOR_GAMMA', size=3,
        update=updateNode)


class MatrixSocket(NodeSocket):
    '''4x4 matrix Socket_type'''
    # ref: http://urchn.org/post/nodal-transform-experiment
    bl_idname = "MatrixSocket"
    bl_label = "Matrix Socket"
    prop_name = StringProperty(default='')

    # beta interface only use for debug, might change
    def sv_get(self, default=None, deepcopy=False):
        if self.links and not self.is_output:
            return SvGetSocket(self, deepcopy)
        else:
            return default

    def sv_set(self, data):
        SvSetSocket(self, data)

    def draw(self, context, layout, node, text):
    #    if not self.is_output and not self.is_linked and self.prop_name:
    #        layout.prop(node,self.prop_name,expand=False)
        if self.is_linked:
            layout.label(text + '. ' + SvGetSocketInfo(self))
        else:
            layout.label(text)

    def draw_color(self, context, node):
        '''if self.is_linked:
            return(.8,.3,.75,1.0)
        else: '''
        return(.2, .8, .8, 1.0)

'''
class ObjectSocket(NodeSocket):
        'ObjectSocket'
        bl_idname = "ObjectSocket"
        bl_label = "Object Socket"

        ObjectProperty = StringProperty(name= "ObjectProperty", update=updateSlot)

        def draw(self, context, layout, node, text):
            if self.is_linked:
                layout.label(text)
            else:
                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(self, 'ObjectProperty', text=text)

        def draw_color(self, context, node):
            return(0.8,0.8,0.2,1.0)
'''


class VerticesSocket(NodeSocketStandard):
    '''String Vertices - one string'''
    bl_idname = "VerticesSocket"
    bl_label = "Vertices Socket"
    prop_name = StringProperty(default='')

    # beta interface only use for debug, might change
    def sv_get(self, default=None, deepcopy=False):
        if self.links and not self.is_output:
            return SvGetSocket(self, deepcopy)
        else:
            return default

    def sv_set(self, data):
        SvSetSocket(self, data)

    def draw(self, context, layout, node, text):
    #    if not self.is_output and not self.is_linked and self.prop_name:
    #        layout.prop(node,self.prop_name,expand=False)
        if self.is_linked:
            layout.label(text + '. ' + SvGetSocketInfo(self))
        else:
            layout.label(text)

    def draw_color(self, context, node):
        return(0.9, 0.6, 0.2, 1.0)


class StringsSocket(NodeSocketStandard):
    '''String any type - one string'''
    bl_idname = "StringsSocket"
    bl_label = "Strings Socket"

    prop_name = StringProperty(default='')

    def sv_get(self, default=None, deepcopy=False):
        if self.links and not self.is_output:
            out = SvGetSocket(self, deepcopy)
            if out:
                return out
        if self.prop_name:
            return [[getattr(self.node, self.prop_name)]]
        return default

    def sv_set(self, data):
        SvSetSocket(self, data)

    def draw(self, context, layout, node, text):
        if self.prop_name:
            if self.is_output:
                t = text
                print('Warning output socket:', self.name, 'in node:', node.name, 'has property attached')
            else:
                prop = node.rna_type.properties.get(self.prop_name, None)
                t = prop.name if prop else text
        else:
            t = text

        if not self.is_output and not self.is_linked and self.prop_name:
            layout.prop(node, self.prop_name)
        elif self.is_linked:
            layout.label(t + '. ' + SvGetSocketInfo(self))
        else:
            layout.label(t)

    def draw_color(self, context, node):
        return(0.6, 1.0, 0.6, 1.0)


class SverchCustomTree(NodeTree):
    ''' Sverchok - architectural node programming of geometry in low level '''
    bl_idname = 'SverchCustomTreeType'
    bl_label = 'Sverchok Node Tree'
    bl_icon = 'RNA'

    def turn_off_ng(self, context):
        sverchok_update(tree=self)
        #should turn off tree. for now it does by updating it

    sv_animate = BoolProperty(name="Animate", default=True)
    sv_show = BoolProperty(name="Show", default=True, update=turn_off_ng)
    sv_bake = BoolProperty(name="Bake", default=True)
    sv_user_colors = StringProperty(default="")

    # get update list for debug info, tuple (fulllist,dictofpartiallists)
    def get_update_lists(self):
        return get_update_lists(self)

    def update(self):
        '''
        Rebuild and update the Sverchok node tree, used at editor changes
        '''
        # startup safety net, a lot things will just break if this isn't
        # stopped...
        try:
            l = bpy.data.node_groups[self.id_data.name]
        except:
            return

        build_update_list(tree=self)
        sverchok_update(tree=self)

    def update_ani(self):
        """
        Updates the Sverchok node tree if animation layers show true. For animation callback
        """
        if self.sv_animate:
            sverchok_update(tree=self)


class SverchCustomTreeNode:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'SverchCustomTreeType'


class SverchNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'SverchCustomTreeType'


def make_categories():
    node_categories = [
        SverchNodeCategory("SVERCHOK_B", "Basic", items=[
            # basic nodes
            NodeItem("ObjectsNode", label="Objects in"),
            NodeItem("BmeshViewerNode", label="BMesh View"),
            # NodeItem("BakeryNode", label="Bake all"),
            NodeItem("ViewerNode", label="Viewer draw"),
            NodeItem("ViewerNode_text", label="Viewer text"),
            NodeItem("IndexViewerNode", label="Viewer INDX"),
            NodeItem("SvTextInNode",  label="Text in"),
            NodeItem("SvTextOutNode",  label="Text out"),
            NodeItem("WifiInNode", label="Wifi in"),
            NodeItem("WifiOutNode", label="Wifi out"),
            # NodeItem("Test1Node", label="Test1"),
            # NodeItem("Test2Node", label="Test2"),
            NodeItem("SvFrameInfoNode", label="Frame info"),
            NodeItem("NoteNode", label="Note"),
            NodeItem("GTextNode", label="GText"),
            NodeItem("ToolsNode", label="Update Button"),
            NodeItem("SvDebugPrintNode", label="Debug print"),
            ]),
        SverchNodeCategory("SVERCHOK_L", "List", items=[
            # lists nodes
            NodeItem("ListLevelsNode", label="List Del Levels"),
            NodeItem("ListJoinNode", label="List Join"),
            NodeItem("ZipNode", label="List Zip"),
            NodeItem("ShiftNode", label="List Shift"),
            NodeItem("ListSliceNode", label="List Slice"),
            NodeItem("SvListSplitNode", label="List Split"),
            NodeItem("ListReverseNode", label="List Reverse"),
            NodeItem("ListLengthNode", label="List Length"),
            NodeItem("ListSumNode", label="List Sum"),
            NodeItem("ListFLNode", label="List First&Last"),
            NodeItem("ListItem2Node", label="List Item"),
            NodeItem("ListRepeaterNode", label="List Repeater"),
            NodeItem("ListFuncNode", label="List Math"),
            NodeItem("ListFlipNode", label="List Flip"),
            NodeItem("MaskListNode", label="List Mask (out)"),
            NodeItem("SvMaskJoinNode", label="List Mask Join (in)"),
            NodeItem("ListSortNode", label="List Sort"),
            NodeItem("ListShuffleNode", label="List Shuffle"),
            NodeItem("ListMatchNode", label="List Match"),
            NodeItem("ConverterNode", label="SocketConvert"),
            ]),
        SverchNodeCategory("SVERCHOK_N", "Number", items=[
            # numbers, formula nodes
            #NodeItem("GenSeriesNode", label="Series float"),
            #NodeItem("GenRangeNode", label="Range float"),
            NodeItem("GenListRangeIntNode", label="Range Int"),
            NodeItem("SvGenFloatRange", label="Range Float"),
            NodeItem("SvListInputNode", label="List Input"),
            NodeItem("RandomNode", label="Random"),
            NodeItem("FloatNode", label="Float"),
            NodeItem("IntegerNode", label="Int"),
            NodeItem("Float2IntNode", label="Float 2 Int"),
            # NodeItem("FormulaNode", label="Formula"),
            NodeItem("Formula2Node", label="Formula"),  # for newbies this is not predictable why "Formula2" renamed
            NodeItem("ScalarMathNode", label="Math"),
            NodeItem("SvMapRangeNode", label="Map Range"),
            ]),
        SverchNodeCategory("SVERCHOK_G", "Generator", items=[
            # objects, new elements, line, plane
            NodeItem("LineNode", label="Line"),
            NodeItem("PlaneNode", label="Plane"),
            NodeItem("SvBoxNode", label="Box"),
            NodeItem("SvCircleNode", label="Circle"),
            NodeItem("CylinderNode", label="Cylinder"),
            NodeItem("SphereNode", label="Sphere"),
            NodeItem("HilbertNode", label="Hilbert"),
            NodeItem("HilbertImageNode", label="Hilbert image"),
            NodeItem("ImageNode", label="Image"),
            NodeItem("RandomVectorNode", label="Random Vector"),
            NodeItem("SvFormulaShapeNode", label="Formula shape"),
            NodeItem("SvScriptNode", label="Scripted Node"),
            ]),
        SverchNodeCategory("SVERCHOK_V", "Vector", items=[
            # Vector nodes
            NodeItem("GenVectorsNode", label="Vector in"),
            NodeItem("VectorsOutNode", label="Vector out"),
            NodeItem("VectorMoveNode", label="Vector Move"),
            NodeItem("VectorMathNode", label="Vector Math"),
            NodeItem("VectorDropNode", label="Vector Drop"),
            NodeItem("VertsDelDoublesNode", label="Vector X Doubles"),
            NodeItem("EvaluateLineNode", label="Vector Evaluate"),
            NodeItem("SvInterpolationNode", label="Vector Interpolation"),
            NodeItem("SvVertSortNode", label="Vector Sort"),
            NodeItem("SvNoiseNode", label="Vector Noise"),
            ]),
        SverchNodeCategory("SVERCHOK_Ma", "Matrix", items=[
            # Matrix nodes
            NodeItem("MatrixApplyNode", label="Matrix Apply"),
            NodeItem("MatrixGenNode", label="Matrix in"),
            NodeItem("MatrixOutNode", label="Matrix out"),
            NodeItem("SvMatrixValueIn", label="Matrix Input"),
            NodeItem("MatrixDeformNode", label="Matrix Deform"),
            NodeItem("MatrixShearNode", label="Matrix Shear"),  # for uniform view renamed
            NodeItem("MatrixInterpolationNode", label="Matrix Interpolation"),
            ]),
        SverchNodeCategory("SVERCHOK_M", "Modifier", items=[
            # modifiers deforms and reorganize and reconstruct data
            NodeItem("AdaptivePolsNode", label="Adaptive Polygons"),
            NodeItem("SvAdaptiveEdgeNode", label="Adaptive Edges"),
            NodeItem("CrossSectionNode", label="Cross Section"),
            NodeItem("SvBisectNode", label="Bisect"),
            NodeItem("SvSolidifyNode", label="Solidify"),
            NodeItem("SvWireframeNode", label="Wireframe"),
            NodeItem("LineConnectNode", label="UV Connection"),
            NodeItem("DelaunayTriangulation2DNode", label="Delaunay 2D "),
            NodeItem("Voronoi2DNode", label="Voronoi 2D"),
            NodeItem("PolygonBoomNode", label="Polygon Boom"),
            NodeItem("Pols2EdgsNode", label="Polygons to Edges"),
            NodeItem("SvMeshJoinNode", label="Mesh Join"),
            NodeItem("SvRemoveDoublesNode", label="Remove Doubles"),
            NodeItem("SvDeleteLooseNode", label="Delete Loose"),
            NodeItem('SvSeparateMeshNode', label="Separate Loose Parts"),
            NodeItem('SvVertMaskNode', label="Mask Vertices"),
            NodeItem("SvConvexHullNode", label="Convex Hull"),
            NodeItem("SvFillsHoleNode", label="Fill Holes"),
            NodeItem("SvIntersectEdgesNode", label="Intersect Edges"),
            NodeItem("SvLatheNode", label="Lathe"),
            ]),
        SverchNodeCategory("SVERCHOK_A", "Analysers", items=[
            # investigate data
            NodeItem("CentersPolsNode", label="Centers Polygons"),
            NodeItem("VectorNormalNode", label="Vector' Normal"),
            NodeItem("DistancePPNode", label="Distance"),
            NodeItem("AreaNode", label="Area"),
            NodeItem("SvBBoxNode", label="Bounding box"),
            NodeItem("SvKDTreeNode", label="KDT Closest Verts"),
            NodeItem("SvKDTreeEdgesNode", label="KDT Closest Edges"),  # KDTree renamed to be clear
            ]),
        SverchNodeCategory("SVERCHOK_X", "Beta", items=[
            # for testing convenience,
            NodeItem("BGLdemoNode", label="BGL debug print"),
            NodeItem("BasicSplineNode", label="Basic Spline"),
            NodeItem("SvOffsetNode", label="Offset"),
            NodeItem("SvEmptyOutNode", label="Empty out"),
            # NodeItem("Gen3DcursorNode", label="3D cursor"),
            NodeItem("EvalKnievalNode", label="Eval Knieval"),
            NodeItem("svBasicArcNode", label="Basic 3pt Arc"),
            NodeItem("Sv3DviewPropsNode", label="3dview properties"),
            NodeItem("ListDecomposeNode", label="List Decompose"), # need to be completely reviewed
            NodeItem("SvReRouteNode", label="Reroute Node"),
            NodeItem("svAxisInputNode", label="Axis X|Y|Z")
            ]),
        ]
    return node_categories

#def Sverchok_nodes_count():
#    cats = make_categories()
#    count = []
#    for cnt in cats:
#        count.append(len(cnt.items))
#    return count

def register():
    bpy.utils.register_class(SvColors)
    bpy.utils.register_class(SverchCustomTree)
    bpy.utils.register_class(MatrixSocket)
    #bpy.utils.register_class(ObjectSocket)
    bpy.utils.register_class(StringsSocket)
    bpy.utils.register_class(VerticesSocket)

def unregister():
    bpy.utils.unregister_class(VerticesSocket)
    bpy.utils.unregister_class(StringsSocket)
    #bpy.utils.unregister_class(ObjectSocket)
    bpy.utils.unregister_class(MatrixSocket)
    bpy.utils.unregister_class(SverchCustomTree)
    bpy.utils.unregister_class(SvColors)


