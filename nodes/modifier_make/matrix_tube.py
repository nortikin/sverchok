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
from mathutils import Matrix, Vector
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (Vector_generate, Matrix_generate, updateNode, zip_long_repeat, ensure_nesting_level, flatten_data, get_edge_loop)
from sverchok.utils.nodes_mixins.sockets_config import ModifierNode
from sverchok.utils.sv_bmesh_utils import empty_bmesh, add_mesh_to_bmesh
import numpy as np
from collections import namedtuple


###### Это надо перенести в utils (оригинал в nodes\analyzer\origins.py)

MeshMode = namedtuple('MeshMode', ['verts', 'edges', 'faces'])
MODE = MeshMode('Verts', 'Edges', 'Faces')

def get_origin(verts, edges=None, faces=None, mode=MODE.faces):
    """
    Return origins of selected type of mesh component 
    close to how Blender draw axis in edit (normal) mode of selected element
    :param verts: list of tuple(float, float, float)
    :param edges: list of tuple(int, int) or None
    :param faces: list of list of int or None
    :param mode: 'Verts', 'Edges' or 'Faces'
    :return: list of centers, normals, tangents and matrixes of vertexes or edges or faces according selected mode
    """
    with empty_bmesh(False) as bm:
        add_mesh_to_bmesh(bm, verts, edges, faces, update_normals=True)

        if mode == MODE.verts:
            origins = [vert.co for vert in bm.verts]
            normals = [vert.normal for vert in bm.verts]
            tangents = [get_vert_tang(v) for v in bm.verts]
        elif mode == MODE.edges:
            if edges is None and faces is None:
                raise ValueError("Edges or Faces should be connected")
            origins =[e.verts[0].co.lerp(e.verts[1].co, 0.5) for e in bm.edges]
            normals, tangents = zip(*[get_edge_normal_tang(e) for e in bm.edges])
        elif mode == MODE.faces:
            if faces is None:
                raise ValueError("Faces should be connected")
            origins = [f.calc_center_median() for f in bm.faces]
            normals = [f.normal for f in bm.faces]
            tangents = [get_face_tangent(f) for f in bm.faces]
        else:
            raise ValueError(f"Unknown mode: {mode}")

        matrixes = [build_matrix(orig, norm, tang) for orig, norm, tang in zip(origins, normals, tangents)]
        return [[v[:] for v in origins], [v[:] for v in normals], [v[:] for v in tangents], matrixes]


def get_vert_tang(vert):
    # returns tangent close to Blender logic in normal mode
    # vert - bmesh vertex
    if len(vert.link_edges) == 2:
        return vert.link_loops[0].calc_tangent().cross(vert.normal)
    elif vert.normal == Vector((0, 0, 1)):
        return Vector((-1, 0, 0))
    elif vert.normal == Vector((0, 0, -1)):
        return Vector((1, 0, 0))
    else:
        return vert.normal.cross(vert.normal.cross(Vector((0, 0, 1)))).normalized()


def get_edge_normal_tang(edge):
    # returns normal and tangent close to Blender logic in normal mode
    # edge - bmesh edge
    direct = (edge.verts[1].co - edge.verts[0].co).normalized()
    _normal = (edge.verts[0].normal + edge.verts[1].normal).normalized()
    tang = direct.cross(_normal)
    normal = tang.cross(direct)
    return normal, tang


def get_face_tangent(face):
    # returns tangent close to Blender logic in normal mode
    # face - bmesh face
    if len(face.edges) > 3:
        return face.calc_tangent_edge_pair().normalized() * -1
    else:
        return face.calc_tangent_edge_diagonal()


def build_matrix(center, normal, tangent):
    # build matrix from 3 vectors (center, normal(z), tangent(y))
    x_axis = tangent.cross(normal)
    return Matrix(list(zip(x_axis.resized(4), tangent.resized(4), normal.resized(4), center.to_4d())))

###### /Это надо перенести в utils (оригинал в nodes\analyzer\origins.py)

def make_edges_and_faces(start_pos, P, M, cap_bottom, cap_top, flags, get_edges, get_faces):
    """
    Generate the cylinder polygons for the given parameters
        P : number of parallels (= number of points in a meridian)
        M : number of meridians (= number of points in a parallel)
        cap_bottom : turn on/off the bottom cap generation
        cap_top    : turn on/off the top cap generation
        flags       : separate (split the parallels into separate poly lists), cyclic of parallels
        get_edges, get_faces: boolean what generate: edges or faces or both? (to decrease memory by arr_vert)
    """
    separate, center, cyclic = flags

    N1 = M # Y
    N2 = P # X

    if get_edges or get_faces:
        steps = np.arange( N1*N2 )
        _arr_verts = np.array ( np.split(steps, N2 ) )  # split array by rows (V)
        if cyclic:
            _arr_verts = np.hstack( (_arr_verts, np.array([_arr_verts[:,0]]).T ) ) # append first row to bottom to horizontal circle


    _list_edges = []
    if get_edges:
        if separate:  # replicate edges in one parallel for every meridian point
            _list_edges = [get_edge_loop(M)] * P
        else:
            _arr_h_edges = np.empty((N2, N1, 2), 'i' ) if cyclic else np.empty((N2, N1-1, 2), 'i' )
            _arr_h_edges[:, :, 0] = _arr_verts[ : ,  :-1 ]  # hor_edges
            _arr_h_edges[:, :, 1] = _arr_verts[ : , 1:   ]  # hor_edges
            _arr_h_edges = _arr_h_edges.reshape(-1,2)

            _arr_v_edges = np.empty( (N2-1, N1, 2), 'i' ) if cyclic else np.empty( (N2-1, N1-1, 2), 'i' )
            _arr_v_edges[:, :, 0] = _arr_verts[ :-1, :-1]  # vert_edges
            _arr_v_edges[:, :, 1] = _arr_verts[1:  , :-1]  # vert_edges
            _arr_v_edges = _arr_v_edges.reshape(-1,2)

            _edges = np.concatenate( ( _arr_h_edges, _arr_v_edges, ) )
            _edges = _edges+start_pos
            _list_edges = _edges.tolist()


    _list_faces = []

    if get_faces:
        if separate:
            _list_faces = [[list(range(M))]] * P
        else:
            steps = np.arange( N1*N2 )
            _arr_verts = np.array ( np.split(steps, N2 ) )  # split array by rows (V)
            _arr_verts+=start_pos
            if cyclic:
                _arr_verts = np.hstack( (_arr_verts, np.array([_arr_verts[:,0]]).T ) ) # append first column to the left to horizontal circle

            _arr_faces = np.empty((N2-1, N1, 4), 'i' ) if cyclic else np.empty((N2-1, N1-1, 4), 'i' )
            _arr_faces[:, :, 0] = _arr_verts[  :-1,  :-1 ]
            _arr_faces[:, :, 1] = _arr_verts[  :-1, 1:   ]
            _arr_faces[:, :, 2] = _arr_verts[ 1:  , 1:   ]
            _arr_faces[:, :, 3] = _arr_verts[ 1:  ,  :-1 ]
            _arr_faces_res = _arr_faces.reshape(-1,4)
            _list_faces = _arr_faces_res.tolist()
            if cap_top:
                l_top = [_arr_verts[-1][:-1].tolist()]  # cyclic do not apply on the top and the bottom
                _list_faces.extend(l_top)

            if cap_bottom:
                l_bottom = [np.flip(_arr_verts[0][:-1]).tolist()]
                l_bottom.extend(_list_faces)
                _list_faces = l_bottom

    return _list_edges, _list_faces

class SvMatrixTubeNodeMK2(ModifierNode, SverchCustomTreeNode, bpy.types.Node):
    ''' takes a list of vertices and a list of matrixes
        the vertices are to be joined in a ring, copied and transformed by the 1st matrix
        and this ring joined to the previous ring.
        The ring doesn't have to be planar.
        outputs lists of vertices, edges and faces
        ends are capped
    '''
    bl_idname = 'SvMatrixTubeNodeMK2'
    bl_label = 'Matrix Tube'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MATRIX_TUBE'

    profile_faces__close_modes = [
            ( 'CLOSED' , "Closed", "Close contour (as 1)", 'PROP_CON', 1),
            ( 'OPENED' , "Opened", "Open contour (as 0)", 'PROP_PROJECTED', 0),
            ( 'INPAIRS', "Pairs" , "Pair list (as 2). ex.: your list is 1,2,2,3,3,4,6,7,7,8 => as program interpret it: [1,2],[2,3],[3,4],[6,7],[7,8]. Be careful. If there is no offset with this index then pair will be skipped", 'CON_TRACKTO', 2),
        ]
    profile_faces__close_mode1 : bpy.props.EnumProperty(
        name = "Open mode",
        description = "Open mode",
        items = profile_faces__close_modes,
        default = 'CLOSED',
        update = updateNode
        )
    
    profile_faces_id_to_extrude_modes = [
        ('BOOLEANS', "Booleans", "Boolean values (0/1) as mask of Voronoi Sites per objects [[0,1,0,0,1,1],[1,1,0,0,1],...]. Has no influence if socket is not connected (All sites are used)", 0),
        ('INDEXES', "Indexes", "Indexes as mask of Voronoi Sites per objects [[1,2,0,4],[0,1,4,5,7],..]. Has no influence if socket is not connected (All sites are used)", 1),
    ]
    profile_faces_id_to_extrude_mode : bpy.props.EnumProperty(
        name = "Mask of shapes",
        items = profile_faces_id_to_extrude_modes,
        default = 'BOOLEANS',
        update = updateNode
        )
    
    profile_faces_id_to_extrude_inversion : bpy.props.BoolProperty(
        name = "Invert",
        default = False,
        description="Invert mask of faces. Has no influence if socket is not connected (All faces are used)",
        update = updateNode) # type: ignore
    
    def draw_profile_faces_indexes_in_socket(self, socket, context, layout):
        grid = layout.grid_flow(row_major=False, columns=3, align=True)
        col = grid.row(align=True)
        if socket.is_linked==True:
            socket_label = socket.objects_number if hasattr(socket, "objects_number")==True else '-'
        else:
            socket_label = ''

        col.enabled = True
        if socket.is_linked==False:
            col.label(text=f"Profile faces indexes {socket_label}")
            col.label(text=f"", icon='ERROR')
            col.label(text=f"needs to be connected")
        else:
            col.label(text=f"{socket.label} {socket_label}")
        pass

    def draw_profile_faces_id_to_extrude_in_socket(self, socket, context, layout):
        grid = layout.grid_flow(row_major=True, columns=2)
        col2 = grid.column()
        col2_row1 = col2.row()
        col2_row1.alignment='LEFT'
        if socket.is_linked:
            col2_row1.label(text=f"{socket.label}. {socket.objects_number or ''}:")
        else:
            col2_row1.label(text=f"{socket.label}:")
        col2_row2 = col2.row()
        col2_row2.alignment='LEFT'
        col2_row2.column(align=True).prop(self, "profile_faces_id_to_extrude_inversion")
        col3 = grid.column()
        col3.prop(self, "profile_faces_id_to_extrude_mode", expand=True)

        col2_row2.enabled = True
        col3.enabled = True
        if not socket.is_linked:
            col2_row2.enabled = False
            col3.enabled = False


    def draw_profile_faces_close_mode_in_socket(self, socket, context, layout):
        grid = layout.grid_flow(row_major=False, columns=3, align=True)
        col = grid.row()
        col.prop(self, 'profile_faces__close_mode1', expand=False, text='Profile close mode')
        if socket.is_linked==True:
            col.enabled = False
        else:
            col.enabled = True
        pass

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "vertices")
        self.inputs.new('SvStringsSocket' , 'profile_faces_indexes')
        self.inputs.new('SvStringsSocket' , 'profile_faces_id_to_extrude')
        self.inputs.new('SvMatrixSocket'  , "tube_matrixes")
        self.inputs.new('SvMatrixSocket'  , "tube_compensation_matrixes")
        #self.inputs.new('SvStringsSocket' , "tube_idx_per_face")
        self.inputs.new('SvStringsSocket' , 'profile_faces_close_mode')

        self.inputs["vertices"].label = "Vertices"
        self.inputs['profile_faces_indexes'].label = 'Faces'
        self.inputs['profile_faces_indexes'].custom_draw = 'draw_profile_faces_indexes_in_socket'
        self.inputs['profile_faces_id_to_extrude'].label = "Faces ids"
        self.inputs['profile_faces_id_to_extrude'].custom_draw = 'draw_profile_faces_id_to_extrude_in_socket'
        self.inputs["tube_matrixes"].label = "Tube Matrixes"
        self.inputs["tube_compensation_matrixes"].label = "Tube Compensation Matrixes"
        #self.inputs["tube_idx_per_face"].label = "Tube indexes per face"
        self.inputs['profile_faces_close_mode'].label = 'Profile Close mode'
        self.inputs['profile_faces_close_mode'].custom_draw = 'draw_profile_faces_close_mode_in_socket'

        self.outputs.new('SvVerticesSocket', "vertices")
        self.outputs.new('SvStringsSocket', "edges")
        self.outputs.new('SvStringsSocket', "faces")
        self.outputs.new('SvMatrixSocket', "tests")

        self.outputs["vertices"].label = "Vertices"
        self.outputs["edges"].label = "Edges"
        self.outputs["faces"].label = "Faces"

    @property
    def sv_internal_links(self):
        return [(self.inputs['vertices'], self.outputs['vertices'])]

    def process(self):
        if not all([sock.is_linked for sock in self.inputs if sock.name in ['tube_matrixes', 'vertices', 'profile_faces_indexes'] ]):
            return
        if not any([sock.is_linked for sock in self.outputs ]):
            return
        
        _vertices              = self.inputs['vertices'].sv_get(default=[[]], deepcopy=False)
        vertices3              = ensure_nesting_level(_vertices, 3)
        _profile_faces_indexes = self.inputs['profile_faces_indexes'].sv_get(default=[[]], deepcopy=False)
        profile_faces_indexes3 = ensure_nesting_level(_profile_faces_indexes, 3)
        _tube_matrixes         = self.inputs['tube_matrixes'].sv_get(default=[[]], deepcopy=False)
        tube_matrixes3         = ensure_nesting_level(_tube_matrixes, 3)
        _tube_compensation_matrixes = self.inputs['tube_compensation_matrixes'].sv_get(default=[[Matrix()]], deepcopy=False)
        tube_compensation_matrixes2 = ensure_nesting_level(_tube_compensation_matrixes, 2)

        #vertices = Vector_generate(self.inputs['vertices'].sv_get())
        #matrixes = Matrix_generate(self.inputs['matrixes'].sv_get())
        verts_out, edges_out, faces_out, tests_out = self.make_tube(vertices3, profile_faces_indexes3, tube_matrixes3, tube_compensation_matrixes2)
        self.outputs['vertices'].sv_set(verts_out)
        self.outputs['edges'].sv_set(edges_out)
        self.outputs['faces'].sv_set(faces_out)
        self.outputs['tests'].sv_set(tests_out)

    def make_tube_00(self, matrixes, vertices, profile_faces_indexes3):
        edges_out = []
        verts_out = []
        faces_out = []
        vID = 0
        nring = len(vertices[0])
        # end face
        faces_out.append(list(range(nring)))
        for i,m in enumerate(matrixes):
            for j,v in enumerate(vertices[0]):
                vout = Matrix(m) @ Vector(v)
                verts_out.append(vout.to_tuple())
                vID = j + i * nring
                # rings
                if j != 0:
                    edges_out.append([vID, vID - 1])
                else:
                    edges_out.append([vID, vID + nring-1])
                # lines
                if i != 0:
                    edges_out.append([vID, vID - nring])
                    # faces
                    if j != 0:
                        faces_out.append([vID, vID - nring, vID - nring - 1, vID-1,])
                    else:
                        faces_out.append([vID, vID - nring,  vID-1, vID + nring-1])
        # end face
        # reversing list fixes face normal direction keeps mesh manifold
        f = list(range(vID, vID-nring, -1))
        faces_out.append(f)
        return verts_out, edges_out, faces_out

    def make_tube(self, overtices, oprofile_faces_indexes3, tube_matrixes3, tube_compensation_matrixes2_input):
        verts_out = []
        edges_out = []
        faces_out = []
        tests_out = []
        vID = 0

        for I, ofaces in enumerate(oprofile_faces_indexes3):
            if len(overtices)<=I-1:
                # Прекращать расчёт, если объектов вершин меньше, чем объектов faces
                break
            overts = overtices[I]
            tube_matrixes_of_object  = tube_matrixes3[I] if len(tube_matrixes3)<=I-1 else tube_matrixes3[-1]
            tube_compensation_matrixes_of_object = tube_compensation_matrixes2_input[I] if len(tube_compensation_matrixes2_input)<=I-1 else tube_compensation_matrixes2_input[-1]

            extruded_verts = []
            start_pos = 0
            obj_edges = []
            obj_faces = []
            faces_origins, faces_normals, faces_tangents, faces_matrixes = get_origin(overts, [], ofaces, "Faces")
            for J, face_indexes in enumerate(ofaces):
                verts = [overts[idx] for idx in face_indexes]

                tube_matrixes_of_object_J  = tube_matrixes_of_object[J] if J<=len(tube_matrixes_of_object)-1 else tube_matrixes_of_object[-1]
                tube_compensation_matrixes_J  = tube_compensation_matrixes_of_object[J] if J<=len(tube_compensation_matrixes_of_object)-1 else tube_compensation_matrixes_of_object[-1]
                tube_matrixes_J_compensated = [tube_compensation_matrixes_J @ m for m in tube_matrixes_of_object_J]
                tube_matrixes_J_compensated_0 = tube_matrixes_J_compensated[0]
                tube_matrixes_J_compensated_0_inverted = tube_matrixes_J_compensated_0.inverted()
                T, tube_matrixes_J_compensated_0_R, S = tube_matrixes_J_compensated_0.decompose()
                e = tube_matrixes_J_compensated_0_R.to_euler('XYZ')
                # reset x,y rotation
                e.x = e.y = 0.0
                tube_matrixes_J_compensated_0_R_Z = e.to_quaternion().to_matrix().to_4x4()
                tube_matrixes_J_compensated_0_R_Z_inverted = tube_matrixes_J_compensated_0_R_Z.inverted()
                tube_matrixes_J_0_initial_position = [tube_matrixes_J_compensated_0_inverted @ m for m in tube_matrixes_J_compensated]
                tube_matrixes_J_0_initial_position = [tube_matrixes_J_compensated_0_R_Z @ m for m in tube_matrixes_J_0_initial_position]

                #faces_origins_J = faces_origins[J]
                faces_matrixes_J = faces_matrixes[J]
                faces_matrixes_J_inverted = faces_matrixes_J.inverted()
                faces_matrixes_J_inverted_compensated_0_R_Z_inverted = tube_matrixes_J_compensated_0_R_Z_inverted @ faces_matrixes_J_inverted
                verts_for_tube = [( faces_matrixes_J_inverted_compensated_0_R_Z_inverted @ Vector(co) ).to_tuple() for co in verts]
                N = len(verts_for_tube)
                K = len(tube_matrixes_J_0_initial_position)
                # 1) собираем все слои вершин
                extruded_verts1 = []
                for M in tube_matrixes_J_0_initial_position:
                    for co in verts_for_tube:
                        # Mathutils: 4x4 @ Vector((x,y,z)) учитывает трансляцию
                        # extruded_verts1.append((M @ Vector(co)).to_tuple())
                        extruded_verts1.append(((M) @ Vector(co)).to_tuple())
                extruded_verts_restored = [( faces_matrixes_J @ Vector(co) ).to_tuple() for co in extruded_verts1]
                extruded_verts.extend(extruded_verts_restored)

                edges, faces = make_edges_and_faces(start_pos, K, N, False, True, (False, False, True), True, True)
                obj_edges.extend(edges)
                obj_faces.extend(faces)
                start_pos+=K*N

            verts_out.append(extruded_verts)
            edges_out.append(obj_edges)
            faces_out.append(obj_faces)
            tests_out.append([faces_matrixes_J])
        # end face
        # reversing list fixes face normal direction keeps mesh manifold
        #f = list(range(vID, vID-nring, -1))
        #faces_out.append(f)
        return verts_out, edges_out, faces_out, tests_out


def register():
    bpy.utils.register_class(SvMatrixTubeNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvMatrixTubeNodeMK2)
