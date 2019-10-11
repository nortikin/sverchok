==== INPUT

# Generator {OBJECT_DATAMODE}

    SvLineNodeMK3
    SvPlaneNodeMK2
    SvNGonNode
    SvBoxNode
    SvCircleNode
    SvCylinderNodeMK2
    SphereNode
    SvIcosphereNode
    SvTorusNode
    SvCricketNode
    ---
    BasicSplineNode
    svBasicArcNode
    RandomVectorNodeMK2
    SvScriptNodeLite
    SvProfileNodeMK3
    SvMeshEvalNode

# Generators Extended {PLUGIN}

    SvBoxRoundedNode
    SvBricksNode
    SvPolygonGridNode
    SvTorusKnotNode
    SvRingNode
    SvEllipseNode
    SvSuperEllipsoidNode
    ---
    ImageNode
    SvImageComponentsNode
    Hilbert3dNode
    HilbertNode
    SvRegularSolid

# Number {SV_NUMBER}

    SvNumberNode
    SvScalarMathNodeMK3
    GenListRangeIntNode
    SvGenFloatRange
    SvRndNumGen
    RandomNode
    Float2IntNode
    ---
    SvMapRangeNode
    SvEasingNode
    SvMixNumbersNode
    ---
    SvGenFibonacci
    SvGenExponential

# Vector {SV_VECTOR}

    GenVectorsNode
    VectorsOutNode
    SvAxisInputNodeMK2
    SvVectorRewire
    ---
    SvVectorMathNodeMK2
    SvVertSortNode
    SvAttractorNode
    ---
    VectorDropNode
    VectorPolarInNode
    VectorPolarOutNode
    ---
    SvVectorLerp
    EvaluateLineNode
    SvInterpolationStripesNode
    SvInterpolationNode
    SvInterpolationNodeMK2
    SvInterpolationNodeMK3
    SvLinearApproxNode
    ---
    SvHomogenousVectorField
    SvNoiseNodeMK2
    SvTurbulenceNode
    SvLacunarityNode
    SvVectorFractal

# Matrix {EMPTY_AXIS}

    SvMatrixGenNodeMK2
    MatrixOutNode
    MatrixDeformNode
    SvMatrixValueIn
    SvMatrixEulerNode
    MatrixShearNode
    MatrixInterpolationNode
    SvMatrixApplyJoinNode
    ---
    SvMatrixNormalNode
    SvMatrixTrackToNode
    SvMatrixMathNode

==== THROUGHPUT

# Transforms {EMPTY_ARROWS}

    SvRotationNodeMK2
    SvScaleNodeMK2
    SvMoveNodeMK2
    SvMirrorNode
    MatrixApplyNode
    SvSimpleDeformNode
    SvBarycentricTransformNode
    ---
    SvTransformSelectNode
    Svb28MatrixArrayNode
    SvIterateNode

# CAD {TOOL_SETTINGS}

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
    SvOffsetLineNode
    SvContourNode
    ---
    SvSubdivideLiteNode

# Modifier {MODIFIER}

    SvRemoveDoublesNode
    VertsDelDoublesNode
    SvLimitedDissolve
    SvRandomizeVerticesNode
    ---
    SvExtrudeEdgesNode
    SvExtrudeSeparateNode
    SvExtrudeRegionNode
    SvBendAlongPathNode
    SvBendAlongSurfaceNode
    SvSplitEdgesNode
    SvProportionalEditNode
    SvDeformationNode
    ---
    SvAdaptiveEdgeNode
    AdaptivePolsNode
    SvDuplicateAlongEdgeNode
    SvFractalCurveNode
    SvSolidifyNode
    SvWireframeNode
    SvPipeNode
    SvBevelCurveNode
    SvMatrixTubeNode

# Topology {MOD_EXPLODE} 

    LineConnectNodeMK2
    SvTopologySimple
    ---
    SvMeshJoinNode
    Pols2EdgsNode
    SvSeparateMeshNodeMK2
    PolygonBoomNode
    SvDeleteLooseNode
    ---
    SvMeshBeautify
    SvTriangulateNode
    SvJoinTrianglesNode
    SvFillsHoleNode
    SvPlanarEdgenetToPolygons
    ---
    SvRecalcNormalsNode
    SvFlipNormalsNode
    ---
    SvConvexHullNodeMK2
    SvSubdivideNode
    DelaunayTriangulation2DNode
    Voronoi2DNode

# List Iteration {NLA}

    ListMatchNode
    ZipNode
    ShiftNodeMK2
    ListRepeaterNode
    ListJoinNode
    ListSliceNode
    SvListSliceLiteNode
    SvListSplitNode
    ListFLNode
    ListReverseNode
    ListFlipNode
    ListShuffleNode
    ListSortNodeMK2

# Data Routing {NETWORK_DRIVE}
    WifiInNode
    WifiOutNode
    NodeReroute
    ConverterNode
    UdpClientNode
    ---
    SvLogicNode
    SvSwitchNode
    SvInputSwitchNodeMOD

==== OBSERVATIONS

# Analyze Entity {VIEWZOOM}

    SvBBoxNode
    SvDiameterNode
    SvVolumeNode
    SvAreaNode
    SvPathLengthNode
    CentersPolsNodeMK2
    CentersPolsNodeMK3
    GetNormalsNode
    VectorNormalNode
    SvEdgeAnglesNode
    ---
    SvMeshFilterNode
    SvPointInside
    SvMeshSelectNode
    SvRaycasterLiteNode
    SvOBJInsolationNode
    ---
    SvNeuroElman1LNode

# Analyze Relationship {CON_CHILDOF}

    SvSelectSimilarNode
    DistancePPNode
    SvIntersectLineSphereNode
    SvIntersectPlanePlaneNode
    SvDistancePointLineNode
    SvDistancePointPlaneNode
    SvDistancetLineLineNode
    SvKDTreeNodeMK2
    SvKDTreeEdgesNodeMK2
    SvKDTreePathNode
    SvBvhOverlapNodeNew
    SvLinkedVertsNode

# List Introspection {VIEWZOOM}

    SvDataShapeNode
    ---
    SvListModifierNode
    SvFixEmptyObjectsNode
    ListLengthNode
    ListSumNodeMK2
    SvListItemNode
    SvListItemInsertNode

# Data Formatting {SYSTEM}

    SvListInputNode
    SvListDecomposeNode
    ListLevelsNode
    ---
    SvDatetimeStrings
    SvVDAttrsNode
    SvExecNodeMod
    ListFuncNode
    Formula2Node
    SvFormulaNodeMk3
    ---
    SvTextInNodeMK2
    SvTextOutNodeMK2

# Masks {MOD_MASK}

    SvVertMaskNode
    MaskListNode
    SvMaskJoinNode
    SvMaskConvertNode
    SvMaskToIndexNode
    SvIndexToMaskNode
    SvCalcMaskNode

==== OUTPUT

# Viz {RESTRICT_VIEW_OFF}

    Sv3DviewPropsNode
    ---
    SvMatrixViewer28
    SvVDBasicLines
    SvVDExperimental
    ---
    SvStethoscopeNodeMK2
    SvIDXViewer28
    SvDebugPrintNode
    ---
    ViewerNodeTextMK3
    NoteNode
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

# BPY Data {FILE_BACKUP}

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

# Scene {FILE_IMAGE}

    SvObjectsNodeMK3
    SvObjInLite
    SvCurveInputNode
    SvObjEdit
    SvFrameInfoNodeMK2
    SvLampOutNode
    SvInstancerNode
    SvDupliInstancesMK4
    SvFCurveInNodeMK1
    ---
    SvVertexGroupNodeMK2
    SvVertexColorNodeMK3

==== PURGATORY

# Unsorted A {SV_ALPHA}

    SvFormulaShapeNode
    SvHeavyTriangulateNode
    SvFormulaDeformMK2Node
    SvFormulaColorNode
    SvMeshUVColorNode
    SvUVPointonMeshNode
    SvSampleUVColorNode
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
    SvSculptMaskNode
    SvSelectMeshVerts
    SvSetCustomMeshNormals
    ---
    SvSpiralNode

# Unsorted B {SV_BETA}

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
    SvCacheNode
    SvUVtextureNode
    SvMultiExtrudeAlt
    SvPulgaPhysicsNode
