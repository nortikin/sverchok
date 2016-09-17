> 
> The following strict rules apply to editing this file:
>
> - do not use tabs, anywhere
> - indent the Node's line using 4 spaces
> - if using an icon then the line must be 80 chars long
> - set the icon right-aligned to the last character
> - if you aren't sure, follow the existing convention
> - use `>` to add a comment, place it at the start of the line.
> 
> Failing to follow these points will break the node category parser. 


## Generators
    LineNode,                     Line,                                    GRIP
    PlaneNode,                    Plane,                             MESH_PLANE
    SvNGonNode,                   NGon,                                RNDCURVE
    SvBoxNode,                    Box,                                MESH_CUBE
    SvCircleNode,                 Circle,                           MESH_CIRCLE
    CylinderNode,                 Cylinder,                       MESH_CYLINDER
    SphereNode,                   Sphere,                         MESH_UVSPHERE
    BasicSplineNode,              2pt Spline,                    CURVE_BEZCURVE
    svBasicArcNode,               3pt Arc,                          SPHERECURVE
    RandomVectorNode,             Random Vector,                       RNDCURVE

## Extended Generators
    SvBoxRoundedNode,             Rounded Box
    HilbertNode,                  Hilbert
    Hilbert3dNode,                Hilbert3d
    HilbertImageNode,             Hilbert image
    ImageNode,                    Image,                             FILE_IMAGE
    SvProfileNode,                ProfileParametric
    SvGenerativeArtNode,          Generative Art
    SvScriptNode,                 Scripted Node,                  SCRIPTPLUGINS
    SvScriptNodeMK3,              Script 3 Node,                  SCRIPTPLUGINS

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

## Transforms
    SvRotationNode,               Rotation,                             MAN_ROT
    SvScaleNode,                  Scale,                              MAN_SCALE
    VectorMoveNode,               Move,                               MAN_TRANS
    SvMirrorNode,                 Mirror,                            MOD_MIRROR
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
    SvLatheNode,                  Lathe,                              MOD_SCREW

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
    RandomNode,                   Random,                              RNDCURVE
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
    SvVertSortNode,               Vector Sort,                         SORTSIZE
    SvNoiseNode,                  Vector Noise,                FORCE_TURBULENCE
    svAxisInputNode,              Vector X | Y | Z,                     MANIPUL

## Matrix
    MatrixGenNode,                Matrix in
    MatrixOutNode,                Matrix out
    MatrixDeformNode,             Matrix Deform
    SvMatrixValueIn,              Matrix Input
    SvMatrixEulerNode,            Matrix Euler
    MatrixShearNode,              Matrix Shear
    MatrixInterpolationNode,      Matrix Interpolation

## Logic
    SvLogicNode,                  Logic
    SvSwitchNode,                 Switch
    SvNeuroElman1LNode,           Neuro

## Viz
    ViewerNode2,                  Viewer Draw,                           RETOPO
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
    SvEmptyOutNode,               Empty out,                  OUTLINER_OB_EMPTY
    SvDupliInstancesMK3,          Dupli instancer
    SvInstancerNode,              Mesh instancer
    SvGetPropNode,                Get property,                    FORCE_VORTEX
    SvSetPropNode,                Set property,                    FORCE_VORTEX
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
    SvBevelNode,                  Bevel
    SvExtrudeEdgesNode,           Extrude Edges
    SvOffsetNode,                 Offset
    SvRecalcNormalsNode,          Recalc normals
    SvEdgeAnglesNode,             Angles at the edges
    SvListDecomposeNode,          List Decompose
    SvFormulaShapeNode,           Formula shape,                            IPO
    SvScriptNodeMK2,              Script 2
    SvMeshFilterNode,             Mesh filter
    SvTriangulateNode,            Triangulate mesh
    SvHeavyTriangulateNode,       Triangulate mesh (heavy)
    SvBricksNode,                 Bricks grid
    SvMatrixApplyJoinNode,        Apply matrix to mesh
    SvMatrixTubeNode,             Matrix Tube

## Alpha Nodes
    SvCurveViewerNode,            Curve Viewer,                       MOD_CURVE
    SvCurveViewerNodeAlt,         Curve Viewer 2D,                    MOD_CURVE
    SvPolylineViewerNode,         Polyline Viewer,                    MOD_CURVE
    SvTypeViewerNode,             Typography Viewer
    SvImageComponentsNode,        Image Decompose,                   GROUP_VCOL
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
