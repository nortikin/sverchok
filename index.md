> ### This file is parsed by menu.py
>
> The following rules apply to editing this file:
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
    ImageNode

## Generators Extended
    SvBoxRoundedNode
    SvBricksNode
    SvPolygonGridNode
    HilbertNode
    Hilbert3dNode
    HilbertImageNode
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

## Curves @ Primitives
    SvExLineCurveNode
    SvCircleCurveMk2Node
    SvEllipseCurveNode
    SvRoundedRectangleNode
    SvArc3ptCurveNode
    SvArcSedCurveNode
    SvExCatenaryCurveNode
    SvFreeCadHelixNode
    ---
    SvExPolylineNode
    SvExFilletPolylineNode
    SvKinkyCurveNode
    SvBiArcNode
    SvPolyArcNode

## Curves @ NURBS
    SvExNurbsCurveNode
    SvApproxNurbsCurveMk2Node
    SvExInterpolateNurbsCurveNode
    SvDeconstructCurveNode
    ---
    SvCurveInsertKnotNode
    SvCurveRemoveKnotNode
    SvCurveRemoveExcessiveKnotsNode
    ---
    SvAdaptivePlotNurbsCurveNode

## Curves @ Bezier
    SvBezierSplineNode
    SvExBezierCurveFitNode

## Curves
    @ Primitives
    SvExCurveFormulaNode
    SvExCubicSplineNode
    SvTangentsCurveNode
    SvExRbfCurveNode
    SvExCirclifyNode
    @ Bezier
    @ NURBS
    ---
    SvExMarchingSquaresNode
    SvExMSquaresOnSurfaceNode
    ---
    SvExApplyFieldToCurveNode
    SvExCastCurveNode
    SvProjectCurveSurfaceNode
    SvOffsetCurveMk2Node
    SvCurveOffsetOnSurfaceNode
    SvExIsoUvCurveNode
    SvExCurveOnSurfaceNode
    ---
    SvExCurveLerpCurveNode
    SvSortCurvesNode
    SvExConcatCurvesNode
    SvExBlendCurvesMk2Node
    SvExFlipCurveNode
    SvReparametrizeCurveNode
    SvExSurfaceBoundaryNode
    ---
    SvIntersectNurbsCurvesNode
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
    SvAdaptivePlotCurveNode
    SvExEvalCurveNode

## Surfaces @ NURBS
    SvExNurbsSurfaceNode
    SvExApproxNurbsSurfaceNode
    SvExInterpolateNurbsSurfaceNode
    SvNurbsLoftNode
    SvNurbsSweepNode
    SvNurbsBirailNode
    SvGordonSurfaceNode
    SvDeconstructSurfaceNode
    ---
    SvExQuadsToNurbsNode
    ---
    SvSurfaceInsertKnotNode
    SvSurfaceRemoveKnotNode
    SvSurfaceRemoveExcessiveKnotsNode

## Surfaces
    SvExPlaneSurfaceNode
    SvExSphereNode
    SvExSurfaceFormulaNode
    SvInterpolatingSurfaceNode
    SvExMinimalSurfaceNode
    SvExMinSurfaceFromCurveNode
    @ NURBS
    ---
    SvExRevolutionSurfaceNode
    SvExTaperSweepSurfaceNode
    SvBendCurveSurfaceNode
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
    SvRotationFieldNode
    SvExImageFieldNode
    SvMeshSurfaceFieldNode
    SvExMeshNormalFieldNode
    SvExVoronoiFieldNode
    SvExMinimalScalarFieldNode
    SvExMinimalVectorFieldNode
    SvExNoiseVectorFieldNode
    ---
    SvExScalarFieldMathNode
    SvExVectorFieldMathNode
    SvScalarFieldCurveMapNode
    SvExFieldDiffOpsNode
    SvScalarFieldCurvatureNode
    SvExMergeScalarFieldsNode
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

## Solids @ Make Face
    SvSolidPolygonFaceNode
    SvSolidWireFaceNode
    SvProjectTrimFaceNode

## Solids @ Analyze
    SvSolidValidateNode
    SvRefineSolidNode
    SvIsSolidClosedNode
    SvSolidCenterOfMassNode
    SvSolidFaceAreaNode
    SvSolidAreaNode
    SvSolidVolumeNode
    SvSolidBoundBoxNode

## Solids
    SvBoxSolidNode
    SvCylinderSolidNode
    SvConeSolidNode
    SvSphereSolidNode
    SvToursSolidNode
    @ Make Face
    SvSolidFaceExtrudeNode
    SvSolidFaceSolidifyNode
    SvSolidFaceRevolveNode
    SvSweepSolidFaceNode
    SvRuledSolidNode
    SvSolidFromFacesNode
    ---
    SvTransformSolidNode
    SvChamferSolidNode
    SvFilletSolidNode
    SvSolidBooleanNode
    SvSolidGeneralFuseNode
    SvMirrorSolidNode
    SvOffsetSolidNode
    SvSplitSolidNode
    SvHollowSolidNode
    ---
    SvIsInsideSolidNode
    SvSolidDistanceNode
    SvSliceSolidNode
    SvMeshToSolidNode
    SvSolidToMeshNodeMk2
    SvSolidVerticesNode
    SvSolidEdgesNode
    SvSolidFacesNode
    SvSelectSolidNode
    SvCompoundSolidNode
    @ Analyze
    SvSolidViewerNode

## Analyzers
    SvBBoxNodeMk3
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
    SvGetNormalsNodeMk2
    SvIntersectLineSphereNode
    SvIntersectCircleCircleNode
    SvIntersectPlanePlaneNode
    SvKDTreeNodeMK2
    SvKDTreeEdgesNodeMK2
    SvKDTreePathNode
    SvNearestPointOnMeshNode
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
    SvMeshSelectNodeMk2
    SvSelectSimilarNode
    SvChessSelection

## Spatial
    SvHomogenousVectorField
    SvRandomPointsOnMesh
    SvPopulateSurfaceMk2Node
    SvPopulateSolidMk2Node
    SvFieldRandomProbeMk3Node
    ---
    DelaunayTriangulation2DNode
    SvDelaunay2DCdt
    SvDelaunay3dMk2Node
    ---
    Voronoi2DNode
    SvExVoronoi3DNode
    SvExVoronoiSphereNode
    SvVoronoiOnSurfaceNode
    SvVoronoiOnMeshNode
    SvVoronoiOnSolidNode
    ---
    SvLloyd2dNode
    SvLloyd3dNode
    SvLloydOnSphereNode
    SvLloydOnMeshNode
    SvLloydSolidNode
    SvLloydSolidFaceNode
    ---
    SvConvexHullNodeMK2
    SvConcaveHullNode

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
    SvMeshCleanNode
    SvSeparateMeshNode
    SvSeparatePartsToIndexes
    SvEdgenetToPathsNode
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
    SvPols2EdgsNodeMk2
    SvMeshJoinNodeMk2
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
    SvSplitEdgesMk3Node
    SvRigidOrigamiNode
    ---
    SvFollowActiveQuads
    SvFlatGeometryNode

## Modifier Make
    LineConnectNodeMK2
    ---
    SvSubdivideNodeMK2
    SvSubdivideToQuadsNode
    SvOffsetLineNode
    SvContourNode
    ---
    SvDualMeshNode
    SvDiamondMeshNode
    SvClipVertsNode
    ---
    SvBevelCurveNode
    SvAdaptiveEdgeNode
    SvAdaptivePolygonsNodeMk3
    SvDuplicateAlongEdgeNode
    SvFractalCurveNode
    SvFrameworkNode
    SvSolidifyNodeMk2
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
    SvUniqueItemsNode
    SvFixEmptyObjectsNode
    SvDatetimeStrings
    SvVDAttrsNodeMk2
    SvPolygonSortNode
    SvFindClosestValue
    SvMultiCacheNode

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
    SvIndexListNode

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
    SvListLevelsNode

## Dictionary
    SvDictionaryIn
    SvDictionaryOut

## CAD
    SvBevelNode
    SvIntersectEdgesNodeMK3
    SvOffsetNode
    SvInsetSpecialMk2
    SvInsetFaces
    SvLatheNode
    SvSmoothNode
    SvRelaxMeshNode
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
    SvMapRangeNode
    SvEasingNode
    SvCurveMapperNode
    SvMixNumbersNode
    SvMixInputsNode
    ---
    SvGenFibonacci
    SvGenExponential
    SvOscillatorNode
    SvSmoothNumbersNode

## Vector
    GenVectorsNode
    VectorsOutNode
    SvAxisInputNodeMK2
    SvVectorMathNodeMK3
    VertsDelDoublesNode
    SvVectorRewire
    ---
    SvVertSortNode
    SvQuadGridSortVertsNode
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
    SvNoiseNodeMK3
    SvTurbulenceNode
    SvLacunarityNode
    SvVectorFractal

## Matrix
    SvMatrixInNodeMK4
    SvMatrixOutNodeMK2
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

## Color
    SvColorInputNode
    SvColorsInNodeMK1
    SvColorsOutNodeMK1
    SvColorMixNode
    SvFormulaColorNode
    SvColorRampNode
    ---
    SvTextureEvaluateNodeMk2

## Logic
    SvLogicNode
    SvSwitchNodeMK2
    SvInputSwitchNodeMOD
    SvNeuroElman1LNode
    SvCustomSwitcher
    SvRangeSwitchNode
    ---
    SvLoopInNode
    SvLoopOutNode
    ---
    SvEvolverNode
    SvGenesHolderNode

## Viz
    Sv3DviewPropsNode
    ---
    SvViewerDrawMk4
    SvMatrixViewer28
    SvIDXViewer28
    SvViewer2D
    ---
    SvMeshViewer
    SvCurveViewerNodeV28
    SvPolylineViewerNode
    SvTypeViewerNodeV28
    SvSkinViewerNodeV28
    SvMetaballOutNode
    SvBezierCurveOutNode
    SvNurbsCurveOutNode
    SvNurbsSurfaceOutNode
    ---
    SvInstancerNodeMK3
    SvDupliInstancesMK5
    SvDupliInstancesLite
    ---
    SvLightViewerNode
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
    ---
    SvStringsToolsNode

## BPY Data
    SvGetPropNode
    SvSetPropNode
    SvObjRemoteNodeMK2
    SvNodeRemoteNodeMK2
    SvGetAssetPropertiesMK2
    SvSetDataObjectNodeMK2
    SvSortObjsNode
    SvFilterObjsNode
    SvSetMeshAttributeNode
    SvPointOnMeshNodeMK2
    SvOBJRayCastNodeMK2
    SvSCNRayCastNodeMK2
    SvSetLoopNormalsNode
    SvSetCollection

## Scene
    SvGetObjectsData
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

## Objects
    SvVertexGroupNodeMK2
    SvVertexColorNodeMK3
    SvAssignMaterialListNode
    SvMaterialIndexNode
    SvSetCustomUVMap

## Exchange
    SvExNurbsToJsonNode
    SvExJsonToNurbsNode
    SvImportSolidNode
    SvExportSolidNode
    SvReceiveFromSorcarNode
    SvExportGcodeNode

## Script
    SvFormulaNodeMk5
    SvFormulaInterpolateNode
    SvExecNodeMod
    SvProfileNodeMK3
    SvMeshEvalNode
    SvGenerativeArtNode
    SvTopologySimple
    ---
    SvScriptNodeLite

## Network
    UdpClientNode
    SvFilePathNode

## Layout
    WifiInNode
    WifiOutNode
    NodeReroute
    ConverterNode

## Pulga Physics
    SvPulgaPhysicsSolverNode
    SvPulgaVectorForceNode
    SvPulgaSpringsForceNode
    SvPulgaDragForceNode
    SvPulgaPinForceNode
    SvPulgaTimedForceNode
    SvPulgaCollisionForceNode
    SvPulgaAttractionForceNode
    SvPulgaAlignForceNode
    SvPulgaFitForceNode
    SvPulgaObstacleForceNode
    SvPulgaRandomForceNode
    SvPulgaBoundingBoxForceNode
    SvPulgaInflateForceNode
    SvPulgaAttractorsForceNodeMk2
    SvPulgaAngleForceNode
    SvPulgaVortexForceNode
    SvPulgaPhysicsNode

## SVG
    SvSvgDocumentNode
    SvSvgCircleNode
    SvSvgPathNodeMk2
    SvSvgMeshNode
    SvSvgTextNode
    SvSvgDimensionNode
    SvSvgGroupNode
    SvSvgFillStrokeNodeMk2
    SvSvgPatternNode

## Beta Nodes
    SvFormulaShapeNode
    SvHeavyTriangulateNode
    SvMeshUVColorNode
    SvUVPointonMeshNode
    SvSampleUVColorNode
    SvSubdivideLiteNode
    SvExtrudeSeparateLiteNode
    SvUnsubdivideNode
    SvLimitedDissolveMK2
    SvArmaturePropsNode
    SvLatticePropsNode
    ---
    SvSculptMaskNode
    SvSelectMeshVerts
    SvSetCustomMeshNormals
    ---
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
    SvSNFunctorB
    SvParticlesMK2Node
    SvJoinTrianglesNode
    SvListSliceLiteNode
    SvCacheNode
    SvUVtextureNode
    SvSeparateMeshNodeMK2
    SvMultiExtrudeAlt
    SvPlanarEdgenetToPolygons
    SvSweepModulator
    ---
    SvGetPropNodeMK2
    SvSetPropNodeMK2
