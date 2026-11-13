# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import EnumProperty, IntProperty, FloatProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (zip_long_repeat, enum_item_4, updateNode)
from sverchok.utils.pulga_physics_modular_core import (
    SvBoundingBoxForce,
    SvBoundingSphereForce,
    SvBoundingSphereSurfaceForce,
    SvBoundingPlaneSurfaceForce,
    SvBoundingMeshForce,
    SvBoundingSolidForce)
from sverchok.dependencies import FreeCAD
from sverchok.utils.pulga_boundaries_extra import (
    SvBoundingEdgesForce, SvBoundingCurveForce, SvBoundingSurfaceForce,
    SvBoundingSolidFastForce
)
from sverchok.utils.curve import SvCurve
from sverchok.utils.surface import SvSurface



def _geometry_items(data, kind):
    """Flatten the Sverchok socket nesting without descending into geometry."""
    if isinstance(data, kind):
        yield data
    elif isinstance(data, (list, tuple)):
        for item in data:
            yield from _geometry_items(item, kind)


def _numeric_items(data):
    """Flatten a scalar socket's levels, preserving their order."""
    import numbers
    if isinstance(data, numbers.Real):
        yield float(data)
    elif isinstance(data, (list, tuple)):
        for item in data:
            yield from _numeric_items(item)
    elif hasattr(data, 'tolist'):
        yield from _numeric_items(data.tolist())
    else:
        raise ValueError('Expected a numeric boundary socket input, got %r' % (type(data),))




def _solid_faces_as_one_boundary(data, make_compound):
    """Turn one group of one or more trimmed FreeCAD faces into one shape."""
    items = []

    def collect(value):
        if isinstance(value, (list, tuple)):
            for child in value:
                collect(child)
        elif value is not None:
            items.append(value)

    collect(data)
    if not items:
        raise ValueError('Solid Face boundary group requires at least one face')
    if len(items) == 1:
        return items[0]

    faces = []
    for item in items:
        shape = getattr(item, 'face', None)
        if shape is None:
            shape = item
        if not hasattr(shape, 'tessellate') or not hasattr(shape, 'distToShape'):
            raise TypeError('Solid Face boundary expects FreeCAD face objects')
        faces.append(shape)
    compound = make_compound(faces)
    if compound is None:
        raise RuntimeError('FreeCAD did not create a compound from the faces')
    return compound


def _solid_face_group_boundaries(data, make_compound):
    """Keep one Pulga force for each top-level item in the Solid Face socket.

    A face at the outer level is one force. An outer-level list of faces is
    one compound force. Nested lists *within a group* may be flattened,
    but different outer-level groups must never be merged.
    """
    if not isinstance(data, (list, tuple)):
        data = [data]

    boundaries = []
    for group in data:
        if isinstance(group, (list, tuple)):
            # Compound only within this top-level group (and preserve the
            # original face wrapper when the group contains one face).
            boundaries.append(_solid_faces_as_one_boundary(group, make_compound))
        elif group is not None:
            boundaries.append(group)
    if not boundaries:
        raise ValueError('Solid Face requires one or more faces or face groups')
    return boundaries

class SvPulgaBoundingBoxForceNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Spatial Ambit
    Tooltip: Define simulation Limits by Volume or Surface
    """
    bl_idname = 'SvPulgaBoundingBoxForceNode'
    bl_label = 'Pulga Boundaries Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_BOUNDARIES_FORCE'

    def update_sockets_and_node(self, context):
        self.update_sockets()
        updateNode(self, context)

    def update_sockets(self):
        self.inputs['Bounding Box'].hide_safe = self.mode != 'Box'
        self.inputs['Center'].hide_safe = not 'Sphere' in self.mode and not 'Plane' in self.mode
        self.inputs['Radius'].hide_safe = not 'Sphere' in self.mode
        self.inputs['Normal'].hide_safe = not 'Plane' in self.mode
        self.inputs['Vertices'].hide_safe = not 'Mesh' in self.mode
        self.inputs['Polygons'].hide_safe = self.mode not in ('Mesh_(Surface)', 'Mesh_(Volume)')
        self.inputs['Solid'].hide_safe = not 'Solid_(' in self.mode
        self.inputs['Solid Face'].hide_safe = self.mode != 'Solid_Face'
        self.inputs['Edges'].hide_safe = self.mode != 'Mesh_(Edges)'
        self.inputs['Curve'].hide_safe = self.mode != 'Curve'
        self.inputs['Surface'].hide_safe = self.mode != 'Surface'
        fast = self.method == 'FAST'
        self.inputs['Resolution'].hide_safe = self.mode != 'Curve' or not fast
        self.inputs['Resolution U'].hide_safe = self.mode != 'Surface' or not fast
        self.inputs['Resolution V'].hide_safe = self.mode != 'Surface' or not fast
        self.inputs['Initial Samples'].hide_safe = self.mode != 'Curve' or fast
        self.inputs['Initial Samples U'].hide_safe = self.mode != 'Surface' or fast
        self.inputs['Initial Samples V'].hide_safe = self.mode != 'Surface' or fast
        self.inputs['Deflection'].hide_safe = not (self.mode.startswith('Solid') and fast)

    mode_items = [
        'Box', 'Sphere', 'Sphere Surface', 'Plane',
        'Mesh (Surface)', 'Mesh (Volume)',
        'Mesh (Edges)', 'Curve', 'Surface',
        'Solid (Surface)', 'Solid (Volume)', 'Solid Face',
    ]
    # Keep enum numeric values stable with or without FreeCAD.
    # Modes 6..8 belonged to Solid before new modes were added.
    mode_enum_items = tuple(
        (identifier, label, description, numeric_id)
        for (identifier, label, description, _), numeric_id in zip(
            enum_item_4(mode_items),
            (0, 1, 2, 3, 4, 5, 9, 10, 11, 6, 7, 8),
        )
    )
    mode: EnumProperty(
        name='Mode', description='Boundaries definition mode',
        items=mode_enum_items,
        default='Box',
        update=update_sockets_and_node)
    center: FloatVectorProperty(
        name='Center',
        description='Bounding Sphere center',
        default=(0,0,0),
        size=3,
        update=updateNode)
    radius: FloatProperty(
        name='Radius',
        description='Bounding Sphere radius',
        default=0.0,
        update=updateNode)
    normal: FloatVectorProperty(
        name='Normal',
        description='Bounding Sphere center',
        default=(0, 0, 0),
        size=3,
        update=updateNode)

    # Fast is the default for all parametric and Solid modes.
    method: EnumProperty(
        name='Method', description='Fast tessellated or Precise parametric projection',
        items=[('FAST', 'Fast', 'Cached segments / triangle BVH'),
               ('PRECISE', 'Precise', 'SciPy nearest point on original geometry')],
        default='FAST', update=update_sockets_and_node)
    resolution: IntProperty(name='Resolution', default=64, min=2, update=updateNode)
    resolution_u: IntProperty(name='Resolution U', default=25, min=2, update=updateNode)
    resolution_v: IntProperty(name='Resolution V', default=25, min=2, update=updateNode)
    initial_samples: IntProperty(name='Initial Samples', default=32, min=3, update=updateNode)
    initial_samples_u: IntProperty(name='Initial Samples U', default=15, min=3, update=updateNode)
    initial_samples_v: IntProperty(name='Initial Samples V', default=15, min=3, update=updateNode)

    solid_deflection: FloatProperty(
        name='Deflection', default=0.1, min=0.0001, precision=4,
        description='FreeCAD tessellation deflection for Fast Solid boundaries',
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Bounding Box")
        self.inputs.new('SvVerticesSocket', "Center").prop_name = 'center'
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('SvVerticesSocket', "Normal").prop_name = 'normal'
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Polygons")
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvCurveSocket', 'Curve')
        self.inputs.new('SvSurfaceSocket', 'Surface')
        self.inputs.new('SvStringsSocket', 'Resolution').prop_name = 'resolution'
        self.inputs.new('SvStringsSocket', 'Resolution U').prop_name = 'resolution_u'
        self.inputs.new('SvStringsSocket', 'Resolution V').prop_name = 'resolution_v'
        self.inputs.new('SvStringsSocket', 'Initial Samples').prop_name = 'initial_samples'
        self.inputs.new('SvStringsSocket', 'Initial Samples U').prop_name = 'initial_samples_u'
        self.inputs.new('SvStringsSocket', 'Initial Samples V').prop_name = 'initial_samples_v'
        self.inputs.new('SvStringsSocket', 'Deflection').prop_name = 'solid_deflection'
        self.inputs.new('SvSolidSocket', "Solid")
        self.inputs.new('SvSurfaceSocket', "Solid Face")
        self.update_sockets()

        self.outputs.new('SvPulgaForceSocket', "Force")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode')
        if self.mode in {'Curve', 'Surface', 'Solid_(Surface)', 'Solid_(Volume)', 'Solid_Face'}:
            layout.prop(self, 'method', text='')

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        if self.mode == 'Box':
            b_box = self.inputs["Bounding Box"].sv_get(deepcopy=False)

            forces_out = []
            for force in b_box:
                forces_out.append(SvBoundingBoxForce(force))
        elif self.mode == 'Sphere':

            center = self.inputs["Center"].sv_get(deepcopy=False)
            radius = self.inputs["Radius"].sv_get(deepcopy=False)

            forces_out = []
            for force in zip_long_repeat(center, radius):
                forces_out.append(SvBoundingSphereForce(*force))
        elif self.mode == 'Sphere_Surface':

            center = self.inputs["Center"].sv_get(deepcopy=False)
            radius = self.inputs["Radius"].sv_get(deepcopy=False)

            forces_out = []
            for force in zip_long_repeat(center, radius):
                forces_out.append(SvBoundingSphereSurfaceForce(*force))
        elif self.mode == 'Plane':

            center = self.inputs["Center"].sv_get(deepcopy=False)
            radius = self.inputs["Normal"].sv_get(deepcopy=False)

            forces_out = []
            for force in zip_long_repeat(center, radius):
                forces_out.append(SvBoundingPlaneSurfaceForce(*force))
        elif self.mode == 'Mesh_(Edges)':
            verts = self.inputs['Vertices'].sv_get(deepcopy=False)
            edges = self.inputs['Edges'].sv_get(deepcopy=False)
            forces_out = [SvBoundingEdgesForce(v, e) for v, e in zip_long_repeat(verts, edges)]
        elif self.mode == 'Curve':
            curves = list(_geometry_items(self.inputs['Curve'].sv_get(deepcopy=False), SvCurve))
            if not curves:
                raise ValueError('Connect at least one Curve boundary')
            resolutions = list(_numeric_items(self.inputs['Resolution'].sv_get(deepcopy=False)))
            samples = list(_numeric_items(self.inputs['Initial Samples'].sv_get(deepcopy=False)))
            forces_out = [SvBoundingCurveForce(curve, self.method, resolution, samples)
                          for curve, resolution, samples in zip_long_repeat(curves, resolutions, samples)]
        elif self.mode == 'Surface':
            surfaces = list(_geometry_items(self.inputs['Surface'].sv_get(deepcopy=False), SvSurface))
            if not surfaces:
                raise ValueError('Connect at least one Surface boundary')
            ru = list(_numeric_items(self.inputs['Resolution U'].sv_get(deepcopy=False)))
            rv = list(_numeric_items(self.inputs['Resolution V'].sv_get(deepcopy=False)))
            su = list(_numeric_items(self.inputs['Initial Samples U'].sv_get(deepcopy=False)))
            sv = list(_numeric_items(self.inputs['Initial Samples V'].sv_get(deepcopy=False)))
            forces_out = [SvBoundingSurfaceForce(surface, self.method, u, v, a, b)
                          for surface, u, v, a, b in zip_long_repeat(surfaces, ru, rv, su, sv)]
        elif 'Mesh' in self.mode:

            verts = self.inputs["Vertices"].sv_get(deepcopy=False)
            polygons = self.inputs["Polygons"].sv_get(deepcopy=False)
            volume = self.mode == "Mesh_(Volume)"
            forces_out = []
            for force in zip_long_repeat(verts, polygons):
                forces_out.append(SvBoundingMeshForce(*force, volume))

        elif 'Solid' in self.mode:
            if FreeCAD is None:
                raise RuntimeError(
                    'Pulga Boundaries: Solid modes require FreeCAD.'
                )
            input_name = 'Solid' if self.mode in ('Solid_(Surface)', 'Solid_(Volume)') else 'Solid Face'
            solids = self.inputs[input_name].sv_get(deepcopy=False)
            volume = self.mode == 'Solid_(Volume)'
            forces_out = []
            # Flat list: separate forces. Nested groups: one force per group.
            # Do not merge all the faces: top-level list matching matters.
            if self.mode == 'Solid_Face':
                import Part
                solids = _solid_face_group_boundaries(solids, Part.makeCompound)
            if self.method == 'FAST':
                deflections = list(_numeric_items(
                    self.inputs['Deflection'].sv_get(deepcopy=False)))
                if not deflections:
                    raise ValueError('Solid Fast boundary requires a Deflection')
                for solid, deflection in zip_long_repeat(solids, deflections):
                    forces_out.append(SvBoundingSolidFastForce(
                        solid, volume=volume, deflection=deflection))
            else:
                for solid in solids:
                    forces_out.append(SvBoundingSolidForce(solid, volume=volume))

        self.outputs[0].sv_set([forces_out])



def register():
    bpy.utils.register_class(SvPulgaBoundingBoxForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaBoundingBoxForceNode)
