# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, updateNode, get_data_nesting_level
from sverchok.utils.geom import PlaneEquation, LineEquation, linear_approximation
from sverchok.utils.solid import SvSolidTopology
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    add_dummy('SvSelectSolidNode', 'Select Solid Elements', 'FreeCAD')
else:
    import FreeCAD
    import Part
    from FreeCAD import Base

class SvSelectSolidNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Select Solid Elements
    Tooltip: Select Vertexes, Edges or Faces of Solid object by location
    """
    bl_idname = 'SvSelectSolidNode'
    bl_label = 'Select Solid Elements'
    bl_icon = 'EDGESEL'
    solid_catergory = "Operators"

    element_types = [
            ('VERTS', "Vertices", "Select vertices first, and then select adjacent edges and faces", 'VERTEXSEL', 0),
            ('EDGES', "Edges", "Select edges first, and then select adjacent vertices and faces", "EDGESEL", 1),
            ('FACES', "Faces", "Select faces first, and then select adjacent vertices and edges", 'FACESEL', 2)
        ]

    criteria_types = [
            ('SIDE', "By Side", "By Side", 0),
            ('NORMAL', "By Normal", "By Normal direction", 1),
            ('SPHERE', "By Center and Radius", "By center and radius", 2),
            ('PLANE', "By Plane", "By plane defined by point and normal", 3),
            ('CYLINDER', "By Cylinder", "By cylinder defined by point, direction vector and radius", 4),
            ('DIRECTION', "By Direction", "By direction", 5),
            ('SOLID_DISTANCE', "By Distance to Solid", "By Distance to Solid", 6),
            ('SOLID_INSIDE', "Inside Solid", "Select elements that are inside given solid", 7)
            #('BBOX', "By Bounding Box", "By bounding box", 6)
        ]

    known_criteria = {
            'VERTS': {'SIDE', 'SPHERE', 'PLANE', 'CYLINDER', 'SOLID_DISTANCE', 'SOLID_INSIDE'},
            'EDGES': {'SIDE', 'SPHERE', 'PLANE', 'CYLINDER', 'DIRECTION', 'SOLID_DISTANCE', 'SOLID_INSIDE'},
            'FACES': {'SIDE', 'NORMAL', 'SPHERE', 'PLANE', 'CYLINDER', 'SOLID_DISTANCE', 'SOLID_INSIDE'}
        }

    @throttled
    def update_type(self, context):
        criteria = self.criteria_type
        available = SvSelectSolidNode.known_criteria[self.element_type]
        if criteria not in available:
            self.criteria_type = available[0]
        else:
            self.update_sockets(context)

    element_type : EnumProperty(
            name = "Select",
            description = "What kind of Solid elements to select first",
            items = element_types,
            default = 'VERTS',
            update = updateNode)

    def get_available_criteria(self, context):
        result = []
        for item in SvSelectSolidNode.criteria_types:
            if item[0] in SvSelectSolidNode.known_criteria[self.element_type]:
                result.append(item)
        return result

    @throttled
    def update_sockets(self, context):
        self.inputs['Direction'].hide_safe = self.criteria_type not in {'SIDE', 'NORMAL', 'PLANE', 'CYLINDER', 'DIRECTION'}
        self.inputs['Center'].hide_safe = self.criteria_type not in {'SPHERE', 'PLANE', 'CYLINDER'}
        self.inputs['Percent'].hide_safe = self.criteria_type not in {'SIDE', 'NORMAL', 'DIRECTION'}
        self.inputs['Radius'].hide_safe = self.criteria_type not in {'SPHERE', 'PLANE', 'CYLINDER', 'SOLID_DISTANCE'}
        self.inputs['Tool'].hide_safe = self.criteria_type not in {'SOLID_DISTANCE', 'SOLID_INSIDE'}
        self.inputs['Precision'].hide_safe = self.element_type == 'VERTS' or self.criteria_type in {'SOLID_DISTANCE'}

    criteria_type : EnumProperty(
            name = "Criteria",
            description = "Type of criteria to select by",
            items = get_available_criteria,
            update = update_sockets)

    include_partial: BoolProperty(name="Include partial selection",
            description="Include partially selected edges/faces - for primary selection",
            default=False,
            update=updateNode)

    include_partial_other: BoolProperty(name="Include partial selection",
            description="Include partially selected vertices/edges/faces - for secondary selection",
            default=False,
            update=updateNode)

    percent: FloatProperty(name="Percent", 
            default=1.0,
            min=0.0, max=100.0,
            update=updateNode)

    radius: FloatProperty(name="Radius", default=1.0, min=0.0, update=updateNode)

    precision: FloatProperty(
        name="Precision",
        default=0.01,
        precision=4,
        update=updateNode)

    tolerance : FloatProperty(
        name = "Tolerance",
        default = 0.01,
        precision = 4,
        update=updateNode)

    include_shell : BoolProperty(
        name = "Including shell",
        description = "indicates if the point lying directly on a face is considered to be inside or not",
        default = False,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'element_type')
        layout.prop(self, 'criteria_type', text='')

        if self.element_type in {'EDGES', 'FACES'} and self.criteria_type not in {'SOLID_DISTANCE'}:
            if self.element_type == 'EDGES':
                text = "Partially selected edges"
            else:
                text = "Partially selected faces"
            layout.prop(self, 'include_partial', text=text)

        if self.element_type == 'VERTS':
            text = "Partially selected edges, faces"
            layout.prop(self, 'include_partial_other', text=text)
        elif self.element_type == 'EDGES':
            text = "Partially selected faces"
            layout.prop(self, 'include_partial_other', text=text)

        if self.criteria_type == 'SOLID_INSIDE':
            layout.prop(self, 'tolerance')
            layout.prop(self, 'include_shell')

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.inputs.new('SvSolidSocket', "Tool")
        d = self.inputs.new('SvVerticesSocket', "Direction")
        d.use_prop = True
        d.prop = (0.0, 0.0, 1.0)

        c = self.inputs.new('SvVerticesSocket', "Center")
        c.use_prop = True
        c.prop = (0.0, 0.0, 0.0)

        self.inputs.new('SvStringsSocket', 'Percent').prop_name = 'percent'
        self.inputs.new('SvStringsSocket', 'Radius').prop_name = 'radius'
        self.inputs.new('SvStringsSocket', 'Precision').prop_name = 'precision'

        self.outputs.new('SvStringsSocket', 'VerticesMask')
        self.outputs.new('SvStringsSocket', 'EdgesMask')
        self.outputs.new('SvStringsSocket', 'FacesMask')

        self.update_sockets(context)

    def map_percent(self, values, percent):
        maxv = max(values)
        minv = min(values)
        if maxv <= minv:
            return maxv
        return maxv - percent * (maxv - minv) * 0.01

    def _by_side(self, points, direction, percent):
        direction = direction / np.linalg.norm(direction)
        values = points.dot(direction)
        threshold = self.map_percent(values, percent)
        return values > threshold

    # VERTS

    def _verts_by_side(self, topo, direction, percent):
        verts = [(v.X ,v.Y, v.Z) for v in topo.solid.Vertexes]
        verts = np.array(verts)
        direction = np.array(direction)
        mask = self._by_side(verts, direction, percent)
        return mask.tolist()

    def _verts_by_sphere(self, topo, center, radius):
        return topo.get_vertices_within_range_mask(center, radius)

    def _verts_by_plane(self, topo, center, direction, radius):
        plane = PlaneEquation.from_normal_and_point(direction, center)
        condition = lambda v: plane.distance_to_point(v) < radius
        return topo.get_vertices_by_location_mask(condition)

    def _verts_by_cylinder(self, topo, center, direction, radius):
        line = LineEquation.from_direction_and_point(direction, center)
        condition = lambda v: line.distance_to_point(v) < radius
        return topo.get_vertices_by_location_mask(condition)

    def _verts_by_solid_distance(self, topo, tool, radius):
        condition = lambda v: v.distToShape(tool)[0] < radius
        mask = [condition(v) for v in topo.solid.Vertexes]
        return mask

    def _verts_by_solid_inside(self, topo, tool):
        condition = lambda v: tool.isInside(v.Point, self.tolerance, self.include_shell)
        mask = [condition(v) for v in topo.solid.Vertexes]
        return mask

    # EDGES

    def _edges_by_side(self, topo, direction, percent):
        direction = np.array(direction)
        all_values = []
        values_per_edge = dict()
        for edge in topo.solid.Edges:
            points = np.array(topo.get_points_by_edge(edge))
            values = points.dot(direction)
            all_values.extend(values.tolist())
            values_per_edge[SvSolidTopology.Item(edge)] = values

        threshold = self.map_percent(all_values, percent)
        check = any if self.include_partial else all
        mask = []
        for edge in topo.solid.Edges:
            values = values_per_edge[SvSolidTopology.Item(edge)]
            test = check(values > threshold)
            mask.append(test)

        return mask

    def _edges_by_sphere(self, topo, center, radius):
        center = np.array(center)
        def condition(points):
            dvs = points - center
            distances = (dvs * dvs).sum(axis=1)
            return distances < radius*radius
        return topo.get_edges_by_location_mask(condition, self.include_partial)

    def _edges_by_plane(self, topo, center, direction, radius):
        plane = PlaneEquation.from_normal_and_point(direction, center)
        def condition(points):
            distances = plane.distance_to_points(points)
            return distances < radius
        return topo.get_edges_by_location_mask(condition, self.include_partial)

    def _edges_by_cylinder(self, topo, center, direction, radius):
        line = LineEquation.from_direction_and_point(direction, center)
        def condition(points):
            distances = line.distance_to_points(points)
            return distances < radius
        return topo.get_edges_by_location_mask(condition, self.include_partial)

    def _edges_by_direction(self, topo, direction, percent):
        direction = np.array(direction)

        def calc_value(points):
            approx = linear_approximation(points)
            line = approx.most_similar_line()
            line_direction = np.array(line.direction)
            return abs(direction.dot(line_direction))

        values = np.array([calc_value(topo.get_points_by_edge(edge)) for edge in topo.solid.Edges])
        threshold = self.map_percent(values, percent)
        return (values > threshold).tolist()

    def _edges_by_solid_distance(self, topo, tool, radius):
        condition = lambda e: e.distToShape(tool)[0] < radius
        mask = [condition(e) for e in topo.solid.Edges]
        return mask

    def _edges_by_solid_inside(self, topo, tool):
        def condition(points):
            good = [tool.isInside(Base.Vector(*p), self.tolerance, self.include_shell) for p in points]
            return np.array(good)
        return topo.get_edges_by_location_mask(condition, self.include_partial)

    # FACES

    def _faces_by_side(self, topo, direction, percent):
        direction = np.array(direction)
        all_values = []
        values_per_face = dict()
        for face in topo.solid.Faces:
            points = np.array(topo.get_points_by_face(face))
            values = points.dot(direction)
            all_values.extend(values.tolist())
            values_per_face[SvSolidTopology.Item(face)] = values

        threshold = self.map_percent(all_values, percent)
        check = any if self.include_partial else all
        mask = []
        for face in topo.solid.Faces:
            values = values_per_face[SvSolidTopology.Item(face)]
            test = check(values > threshold)
            mask.append(test)

        return mask

    def _faces_by_normal(self, topo, direction, percent):
        direction = np.array(direction)

        def calc_value(normal):
            return direction.dot(normal)

        values = np.array([calc_value(topo.get_normal_by_face(face)) for face in topo.solid.Faces])
        threshold = self.map_percent(values, percent)
        return (values > threshold).tolist()

    def _faces_by_sphere(self, topo, center, radius):
        center = np.array(center)
        def condition(points):
            dvs = points - center
            distances = (dvs * dvs).sum(axis=1)
            return distances < radius*radius
        return topo.get_faces_by_location_mask(condition, self.include_partial)

    def _faces_by_plane(self, topo, center, direction, radius):
        plane = PlaneEquation.from_normal_and_point(direction, center)
        def condition(points):
            distances = plane.distance_to_points(points)
            return distances < radius
        return topo.get_faces_by_location_mask(condition, self.include_partial)

    def _faces_by_cylinder(self, topo, center, direction, radius):
        line = LineEquation.from_direction_and_point(direction, center)
        def condition(points):
            distances = line.distance_to_points(points)
            return distances < radius
        return topo.get_faces_by_location_mask(condition, self.include_partial)

    def _faces_by_solid_distance(self, topo, tool, radius):
        condition = lambda f: f.distToShape(tool)[0] < radius
        mask = [condition(f) for f in topo.solid.Faces]
        return mask

    def _faces_by_solid_inside(self, topo, tool):
        def condition(points):
            good = [tool.isInside(Base.Vector(*p), self.tolerance, self.include_shell) for p in points]
            return np.array(good)
        return topo.get_faces_by_location_mask(condition, self.include_partial)

    # SWITCH

    def calc_mask(self, solid, tool, precision, direction, center, percent, radius):
        topo = SvSolidTopology(solid)
        if self.element_type == 'VERTS':
            if self.criteria_type == 'SIDE':
                vertex_mask = self._verts_by_side(topo, direction, percent)
            elif self.criteria_type == 'SPHERE':
                vertex_mask = self._verts_by_sphere(topo, center, radius)
            elif self.criteria_type == 'PLANE':
                vertex_mask = self._verts_by_plane(topo, center, direction, radius)
            elif self.criteria_type == 'CYLINDER':
                vertex_mask = self._verts_by_cylinder(topo, center, direction, radius)
            elif self.criteria_type == 'SOLID_DISTANCE':
                vertex_mask = self._verts_by_solid_distance(topo, tool, radius)
            elif self.criteria_type == 'SOLID_INSIDE':
                vertex_mask = self._verts_by_solid_inside(topo, tool)
            else:
                raise Exception("Unknown criteria for vertices")
            verts = [v for c, v in zip(vertex_mask, solid.Vertexes) if c]
            edge_mask = topo.get_edges_by_vertices_mask(verts, self.include_partial_other)
            face_mask = topo.get_faces_by_vertices_mask(verts, self.include_partial_other)
        elif self.element_type == 'EDGES':
            topo.tessellate(precision)
            if self.criteria_type == 'SIDE':
                edge_mask = self._edges_by_side(topo, direction, percent)
            elif self.criteria_type == 'SPHERE':
                edge_mask = self._edges_by_sphere(topo, center, radius)
            elif self.criteria_type == 'PLANE':
                edge_mask = self._edges_by_plane(topo, center, direction, radius)
            elif self.criteria_type == 'CYLINDER':
                edge_mask = self._edges_by_cylinder(topo, center, direction, radius)
            elif self.criteria_type == 'DIRECTION':
                edge_mask = self._edges_by_direction(topo, direction, percent)
            elif self.criteria_type == 'SOLID_DISTANCE':
                edge_mask = self._edges_by_solid_distance(topo, tool, radius)
            elif self.criteria_type == 'SOLID_INSIDE':
                edge_mask = self._edges_by_solid_inside(topo, tool)
            else:
                raise Exception("Unknown criteria for edges")
            edges = [e for c, e in zip(edge_mask, solid.Edges) if c]
            vertex_mask = topo.get_vertices_by_edges_mask(edges)
            face_mask = topo.get_faces_by_edges_mask(edges, self.include_partial_other)
        else: # FACES
            topo.tessellate(precision)
            if self.criteria_type == 'SIDE':
                face_mask = self._faces_by_side(topo, direction, percent)
            elif self.criteria_type == 'NORMAL':
                topo.calc_normals()
                face_mask = self._faces_by_normal(topo, direction, percent)
            elif self.criteria_type == 'SPHERE':
                face_mask = self._faces_by_sphere(topo, center, radius)
            elif self.criteria_type == 'PLANE':
                face_mask = self._faces_by_plane(topo, center, direction, radius)
            elif self.criteria_type == 'CYLINDER':
                face_mask = self._faces_by_cylinder(topo, center, direction, radius)
            elif self.criteria_mask == 'SOLID_DISTANCE':
                face_mask = self._faces_by_solid_distance(topo, tool, radius)
            elif self.criteria_type == 'SOLID_INSIDE':
                face_mask = self._faces_by_solid_inside(topo, tool)
            else:
                raise Exception("Unknown criteria type for faces")
            faces = [f for c, f in zip(face_mask, solid.Faces) if c]
            vertex_mask = topo.get_vertices_by_faces_mask(faces)
            edge_mask = topo.get_edges_by_faces_mask(faces)

        return vertex_mask, edge_mask, face_mask

    def process(self):

        if not any(output.is_linked for output in self.outputs):
            return

        solid_s = self.inputs['Solid'].sv_get()
        if self.criteria_type in {'SOLID_DISTANCE', 'SOLID_INSIDE'}:
            tool_s = self.inputs['Tool'].sv_get()
            tool_s = ensure_nesting_level(tool_s, 2, data_types=(Part.Shape,))
        else:
            tool_s = [[None]]
        direction_s = self.inputs['Direction'].sv_get()
        center_s = self.inputs['Center'].sv_get()
        percent_s = self.inputs['Percent'].sv_get()
        radius_s = self.inputs['Radius'].sv_get()
        precision_s = self.inputs['Precision'].sv_get()

        input_level = get_data_nesting_level(solid_s, data_types=(Part.Shape,))
        solid_s = ensure_nesting_level(solid_s, 2, data_types=(Part.Shape,))
        direction_s = ensure_nesting_level(direction_s, 3)
        center_s = ensure_nesting_level(center_s, 3)
        percent_s = ensure_nesting_level(percent_s, 2)
        radius_s = ensure_nesting_level(radius_s, 2)
        precision_s = ensure_nesting_level(precision_s, 2)

        vertex_mask_out = []
        edge_mask_out = []
        face_mask_out = []
        for objects in zip_long_repeat(solid_s, tool_s, direction_s, center_s, percent_s, radius_s, precision_s):
            vertex_mask_new = []
            edge_mask_new = []
            face_mask_new = []
            for solid, tool, direction, center, percent, radius, precision in zip_long_repeat(*objects):
                vertex_mask, edge_mask, face_mask = self.calc_mask(solid, tool, precision, direction, center, percent, radius)
                vertex_mask_new.append(vertex_mask)
                edge_mask_new.append(edge_mask)
                face_mask_new.append(face_mask)

            if input_level == 2:
                vertex_mask_out.append(vertex_mask_new)
                edge_mask_out.append(edge_mask_new)
                face_mask_out.append(face_mask_new)
            else:
                vertex_mask_out.extend(vertex_mask_new)
                edge_mask_out.extend(edge_mask_new)
                face_mask_out.extend(face_mask_new)

        self.outputs['VerticesMask'].sv_set(vertex_mask_out)
        self.outputs['EdgesMask'].sv_set(edge_mask_out)
        self.outputs['FacesMask'].sv_set(face_mask_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSelectSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSelectSolidNode)

