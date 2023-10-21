# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from math import sin, cos, radians

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_modes, list_match_func
from sverchok.utils.decorators_compilation import jit, njit
import numpy as np

# from numba.typed import List
# @njit(cache=True)
def make_sphere_verts_combined(U, V, Radius):

    N1 = U # X
    N2 = V # Y
    n1_i = np.arange(N1, dtype=np.int16)
    _n1  = np.repeat( [np.array(n1_i)], N2-2, axis = 0)        # index n1
    n2_i = np.arange(1, N2-1, dtype=np.int16)
    _n2  = np.repeat( [np.array(n2_i)], N1, axis = 0).T # index n2

    theta = radians(360 / U)
    phi = radians(180 / (V-1))

    _theta = theta*_n1
    _phi = phi*_n2
    _X = Radius * np.cos(_theta) * np.sin(_phi)
    _Y = Radius * np.sin(_theta) * np.sin(_phi)
    _Z = Radius * np.cos(_phi)
    _verts = np.dstack((_X, _Y, _Z))
    _verts = _verts.reshape(-1, 3)
    list_verts = [[0,0,Radius]]
    list_verts.extend(_verts.tolist())
    list_verts.append([0,0,-Radius])
    return list_verts

def make_sphere_verts_separate(U, V, Radius):
    theta = radians(360 / U)
    phi = radians(180 / (V-1))

    pts = []
    pts = [[[0, 0, Radius] for i in range(U)]]
    for i in range(1, V-1):
        pts_u = []
        sin_phi_i = sin(phi*i)
        for j in range(U):
            X = Radius*cos(theta*j)*sin_phi_i
            Y = Radius*sin(theta*j)*sin_phi_i
            Z = Radius*cos(phi*i)
            pts_u.append([X, Y, Z])
        pts.append(pts_u)

    points_top = [[0, 0, -Radius] for i in range(U)]
    pts.append(points_top)
    return pts


# @jit(cache=True)
def sphere_verts(U, V, Radius, Separate):
    if Separate:
        return make_sphere_verts_separate(U, V, Radius)
    else:
        return make_sphere_verts_combined(U, V, Radius)

# @njit(cache=True)
def sphere_edges(U, V):

    N1 = U # X
    N2 = V # Y
    steps = np.arange(N1*(N2-2) ) + 1  # skip first verts at [0,0,Radius] and finish before [0,0,-Radius]
    

    arr_verts = np.array ( np.split(steps, (N2-2) ) )  # split array vertically
    arr_verts = np.hstack( (arr_verts, np.array([arr_verts[:,0]]).T ) ) # append first row to bottom to horizontal circle

    _arr_h_edges = np.zeros((N2-2, N1, 2), 'i' )
    _arr_h_edges[:, :, 0] = arr_verts[ : ,  :-1 ]  # hor_edges
    _arr_h_edges[:, :, 1] = arr_verts[ : , 1:   ]  # hor_edges
    _arr_h_edges = _arr_h_edges.reshape(-1,2)

    _arr_v_edges = np.zeros((N2-2-1, N1, 2), 'i' )  # -1: vert edges except top and bottom point and less than 1 than exists vertcal points
    _arr_v_edges[:, :, 0] = arr_verts[ :-1, :-1]  # hor_edges
    _arr_v_edges[:, :, 1] = arr_verts[1:  , :-1]  # hor_edges
    _arr_v_edges = _arr_v_edges.reshape(-1,2)

    _edges = np.concatenate( 
        (
         _arr_h_edges,
         _arr_v_edges,
         np.dstack( ( arr_verts[0:1, :-1]-arr_verts[0:1, :-1]              , arr_verts[ 0: 1, :-1]) ).reshape(-1,2), # self subtract to get  array of 0 appropriate length
         np.dstack( ( arr_verts[0:1, :-1]-arr_verts[0:1, :-1] + N1*(N2-2)+1, arr_verts[-1:  , :-1]) ).reshape(-1,2),
        ) )
    _list_edges = _edges.tolist()
    return _list_edges

# @njit(cache=True)
def sphere_faces(U, V):

    N1 = U # X
    N2 = V # Y
    steps     = np.arange(N1*(N2-2) ) + 1  # skip first verts at [0,0,Radius] and finish before [0,0,-Radius]
    _arr_middle_verts = np.array ( np.split(steps, (N2-2) ) )  # split array vertically
    _arr_middle_verts = np.hstack( (_arr_middle_verts, np.array([_arr_middle_verts[:,0]]).T ) ) # append first row to bottom to horizontal circle

    _arr_middle_faces          = np.zeros((N2-3, N1, 4), 'i' )
    _arr_middle_faces[:, :, 0] = _arr_middle_verts[1:  ,  :-1 ]
    _arr_middle_faces[:, :, 1] = _arr_middle_verts[1:  , 1:   ]
    _arr_middle_faces[:, :, 2] = _arr_middle_verts[ :-1, 1:   ]
    _arr_middle_faces[:, :, 3] = _arr_middle_verts[ :-1,  :-1 ]
    _arr_middle_faces          = _arr_middle_faces.reshape(-1,4)

    _arr_faces_top_bottom = np.concatenate(
        (
            np.dstack( (                                                          _arr_middle_verts[  0:1, :-1], _arr_middle_verts[  :1, 1:  ], np.zeros_like(_arr_middle_verts[0,:-1]) + 0) ).reshape(-1,3),  # top triangled faces
            np.dstack( (  np.zeros_like(_arr_middle_verts[-1,:-1]) + N1*(N2-2)+1, _arr_middle_verts[ -1: ,1:  ], _arr_middle_verts[ -1:,  :-1]) ).reshape(-1,3), # bottom triangled faces
        )
    )
    _arr_faces_top_bottom = _arr_faces_top_bottom.reshape(-1,3)
    _arr_faces_top_bottom = _arr_faces_top_bottom.tolist()
    _list_faces = _arr_middle_faces.tolist()
    _list_faces.extend( _arr_faces_top_bottom )
    return _list_faces

class SphereNode(SverchCustomTreeNode, bpy.types.Node):
    '''UV Sphere. [default]
    Radius: [1.0]
    U, min 3: [24]
    V, min 3: [24]
    '''
    bl_idname = 'SphereNode'
    bl_label = 'Sphere'
    bl_icon = 'MESH_UVSPHERE'

    replacement_nodes = [('SvIcosphereNode', None, dict(Polygons='Faces'))]

    rad_: FloatProperty(name='Radius', description='Radius',
                         default=1.0,
                         options={'ANIMATABLE'}, update=updateNode)
    U_: IntProperty(name='U', description='U',
                     default=24, min=3,
                     options={'ANIMATABLE'}, update=updateNode)
    V_: IntProperty(name='V', description='V',
                     default=24, min=3,
                     options={'ANIMATABLE'}, update=updateNode)

    Separate: BoolProperty(name='Separate', description='Separate UV coords',
                            default=False,
                            update=updateNode)
    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths, object level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'rad_'
        self.inputs.new('SvStringsSocket', "U").prop_name = 'U_'
        self.inputs.new('SvStringsSocket', "V").prop_name = 'V_'

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polygons")

    def draw_buttons(self, context, layout):
        layout.prop(self, "Separate", text="Separate")
        
    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "Separate", text="Separate")
        layout.prop(self, "list_match")

    def process(self):
        # inputs
        if 'Polygons' not in self.outputs:
            return

        Radius = self.inputs['Radius'].sv_get()[0]
        U = [max(int(u), 3) for u in self.inputs['U'].sv_get()[0]]
        V = [max(int(v), 3) for v in self.inputs['V'].sv_get()[0]]

        params = list_match_func[self.list_match]([U, V, Radius])

        # outputs
        if self.outputs['Vertices'].is_linked:
            verts = [sphere_verts(u, v, r, self.Separate) for u, v, r in zip(*params)]
            self.outputs['Vertices'].sv_set(verts)

        if self.outputs['Edges'].is_linked:
            edges = [sphere_edges(u, v) for u, v, r in zip(*params)]
            self.outputs['Edges'].sv_set(edges)

        if self.outputs['Polygons'].is_linked:
            faces = [sphere_faces(u, v) for u, v, r in zip(*params)]
            self.outputs['Polygons'].sv_set(faces)


def register():
    bpy.utils.register_class(SphereNode)


def unregister():
    bpy.utils.unregister_class(SphereNode)
