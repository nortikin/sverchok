
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.sv_mesh_utils import polygons_to_edges
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, edge_data_from_bmesh_edges
from sverchok.utils.geom import PlaneEquation, center
from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import geomdl, FreeCAD

class SvExQuadsToNurbsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Quad to NURBS
    Tooltip: Make a smooth NURBS surface patch from each quad face
    """
    bl_idname = 'SvExQuadsToNurbsNode'
    bl_label = 'Quads to NURBS'
    bl_icon = 'SURFACE_NSURFACE'

    degree_u : IntProperty(
            name = "Degree U",
            min = 2, max = 4,
            default = 3,
            update = updateNode)

    degree_v : IntProperty(
            name = "Degree V",
            min = 2, max = 4,
            default = 3,
            update = updateNode)

    vertex_weight : FloatProperty(
            name = "Vertex weight",
            default = 1.0,
            update = updateNode)

    edge_weight : FloatProperty(
            name = "Edge weight",
            default = 1.0,
            update = updateNode)

    face_weight : FloatProperty(
            name = "Face weight",
            default = 1.0,
            update = updateNode)

    tangent_weight : FloatProperty(
            name = "Tangent weight",
            default = 1.0,
            min = 0, max=3.0,
            update = updateNode)

    def get_implementations(self, context):
        items = []
        i = 0
        if geomdl is not None:
            item = (SvNurbsSurface.GEOMDL, "Geomdl", "Geomdl (NURBS-Python) package implementation",i)
            i += 1
            items.append(item)
        item = (SvNurbsSurface.NATIVE, "Sverchok", "Sverchok built-in implementation", i)
        items.append(item)
        i += 1
        if FreeCAD is not None:
            item = (SvNurbsMaths.FREECAD, "FreeCAD", "FreeCAD library implementation",i)
            items.append(item)
        return items

    implementation : EnumProperty(
            name = "Implementation",
            items = get_implementations,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', "Faces")
        self.inputs.new('SvStringsSocket', "VertexWeight").prop_name = 'vertex_weight'
        self.inputs.new('SvStringsSocket', "EdgeWeight").prop_name = 'edge_weight'
        self.inputs.new('SvStringsSocket', "FaceWeight").prop_name = 'face_weight'
        self.inputs.new('SvStringsSocket', "TangentWeight").prop_name = 'tangent_weight'
        self.inputs.new('SvStringsSocket', "DegreeU").prop_name = 'degree_u'
        self.inputs.new('SvStringsSocket', "DegreeV").prop_name = 'degree_v'
        self.outputs.new('SvSurfaceSocket', "Surfaces")
        self.outputs.new('SvVerticesSocket', "ControlPoints")
        self.outputs.new('SvStringsSocket', "Weights")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'implementation', text='')

    def make_surface(self,face, degree_u, degree_v, vertices, planes, vert_weights, tangent_weights, face_weight, edge_weights_dict, edge_planes_dict):
        """
        V0 ------ [E01] --- [E0C] --- [E02] --- V1
        |          |         |        |         |
        |          |         |        |         |
        |          |         |        |         |
        [E11] --- [F1] ---- [E0F] --- [F2] --- [E21]
        |          |         |        |         |
        |          |         |        |         |
        |          |         |        |         |
        [E1C] --- [E1F] --- [CC] --- [E2F] --- [E2C]
        |          |         |        |         |
        |          |         |        |         |
        |          |         |        |         |
        [E12] --- [F3] ---- [E3F] --- [F4] --- [E22]
        |          |         |        |         |
        |          |         |        |         |
        |          |         |        |         |
        V3 ------ [E31] --- [E3C] --- [E32] --- V2
        """
        tangent_weights = [w/3.0 for w in tangent_weights]
        vertices = [Vector(v) for v in vertices]

        def  mk_edge_point(i, j):
            return (vertices[j] - vertices[i]) * tangent_weights[i] + vertices[i]

        def mk_face_corner_point(i, j, k):
            dv1 = (vertices[j] - vertices[i]) * tangent_weights[i]
            dv2 = (vertices[k] - vertices[i]) * tangent_weights[i]
            #m = face_weight
            return planes[i].projection_of_point(vertices[i] + dv1 + dv2)

        # edge planes
        e0p = edge_planes_dict[(face[0], face[1])]
        e1p = edge_planes_dict[(face[0], face[3])]
        e2p = edge_planes_dict[(face[1], face[2])]
        e3p = edge_planes_dict[(face[2], face[3])]

        def mk_edge_center_point(ep1, ep2):
            return (ep1 + ep2) / 2.0

        def mk_face_edge_point(edge_plane, edge_point, edge_vec, vec1, vec2):
            length = (vec1.length + vec2.length) / 2.0
            vec = edge_plane.normal.cross(edge_vec)
            #print("EV: %s, N: %s, L: %s, Res: %s" % (edge_vec, edge_plane.normal, length, vec))
            vec = length * vec.normalized()
            return edge_point + vec

        e01 = planes[0].projection_of_point(mk_edge_point(0, 1))
        e02 = planes[1].projection_of_point(mk_edge_point(1, 0))
        e11 = planes[0].projection_of_point(mk_edge_point(0, 3))
        e21 = planes[1].projection_of_point(mk_edge_point(1, 2))
        f1 = mk_face_corner_point(0, 1, 3)
        f2 = mk_face_corner_point(1, 0, 2)
        e12 = planes[3].projection_of_point(mk_edge_point(3, 0))
        e31 = planes[3].projection_of_point(mk_edge_point(3, 2))
        e32 = planes[2].projection_of_point(mk_edge_point(2, 3))
        e22 = planes[2].projection_of_point(mk_edge_point(2, 1))
        f3 = mk_face_corner_point(3, 0, 2)
        f4 = mk_face_corner_point(2, 3, 1)

        e0c = mk_edge_center_point(e01, e02)
        e1c = mk_edge_center_point(e11, e12)
        e2c = mk_edge_center_point(e21, e22)
        e3c = mk_edge_center_point(e31, e32)

        e0f = mk_face_edge_point(e0p, e0c, (vertices[1] - vertices[0]), (f1 - e01), (f2 - e02))
        e1f = mk_face_edge_point(e1p, e1c, (vertices[0] - vertices[3]), (f3 - e12), (f1 - e11))
        e2f = mk_face_edge_point(e2p, e2c, (vertices[2] - vertices[1]), (f2 - e21), (f4 - e22))
        e3f = mk_face_edge_point(e3p, e3c, (vertices[3] - vertices[2]), (f3 - e31), (f4 - e32))

        cc = center([f1, e0f, f2, e2f, f4, e3f, f3, e1f])

        control_points = [
                [vertices[0], e01, e0c, e02, vertices[1]],
                [e11, f1, e0f, f2, e21],
                [e1c, e1f, cc, e2f, e2c],
                [e12, f3, e3f, f4, e22],
                [vertices[3], e31, e3c, e32, vertices[2]]
            ]

        # edge point weights
        e0w = edge_weights_dict[(face[0], face[1])]
        e1w = edge_weights_dict[(face[0], face[3])]
        e2w = edge_weights_dict[(face[1], face[2])]
        e3w = edge_weights_dict[(face[2], face[3])]

        weights = [
                [vert_weights[0], e0w, e0w, e0w, vert_weights[1]],
                [e1w, face_weight, face_weight, face_weight, e2w],
                [e1w, face_weight, face_weight, face_weight, e2w],
                [e1w, face_weight, face_weight, face_weight, e2w],
                [vert_weights[3], e3w, e3w, e3w, vert_weights[2]]
            ]

        new_surf = SvNurbsSurface.build(
                self.implementation,
                degree_u, degree_v,
                sv_knotvector.generate(degree_u, 5),
                sv_knotvector.generate(degree_v, 5),
                np.array(control_points),
                np.array(weights)
            )
        return new_surf, control_points, weights

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get()
        faces_s = self.inputs['Faces'].sv_get()
        vertex_weight_s = self.inputs['VertexWeight'].sv_get()
        edge_weight_s = self.inputs['EdgeWeight'].sv_get()
        face_weight_s = self.inputs['FaceWeight'].sv_get()
        tangent_weight_s = self.inputs['TangentWeight'].sv_get()
        degree_u_s = self.inputs['DegreeU'].sv_get()
        degree_v_s = self.inputs['DegreeV'].sv_get()
        
        surface_out = []
        control_points_out = []
        weights_out = []
        inputs = zip_long_repeat(vertices_s, edges_s, faces_s, degree_u_s, degree_v_s, vertex_weight_s, edge_weight_s, face_weight_s, tangent_weight_s)
        for vertices, edges, faces, degree_u, degree_v, vertex_weights, edge_weights, face_weights, tangent_weights in inputs:
            fullList(degree_u, len(faces))
            fullList(degree_v, len(faces))

            if not edges:
                edges = polygons_to_edges([faces], True)[0]

            fullList(vertex_weights, len(vertices))
            fullList(tangent_weights, len(vertices))
            fullList(edge_weights, len(edges))
            fullList(face_weights, len(faces))

            bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True, markup_edge_data=True)
            normals = [vertex.normal for vertex in bm.verts]
            edge_planes_dict = dict()
            for edge in bm.edges:
                edge_v = edge.verts[1].co - edge.verts[0].co
                edge_c = (edge.verts[0].co + edge.verts[1].co) / 2.0
                edge_ort_plane = PlaneEquation.from_normal_and_point(edge_v, edge_c)
                face_normals = [face.normal for face in edge.link_faces]
                faces_normal = sum(face_normals, Vector())
                projected_faces_normal = edge_ort_plane.projection_of_point(faces_normal)
                #print("EV: %s, No.sum: %s, Pr.N: %s" % (edge_v, faces_normal, projected_faces_normal))
                edge_plane = PlaneEquation.from_normal_and_point(projected_faces_normal, edge_c)
                edge_planes_dict[(edge.verts[0].index, edge.verts[1].index)] = edge_plane
                edge_planes_dict[(edge.verts[1].index, edge.verts[0].index)] = edge_plane
            bm.free()

            vert_planes = [PlaneEquation.from_normal_and_point(normal, point) for normal, point in zip(normals, vertices)]

            edge_weights_dict = dict()
            #edge_planes_dict = dict()
            for (i, j), edge_weight in zip(edges, edge_weights):
                edge_weights_dict[(i, j)] = edge_weight
                edge_weights_dict[(j, i)] = edge_weight
                #edge_planes_dict[(i, j)] = edge_plane
                #edge_planes_dict[(j, i)] = edge_plane

            for i, (face, degree_u, degree_v, face_weight) in enumerate(zip(faces, degree_u, degree_v, face_weights)):
                if len(face) != 4:
                    self.info("Face #%s is not a Quad, skip it", i)
                    continue
                face_verts = [vertices[i] for i in face]
                face_planes = [vert_planes[i] for i in face]
                face_vert_weights = [vertex_weights[i] for i in face]
                face_tangent_weights = [tangent_weights[i] for i in face]
                #face_edges = list(zip(face, face[1:])) + [(face[-1], face[0])]
                #face_edge_weights = [edge_weights_dict[edge] for edge in face_edges]
                surface, ctrlpts, weights = self.make_surface(face,
                                degree_u, degree_v,
                                face_verts, face_planes,
                                face_vert_weights, face_tangent_weights, face_weight,
                                edge_weights_dict, edge_planes_dict)
                surface_out.append(surface)
                control_points_out.append(list(map(tuple,ctrlpts)))
                weights_out.append(weights)

        self.outputs['Surfaces'].sv_set(surface_out)
        self.outputs['ControlPoints'].sv_set(control_points_out)
        self.outputs['Weights'].sv_set(weights_out)

def register():
    bpy.utils.register_class(SvExQuadsToNurbsNode)

def unregister():
    bpy.utils.unregister_class(SvExQuadsToNurbsNode)

