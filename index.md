> ### This file is parsed by menu.py
>
> The following strict rules apply to editing this file:
>
> - do not use tabs, anywhere
> - indent the Node's line using 4 spaces
> - if you aren't sure, follow the existing convention
>
> Failing to follow these points will break the node category parser.

## Generator
    SvLineNodeMK3
    SvPlaneNodeMK2
    SvNGonNode
    SvBoxNode
    SvCircleNode
    SvCylinderNodeMK2
    SphereNode
    SvIcosphereNode
    SvTorusNode
    SvSuzanneNode
    SvCricketNode
    ---
    BasicSplineNode
    SvQuadraticSplineNode
    svBasicArcNode
    RandomVectorNodeMK2
    SvScriptNodeLite
    SvSNFunctorB
    ImageNode

## Generators Extended
    SvBoxRoundedNode
    SvBricksNode
    SvPolygonGridNode
    HilbertNode
    Hilbert3dNode
    HilbertImageNode
    SvProfileNodeMK3
    SvMeshEvalNode
    SvGenerativeArtNode
    SvImageComponentsNode
    SvTorusKnotNode
    SvRingNode
    SvEllipseNode
    SvSuperEllipsoidNode
    SvRegularSolid
    SvConicSectionNode
    SvTriangleNode

## Analyzers
    SvBBoxNodeMk2
    SvDiameterNode
    SvVolumeNode
    SvAreaNode
    DistancePPNode
    SvDistancePointLineNode
    SvDistancePointPlaneNode
    SvDistancetLineLineNode
    SvPathLengthNode
    CentersPolsNodeMK3
    GetNormalsNode
    VectorNormalNode
    SvIntersectLineSphereNode
    SvIntersectCircleCircleNode
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
    SvDeformationNode
    SvLinkedVertsNode

## Transforms
    SvRotationNodeMK2
    SvScaleNodeMK2
    SvMoveNodeMK2
    SvMirrorNode
    MatrixApplyNode
    SvBarycentricTransformNode
    ---
    Svb28MatrixArrayNode
    ---
    SvTransformSelectNode
    SvSimpleDeformNode
    SvBendAlongPathNode
    SvBendAlongSurfaceNode
    SvRandomizeVerticesNode

## Modifier Change
    SvDeleteLooseNode
    SvRemoveDoublesNode
    SvSeparateMeshNode
    SvLimitedDissolve
    SvMeshBeautify
    SvTriangulateNode
    ---
    PolygonBoomNode
    Pols2EdgsNode
    SvMeshJoinNode
    ---
    SvFillsHoleNode
    SvRecalcNormalsNode
    SvFlipNormalsNode
    ---
    SvExtrudeEdgesNode
    SvExtrudeSeparateNode
    SvExtrudeRegionNode
    SvVertMaskNode
    SvSplitEdgesNode

## Modifier Make
    LineConnectNodeMK2
    ---
    SvConvexHullNodeMK2
    SvSubdivideNode
    DelaunayTriangulation2DNode
    Voronoi2DNode
    SvOffsetLineNode
    SvContourNode
    SvDualMeshNode
    ---
    SvBevelCurveNode
    SvAdaptiveEdgeNode
    SvAdaptivePolygonsNodeMk2
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
    SvMaskToIndexNode
    SvIndexToMaskNode
    SvCalcMaskNode

## List Mutators
    SvListModifierNode
    SvFixEmptyObjectsNode
    SvDatetimeStrings
    SvVDAttrsNode
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
    SvListItemNode
    SvListItemInsertNode
    ListReverseNode
    ListShuffleNode
    ListSortNodeMK2
    ListFlipNode

## CAD
    SvBevelNode
    SvIntersectEdgesNodeMK2
    SvOffsetNode
    SvInsetSpecial
    SvLatheNode
    SvSmoothNode
    SvSmoothLines
    ---
    CrossSectionNode
    SvBisectNode
    SvWafelNode

## Number
    SvNumberNode
    SvScalarMathNodeMK4
    GenListRangeIntNode
    SvGenFloatRange
    SvListInputNode
    SvRndNumGen
    RandomNode
    Float2IntNode
    ---
    SvExecNodeMod
    SvMapRangeNode
    SvEasingNode
    SvMixNumbersNode
    SvFormulaNodeMk3
    ---
    SvGenFibonacci
    SvGenExponential
    SvOscillatorNode

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
    SvVectorLerp
    SvInterpolationStripesNode
    SvInterpolationNodeMK3
    SvInterpolationNodeMK2
    SvLinearApproxNode
    ---
    SvHomogenousVectorField
    SvNoiseNodeMK2
    SvTurbulenceNode
    SvLacunarityNode
    SvVectorFractal

## Matrix
    SvMatrixGenNodeMK2
    MatrixOutNode
    SvMatrixApplyJoinNode
    SvIterateNode
    MatrixDeformNode
    SvMatrixValueIn
    SvMatrixEulerNode
    MatrixShearNode
    SvMatrixNormalNode
    SvMatrixTrackToNode
    SvMatrixMathNode
    MatrixInterpolationNode

## Quaternion
    SvQuaternionInNode
    SvQuaternionOutNode
    SvQuaternionMathNode

## Logic
    SvLogicNode
    SvSwitchNode
    SvInputSwitchNodeMOD
    SvNeuroElman1LNode

## Viz
    Sv3DviewPropsNode
    ---
    SvMatrixViewer28
    SvVDBasicLines
    SvVDExperimental
    ---
    SvIDXViewer28
    ---
    SvBmeshViewerNodeV28
    SvCurveViewerNodeV28
    SvPolylineViewerNodeV28
    SvTypeViewerNodeV28
    SvSkinViewerNodeV28
    SvMetaballOutNode
    ---
    SvTextureViewerNode
    SvTextureViewerNodeLite

## Text
    ViewerNodeTextMK3
    SvTextInNodeMK2
    SvTextOutNodeMK2
    NoteNode
    SvDataShapeNode
    SvStethoscopeNodeMK2
    SvDebugPrintNode

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
    UdpClientNode

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
    SvArmaturePropsNode
    SvLatticePropsNode
    ---
    SvColorsInNodeMK1
    SvColorInputNode
    SvColorsOutNodeMK1
    ---
    SvSculptMaskNode
    SvSelectMeshVerts
    SvSetCustomMeshNormals
    ---
    SvSpiralNode
    SvCombinatoricsNode

## Alpha Nodes
    SvBManalyzinNode
    SvBMObjinputNode
    SvBMoutputNode
    SvBMtoElementNode
    SvBMOpsNodeMK2
    ---
    SvCSGBooleanNodeMK2
    SvNumpyArrayNode
    SvParticlesNode
    SvParticlesMK2Node
    SvJoinTrianglesNode
    SvListSliceLiteNode
    SvCacheNode
    SvUVtextureNode
    SvSeparateMeshNodeMK2
    SvMultiExtrudeAlt
    SvPlanarEdgenetToPolygons
    SvPulgaPhysicsNode
    SvTopologySimple
