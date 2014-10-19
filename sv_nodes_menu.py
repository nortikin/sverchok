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


def make_node_cats():

    node_cats = OrderedDict()
    '''  bl_idname, shortname, <icon> (optional) '''

    node_cats["Generators"] = [
        ["LineNode",            "Line",                  "GRIP"],
        ["PlaneNode",           "Plane",           "MESH_PLANE"],
        ["SvBoxNode",           "Box",              "MESH_CUBE"],
        ["SvCircleNode",        "Circle",         "MESH_CIRCLE"],
        ["CylinderNode",        "Cylinder",     "MESH_CYLINDER"],
        ["SphereNode",          "Sphere",       "MESH_UVSPHERE"],
        ['BasicSplineNode',     "2pt Spline",  "CURVE_BEZCURVE"],
        ["svBasicArcNode",      "3pt Arc",        "SPHERECURVE"]
    ]

    node_cats["Extended Generators"] = [
        ["SvBoxRoundedNode",    "Rounded Box"],
        ["HilbertNode",         "Hilbert"],
        ["Hilbert3dNode",       "Hilbert3d"],
        ["HilbertImageNode",    "Hilbert image"],
        ["ImageNode",           "Image",                "FILE_IMAGE"],
        ["SvFormulaShapeNode",  "Formula shape",               "IPO"],
        ["SvProfileNode",       "ProfileParametric"],
        ["SvScriptNode",        "Scripted Node",     "SCRIPTPLUGINS"]
    ]

    node_cats["Analyzers"] = [
        # investigate data
        ["SvBBoxNode",          "Bounding box"],
        ["SvVolumeNode",        "Volume"],
        ["AreaNode",            "Area"],
        ["DistancePPNode",      "Distance"],
        ["CentersPolsNode",     "Centers Polygons"],
        ["VectorNormalNode",    "Vertex Normal"],
        # making something different
        ["SvVertexGroupNode",   "Vertext group"],
        ["SvRayCastNode",       "Raycast"],
        # proximity anaylyses.
        ["SvKDTreeNode",        "KDT Closest Verts"],
        ["SvKDTreeEdgesNode",   "KDT Closest Edges"]
    ]

    node_cats["Transforms (Vec, Mat)"] = [
        ["SvRotationNode",      "Rotation",    "MAN_ROT"],
        ["SvScaleNode",         "Scale",       "MAN_SCALE"],
        ["VectorMoveNode",      "Vector Move", "MAN_TRANS"],
        ["SvMirrorNode",        "Mirror",      "MOD_MIRROR"],
        ["SvMatrixEulerNode",   "Matrix Euler"],
        ["MatrixShearNode",     "Matrix Shear"],
        ["MatrixApplyNode",     "Matrix Apply"],
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
        # bl_idname, shortname, <icon> (optional)
        ['LineConnectNode',     'UV Connection'],
        ['AdaptivePolsNode',    'Adaptive Polygons'],
        ['SvAdaptiveEdgeNode',  'Adaptive Edges'],
        ['CrossSectionNode',    'Cross Section'],
        ['SvBisectNode',        'Bisect'],
        ['SvSolidifyNode',      'Solidify'],
        ['SvWireframeNode',     'Wireframe'],
        ['DelaunayTriangulation2DNode', 'Delaunay 2D '],
        ['Voronoi2DNode',       'Voronoi 2D'],
        ['SvConvexHullNode',    'Convex Hull'],
        ['SvLatheNode',         'Lathe',            'MOD_SCREW'],
    ]

    node_cats["List Masks"] = [
        ["MaskListNode",        "List Mask (out)"],
        ["SvMaskJoinNode",      "List Mask Join (in)"],
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

    node_cats["Vector"] = [
        ['RandomVectorNode',    'Random Vector',        'RNDCURVE'],
        ['GenVectorsNode',      'Vector in'],
        ['VectorsOutNode',      'Vector out'],
        ['VectorMathNode',      'Vector Math'],
        ['VectorDropNode',      'Vector Drop'],
        ['VertsDelDoublesNode', 'Vector X Doubles'],
        ['EvaluateLineNode',    'Vector Evaluate'],
        ['SvInterpolationNode', 'Vector Interpolation'],
        ['SvVertSortNode',      'Vector Sort',          'SORTSIZE'],
        ['SvNoiseNode',         'Vector Noise', 'FORCE_TURBULENCE'],
        ['svAxisInputNode',     'Vector X | Y | Z',      'MANIPUL'],
    ]

    node_cats["Matrix"] = [
        ["MatrixGenNode",       "Matrix in"],
        ["MatrixOutNode",       "Matrix out"],
        ["SvMatrixValueIn",     "Matrix Input"],
        ["MatrixDeformNode",    "Matrix Deform"],
        ["MatrixInterpolationNode", "Matrix Interpolation"]
    ]

    node_cats["Conditionals"] = [
        ["SvLogicNode",         "Logic"],
        ["SvSwitchNode",        "Switch"],
        ["SvNeuroElman1LNode",  "Neuro"],
    ]

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

    node_cats["Beta Nodes"] = [
        # for testing convenience,
        ["ViewerNode2",         "Viewer draw MK2",         'RETOPO'],
        ["SvOffsetNode",        "Offset"],
        ["SvEmptyOutNode",      "Empty out",    "OUTLINER_OB_EMPTY"],
        # need to be completely reviewed
        ["SvListDecomposeNode", "List Decompose"],
        # should be removed...
        ["SvReRouteNode",       "Reroute Point"],
        ["SvInstancerNode",     "mesh instancer"],
        ["SvWafelNode",         "Wafel"],
        ["SvScriptNodeMK2",     "Script 2"],
    ]

    node_cats["Alpha Nodes"] = [
        ["SvObjRemoteNode",       "Scene Objects"],
        ["SvImageComponentsNode", "Image Decompose",  "GROUP_VCOL"],
        ["SvJoinTrianglesNode",   "Join Triangles"],
        ["EvalKnievalNode",       "Eval Knieval",   'FORCE_VORTEX']
    ]

    return node_cats


def juggle_and_join(node_cats):
    '''
    this step post processes the extended catagorization used
    by ctrl+space dynamic menu, and attempts to merge previously
    joined catagories. Why? Because the default menu gets very
    long if there are too many catagories.

    The only real alternative to this approach is to write a
    replacement for nodeitems_utils which respects catagories
    and submenus.

    '''
    node_cats = node_cats.copy()

    # join beta and alpha node cats
    alpha = node_cats.pop('Alpha Nodes')
    node_cats['Beta Nodes'].extend(alpha)

    # put masks into list main
    masks = node_cats.pop("List Masks")
    node_cats["List main"].extend(masks)

    # add extended gens to Gens menu
    gen_ext = node_cats.pop("Extended Generators")
    node_cats["Generators"].extend(gen_ext)

    return node_cats


def make_categories():
    original_categories = make_node_cats()
    node_cats = juggle_and_join(original_categories)

    node_categories = []
    howmanynodesare = 0
    for category, nodes in node_cats.items():
        name_big = "SVERCHOK_" + category.replace(' ', '_')
        node_categories.append(SverchNodeCategory(
            name_big, category,
            # bl_idname, name
            items=[NodeItem(props[0], props[1]) for props in nodes]))
        howmanynodesare += len(nodes)

    return node_categories, howmanynodesare
