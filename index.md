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

## Generator
    SvLineNodeMK3
    SvPlaneNodeMK2
    SvNGonNode
    SvBoxNode
    SvCircleNode
    CylinderNode
    SvCylinderNodeMK2
    SphereNode
    SvIcosphereNode
    SvTorusNode
    SvSuzanneNode
    ---
    BasicSplineNode
    svBasicArcNode
    RandomVectorNodeMK2
    SvScriptNodeLite
    ImageNode

## Generators Extended
    SvBoxRoundedNode
    SvBricksNode
    SvPolygonGridNode
    HilbertNode
    Hilbert3dNode
    HilbertImageNode
    SvProfileNodeMK2
    SvProfileNodeMK3
    SvMeshEvalNode
    SvGenerativeArtNode
    SvImageComponentsNode
    SvScriptNode
    SvTorusKnotNode
    SvRingNode
    SvEllipseNode
    SvSuperEllipsoidNode
    SvSmoothLines
    SvRegularSolid

## Analyzers
    SvBBoxNode
    SvDiameterNode
    SvVolumeNode
    AreaNode
    DistancePPNode
    SvDistancePointLineNode
    SvDistancePointPlaneNode
    SvDistancetLineLineNode
    SvPathLengthNode
    CentersPolsNodeMK2
    CentersPolsNodeMK3
    GetNormalsNode
    VectorNormalNode
    SvIntersectLineSphereNode
    SvIntersectPlanePlaneNode
    SvKDTreeNodeMK2
    SvKDTreeEdgesNodeMK2
    SvKDTreePathNode
    SvBvhOverlapNodeNew
    SvMeshFilterNode
    SvEdgeAnglesNode
    SvMeshSelectNode
    SvSelectSimilarNode
    SvPointInside
    SvProportionalEditNode
    SvRaycasterLiteNode
    SvOBJInsolationNode
    EvaluateImageNode
    SvDeformationNode
    SvLinkedVertsNode

## Transforms
    SvRotationNode
    SvScaleNodeMK2
    SvMoveNodeMK2
    SvMirrorNode
    MatrixApplyNode
    SvSimpleDeformNode
    SvBarycentricTransformNode
    SvAlignMeshByMesh

## Modifier Change
    SvDeleteLooseNode
    SvRemoveDoublesNode
    SvSeparateMeshNode
    SvLimitedDissolve
    SvMeshBeautify
    ---
    PolygonBoomNode
    Pols2EdgsNode
    SvMeshJoinNode
    SvMeshSwitchNode
    ---
    SvBevelNode
    SvSubdivideNode
    SvSmoothNode
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
    SvBendAlongPathNode
    SvBendAlongSurfaceNode
    SvVertMaskNode
    SvTransformSelectNode
    SvSplitEdgesNode

## Modifier Make
    LineConnectNodeMK2
    SvLatheNode
    SvBevelCurveNode
    SvConvexHullNode
    SvConvexHullNodeMK2
    DelaunayTriangulation2DNode
    Voronoi2DNode
    SvWafelNode
    CrossSectionNode
    SvBisectNode
    ---
    SvAdaptiveEdgeNode
    AdaptivePolsNode
    SvDuplicateAlongEdgeNode
    SvFractalCurveNode
    SvSolidifyNode
    SvWireframeNode
    SvPipeNode
    SvMatrixTubeNode

## List Masks
    MaskListNode
    SvMaskJoinNode
    SvMaskConvertNode
    SvCalcMaskNode

## List Mutators
    SvListModifierNode
    SvFixEmptyObjectsNode
    SvDatetimeStrings
    SvPolygonSortNode

## List Main
    ListJoinNode
    ZipNode
    ListLevelsNode
    ListLengthNode
    ListSumNodeMK2
    ListMatchNode
    ListFuncNode
    SvListDecomposeNode
    SvListStatisticsNode

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
    SvScalarMathNodeMK2
    Formula2Node
    SvFormulaNodeMk3
    SvExecNodeMod
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
    SvMixInputsNode

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
    SvLinearApproxNode
    ---
    SvHomogenousVectorField
    SvNoiseNodeMK2
    SvVectorFractal
    SvLacunarityNode
    SvTurbulenceNode

## Matrix
    SvMatrixGenNodeMK2
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
    SvInputSwitchNode
    SvNeuroElman1LNode
    SvCustomSwitcher

## Viz
    ViewerNode2
    SvBmeshViewerNodeMK2
    IndexViewerNode
    SvMetaballOutNode
    SvTextureViewerNode
    Sv3DviewPropsNode

## Text
    ViewerNodeTextMK3
    SvTextInNodeMK2
    SvTextOutNodeMK2
    NoteNode
    SvDataShapeNode
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
    SvCurveInputNode
    SvObjEdit
    SvFrameInfoNodeMK2
    SvLampOutNode
    SvEmptyOutNode
    SvInstancerNode
    SvDupliInstancesMK4
    SvFCurveInNodeMK1

## Objects
    SvVertexGroupNodeMK2
    SvVertexColorNodeMK3

## Layout
    WifiInNode
    WifiOutNode
    NodeReroute
    ConverterNode

## Network
    SvUdpClientNodeMK2

## Beta Nodes
    SvFormulaShapeNode
    SvHeavyTriangulateNode
    SvFormulaDeformMK2Node
    SvFormulaColorNode
    SvMeshUVColorNode
    SvUVPointonMeshNode
    SvSampleUVColorNode
    SvSubdivideLiteNode
    SvExtrudeSeparateLiteNode
    SvBVHnearNewNode
    SvUnsubdivideNode
    SvLimitedDissolveMK2
    SvMetaballOutLiteNode
    SvArmaturePropsNode
    SvLatticePropsNode
    ---
    SvColorsInNodeMK1
    SvColorInputNode
    SvColorsOutNodeMK1
    ---
    SvMatrixNormalNode
    SvMatrixTrackToNode
    SvMatrixMathNode
    ---
    SvSculptMaskNode
    SvGreasePencilStrokes
    SvTextureViewerNodeLite
    SvSelectMeshVerts
    SvSetCustomMeshNormals
    ---
    SvSpiralNode
    SvExportGcodeNode
    SvCombinatoricsNode

## Alpha Nodes
    SvCurveViewerNode
    SvCurveViewerNodeAlt
    SvPolylineViewerNodeMK1
    SvTypeViewerNode
    SvSkinViewerNodeMK1b
    SvMatrixViewer
    ---
    SvBManalyzinNode
    SvBMObjinputNode
    SvBMoutputNode
    SvBMtoElementNode
    SvBMOpsNodeMK2
    ---
    SvInsetSpecial
    SvCSGBooleanNodeMK2
    SvNumpyArrayNode
    SvParticlesNode
    SvParticlesMK2Node
    SvJoinTrianglesNode
    SvListSliceLiteNode
    SvCacheNode
    SvUVtextureNode
    SvSeparateMeshNodeMK2
    SvIndexToMaskNode
    SvMultiExtrudeAlt
    SvOffsetLineNode
    SvContourNode
    SvPlanarEdgenetToPolygons
    SvSwitchNodeMK2
    ---
    SvQuaternionOutNode
    SvQuaternionInNode
    SvQuaternionMathNode
    SvPulgaPhysicsNode
    SvProjectPointToLine
