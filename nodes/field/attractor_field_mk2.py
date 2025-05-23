
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty
from mathutils import bvhtree

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

from sverchok.utils.field.scalar import SvMergedScalarField
from sverchok.utils.field.vector_operations import (
        SvAverageVectorField,
        SvSelectVectorField)
from sverchok.utils.field.attractor import (SvScalarFieldPointDistance,
        SvKdtScalarField,
        SvLineAttractorScalarField, SvPlaneAttractorScalarField, 
        SvCircleAttractorScalarField,
        SvEdgeAttractorScalarField,
        SvBvhAttractorScalarField,
        SvVectorFieldPointDistance,
        SvKdtVectorField,
        SvLineAttractorVectorField, SvPlaneAttractorVectorField,
        SvCircleAttractorVectorField,
        SvEdgeAttractorVectorField,
        SvBvhAttractorVectorField
        )
from sverchok.utils.math import all_falloff_types, falloff_array
from sverchok.utils.kdtree import SvKdTree

class SvAttractorFieldNodeMk2(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Attractor Field
    Tooltip: Generate scalar and vector attraction fields
    """
    bl_idname = 'SvAttractorFieldNodeMk2'
    bl_label = 'Attractor Field'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EX_ATTRACT'

    def update_type(self, context):
        self.inputs['Direction'].hide_safe = (self.attractor_type in ['Point', 'Mesh', 'Edge'])
        self.inputs['Amplitude'].hide_safe = (self.falloff_type == 'NONE')
        coeff_types = ['inverse_exp', 'gauss', 'smooth', 'sphere', 'root', 'invsquare', 'sharp', 'linear', 'const']
        self.inputs['Coefficient'].hide_safe = (self.falloff_type not in coeff_types)
        self.inputs['Faces'].hide_safe = (self.attractor_type != 'Mesh')
        self.inputs['Edges'].hide_safe = (self.attractor_type != 'Edge')
        self.inputs['Radius'].hide_safe = (self.attractor_type != 'Circle')
        updateNode(self, context)

    falloff_type: EnumProperty(
        name="Falloff type", items=all_falloff_types, default='NONE', update=update_type)

    amplitude: FloatProperty(
        name="Amplitude", default=0.5, min=0.0, update=updateNode)

    coefficient: FloatProperty(
        name="Coefficient", default=0.5, update=updateNode)

    clamp: BoolProperty(
        name="Clamp", description="Restrict coefficient with R", default=False, update=updateNode)

    types = [
            ("Point", "Point", "Attraction to single or multiple points", 0),
            ("Line", "Line", "Attraction to straight line", 1),
            ("Plane", "Plane", "Attraction to plane", 2),
            ("Mesh", "Mesh - Faces", "Attraction to mesh faces", 3),
            ("Edge", "Mesh - Edges", "Attraction to mesh edges", 4),
            ("Circle", "Circle", "Attraction to circle", 5)
        ]

    attractor_type: EnumProperty(
        name="Attractor type", items=types, default='Point', update=update_type)

    point_modes = [
        ('AVG', "Average", "Use average distance to all attraction centers", 0),
        ('MIN', "Nearest", "Use minimum distance to any of attraction centers", 1),
        ('SEP', "Separate", "Generate a separate field for each attraction center", 2)
    ]

    merge_mode : EnumProperty(
        name = "Join mode",
        description = "How to define the distance when multiple attraction centers are used",
        items = point_modes,
        default = 'AVG',
        update = updateNode)

    signed : BoolProperty(
            name = "Signed",
            default = False,
            update = updateNode)

    radius : FloatProperty(
            name = "Radius",
            description = "Circle radius",
            default = 1.0,
            min = 0,
            update = updateNode)

    metrics = [
            ('DISTANCE', 'Euclidean', "Euclidean distance metric", 0),
            ('MANHATTAN', 'Manhattan', "Manhattan distance metric", 1),
            ('CHEBYSHEV', 'Chebyshev', "Chebyshev distance", 2),
            ('CUSTOM', "Custom", "Custom Minkowski metric defined by exponent factor", 3)
        ]

    metric : EnumProperty(
            name = "Metric",
            items = metrics,
            default = 'DISTANCE',
            update = updateNode)

    power : FloatProperty(
            name = "Exponent",
            description = "Exponent for Minkowski metric",
            min = 1.0,
            default = 2,
            update = updateNode)

    def sv_init(self, context):
        d = self.inputs.new('SvVerticesSocket', "Center")
        d.use_prop = True
        d.default_property = (0.0, 0.0, 0.0)

        d = self.inputs.new('SvVerticesSocket', "Direction")
        d.use_prop = True
        d.default_property = (0.0, 0.0, 1.0)

        self.inputs.new('SvStringsSocket', 'Radius').prop_name = 'radius'
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'Amplitude').prop_name = 'amplitude'
        self.inputs.new('SvStringsSocket', 'Coefficient').prop_name = 'coefficient'

        self.outputs.new('SvVectorFieldSocket', "VField")
        self.outputs.new('SvScalarFieldSocket', "SField")
        self.update_type(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'attractor_type')
        if self.attractor_type != 'Mesh':
            layout.prop(self, 'merge_mode')
        elif self.attractor_type == 'Mesh':
            layout.prop(self, 'signed', toggle=True)
        if self.attractor_type == 'Point':
            layout.prop(self, 'metric')
            if self.metric == 'CUSTOM':
                layout.prop(self, 'power')
        layout.prop(self, 'falloff_type')
        layout.prop(self, 'clamp')

    def get_power(self):
        if self.metric == 'DISTANCE':
            return 2
        elif self.metric == 'MANHATTAN':
            return 1
        elif self.metric == 'CHEBYSHEV':
            return np.inf
        else:
            return self.power

    def to_point(self, centers, falloff):
        if self.metric == 'DISTANCE':
            metric_single = 'EUCLIDEAN'
        else:
            metric_single = self.metric
        n = len(centers)
        if n == 1:
            sfield = SvScalarFieldPointDistance(centers[0], falloff=falloff, metric=metric_single, power=self.get_power())
            vfield = SvVectorFieldPointDistance(centers[0], falloff=falloff, metric=metric_single, power=self.get_power())
        elif self.merge_mode == 'AVG':
            sfields = [SvScalarFieldPointDistance(center, falloff=falloff, metric=metric_single, power=self.get_power()) for center in centers]
            sfield = SvMergedScalarField('AVG', sfields)
            vfields = [SvVectorFieldPointDistance(center, falloff=falloff, metric=metric_single, power=self.get_power()) for center in centers]
            vfield = SvAverageVectorField(vfields)
        elif self.merge_mode == 'MIN':
            kdt = SvKdTree.new(SvKdTree.best_available_implementation(), centers, power=self.get_power())
            vfield = SvKdtVectorField(kdt=kdt, falloff=falloff)
            sfield = SvKdtScalarField(kdt=kdt, falloff=falloff)
        else: # SEP
            sfield = [SvScalarFieldPointDistance(center, falloff=falloff, metric=metric_single, power=self.get_power()) for center in centers]
            vfield = [SvVectorFieldPointDistance(center, falloff=falloff, metric=metric_single, power=self.get_power()) for center in centers]
        return vfield, sfield

    def merge_fields(self, vfields, sfields):
        if len(sfields) == 1:
            return vfields[0], sfields[0]
        elif self.merge_mode == 'AVG':
            sfield = SvMergedScalarField('AVG', sfields)
            vfield = SvAverageVectorField(vfields)
            return vfield, sfield
        elif self.merge_mode == 'MIN':
            sfield = SvMergedScalarField('MIN', sfields)
            if self.falloff_type == 'NONE':
                vfield = SvSelectVectorField(vfields, 'MIN')
            else:
                vfield = SvSelectVectorField(vfields, 'MAX')
            return vfield, sfield
        else: # SEP:
            return vfields, sfields

    def to_line(self, centers, directions, falloff):
        vfields = []
        sfields = []
        for center, direction in zip_long_repeat(centers, directions):
            sfield = SvLineAttractorScalarField(np.array(center), np.array(direction), falloff=falloff)
            vfield = SvLineAttractorVectorField(np.array(center), np.array(direction), falloff=falloff)
            vfields.append(vfield)
            sfields.append(sfield)
        return self.merge_fields(vfields, sfields)

    def to_plane(self, centers, directions, falloff):
        vfields = []
        sfields = []
        for center, direction in zip_long_repeat(centers, directions):
            sfield = SvPlaneAttractorScalarField(np.array(center), np.array(direction), falloff=falloff)
            vfield = SvPlaneAttractorVectorField(np.array(center), np.array(direction), falloff=falloff)
            vfields.append(vfield)
            sfields.append(sfield)
        return self.merge_fields(vfields, sfields)

    def to_circle(self, centers, directions, radiuses, falloff):
        sfields = []
        vfields = []
        for center, direction, radius in zip_long_repeat(centers, directions, radiuses):
            sfield = SvCircleAttractorScalarField(center, radius, direction, falloff)
            vfield = SvCircleAttractorVectorField(center, radius, direction, falloff)
            sfields.append(sfield)
            vfields.append(vfield)
        return self.merge_fields(vfields, sfields)

    def to_mesh(self, verts, faces, falloff):
        bvh = bvhtree.BVHTree.FromPolygons(verts, faces)
        sfield = SvBvhAttractorScalarField(bvh=bvh, falloff=falloff, signed=self.signed)
        vfield = SvBvhAttractorVectorField(bvh=bvh, falloff=falloff)
        return vfield, sfield

    def to_edges(self, verts, edges, falloff):
        sfields = []
        vfields = []
        for i1, i2 in edges:
            v1 = verts[i1]
            v2 = verts[i2]
            sfield = SvEdgeAttractorScalarField(v1, v2, falloff)
            vfield = SvEdgeAttractorVectorField(v1, v2, falloff)
            sfields.append(sfield)
            vfields.append(vfield)
        return self.merge_fields(vfields, sfields)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        center_s = self.inputs['Center'].sv_get()
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Faces'].sv_get(default=[[]])
        directions_s = self.inputs['Direction'].sv_get()
        radius_s = self.inputs['Radius'].sv_get()
        amplitudes_s = self.inputs['Amplitude'].sv_get()
        coefficients_s = self.inputs['Coefficient'].sv_get()

        vfields_out = []
        sfields_out = []

        objects = zip_long_repeat(center_s, edges_s, faces_s, directions_s, radius_s, amplitudes_s, coefficients_s)
        for centers, edges, faces, direction, radius, amplitude, coefficient in objects:
            if isinstance(amplitude, (list, tuple)):
                amplitude = amplitude[0]
            if isinstance(coefficient, (list, tuple)):
                coefficient = coefficient[0]
            if not isinstance(radius, (list, tuple)):
                radius = [radius]

            if self.falloff_type == 'NONE':
                falloff_func = None
            else:
                falloff_func = falloff_array(self.falloff_type, amplitude, coefficient, self.clamp)
            
            if self.attractor_type == 'Point':
                vfield, sfield = self.to_point(centers, falloff_func)
            elif self.attractor_type == 'Line':
                vfield, sfield = self.to_line(centers, direction, falloff_func)
            elif self.attractor_type == 'Plane':
                vfield, sfield = self.to_plane(centers, direction, falloff_func)
            elif self.attractor_type == 'Mesh':
                vfield, sfield = self.to_mesh(centers, faces, falloff_func)
            elif self.attractor_type == 'Edge':
                vfield, sfield = self.to_edges(centers, edges, falloff_func)
            elif self.attractor_type == 'Circle':
                vfield, sfield = self.to_circle(centers, direction, radius, falloff_func)
            else:
                raise Exception("not implemented yet")

            vfields_out.append(vfield)
            sfields_out.append(sfield)

        self.outputs['SField'].sv_set(sfields_out)
        self.outputs['VField'].sv_set(vfields_out)

def register():
    bpy.utils.register_class(SvAttractorFieldNodeMk2)

def unregister():
    bpy.utils.unregister_class(SvAttractorFieldNodeMk2)

