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
    SvScriptNodeLite    
    ImageNode
    SvTorusNode

## Generators Extended
    SvBoxRoundedNode
    HilbertNode
    Hilbert3dNode
    HilbertImageNode
    SvProfileNode
    SvMeshEvalNode
    SvGenerativeArtNode
    SvImageComponentsNode
    SvScriptNode
    SvTorusKnotNode
    SvHexaGridNode
    SvRingNode
    SvPlaneNodeMK2
    SvLineNodeMK2

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
    SvMeshSelectNode
    SvProportionalEditNode

## Transforms
    SvRotationNode
    SvScaleNode
    VectorMoveNode
    SvMirrorNode
    MatrixApplyNode
    SvSimpleDeformNode

## Modifier Change
    SvDeleteLooseNode
    SvRemoveDoublesNode
    SvSeparateMeshNode
    SvLimitedDissolve
    ---
    PolygonBoomNode
    Pols2EdgsNode
    SvMeshJoinNode
    ---
    SvBevelNode
    SvIntersectEdgesNodeMK2
    SvOffsetNode
    SvFillsHoleNode
    SvTriangulateNode
    ---
    SvFlipNormalsNode
    SvRecalcNormalsNode
    SvRandomizeVerticesNode
    ---
    SvIterateNode
    SvExtrudeEdgesNode
    SvExtrudeSeparateNode
    SvExtrudeRegionNode
    SvVertMaskNode
    SvTransformSelectNode

## Modifier Make
    LineConnectNodeMK2
    SvLatheNode
    SvConvexHullNode
    DelaunayTriangulation2DNode
    Voronoi2DNode
    SvWafelNode
    CrossSectionNode
    SvBisectNode
    ---
    SvAdaptiveEdgeNode
    AdaptivePolsNode
    SvDuplicateAlongEdgeNode
    SvSolidifyNode
    SvWireframeNode
    SvPipeNode
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
    SvNumberNode
    FloatNode
    IntegerNode
    Float2IntNode
    ScalarMathNode
    Formula2Node
    ---
    GenListRangeIntNode
    SvGenFloatRange
    SvMapRangeNode
    SvListInputNode
    SvGenFibonacci
    SvGenExponential
    ---
    SvRndNumGen
    RandomNode
    SvEasingNode
    SvMixNumbersNode

## Vector
    GenVectorsNode
    VectorsOutNode
    SvAxisInputNodeMK2
    SvVectorMathNodeMK2
    VertsDelDoublesNode
    SvVectorRewire
    ---
    SvVertSortNode
    VectorDropNode
    VectorPolarInNode
    VectorPolarOutNode
    SvAttractorNode
    ---
    EvaluateLineNode
    SvVectorLerp
    SvInterpolationStripesNode
    SvInterpolationNode
    SvInterpolationNodeMK2
    SvInterpolationNodeMK3
    ---
    SvNoiseNodeMK2
    SvVectorFractal
    SvLacunarityNode
    SvTurbulenceNode

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
    SvTextureViewerNode

## Text
    ViewerNodeTextMK2
    SvTextInNode
    SvTextOutNode
    NoteNode
    GTextNode
    SvDebugPrintNode
    SvStethoscopeNodeMK2

## BPY Data
    SvGetPropNode
    SvSetPropNode
    SvObjRemoteNodeMK2
    SvNodeRemoteNode
    SvGetAssetProperties
    SvSetDataObjectNodeMK2
    SvSortObjsNode
    SvFilterObjsNode
    SvObjectToMeshNodeMK2
    SvPointOnMeshNodeMK2
    SvOBJRayCastNodeMK2
    SvSCNRayCastNodeMK2

## Scene
    SvObjectsNodeMK3
    SvObjInLite
    SvObjEdit
    SvFrameInfoNodeMK2
    SvEmptyOutNode
    SvInstancerNode
    SvDupliInstancesMK4

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
    SvHeavyTriangulateNode
    SvColorsInNode
    SvColorsOutNode
    SvMatrixNormalNode
    SvSculptMaskNode
    SvGreasePencilStrokes

## Alpha Nodes
    SvCurveViewerNode
    SvCurveViewerNodeAlt
    SvPolylineViewerNodeMK1
    SvTypeViewerNode
    SvJoinTrianglesNode
    SvCacheNode
    SvInsetSpecial
    SvSkinViewerNodeMK1b
    SvCSGBooleanNode
    SvParticlesNode
    SvParticlesMK2Node
    SvUVtextureNode
    SvNumpyArrayNode
    SvBMVertsNode
    SvBMOpsNode
    SvBMinputNode
    SvBMoutputNode
    SvBMtoElementNode
    SvExecNodeMod
    SvSeparateMeshNodeMK2
    SvBvhOverlapNodeNew
