> 
> The following strict rules apply to editing this file:
>
> - do not use tabs, anywhere
> - indent the Node's line using 4 spaces
> - use `>` to add a comment, place it at the start of the line.
> - if you aren't sure, follow the existing convention
> 
> Failing to follow these points will break the node category parser. 


## Generators
    LineNode,                     Line
    PlaneNode,                    Plane
    SvNGonNode,                   NGon
    SvBoxNode,                    Box
    SvCircleNode,                 Circle
    CylinderNode,                 Cylinder
    SphereNode,                   Sphere
    BasicSplineNode,              2pt Spline
    svBasicArcNode,               3pt Arc
    RandomVectorNode,             Random Vector
    SvBricksNode,                 Bricks grid
    ImageNode,                    Image

## Extended Generators
    SvBoxRoundedNode,             Rounded Box
    HilbertNode,                  Hilbert
    Hilbert3dNode,                Hilbert3d
    HilbertImageNode,             Hilbert image
    SvProfileNode,                ProfileParametric
    SvGenerativeArtNode,          Generative Art
    SvImageComponentsNode,        Image Decompose
    SvScriptNode,                 Scripted Node
    SvScriptNodeMK3,              Script 3 Node

## Analyzers
    SvBBoxNode,                   Bounding box
    SvVolumeNode,                 Volume
    AreaNode,                     Area
    DistancePPNode,               Distance
    CentersPolsNodeMK2,           Centers Polygons 2
    CentersPolsNodeMK3,           Centers Polygons 3
    GetNormalsNode,               Calculate normals
    VectorNormalNode,             Vertex Normal
    SvKDTreeNode,                 KDT Closest Verts
    SvKDTreeEdgesNode,            KDT Closest Edges
    SvMeshFilterNode,             Mesh filter
    SvEdgeAnglesNode,             Angles at the edges

## Transforms
    SvRotationNode,               Rotation
    SvScaleNode,                  Scale
    VectorMoveNode,               Move
    SvMirrorNode,                 Mirror
    MatrixApplyNode,              Matrix Apply

## Modifier Change
    PolygonBoomNode,              Polygon Boom
    Pols2EdgsNode,                Polygons to Edges
    SvMeshJoinNode,               Mesh Join
    SvRemoveDoublesNode,          Remove Doubles
    SvDeleteLooseNode,            Delete Loose
    SvSeparateMeshNode,           Separate Loose Parts
    SvExtrudeSeparateNode,        Extrude Separate Faces
    SvRandomizeVerticesNode,      Randomize input vertices
    SvVertMaskNode,               Mask Vertices
    SvFillsHoleNode,              Fill Holes
    SvLimitedDissolve,            Limited Dissolve
    SvIntersectEdgesNode,         Intersect Edges
    SvIterateNode,                Iterate matrix transformation
    SvBevelNode,                  Bevel
    SvExtrudeEdgesNode,           Extrude Edges
    SvOffsetNode,                 Offset
    SvTriangulateNode,            Triangulate mesh
    SvRecalcNormalsNode,          Recalc normals

## Modifier Make
    LineConnectNodeMK2,           UV Connection
    AdaptivePolsNode,             Adaptive Polygons
    SvAdaptiveEdgeNode,           Ad aptive Edges
    CrossSectionNode,             Cross Section
    SvBisectNode,                 Bisect
    SvSolidifyNode,               Solidify
    SvWireframeNode,              Wireframe
    DelaunayTriangulation2DNode,  Delaunay 2D
    Voronoi2DNode,                Voronoi 2D
    SvPipeNode,                   Pipe
    SvDuplicateAlongEdgeNode,     Duplicate objects along edge
    SvWafelNode,                  Wafel
    SvConvexHullNode,             Convex Hull
    SvLatheNode,                  Lathe
    SvMatrixTubeNode,             Matrix Tube

## List Masks
    MaskListNode,                 List Mask (out)
    SvMaskJoinNode,               List Mask Join (in)

## List main
    ListJoinNode,                 List Join
    ZipNode,                      List Zip
    ListLevelsNode,               List Del Levels
    ListLengthNode,               List Length
    ListSumNodeMK2,               List Sum
    ListMatchNode,                List Match
    ListFuncNode,                 List Math
    SvListDecomposeNode,          List Decompose

## List struct
    ShiftNodeMK2,                 List Shift
    ListRepeaterNode,             List Repeater
    ListSliceNode,                List Slice
    SvListSplitNode,              List Split
    ListFLNode,                   List First&Last
    ListItem2Node,                List Item
    ListReverseNode,              List Reverse
    ListShuffleNode,              List Shuffle
    ListSortNodeMK2,              List Sort
    ListFlipNode,                 List Flip

## Number
    GenListRangeIntNode,          Range Int
    SvGenFloatRange,              Range Float
    SvListInputNode,              List Input
    RandomNode,                   Random
    FloatNode,                    Float
    IntegerNode,                  Int
    Float2IntNode,                Float 2 Int
    Formula2Node,                 Formula
    ScalarMathNode,               Math
    SvMapRangeNode,               Map Range
    SvEasingNode,                 Easing 0..1
    SvGenFibonacci,               Fibonacci sequence
    SvGenExponential,             Exponential sequence

## Vector
    GenVectorsNode,               Vector in
    VectorsOutNode,               Vector out
    VectorMathNode,               Vector Math
    VectorDropNode,               Vector Drop
    VectorPolarInNode,            Vector polar input
    VectorPolarOutNode,           Vector polar output
    VertsDelDoublesNode,          Vector X Doubles
    EvaluateLineNode,             Vector Evaluate
    SvInterpolationNode,          Vector Interpolation
    SvInterpolationNodeMK2,       Vector Interpolation mk2
    SvInterpolationNodeMK3,       Vector Interpolation mk3
    SvVertSortNode,               Vector Sort
    SvNoiseNode,                  Vector Noise
    svAxisInputNode,              Vector X | Y | Z

## Matrix
    MatrixGenNode,                Matrix in
    MatrixOutNode,                Matrix out
    MatrixDeformNode,             Matrix Deform
    SvMatrixValueIn,              Matrix Input
    SvMatrixEulerNode,            Matrix Euler
    MatrixShearNode,              Matrix Shear
    MatrixInterpolationNode,      Matrix Interpolation
    SvMatrixApplyJoinNode,        Apply matrix to mesh

## Logic
    SvLogicNode,                  Logic
    SvSwitchNode,                 Switch
    SvNeuroElman1LNode,           Neuro

## Viz
    ViewerNode2,                  Viewer Draw
    SvBmeshViewerNodeMK2,         Viewer BMeshMK2
    IndexViewerNode,              Viewer Index
    Sv3DviewPropsNode,            3dview Props

## Text
    ViewerNode_text,              Viewer text
    SvTextInNode,                 Text in
    SvTextOutNode,                Text out
    NoteNode,                     Note
    GTextNode,                    GText
    SvDebugPrintNode,             Debug print
    SvStethoscopeNode,            Stethoscope

## Scene
    ObjectsNode,                  Objects in
    SvObjRemoteNode,              Object Remote (Control)
    SvFrameInfoNode,              Frame info
    SvEmptyOutNode,               Empty out
    SvDupliInstancesMK3,          Dupli instancer
    SvInstancerNode,              Mesh instancer
    SvGetPropNode,                Get property
    SvSetPropNode,                Set property
    SvVertexGroupNode,            Vertex group
    SvRayCastSceneNode,           Scene Raycast
    SvRayCastObjectNode,          Object ID Raycast
    SvVertexColorNode,            Vertex color
    SvVertexColorNodeMK2,         Vertex color new

## Layout
    WifiInNode,                   Wifi in
    WifiOutNode,                  Wifi out
    NodeReroute,                  Reroute Point
    ConverterNode,                SocketConvert

## Network
    UdpClientNode,                UDP Client

## Beta Nodes
    SvFormulaShapeNode,           Formula shape
    SvScriptNodeMK2,              Script 2
    SvHeavyTriangulateNode,       Triangulate mesh (heavy)

## Alpha Nodes
    SvCurveViewerNode,            Curve Viewer
    SvCurveViewerNodeAlt,         Curve Viewer 2D
    SvPolylineViewerNode,         Polyline Viewer
    SvTypeViewerNode,             Typography Viewer
    SvJoinTrianglesNode,          Join Triangles
    SvCacheNode,                  Cache
    SvInsetSpecial,               Inset Special
    SkinViewerNode,               Skin Mesher
    SvCSGBooleanNode,             CSG Boolean
    SvNumpyArrayNode,             Numpy Array
    SvNodeRemoteNode,             Node Remote (Control)
    SvGetDataObjectNode,          Object ID Get
    SvSetDataObjectNode,          Object ID Set
    SvSortObjsNode,               Object ID Sort
    SvObjectToMeshNode,           Object ID Out
    SvFilterObjsNode,             Object ID Filter
    SvPointOnMeshNode,            Object ID Point on Mesh
    SvBMVertsNode,                BMesh Props
    SvBMOpsNode,                  BMesh Ops
    SvBMinputNode,                BMesh In
    SvBMoutputNode,               BMesh Out
    SvBMtoElementNode,            BMesh Elements
