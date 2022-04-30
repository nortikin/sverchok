# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import bmesh
import mathutils


from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

class SvTriangleFillScanline(bpy.types.Node, SverchCustomTreeNode):
    
    """
    Triggers: triangle fill scanline
    Tooltip: 
    
    Similar to the edges to faces node, with the exception that 
    - do your masking in a different node!
    - it uses bmesh.ops.triangle_fill instead (which is used in the Curve object 2D mode)
    - has option to mask edges and join input mesh before execution
    - https://docs.blender.org/api/current/bmesh.ops.html?highlight=triangle_fill#bmesh.ops.triangle_fill
    """

    bl_idname = 'SvTriangleFillScanline'
    bl_label = 'Triangle Fill Lite'
    bl_icon = 'MESH_GRID'
    sv_icon = 'SV_PLANAR_EDGES_TO_POLY'

    # replace node : SvEdgesToFace2D

    merge_incoming: bpy.props.BoolProperty(name="merge incoming", default=True, update=updateNode,
        description="enabled, this mode will merge the incoming verts+edges into a single Mesh")
    use_dissolve: bpy.props.BoolProperty(name="use dissolve", default=False, update=updateNode,
        description="dissolve resulting faces")
    use_beauty: bpy.props.BoolProperty(name="use beauty", default=False, update=updateNode,
        description="use best triangulation division")


    def sv_init(self, context):
        self.inputs.new("SvVerticesSocket", "Verts")
        self.inputs.new("SvStringsSocket", "Edges")
        self.outputs.new("SvVerticesSocket", "Verts")
        self.outputs.new("SvStringsSocket", "Edges")
        self.outputs.new("SvStringsSocket", "Polygons")

    def draw_buttons(self, context, layout):
        layout.prop(self, "merge_incoming")

    def process(self):
        if not self.inputs["Verts"].is_linked: return

        bool_parameters = dict(use_beauty=self.use_beauty, use_dissolve=self.use_dissolve)
        def _get(name): return self.inputs[name].sv_get()
        def _set_multiple_sockets(data): _ = [self.outputs[i].sv_set(data[i]) for i in range(3)]

        def perform_ops(verts, edges):
            bm = bmesh_from_pydata(verts, edges, [])
            bmesh.ops.triangle_fill(bm, **(bool_parameters | dict(edges=bm.edges[:])))   # pass normal?
            return pydata_from_bmesh(bm)            
        
        if not self.inputs["Edges"].is_linked:
            '''
            - generate edges, each separate set of verts will be considered as a closed ring
            - hide merge, verts will be merged anyway
            '''
            vert_list = []
            edge_list = []

        else:
            VERTS_IN = self.inputs["Verts"].sv_get()
            EDGES_IN = self.inputs["Edges"].sv_get()

            if self.merge_incoming:
                
                if len(VERTS_IN) == 1:
                    verts, edges = VERTS_IN[0], EDGES_IN[0]
                elif len(VERTS_IN) > 1:
                    verts, edges, _ = mesh_join(VERTS_IN, EDGES_IN, [])
                
                out = perform_ops(verts, edges)
                _set_multiple_sockets(([out[0]], [out[1]], [out[2]]))
            else:
                out = [perform_ops(*geom) for geom in zip(VERTS_IN, EDGES_IN)]
                _set_multiple_sockets(zip(*out))

        


classes = [SvTriangleFillScanline]
register, unregister = bpy.utils.register_classes_factory(classes)
