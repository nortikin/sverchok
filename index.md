> ### This file is parsed by menu.py
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
    LineNode
    PlaneNode
    SvNGonNode
    SvBoxNode
    SvCircleNode
    CylinderNode
    SphereNode
    BasicSplineNode
    svBasicArcNode
    RandomVectorNodeMK2
    SvBricksNode
    ImageNode

## Generators Extended
    SvBoxRoundedNode
    HilbertNode
    Hilbert3dNode
    HilbertImageNode
    SvProfileNode
    SvGenerativeArtNode
    SvImageComponentsNode
    SvScriptNode
    SvScriptNodeMK3

## Analyzers
    SvBBoxNode
    SvVolumeNode
    AreaNode
    DistancePPNode
    CentersPolsNodeMK2
    CentersPolsNodeMK3
    GetNormalsNode
    VectorNormalNode
    SvKDTreeNode
    SvKDTreeEdgesNodeMK2
    SvMeshFilterNode
    SvEdgeAnglesNode

## Transforms
    SvRotationNode
    SvScaleNode
    VectorMoveNode
    SvMirrorNode
    MatrixApplyNode

## Modifier Change
    PolygonBoomNode
    Pols2EdgsNode
    SvMeshJoinNode
    SvRemoveDoublesNode
    SvDeleteLooseNode
    SvSeparateMeshNode
    SvExtrudeSeparateNode
    SvRandomizeVerticesNode
    SvVertMaskNode
    SvFillsHoleNode
    SvLimitedDissolve
    SvIntersectEdgesNode
    SvIterateNode
    SvBevelNode
    SvExtrudeEdgesNode
    SvOffsetNode
    SvTriangulateNode
    SvRecalcNormalsNode

## Modifier Make
    LineConnectNodeMK2
    AdaptivePolsNode
    SvAdaptiveEdgeNode
    CrossSectionNode
    SvBisectNode
    SvSolidifyNode
    SvWireframeNode
    DelaunayTriangulation2DNode
    Voronoi2DNode
    SvPipeNode
    SvDuplicateAlongEdgeNode
    SvWafelNode
    SvConvexHullNode
    SvLatheNode
    SvMatrixTubeNode

## List Masks
    MaskListNode
    SvMaskJoinNode

## List Mutators
    SvListModifierNode

## List Main
    ListJoinNode
    ZipNode
    ListLevelsNode
    ListLengthNode
    ListSumNodeMK2
    ListMatchNode
    ListFuncNode
    SvListDecomposeNode

## List Struct
    ShiftNodeMK2
    ListRepeaterNode
    ListSliceNode
    SvListSplitNode
    ListFLNode
    ListItem2Node
    ListReverseNode
    ListShuffleNode
    ListSortNodeMK2
    ListFlipNode

## Number
    GenListRangeIntNode
    SvGenFloatRange
    SvListInputNode
    RandomNode
    FloatNode
    IntegerNode
    Float2IntNode
    Formula2Node
    ScalarMathNode
    SvMapRangeNode
    SvEasingNode
    SvGenFibonacci
    SvGenExponential

## Vector
    GenVectorsNode
    VectorsOutNode
    SvVectorMathNodeMK2
    VectorDropNode
    VectorPolarInNode
    VectorPolarOutNode
    VertsDelDoublesNode
    EvaluateLineNode
    SvInterpolationStripesNode
    SvInterpolationNode
    SvInterpolationNodeMK2
    SvInterpolationNodeMK3
    SvVertSortNode
    SvNoiseNodeMK2
    svAxisInputNode
    SvAxisInputNodeMK2

## Matrix
    MatrixGenNode
    MatrixOutNode
    MatrixDeformNode
    SvMatrixValueIn
    SvMatrixEulerNode
    MatrixShearNode
    MatrixInterpolationNode
    SvMatrixApplyJoinNode

## Logic
    SvLogicNode
    SvSwitchNode
    SvNeuroElman1LNode

## Viz
    ViewerNode2
    SvBmeshViewerNodeMK2
    IndexViewerNode
    Sv3DviewPropsNode

## Text
    ViewerNodeTextMK2
    SvTextInNode
    SvTextOutNode
    NoteNode
    GTextNode
    SvDebugPrintNode
    SvStethoscopeNode

## Scene
    SvObjectsNodeMK3
    SvObjRemoteNodeMK2
    SvFrameInfoNode
    SvEmptyOutNode
    SvInstancerNode
    SvDupliInstancesMK4
    SvGetPropNode
    SvSetPropNode

## Objects
    SvVertexGroupNodeMK2
    SvVertexColorNodeMK2

## Layout
    WifiInNode
    WifiOutNode
    NodeReroute
    ConverterNode

## Network
    UdpClientNode

## Beta Nodes
    SvFormulaShapeNode
    SvScriptNodeMK2
    SvHeavyTriangulateNode
    SvPointOnMeshNodeMK2
    SvOBJRayCastNodeMK2
    SvSCNRayCastNodeMK2
    SvObjectToMeshNodeMK2
    SvObjInLite
    SvScriptNodeLite
    SvRndNumGen

## Alpha Nodes
    SvCurveViewerNode
    SvCurveViewerNodeAlt
    SvPolylineViewerNode
    SvTypeViewerNode
    SvJoinTrianglesNode
    SvCacheNode
    SvInsetSpecial
    SvSkinViewerNodeMK1b
    SvCSGBooleanNode
    SvParticlesNode
    SvUVtextureNode
    SvNumpyArrayNode
    SvNodeRemoteNode
    SvGetDataObjectNode
    SvSetDataObjectNodeMK2
    SvObjEdit
    SvSortObjsNode
    SvFilterObjsNode
    SvBMVertsNode
    SvBMOpsNode
    SvBMinputNode
    SvBMoutputNode
    SvBMtoElementNode
    SvExecNodeMod
    SvSeparateMeshNodeMK2
