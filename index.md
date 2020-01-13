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
    SvPentagonTilerNode

## Analyzers
    SvBBoxNodeMk2
    SvComponentAnalyzerNode
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
    SvPointInside
    SvProportionalEditNode
    SvWavePainterNode
    SvRaycasterLiteNode
    SvOBJInsolationNode
    SvDeformationNode
    SvLinkedVertsNode
    SvProjectPointToLine
    ---
    SvMeshSelectNode
    SvSelectSimilarNode
    SvChessSelection

## Transforms
    SvRotationNodeMK2
    SvScaleNodeMK2
    SvMoveNodeMK2
    SvSymmetrizeNode
    SvMirrorNodeMk2
    MatrixApplyNode
    SvBarycentricTransformNode
    SvAlignMeshByMesh
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
    SvSeparatePartsToIndexes
    SvLimitedDissolve
    SvPlanarFacesNode
    SvSplitFacesNode
    SvMeshBeautify
    SvTriangulateNode
    SvMakeMonotone
    ---
    PolygonBoomNode
    SvDissolveFaces2D
    Pols2EdgsNode
    SvMeshJoinNode
    ---
    SvFillsHoleNode
    SvRecalcNormalsNode
    SvFlipNormalsNode
    ---
    SvExtrudeEdgesNodeMk2
    SvExtrudeSeparateNode
    SvExtrudeRegionNode
    SvVertMaskNode
    SvSplitEdgesNode
    ---
    SvFollowActiveQuads

## Modifier Make
    LineConnectNodeMK2
    ---
    SvConvexHullNodeMK2
    SvSubdivideNode
    DelaunayTriangulation2DNode
    SvDelaunay2DCdt
    Voronoi2DNode
    SvOffsetLineNode
    SvContourNode
    SvDualMeshNode
    SvRandomPointsOnMesh
    ---
    SvBevelCurveNode
    SvAdaptiveEdgeNode
    SvAdaptivePolygonsNodeMk2
    SvDuplicateAlongEdgeNode
    SvFractalCurveNode
    SvFrameworkNode
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
    
## Dictionary
    SvDictionaryIn
    SvDictionaryOut

## CAD
    SvBevelNode
    SvIntersectEdgesNodeMK2
    SvOffsetNode
    SvInsetSpecial
    SvInsetFaces
    SvLatheNode
    SvSmoothNode
    SvSmoothLines
    ---
    CrossSectionNode
    SvBisectNode
    SvEdgesToFaces2D
    SvMergeMesh2D
    SvMergeMesh2DLite
    SvCropMesh2D
    SvWafelNode

## Number
    SvNumberNode
    SvScalarMathNodeMK4
    SvGenNumberRange
    SvListInputNode
    SvRndNumGen
    RandomNode
    Float2IntNode
    ---
    SvExecNodeMod
    SvMapRangeNode
    SvEasingNode
    SvMixNumbersNode
    SvMixInputsNode
    SvFormulaNodeMk3
    ---
    SvGenFibonacci
    SvGenExponential
    SvOscillatorNode

## Vector
    GenVectorsNode
    VectorsOutNode
    SvAxisInputNodeMK2
    SvVectorMathNodeMK3
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
    SvSwitchNodeMK2
    SvInputSwitchNodeMOD
    SvNeuroElman1LNode
    SvCustomSwitcher

## Viz
    Sv3DviewPropsNode
    ---
    SvVDExperimental
    SvMatrixViewer28
    SvIDXViewer28
    ---
    SvBmeshViewerNodeV28
    SvCurveViewerNodeV28
    SvPolylineViewerNodeV28
    SvTypeViewerNodeV28
    SvSkinViewerNodeV28
    SvMetaballOutNode
    ---
    SvEmptyOutNode
    ---
    SvTextureViewerNode
    SvTextureViewerNodeLite
    SvWaveformViewer

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
    SvAssignMaterialListNode
    SvMaterialIndexNode
    SvSetCustomUVMap

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
