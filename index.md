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
    SvLineNodeMK4
    SvSegmentGenerator
    SvPlaneNodeMk3
    SvNGonNode
    SvBoxNodeMk2
    SvCircleNode
    SvCylinderNodeMK2
    SphereNode
    SvIcosphereNode
    SvTorusNodeMK2
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
    SvTorusKnotNodeMK2
    SvRingNodeMK2
    SvEllipseNodeMK2
    SvSuperEllipsoidNode
    SvRegularSolid
    SvConicSectionNode
    SvTriangleNode
    SvPentagonTilerNode
    SvSpiralNodeMK2

## Curves
    SvExLineCurveNode
    SvExCircleNode
    SvRoundedRectangleNode
    SvArc3ptCurveNode
    SvArcSedCurveNode
    SvExCurveFormulaNode
    SvExPolylineNode
    SvExFilletPolylineNode
    SvExCubicSplineNode
    ---
    SvExApplyFieldToCurveNode
    SvExCastCurveNode
    SvExIsoUvCurveNode
    SvExCurveOnSurfaceNode
    ---
    SvExCurveLerpCurveNode
    SvExConcatCurvesNode
    SvExFlipCurveNode
    SvExSurfaceBoundaryNode
    ---
    SvExCurveEndpointsNode
    SvExCurveSegmentNode
    SvExCurveRangeNode
    SvSplitCurveNode
    SvExCurveLengthNode
    SvExCurveFrameNode
    SvExCurveCurvatureNode
    SvExCurveTorsionNode
    SvExCurveZeroTwistFrameNode
    SvExCurveLengthParameterNode
    SvLengthRebuildCurveNode
    ---
    SvExEvalCurveNode

## Surfaces
    SvExPlaneSurfaceNode
    SvExSphereNode
    SvExSurfaceFormulaNode
    SvInterpolatingSurfaceNode
    ---
    SvExRevolutionSurfaceNode
    SvExTaperSweepSurfaceNode
    SvExExtrudeCurveVectorNode
    SvExExtrudeCurveCurveSurfaceNode
    SvExExtrudeCurvePointNode
    SvExCurveLerpNode
    SvExSurfaceLerpNode
    SvExApplyFieldToSurfaceNode
    ---
    SvExSurfaceDomainNode
    SvExSurfaceSubdomainNode
    SvFlipSurfaceNode
    SvSwapSurfaceNode
    SvSurfaceNormalsNode
    SvSurfaceGaussCurvatureNode
    SvSurfaceCurvaturesNode
    ---
    SvExTessellateTrimSurfaceNode
    SvAdaptiveTessellateNode
    SvExEvalSurfaceNode

## Fields
    SvCoordScalarFieldNode
    SvExScalarFieldFormulaNode
    SvExVectorFieldFormulaNode
    SvExComposeVectorFieldNode
    SvExDecomposeVectorFieldNode
    SvExScalarFieldPointNode
    SvAttractorFieldNodeMk2
    SvExImageFieldNode
    SvExVoronoiFieldNode
    SvExNoiseVectorFieldNode
    ---
    SvExScalarFieldMathNode
    SvExMergeScalarFieldsNode
    SvExVectorFieldMathNode
    SvExFieldDiffOpsNode
    SvScalarFieldCurvatureNode
    ---
    SvExBendAlongCurveFieldNode
    SvExBendAlongSurfaceFieldNode
    ---
    SvExScalarFieldEvaluateNode
    SvExVectorFieldEvaluateNode
    SvExVectorFieldApplyNode
    ---
    SvExVectorFieldGraphNode
    SvExVectorFieldLinesNode

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
    SvPathLengthMk2Node
    SvOrigins
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
    SvLinearApproxNode
    SvCircleApproxNode
    SvSphereApproxNode
    SvInscribedCircleNode
    SvSteinerEllipseNode
    ---
    SvMeshSelectNode
    SvSelectSimilarNode
    SvChessSelection

## Transforms
    SvMoveNodeMk3
    SvRotationNodeMk3
    SvScaleNodeMk3
    SvSymmetrizeNode
    SvMirrorNodeMk2
    MatrixApplyNode
    SvBarycentricTransformNode
    SvAlignMeshByMesh
    ---
    SvTransformSelectNode
    SvTransformMesh
    SvSimpleDeformNode
    SvBendAlongPathNode
    SvBendAlongSurfaceNode
    SvDisplaceNodeMk2
    SvNoiseDisplaceNode
    SvRandomizeVerticesNode
    SvCastNode
    SvFormulaDeformMK2Node

## Modifier Change
    SvDeleteLooseNode
    SvMergeByDistanceNode
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
    SvEdgeBoomNode
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
    SvPokeFacesNode
    SvVertMaskNode
    SvSplitEdgesNode
    ---
    SvFollowActiveQuads

## Modifier Make
    LineConnectNodeMK2
    ---
    SvConvexHullNodeMK2
    SvSubdivideNodeMK2
    DelaunayTriangulation2DNode
    SvDelaunay2DCdt
    Voronoi2DNode
    SvOffsetLineNode
    SvContourNode
    SvRandomPointsOnMesh
    ---
    SvDualMeshNode
    SvDiamondMeshNode
    SvClipVertsNode
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
    SvConstantListNode
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
    SvListSortNode
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
    SvCutObjBySurfaceNode
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
    SvCurveMapperNode
    SvMixNumbersNode
    SvMixInputsNode
    SvFormulaNodeMk3
    SvFormulaInterpolateNode
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
    ---
    SvHomogenousVectorField
    SvFieldRandomProbeNode
    SvNoiseNodeMK2
    SvTurbulenceNode
    SvLacunarityNode
    SvVectorFractal

## Matrix
    SvMatrixInNodeMK4
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
    SvQuaternionInNodeMK2
    SvQuaternionOutNodeMK2
    SvQuaternionMathNode
    SvRotationDifference

## Logic
    SvLogicNode
    SvSwitchNodeMK2
    SvInputSwitchNodeMOD
    SvNeuroElman1LNode
    SvCustomSwitcher
    SvRangeSwitchNode

## Viz
    Sv3DviewPropsNode
    ---
    SvVDExperimental
    SvMatrixViewer28
    SvIDXViewer28
    SvViewer2D
    ---
    SvBmeshViewerNodeV28
    SvCurveViewerNodeV28
    SvPolylineViewerNodeV28
    SvTypeViewerNodeV28
    SvSkinViewerNodeV28
    SvMetaballOutNode
    SvNurbsCurveOutNode
    SvNurbsSurfaceOutNode
    ---
    SvGreasePencilStrokes
    SvEmptyOutNode
    ---
    SvTextureViewerNode
    SvTextureViewerNodeLite
    SvWaveformViewer
    SvConsoleNode

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
    SvNodeRemoteNodeMK2
    SvGetAssetPropertiesMK2
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
    SvInstancerNodeMK2
    SvDupliInstancesMK4
    SvFCurveInNodeMK1
    SvCollectionPicker
    SvSelectionGrabberLite
    SvTimerNode

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
    SvFormulaColorNode
    SvTextureEvaluateNodeMk2
    SvColorRampNode
    ---
    SvSculptMaskNode
    SvSelectMeshVerts
    SvSetCustomMeshNormals
    ---
    SvCombinatoricsNode
    SvFormulaNodeMk4    

## Alpha Nodes
    SvBManalyzinNode
    SvBMObjinputNode
    SvBMoutputNode
    SvBMtoElementNode
    SvBMOpsNodeMK2
    ---
    SvCSGBooleanNodeMK2
    SvNumpyArrayNode
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
    SvSweepModulator
    ---
    SvGetPropNodeMK2
    SvSetPropNodeMK2
