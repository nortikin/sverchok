
import numpy as np

import bpy
from bpy.props import EnumProperty, BoolProperty, IntProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, split_by_count
from sverchok.utils.surface.nurbs import SvGeomdlSurface
from sverchok.utils.surface.freecad import SvSolidFaceSurface
from sverchok.dependencies import geomdl, FreeCAD

if geomdl is not None:
    from geomdl import fitting

if FreeCAD is not None:
    import Part
    from Part import BSplineSurface


class SvExApproxNurbsSurfaceNodeMK2(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: NURBS Surface
    Tooltip: Approximate NURBS Surface
    """
    bl_idname = 'SvExApproxNurbsSurfaceNodeMK2'
    bl_label = 'Approximate NURBS Surface'
    bl_icon = 'SURFACE_NSURFACE'

    input_modes = [
            ('1D', "Single list", "List of all control points (concatenated)", 1),
            ('2D', "Separated lists", "List of lists of control points", 2)
        ]

    def update_sockets(self, context):
        self.inputs['USize'].hide_safe = self.input_mode == '2D'
        self.inputs['DegreeU'].hide_safe = (self.implementation == 'FREECAD') and ((self.input_mode == '1D') or (self.input_mode == '2D'))
        self.inputs['DegreeV'].hide_safe = (self.implementation == 'FREECAD') and ((self.input_mode == '1D') or (self.input_mode == '2D'))
        self.inputs['PointsCntU'].hide_safe = not (self.implementation == 'GEOMDL' and self.has_points_cnt)
        self.inputs['PointsCntV'].hide_safe = not (self.implementation == 'GEOMDL' and self.has_points_cnt)

        self.inputs['DegreeMin'].hide_safe = not (self.implementation == 'FREECAD')
        self.inputs['DegreeMax'].hide_safe = not (self.implementation == 'FREECAD')
        self.inputs['Tolerance'].hide_safe = not (self.implementation == 'FREECAD')
        self.inputs['LengthWeight'].hide_safe = not (self.implementation == 'FREECAD' and self.method == 'vari_smoothing')
        self.inputs['CurvatureWeight'].hide_safe = not (self.implementation == 'FREECAD' and self.method == 'vari_smoothing')
        self.inputs['TorsionWeight'].hide_safe = not (self.implementation == 'FREECAD' and self.method == 'vari_smoothing')

        updateNode(self, context)

    input_mode : EnumProperty(
            name = "Input mode",
            default = '1D',
            items = input_modes,
            update = update_sockets)

    u_size : IntProperty(
            name = "U Size",
            default = 5,
            min = 3,
            update = updateNode)

    degree_u : IntProperty(
            name = "Degree U",
            min = 2, max = 6,
            default = 3,
            update = updateNode)

    degree_v : IntProperty(
            name = "Degree V",
            min = 2, max = 6,
            default = 3,
            update = updateNode)

    centripetal : BoolProperty(
            name = "Centripetal",
            default = False,
            update = updateNode)

    has_points_cnt : BoolProperty(
            name = "Specify points count",
            default = False,
            update = update_sockets)

    points_cnt_u : IntProperty(
            name = "Points count U",
            min = 3, default = 5,
            update = updateNode)

    points_cnt_v : IntProperty(
            name = "Points count V",
            min = 3, default = 5,
            update = updateNode)

    implementations = []
    if geomdl is not None:
        implementations.append(('GEOMDL', "Geomdl", "Geomdl (NURBS-Python) package implementation", 0))
    if FreeCAD is not None:
        implementations.append(('FREECAD', "FreeCAD", "FreeCAD package implementation", 1))

    implementation : EnumProperty(
            name = "Implementation",
            description = "Approximation algorithm implementation",
            items = implementations,
            update = update_sockets)

    method: EnumProperty(
            name = 'Method',
            description = "Approximation Method",
            default = "parametrization",
            items = [("parametrization", "Parametrization", "Parametrize the init points using certain metric"),
                     ("vari_smoothing", "Variational Smoothing", "Smoothing algorithm, which tries to minimize an additional criterium")
                    ],
        update = update_sockets)

    degree_min : IntProperty(
            name = "Minimal Degree",
            min = 1,
            default = 3,
            update = updateNode)

    degree_max : IntProperty(
            name = "Maximal Degree",
            min = 1,
            default = 5,
            update = updateNode)

    tolerance : FloatProperty(
            name = "Tolerance",
            description = "Maximal distance from the init points",
            default = 0.0001,
            precision = 6,
            min = 0.0,
            update = updateNode)

    continuity: EnumProperty(
        name = 'Continuity',
        description = "Internal Curve Continuity",
        default = "C2",
        items = [('C0', "C0", "Only positional continuity", 0),
                 ('C1', "C1", "Continuity of the first derivative all along the Surface", 1),
                 ('C2', "C2", "Continuity of the second derivative all along the Surface", 2)
                ],
        update = updateNode)

    length_weight : FloatProperty(
            name = "Length Weight",
            description = "Variational smoothing parameter",
            default = 1.0,
            precision = 6,
            min = 0.0,
            update = updateNode)

    curvature_weight : FloatProperty(
            name = "Curvature Weight",
            description = "Variational smoothing parameter",
            default = 1.0,
            precision = 6,
            min = 0.0,
            update = updateNode)

    torsion_weight : FloatProperty(
            name = "Torsion Weight",
            description = "Variational smoothing parameter",
            default = 1.0,
            precision = 6,
            min = 0.0,
            update = updateNode)

    param_type: EnumProperty(name='Metric',
        description = "Parametrization Type",
        default = "ChordLength",
        items = [("ChordLength", "Euclidean", "Also known as Chord-Length or Distance. Parameters of points are proportionate to distances between them", 0),
                 ("Centripetal", "Centripetal", "Parameters of points are proportionate to square roots of distances between them", 1),
                 ("Uniform", "Points", "Also known as Uniform. Parameters of points are distributed uniformly", 2)
                ],
        update = updateNode)

    def sv_init(self, context):
        # common inputs:
        self.inputs.new('SvStringsSocket', "USize").prop_name = 'u_size'
        self.inputs.new('SvVerticesSocket', "Vertices")
        # geomdl inputs:
        self.inputs.new('SvStringsSocket', "DegreeU").prop_name = 'degree_u'
        self.inputs.new('SvStringsSocket', "DegreeV").prop_name = 'degree_v'
        self.inputs.new('SvStringsSocket', "PointsCntU").prop_name = 'points_cnt_u'
        self.inputs.new('SvStringsSocket', "PointsCntV").prop_name = 'points_cnt_v'
        # FreeCAD inputs:
        self.inputs.new('SvStringsSocket', "LengthWeight").prop_name = 'length_weight'
        self.inputs.new('SvStringsSocket', "CurvatureWeight").prop_name = 'curvature_weight'
        self.inputs.new('SvStringsSocket', "TorsionWeight").prop_name = 'torsion_weight'
        self.inputs.new('SvStringsSocket', "DegreeMin").prop_name = 'degree_min'
        self.inputs.new('SvStringsSocket', "DegreeMax").prop_name = 'degree_max'
        self.inputs.new('SvStringsSocket', "Tolerance").prop_name = 'tolerance'
        # common outputs:
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.outputs.new('SvVerticesSocket', "ControlPoints")
        self.outputs.new('SvStringsSocket', "KnotsU")
        self.outputs.new('SvStringsSocket', "KnotsV")

        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'implementation', text='')
        if self.implementation == 'GEOMDL':
            layout.prop(self, 'centripetal')
            layout.prop(self, 'has_points_cnt')
        else: # FreeCAD implementation:
            layout.prop(self, 'continuity')
            layout.prop(self, 'method')
            if self.method == 'parametrization':
                layout.prop(self, 'param_type')
            else: # Variational Smoothing:
                pass
        layout.prop(self, "input_mode")


    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        u_size_s = self.inputs['USize'].sv_get()
        degree_u_s = self.inputs['DegreeU'].sv_get()
        degree_v_s = self.inputs['DegreeV'].sv_get()
        points_cnt_u_s = self.inputs['PointsCntU'].sv_get()
        points_cnt_v_s = self.inputs['PointsCntV'].sv_get()

        degree_min_s = self.inputs['DegreeMin'].sv_get()
        degree_max_s = self.inputs['DegreeMax'].sv_get()
        tolerance_s = self.inputs['Tolerance'].sv_get()
        length_weight_s = self.inputs['LengthWeight'].sv_get()
        curvature_weight_s = self.inputs['CurvatureWeight'].sv_get()
        torsion_weight_s = self.inputs['TorsionWeight'].sv_get()

        if self.input_mode == '1D':
            vertices_s = ensure_nesting_level(vertices_s, 3)
        else:
            vertices_s = ensure_nesting_level(vertices_s, 4)

        surfaces_out = []
        points_out = []
        knots_u_out = []
        knots_v_out = []
        for (vertices,
            degree_u,
            degree_v,
            points_cnt_u,
            points_cnt_v,
            u_size, degree_min,
            degree_max, tolerance, 
            length_weight,
            curvature_weight,
            torsion_weight) \
            in zip_long_repeat(vertices_s,
                               degree_u_s,
                               degree_v_s,
                               points_cnt_u_s,
                               points_cnt_v_s,
                               u_size_s,
                               degree_min_s,
                               degree_max_s,
                               tolerance_s,
                               length_weight_s,
                               curvature_weight_s,
                               torsion_weight_s
                               ):

            if isinstance(degree_u, (tuple, list)):
                degree_u = degree_u[0]
            if isinstance(degree_v, (tuple, list)):
                degree_v = degree_v[0]
            if isinstance(u_size, (tuple, list)):
                u_size = u_size[0]
            if isinstance(points_cnt_u, (tuple, list)):
                points_cnt_u = points_cnt_u[0]
            if isinstance(points_cnt_v, (tuple, list)):
                points_cnt_v = points_cnt_v[0]

            if isinstance(degree_min, (tuple, list)):
                degree_min = degree_min[0]
            if isinstance(degree_max, (tuple, list)):
                degree_max = degree_max[0]
            if isinstance(tolerance, (tuple, list)):
                tolerance = tolerance[0]
            if isinstance(length_weight, (tuple, list)):
                length_weight = length_weight[0]
            if isinstance(curvature_weight, (tuple, list)):
                curvature_weight = curvature_weight[0]
            if isinstance(torsion_weight, (tuple, list)):
                torsion_weight = torsion_weight[0]

            if self.input_mode == '1D':
                n_u = u_size
                n_v = len(vertices) // n_u
            else:
                n_u = len(vertices[0])
                for i, verts_i in enumerate(vertices):
                    if len(verts_i) != n_u:
                        raise Exception("Number of vertices in row #{} is not the same as in the first ({} != {})!".format(i, n_u, len(verts_i)))
                vertices = sum(vertices, [])
                n_v = len(vertices) // n_u

            if geomdl is not None and self.implementation == 'GEOMDL':
                kwargs = dict(centripetal = self.centripetal)
                if self.has_points_cnt:
                    kwargs['ctrlpts_size_u'] = points_cnt_u
                    kwargs['ctrlpts_size_v'] = points_cnt_v
                surf = fitting.approximate_surface(vertices, n_u, n_v, degree_u, degree_v, **kwargs)
                surf = SvGeomdlSurface(surf)
            else: # FreeCAD:
                if degree_min > degree_max:
                    raise Exception("Minimal Degree must be lower or equal to Maximal Degree")

                continuity_int = int(self.continuity[1]) # continuity as integer
                vertices_np = np.array(split_by_count(vertices, n_v))
                surf = Part.BSplineSurface()
                if self.method == 'vari_smoothing':
                    surf.approximate(Points = vertices_np,
                                        DegMin = degree_min,
                                        DegMax = degree_max,
                                        Tolerance = tolerance,
                                        Continuity = continuity_int,
                                        LengthWeight = length_weight,
                                        CurvatureWeight = curvature_weight,
                                        TorsionWeight = torsion_weight
                                        )
                else: # Parametrization:
                    surf.approximate(Points = vertices_np,
                                        DegMin = degree_min,
                                        DegMax = degree_max,
                                        Tolerance = tolerance,
                                        Continuity = continuity_int,
                                        ParamType = self.param_type
                                        )
                surf = SvSolidFaceSurface(surf.toShape()).to_nurbs()

            points_out.append(surf.get_control_points().tolist())
            knots_u_out.append(surf.get_knotvector_u().tolist())
            knots_v_out.append(surf.get_knotvector_v().tolist())
            surfaces_out.append(surf)

        self.outputs['Surface'].sv_set(surfaces_out)
        self.outputs['ControlPoints'].sv_set(points_out)
        self.outputs['KnotsU'].sv_set(knots_u_out)
        self.outputs['KnotsV'].sv_set(knots_v_out)


def register():
    bpy.utils.register_class(SvExApproxNurbsSurfaceNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvExApproxNurbsSurfaceNodeMK2)
