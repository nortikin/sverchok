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

from nodeitems_utils import NodeCategory, NodeItem
import nodeitems_utils


class SverchNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'SverchCustomTreeType'


def make_node_cats():

    node_cats = OrderedDict()
    '''  bl_idname, shortname, <icon> (optional) '''

# blue-green
    node_cats["Generators"] = [
        ["LineNode",            "Line",                  "GRIP"],
        ["PlaneNode",           "Plane",           "MESH_PLANE"],
        ['SvNGonNode',          'NGon',              'RNDCURVE'],
        ["SvBoxNode",           "Box",              "MESH_CUBE"],
        ["SvCircleNode",        "Circle",         "MESH_CIRCLE"],
        ["CylinderNode",        "Cylinder",     "MESH_CYLINDER"],
        ["SphereNode",          "Sphere",       "MESH_UVSPHERE"],
        ['BasicSplineNode',     "2pt Spline",  "CURVE_BEZCURVE"],
        ["svBasicArcNode",      "3pt Arc",        "SPHERECURVE"],
        ['RandomVectorNode',    'Random Vector',     'RNDCURVE'],
    ]

    node_cats["Extended Generators"] = [
        ["SvBoxRoundedNode",    "Rounded Box"],
        ["HilbertNode",         "Hilbert"],
        ["Hilbert3dNode",       "Hilbert3d"],
        ["HilbertImageNode",    "Hilbert image"],
        ["SvGenFibonacci",      "Fibonacci sequence"],
        ["SvGenExponential",    "Exponential sequence"],
        ["ImageNode",           "Image",                "FILE_IMAGE"],
        ["SvProfileNode",       "ProfileParametric"],
        ["SvScriptNode",        "Scripted Node",     "SCRIPTPLUGINS"],
    ]

    node_cats["Analyzers"] = [
        # investigate data
        ["SvBBoxNode",          "Bounding box"],
        ["SvVolumeNode",        "Volume"],
        ["AreaNode",            "Area"],
        ["DistancePPNode",      "Distance"],
        ["CentersPolsNode",     "Centers Polygons"],
        ["GetNormalsNode",      "Calculate normals"],
        ["VectorNormalNode",    "Vertex Normal"],
        # proximity analyses.
        ["SvKDTreeNode",        "KDT Closest Verts"],
        ["SvKDTreeEdgesNode",   "KDT Closest Edges"],
    ]

    node_cats["Transforms"] = [
        ["SvRotationNode",      "Rotation",    "MAN_ROT"],
        ["SvScaleNode",         "Scale",       "MAN_SCALE"],
        ["VectorMoveNode",      "Move",        "MAN_TRANS"],
        ["SvMirrorNode",        "Mirror",      "MOD_MIRROR"],
        ["MatrixApplyNode",     "Matrix Apply"],
    ]

    node_cats["Modifier Change"] = [
        # modifiers deforms and reorganize and reconstruct data
        ["PolygonBoomNode",      "Polygon Boom"],
        ["Pols2EdgsNode",        "Polygons to Edges"],
        ["SvMeshJoinNode",       "Mesh Join"],
        ["SvRemoveDoublesNode",  "Remove Doubles"],
        ["SvDeleteLooseNode",    "Delete Loose"],
        ["SvSeparateMeshNode",   "Separate Loose Parts"],
        ["SvExtrudeSeparateNode", "Extrude Separate Faces"],
        ["SvRandomizeVerticesNode", "Randomize input vertices"],
        ["SvVertMaskNode",       "Mask Vertices"],
        ["SvFillsHoleNode",      "Fill Holes"],
        ["SvIntersectEdgesNode", "Intersect Edges"],
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
        ['SvPipeNode',          'Pipe'],
        ["SvDuplicateAlongEdgeNode", "Duplicate objects along edge"],
        ["SvWafelNode",         "Wafel"],
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
        ["ListFlipNode",        "List Flip"],
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
        ['GenVectorsNode',      'Vector in'],
        ['VectorsOutNode',      'Vector out'],
        ['VectorMathNode',      'Vector Math'],
        ['VectorDropNode',      'Vector Drop'],
        ["VectorPolarInNode",   "Vector polar input"],
        ["VectorPolarOutNode",  "Vector polar output"],
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
        ["MatrixDeformNode",    "Matrix Deform"],
        ["SvMatrixValueIn",     "Matrix Input"],
        ["SvMatrixEulerNode",   "Matrix Euler"],
        ["MatrixShearNode",     "Matrix Shear"],
        ["MatrixInterpolationNode", "Matrix Interpolation"],
    ]

    node_cats["Logic"] = [
        ["SvLogicNode",         "Logic"],
        ["SvSwitchNode",        "Switch"],
        ["SvNeuroElman1LNode",  "Neuro"],
    ]

# orange
    node_cats["Viz"] = [
        ["ViewerNode2",         "Viewer Draw",         'RETOPO'],
        ["BmeshViewerNode",     "Viewer BMesh"],
        ["IndexViewerNode",     "Viewer Index"],
        ["Sv3DviewPropsNode",   "3dview Props"],
    ]

# greish blue
    node_cats["Text"] = [
        ["ViewerNode_text",     "Viewer text"],
        ["SvTextInNode",        "Text in"],
        ["SvTextOutNode",       "Text out"],
        ["NoteNode",            "Note"],
        ["GTextNode",           "GText"],
        ["SvDebugPrintNode",    "Debug print"],
        ["SvStethoscopeNode",   "Stethoscope"],
    ]

# green
    node_cats["Scene"] = [
        ["ObjectsNode",         "Objects in"],
        ["SvObjRemoteNode",     "Scene Objects"],
        ["SvFrameInfoNode",     "Frame info"],
        ["SvEmptyOutNode",      "Empty out",    "OUTLINER_OB_EMPTY"],
        ["SvInstancerNode",     "mesh instancer"],
        ["SvGetPropNode",       "Get property",   'FORCE_VORTEX'],
        ["SvSetPropNode",       "Set property",   'FORCE_VORTEX'],
        ["SvVertexGroupNode",   "Vertext group"],
        ["SvRayCastNode",       "Raycast"],
    ]

# violet
    node_cats["Layout"] = [
        ["WifiInNode",          "Wifi in"],
        ["WifiOutNode",         "Wifi out"],
        ["NodeReroute",         "Reroute Point"],
        ["ConverterNode",       "SocketConvert"],
    ]

    node_cats["Beta Nodes"] = [
        # for testing convenience, and while no documentation
        ['SvBevelNode',         "Bevel"],
        ["SvOffsetNode",        "Offset"],
        ["SvListDecomposeNode", "List Decompose"],
        ["SvFormulaShapeNode",  "Formula shape", "IPO"],
        ["SvScriptNodeMK2",     "Script 2"],
        ["SvMeshFilterNode", "Mesh filter"],
        ['SvBmeshViewerNodeMK2', 'BMeshView2'],
        ['SvBricksNode', 'Bricks grid'],
        ["SvMatrixApplyJoinNode", "Apply matrix to mesh"],
        ["SvIterateNode", "Iterate matrix transformation"],
    ]

    node_cats["Alpha Nodes"] = [
        ["SvImageComponentsNode", "Image Decompose",  "GROUP_VCOL"],
        ["SvJoinTrianglesNode",   "Join Triangles"],
        ["SvCurveViewerNode",     "Curve Viewer",      'MOD_CURVE'],
        ["SvCacheNode",           "Cache"],
        ["SvInsetSpecial",        "Inset Special"],
        ["SkinViewerNode",        "Skin Mesher"],
        ["SvCSGBooleanNode",      "CSG Boolean"],
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
    node_count = 0
    for category, nodes in node_cats.items():
        name_big = "SVERCHOK_" + category.replace(' ', '_')
        node_categories.append(SverchNodeCategory(
            name_big, category,
            # bl_idname, name
            items=[NodeItem(props[0], props[1]) for props in nodes]))
        node_count += len(nodes)

    return node_categories, node_count


def reload_menu():
    menu, node_count = make_categories()
    if 'SVERCHOK' in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK")
    nodeitems_utils.register_node_categories("SVERCHOK", menu)


def register():
    menu, node_count = make_categories()
    if 'SVERCHOK' in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK")
    nodeitems_utils.register_node_categories("SVERCHOK", menu)

    print("\n** Sverchok loaded with {i} nodes **".format(i=node_count))


def unregister():
    if 'SVERCHOK' in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK")
