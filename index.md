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
    RandomVectorNodeMK3
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
    SvReceiveFromSorcarNode
    SvGenerativeArtNode
    SvImageComponentsNode
    SvWFCTextureNode
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
    SvEllipseCurveNode
    SvRoundedRectangleNode
    SvArc3ptCurveNode
    SvArcSedCurveNode
    SvExCatenaryCurveNode
    SvPolyArcNode
    SvExCurveFormulaNode
    SvExPolylineNode
    SvExFilletPolylineNode
    SvExCubicSplineNode
    SvBezierSplineNode
    SvExNurbsCurveNode
    SvKinkyCurveNode
    SvTangentsCurveNode
    SvExRbfCurveNode
    SvExCirclifyNode
    ---
    SvExApproxNurbsCurveNode
    SvExInterpolateNurbsCurveNode
    SvExBezierCurveFitNode
    SvExMarchingSquaresNode
    SvExMSquaresOnSurfaceNode
    ---
    SvExApplyFieldToCurveNode
    SvExCastCurveNode
    SvOffsetCurveMk2Node
    SvCurveOffsetOnSurfaceNode
    SvExIsoUvCurveNode
    SvExCurveOnSurfaceNode
    ---
    SvExCurveLerpCurveNode
    SvExConcatCurvesNode
    SvExBlendCurvesNode
    SvExFlipCurveNode
    SvReparametrizeCurveNode
    SvExSurfaceBoundaryNode
    ---
    SvExNearestPointOnCurveNode
    SvExOrthoProjectCurveNode
    SvExCurveEndpointsNode
    SvExCurveSegmentNode
    SvExCurveRangeNode
    SvExtendCurveNode
    SvSplitCurveNode
    SvExCurveLengthNode
    SvExCurveFrameNode
    SvCurveFrameOnSurfNode
    SvExCurveCurvatureNode
    SvExCurveTorsionNode
    SvExCurveExtremesNode
    SvExCurveZeroTwistFrameNode
    SvExSlerpCurveFrameNode
    SvExCurveLengthParameterNode
    SvLengthRebuildCurveNode
    SvExCrossCurvePlaneNode
    SvExCrossCurveSurfaceNode
    ---
    SvExEvalCurveNode

## Surfaces
    SvExPlaneSurfaceNode
    SvExSphereNode
    SvExSurfaceFormulaNode
    SvInterpolatingSurfaceNode
    SvExNurbsSurfaceNode
    SvExMinimalSurfaceNode
    SvExMinSurfaceFromCurveNode
    ---
    SvExApproxNurbsSurfaceNode
    SvExInterpolateNurbsSurfaceNode
    SvExQuadsToNurbsNode
    ---
    SvExRevolutionSurfaceNode
    SvExTaperSweepSurfaceNode
    SvExExtrudeCurveVectorNode
    SvExExtrudeCurveCurveSurfaceNode
    SvExExtrudeCurvePointNode
    SvPipeSurfaceNode
    SvExCurveLerpNode
    SvExSurfaceLerpNode
    SvCoonsPatchNode
    SvBlendSurfaceNode
    SvExApplyFieldToSurfaceNode
    ---
    SvExSurfaceDomainNode
    SvExSurfaceSubdomainNode
    SvFlipSurfaceNode
    SvSwapSurfaceNode
    SvReparametrizeSurfaceNode
    SvSurfaceNormalsNode
    SvSurfaceGaussCurvatureNode
    SvSurfaceCurvaturesNode
    SvExSurfaceExtremesNode
    SvExNearestPointOnSurfaceNode
    SvExOrthoProjectSurfaceNode
    SvExRaycastSurfaceNode
    ---
    SvExImplSurfaceRaycastNode
    SvExMarchingCubesNode
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
    SvExMeshNormalFieldNode
    SvExVoronoiFieldNode
    SvExMinimalScalarFieldNode
    SvExMinimalVectorFieldNode
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
    SvExScalarFieldGraphNode

## Solids
   SvBoxSolidNode
   SvCylinderSolidNode
   SvConeSolidNode
   SvSphereSolidNode
   SvToursSolidNode
   SvTransformSolidNode
   SvChamferSolidNode
   SvFilletSolidNode
   SvSolidBooleanNode
   SvMirrorSolidNode
   SvOffsetSolidNode
   SvIsInsideSolidNode
   SvSolidDistanceNode
   SvSliceSolidNode
   SvMeshToSolidNode
   SvSolidToMeshNodeMk2
   SvSolidVerticesNode
   SvSolidEdgesNode
   SvSolidFacesNode
   SvSolidViewerNode

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
    SvDissolveMeshElements
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
    SvExVoronoi3DNode
    SvExDelaunay3DNode
    SvExVoronoiSphereNode
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
    SvFindClosestValue

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
    ---
    SvEvolverNode
    SvGenesHolderNode

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
    SvInstancerNodeMK3
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
    SvDataShapeNode
    SvStethoscopeNodeMK2
    SvDebugPrintNode
    ---
    SvTextInNodeMK2
    SvTextOutNodeMK2
    ---
    NoteNode
    SvGTextNode

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
    SvFCurveInNodeMK1
    SvCollectionPicker
    SvBezierInNode
    SvExNurbsInNode
    ---
    SvSelectionGrabberLite
    SvObjEdit
    ---
    SvFrameInfoNodeMK2
    SvTimerNode
    ---
    SvInstancerNode
    SvDupliInstancesMK4
    SvLampOutNode

## Objects
    SvVertexGroupNodeMK2
    SvVertexColorNodeMK3
    SvAssignMaterialListNode
    SvMaterialIndexNode
    SvSetCustomUVMap

## Ladybug
    SvExLadyBugLocationNode
    SvExLadyBugSunPositionNode

## Exchange
    SvExNurbsToJsonNode
    SvExJsonToNurbsNode
    SvImportSolidNode
    SvExportSolidNode

## Network
    UdpClientNode
    SvFilePathNode

## Layout
    WifiInNode
    WifiOutNode
    NodeReroute
    ConverterNode

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
