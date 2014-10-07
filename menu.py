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

from nodeitems_utils import NodeItem
from node_tree import SverchNodeCategory


def make_categories():

    node_cats = OrderedDict()
    ''' [node's bl_idname,      name in menu] '''

    node_cats["Basic Viz"] = [
        ["ViewerNode",          "Viewer draw"],
        ["ViewerNode_text",     "Viewer text"],
        ["IndexViewerNode",     "Viewer INDX"],
        ["Sv3DviewPropsNode",   "3dview Props"],
        ["BmeshViewerNode",     "Viewer BMesh"]
    ]

    node_cats["Basic Data"] = [
        ["ObjectsNode",         "Objects in"],
        ["SvTextInNode",        "Text in"],
        ["SvTextOutNode",       "Text out"],
        ["WifiInNode",          "Wifi in"],
        ["WifiOutNode",         "Wifi out"]
    ]

    node_cats["Basic Debug"] = [
        ["SvFrameInfoNode",     "Frame info"],
        ["NoteNode",            "Note"],
        ["GTextNode",           "GText"],
        ["SvDebugPrintNode",    "Debug print"],
        ["SvStethoscopeNode",   "Stethoscope"]
    ]

    node_cats["List main"] = [
        ["ListJoinNode",        "List Join"],
        ["ZipNode",             "List Zip"],
        ["ListLevelsNode",      "List Del Levels"],
        ["ListLengthNode",      "List Length"],
        ["ListSumNode",         "List Sum"],
        ["ListMatchNode",       "List Match"],
        ["ListFuncNode",        "List Math"],
        ["ConverterNode",       "SocketConvert"]
    ]

    node_cats["List struct"] = [
        ["ShiftNode",           "List Shift"],
        ["ListRepeaterNode",    "List Repeater"],
        ["ListSliceNode",       "List Slice"],
        ["SvListSplitNode",     "List Split"],
        ["ListFLNode",          "List First&Last"],
        ["ListItem2Node",       "List Item"],
        ["ListReverseNode",     "List Reverse"],
        ["ListShuffleNode",     "List Shuffle"],
        ["ListSortNode",        "List Sort"],
        ["ListFlipNode",        "List Flip"]
    ]

    node_cats["Number"] = [
        # numbers, formula nodes
        ["GenListRangeIntNode", "Range Int"],
        ["SvGenFloatRange",     "Range Float"],
        ["SvListInputNode",     "List Input"],
        ["RandomNode",          "Random"],
        ["FloatNode",           "Float"],
        ["IntegerNode",         "Int"],
        ["Float2IntNode",       "Float 2 Int"],
        # ["FormulaNode", "Formula"],
        # for newbies this is not predictable why "Formula2" renamed
        ["Formula2Node",        "Formula"],
        ["ScalarMathNode",      "Math"],
        ["SvMapRangeNode",      "Map Range"]
    ]

    node_cats["Generator Primitive"] = [
        # objects, new elements, line, plane
        ["LineNode",            "Line"],
        ["PlaneNode",           "Plane"],
        ["SvBoxNode",           "Box"],
        ["SvCircleNode",        "Circle"],
        ["CylinderNode",        "Cylinder"],
        ["SphereNode",          "Sphere"],
        ["BasicSplineNode",     "2pt Spline"],
        ["svBasicArcNode",      "3pt Arc"],
    ]

    node_cats["Generator Special"] = [
        ["SvBoxRoundedNode",    "Rounded Box"],
        ["HilbertNode",         "Hilbert"],
        ["Hilbert3dNode",       "Hilbert3d"],
        ["HilbertImageNode",    "Hilbert image"],
        ["ImageNode",           "Image"],
        ["SvFormulaShapeNode",  "Formula shape"],
        ["SvProfileNode",       "ProfileParametric"],
        ["SvScriptNode",        "Scripted Node"]
    ]

    node_cats["Vector"] = [
        ["RandomVectorNode",    "Random Vector"],
        ["GenVectorsNode",      "Vector in"],
        ["VectorsOutNode",      "Vector out"],
        ["VectorMathNode",      "Vector Math"],
        ["VectorDropNode",      "Vector Drop"],
        ["VertsDelDoublesNode", "Vector X Doubles"],
        ["EvaluateLineNode",    "Vector Evaluate"],
        ["SvInterpolationNode", "Vector Interpolation"],
        ["SvVertSortNode",      "Vector Sort"],
        ["SvNoiseNode",         "Vector Noise"],
        ["svAxisInputNode",     "Vector X | Y | Z"]
    ]

    node_cats["Matrix"] = [
        ["MatrixGenNode",       "Matrix in"],
        ["MatrixOutNode",       "Matrix out"],
        ["SvMatrixValueIn",     "Matrix Input"],
        ["MatrixDeformNode",    "Matrix Deform"],
        ["MatrixInterpolationNode", "Matrix Interpolation"]
    ]

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
        ["SvIntersectEdgesNode", "Intersect Edges"]
    ]

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
        ["SvLatheNode",         "Lathe"]
    ]

    node_cats["Logic"] = [
        ["SvLogicNode",         "Logic"],
        ["MaskListNode",        "List Mask (out)"],
        ["SvMaskJoinNode",      "List Mask Join (in)"],
        ["SvSwitchNode",        "Switch"],
        ["SvNeuroElman1LNode",  "Neuro"],
    ]

    node_cats["Analyser"] = [
        # investigate data
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

    node_cats["Beta test"] = [
        # for testing convenience,
        ["ViewerNode2",         "Viewer draw MK2"],
        ["SvOffsetNode",        "Offset"],
        ["SvEmptyOutNode",      "Empty out"],
        # need to be completely reviewed
        ["SvListDecomposeNode", "List Decompose"],
        # should be removed...
        ["SvReRouteNode",       "Reroute Point"],
        ["SvInstancerNode",     "mesh instancer"],
        ["SvWafelNode",         "Wafel"],
        ["SvVertexGroupNode",   "Vertext group"],
        ["SvRayCastNode",       "Raycast"]
    ]

    node_cats["Transforms"] = [
        ["SvRotationNode",      "Rotation"],
        ["SvScaleNode",         "Scale"],
        ["SvMatrixEulerNode",   "Matrix Euler"],
        ["SvMirrorNode",        "Mirror"],
        ["MatrixShearNode",     "Matrix Shear"],  # for uniform view renamed
        ["MatrixApplyNode",     "Matrix Apply"],
        ["VectorMoveNode",      "Vector Move"],
    ]

    dev_tests = False
    if dev_tests:
        node_cats["Alpha test"] = [
            ["SvObjRemoteNode",     "Scene Objects"],
            ["SvImageComponentsNode", "Image Decompose"],
            ["SvJoinTrianglesNode", "Join Triangles"],
            ["EvalKnievalNode",     "Eval Knieval"]
        ]

    node_categories = []
    howmanynodesare = 0
    for category, nodes in node_cats.items():
        name_big = "SVERCHOK_" + category.replace(' ', '_')
        node_categories.append(SverchNodeCategory(
            name_big, category,
            items=[NodeItem(bl_idname, name) for bl_idname, name in nodes]))
        howmanynodesare += len(nodes)

    return node_categories, howmanynodesare
