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

from collections import OrderedDict

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
                msg = "Warning output socket: {name} in node: {node} has property attached"
                print(msg.format(name=self.name, node=node.name))
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

    node_cats = OrderedDict()
    ''' [node's bl_idname,   name in menu] '''

    node_cats["Basic Viz"] = [
        ["BmeshViewerNode", "Viewer BMesh"],
        ["ViewerNode",      "Viewer draw"],
        ["ViewerNode_text", "Viewer text"],
        ["IndexViewerNode", "Viewer INDX"]]

    node_cats["Basic Data"] = [
        ["ObjectsNode",     "Objects in"],
        ["SvTextInNode",    "Text in"],
        ["SvTextOutNode",   "Text out"],
        ["WifiInNode",      "Wifi in"],
        ["WifiOutNode",     "Wifi out"]]

    node_cats["Basic Debug"] = [
        # ["Test1Node",     "Test1"],
        # ["Test2Node",     "Test2"],
        # ["ToolsNode",     "Update Button"],
        ["SvFrameInfoNode", "Frame info"],
        ["NoteNode",        "Note"],
        ["GTextNode",       "GText"],
        ["SvDebugPrintNode", "Debug print"]]

    node_cats["List main"] = [
        ["ListJoinNode",    "List Join"],
        ["ZipNode",         "List Zip"],
        ["ListLevelsNode",  "List Del Levels"],
        ["ListLengthNode",  "List Length"],
        ["ListSumNode",     "List Sum"],
        ["MaskListNode",    "List Mask (out)"],
        ["SvMaskJoinNode",  "List Mask Join (in)"],
        ["ListMatchNode",   "List Match"],
        ["ListFuncNode",    "List Math"],
        ["ConverterNode",   "SocketConvert"]]

    node_cats["List struct"] = [
        ["ShiftNode",       "List Shift"],
        ["ListRepeaterNode", "List Repeater"],
        ["ListSliceNode",   "List Slice"],
        ["SvListSplitNode", "List Split"],
        ["ListFLNode",      "List First&Last"],
        ["ListItem2Node",   "List Item"],
        ["ListReverseNode", "List Reverse"],
        ["ListShuffleNode", "List Shuffle"],
        ["ListSortNode",    "List Sort"],
        ["ListFlipNode",    "List Flip"]]

    node_cats["Number"] = [
        # numbers, formula nodes
        ["GenListRangeIntNode", "Range Int"],
        ["SvGenFloatRange", "Range Float"],
        ["SvListInputNode", "List Input"],
        ["RandomNode",      "Random"],
        ["FloatNode",       "Float"],
        ["IntegerNode",     "Int"],
        ["Float2IntNode",   "Float 2 Int"],
        # ["FormulaNode", "Formula"],
        # for newbies this is not predictable why "Formula2" renamed
        ["Formula2Node",    "Formula"],
        ["ScalarMathNode",  "Math"],
        ["SvMapRangeNode",  "Map Range"]]

    node_cats["Generator"] = [
        # objects, new elements, line, plane
        ["LineNode",        "Line"],
        ["PlaneNode",       "Plane"],
        ["SvBoxNode",       "Box"],
        ["SvCircleNode",    "Circle"],
        ["CylinderNode",    "Cylinder"],
        ["SphereNode",      "Sphere"],
        ["HilbertNode",     "Hilbert"],
        ["Hilbert3dNode",   "Hilbert3d"],
        ["HilbertImageNode", "Hilbert image"],
        ["ImageNode",       "Image"],
        ["RandomVectorNode", "Random Vector"],
        ["SvFormulaShapeNode", "Formula shape"],
        ["SvScriptNode", "Scripted Node"]]

    node_cats["Vector"] = [
        ["GenVectorsNode",  "Vector in"],
        ["VectorsOutNode",  "Vector out"],
        ["VectorMoveNode",  "Vector Move"],
        ["VectorMathNode",  "Vector Math"],
        ["VectorDropNode",  "Vector Drop"],
        ["VertsDelDoublesNode", "Vector X Doubles"],
        ["EvaluateLineNode", "Vector Evaluate"],
        ["SvInterpolationNode", "Vector Interpolation"],
        ["SvVertSortNode", "Vector Sort"],
        ["SvNoiseNode", "Vector Noise"]]

    node_cats["Matrix"] = [
        ["MatrixApplyNode",     "Matrix Apply"],
        ["MatrixGenNode",       "Matrix in"],
        ["MatrixOutNode",       "Matrix out"],
        ["SvMatrixValueIn",     "Matrix Input"],
        ["MatrixDeformNode",    "Matrix Deform"],
        ["MatrixShearNode",     "Matrix Shear"],  # for uniform view renamed
        ["MatrixInterpolationNode", "Matrix Interpolation"]]

    node_cats["Modifier Change"] = [
        # modifiers deforms and reorganize and reconstruct data
        ["PolygonBoomNode",     "Polygon Boom"],
        ["Pols2EdgsNode",       "Polygons to Edges"],
        ["SvMeshJoinNode",      "Mesh Join"],
        ["SvRemoveDoublesNode", "Remove Doubles"],
        ["SvDeleteLooseNode",   "Delete Loose"],
        ["SvSeparateMeshNode",  "Separate Loose Parts"],
        ["SvVertMaskNode",      "Mask Vertices"],
        ["SvFillsHoleNode",     "Fill Holes"],
        ["SvIntersectEdgesNode", "Intersect Edges"]]

    node_cats["Modifier Make"] = [
        ["LineConnectNode",     "UV Connection"],
        ["AdaptivePolsNode",    "Adaptive Polygons"],
        ["SvAdaptiveEdgeNode",  "Adaptive Edges"],
        ["CrossSectionNode",    "Cross Section"],
        ["SvBisectNode",        "Bisect"],
        ["SvSolidifyNode",      "Solidify"],
        ["SvWireframeNode",     "Wireframe"],
        ["DelaunayTriangulation2DNode", "Delaunay 2D "],
        ["Voronoi2DNode",       "Voronoi 2D"],
        ["SvConvexHullNode",    "Convex Hull"],
        ["SvLatheNode",         "Lathe"]]

    node_cats["Analyser"] = [
        # investigate data
        ["CentersPolsNode",     "Centers Polygons"],
        ["VectorNormalNode",    "Vertex Normal"],
        ["DistancePPNode",      "Distance"],
        ["AreaNode",            "Area"],
        ["SvBBoxNode",          "Bounding box"],
        ["SvKDTreeNode",        "KDT Closest Verts"],
        ["SvKDTreeEdgesNode",   "KDT Closest Edges"]]

    node_cats["Beta test"] = [
        # for testing convenience,
        ["BGLdemoNode",         "Viewer BGL debug"],
        ["BasicSplineNode",     "2pt Spline"],
        ["svBasicArcNode",      "3pt Arc"],
        ["SvOffsetNode",        "Offset"],
        ["SvEmptyOutNode",      "Empty out"],
        # ["Gen3DcursorNode", "3D cursor"],
        ["EvalKnievalNode",     "Eval Knieval"],
        ["Sv3DviewPropsNode",   "3dview Props"],
        # need to be completely reviewed
        ["ListDecomposeNode",   "List Decompose"],
        ["SvReRouteNode",       "Reroute Point"],
        ["svAxisInputNode",     "Vector X | Y | Z"]]

    node_categories = []
    for category, nodes in node_cats.items():
        name_big = "SVERCHOK_" + category.replace(' ', '_')
        node_categories.append(SverchNodeCategory(
            name_big, category,
            items=[NodeItem(bl_idname, name) for bl_idname, name in nodes]))

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
