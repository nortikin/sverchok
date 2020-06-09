import bpy
import ast
from bpy.props import StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.modules.geom_sorcar import make_sorcar_logo

class SvReceiveFromSorcarNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: sorcar sc receive
    Tooltip: Receive Mesh Data From Sorcar
    
    A dedicated node to output components (vert/edge/face) and their selection mask, set externally by Sorcar node.
    """
    bl_idname = 'SvReceiveFromSorcarNode'
    bl_label = 'Receive From Sorcar'
    sv_icon = 'SV_RECEIVE_FROM_SORCAR'


    # Get default mesh data (Sorcar logo)
    sc_v, sc_e, sc_f = make_sorcar_logo()

    # Get selection mask for each component (all True by default)
    sv_v_mask = [[True]*len(sc_v)]
    sv_e_mask = [[True]*len(sc_e)]
    sv_f_mask = [[True]*len(sc_f)]


    # Node properties to hold mesh data internally (to prevent fetching data from Sorcar node at every evaluation)
    verts: StringProperty(name='Vertices', description='list of locations (vector of 3 floats) of each vertex',
                         default=repr([sc_v]))
    edges: StringProperty(name='Edges', description='list of pair of vertices (edge-keys) for each edge',
                         default=repr([sc_e]))
    faces: StringProperty(name='Faces', description='list of polygons (faces) made by a list of vertex indices',
                         default=repr([sc_f]))

    verts_mask: StringProperty(name='Vertices Mask', description='list of bool corresponding to vertex selection',
                         default=repr(sv_v_mask))
    edges_mask: StringProperty(name='Edges Mask', description='list of bool corresponding to edge selection',
                         default=repr(sv_e_mask))
    faces_mask: StringProperty(name='Faces Mask', description='list of bool corresponding to face selection',
                         default=repr(sv_f_mask))
    

    # Helper function to set mesh data and update node-tree only once
    def set_mesh(self, verts, edges, faces, verts_mask, edges_mask, faces_mask):
        self.verts = verts
        self.edges = edges
        self.faces = faces

        self.verts_mask = verts_mask
        self.edges_mask = edges_mask
        self.faces_mask = faces_mask

        updateNode(self, None)
    

    def sv_init(self, context):
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polygons")

        self.outputs.new('SvStringsSocket', "VerticesMask")
        self.outputs.new('SvStringsSocket', "EdgesMask")
        self.outputs.new('SvStringsSocket', "PolygonsMask")


    def process(self):
        if self.outputs['Vertices'].is_linked:
            self.outputs['Vertices'].sv_set(ast.literal_eval(self.verts))
        if self.outputs['Edges'].is_linked:
            self.outputs['Edges'].sv_set(ast.literal_eval(self.edges))
        if self.outputs['Polygons'].is_linked:
            self.outputs['Polygons'].sv_set(ast.literal_eval(self.faces))
        
        if self.outputs['VerticesMask'].is_linked:
            self.outputs['VerticesMask'].sv_set(ast.literal_eval(self.verts_mask))
        if self.outputs['EdgesMask'].is_linked:
            self.outputs['EdgesMask'].sv_set(ast.literal_eval(self.edges_mask))
        if self.outputs['PolygonsMask'].is_linked:
            self.outputs['PolygonsMask'].sv_set(ast.literal_eval(self.faces_mask))


def register():
    bpy.utils.register_class(SvReceiveFromSorcarNode)


def unregister():
    bpy.utils.unregister_class(SvReceiveFromSorcarNode)
