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
from bpy.props import (
    BoolProperty, StringProperty, IntProperty,
    FloatProperty, FloatVectorProperty)

from mathutils import Matrix

from node_tree import (
    SvColors, SverchCustomTreeNode,
    StringsSocket, VerticesSocket, MatrixSocket)

from data_structure import (
    cache_viewer_baker, node_id, updateNode, dataCorrect,
    Vector_generate, Matrix_generate, SvGetSocketAnyType)

from utils.viewer_draw_mk2 import callback_disable, callback_enable
# from nodes.basic_view.viewer import SvObjBake


class SvObjBakeMK2(bpy.types.Operator):
    """ B A K E   OBJECTS """
    bl_idname = "node.sverchok_mesh_baker_mk2"
    bl_label = "Sverchok mesh baker mk2"
    bl_options = {'REGISTER', 'UNDO'}

    idname = StringProperty(
        name='idname',
        description='name of parent node',
        default='')

    idtree = StringProperty(
        name='idtree',
        description='name of parent tree',
        default='')

    def execute(self, context):
        global cache_viewer_baker

        node_group = bpy.data.node_groups[self.idtree]
        node = node_group.nodes[self.idname]
        nid = node_id(node)

        matrix_cache = cache_viewer_baker[nid+'m']
        vertex_cache = cache_viewer_baker[nid+'v']
        edgpol_cache = cache_viewer_baker[nid+'ep']

        if matrix_cache and not vertex_cache:
            return {'CANCELLED'}

        v = dataCorrect(vertex_cache)
        e = self.dataCorrect3(edgpol_cache)
        m = self.dataCorrect2(matrix_cache, v)
        self.makeobjects(v, e, m)
        return {'FINISHED'}

    def dataCorrect2(self, destination, obj):
        if destination:
            return dataCorrect(destination)
        return [Matrix() for v in obj]

    def dataCorrect3(self, destination, fallback=[]):
        if destination:
            return dataCorrect(destination)
        return fallback

    def makeobjects(self, vers, edg_pol, mats):
        try:
            num_keys = len(edg_pol[0][0])
        except:
            num_keys = 0

        vertices = Vector_generate(vers)
        matrixes = Matrix_generate(mats)
        edgs, pols, max_vert_index, fht = [], [], [], []

        if num_keys >= 2:
            for k in edg_pol:
                maxi = max(max(a) for a in k)
                fht.append(maxi)

        for u, f in enumerate(fht):
            max_vert_index.append(min(len(vertices[u]), fht[u]))

        objects = {}
        for i, m in enumerate(matrixes):
            k = i
            lenver = len(vertices) - 1
            if i > lenver:
                v = vertices[-1]
                k = lenver
            else:
                v = vertices[k]

            if max_vert_index:
                if (len(v)-1) < max_vert_index[k]:
                    continue

                elif max_vert_index[k] < (len(v)-1):
                    nonneed = (len(v)-1) - max_vert_index[k]
                    for q in range(nonneed):
                        v.pop((max_vert_index[k]+1))

            e, p = [], []
            if num_keys == 2:
                e = edg_pol[k]
            elif num_keys > 2:
                p = edg_pol[k]

            objects[str(i)] = self.makemesh(i, v, e, p, m)

        for ob, me in objects.values():
            calcedg = False if (num_keys == 2) else True
            me.update(calc_edges=calcedg)
            bpy.context.scene.objects.link(ob)

    def makemesh(self, i, v, e, p, m):
        name = 'Sv_' + str(i)
        me = bpy.data.meshes.new(name)
        me.from_pydata(v, e, p)
        ob = bpy.data.objects.new(name, me)
        ob.matrix_world = m
        ob.show_name = False
        ob.hide_select = False
        return ob, me


class ViewerNode2(bpy.types.Node, SverchCustomTreeNode):
    ''' ViewerNode2 '''
    bl_idname = 'ViewerNode2'
    bl_label = 'Viewer Draw2'
    bl_icon = 'OUTLINER_OB_EMPTY'

    n_id = StringProperty(default='', options={'SKIP_SAVE'})

    activate = BoolProperty(
        name='Show', description='Activate',
        default=1, update=updateNode)

    transparant = BoolProperty(
        name='Transparant', description='transparant',
        default=0, update=updateNode)

    shading = BoolProperty(
        name='Shading', description='shade or flat',
        default=0, update=updateNode)

    light_direction = FloatVectorProperty(
        name='light_direction', subtype='DIRECTION', min=0, max=1, size=3,
        default=(0.2, 0.6, 0.4), update=updateNode)

    # geometry colors
    vertex_colors = FloatVectorProperty(
        name='vertex_colors', subtype='COLOR', min=0, max=1, size=3,
        default=(0.938, 0.948, 0.900), update=updateNode)

    edge_colors = FloatVectorProperty(
        name='edge_colors', subtype='COLOR', min=0, max=1, size=3,
        default=(0.5, 0.752, 0.899), update=updateNode)

    face_colors = FloatVectorProperty(
        name='face_colors', subtype='COLOR', min=0, max=1, size=3,
        default=(0.0301, 0.488, 0.899), update=updateNode)

    # display toggles
    display_verts = BoolProperty(
        name="Vertices", description="Display vertices",
        default=True,
        update=updateNode)

    display_edges = BoolProperty(
        name="Edges", description="Display edges",
        update=updateNode)

    display_faces = BoolProperty(
        name="Faces", description="Display faces",
        update=updateNode)

    vertex_size = FloatProperty(
        min=0.0, max=10.0, default=3.2, step=0.2, name='vertex_size',
        update=updateNode)

    edge_width = IntProperty(
        min=1, max=10, default=2, step=1, name='edge_width',
        update=updateNode)

    # misc options
    ngon_tessellate = BoolProperty(
        default=0, name='ngon_tessellate',
        description='useful for concave ngons, forces ngons to be tessellated',
        update=updateNode)

    bakebuttonshow = BoolProperty(
        name='bakebuttonshow', description='show bake button on node',
        default=False,
        update=updateNode)

    callback_timings = BoolProperty(
        name='timings', description='print timings for callback',
        default=False,
        update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edg_pol', 'edg_pol')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')
        self.use_custom_color = True

    def draw_main_ui_elements(self, context, layout):
        view_icon = 'RESTRICT_VIEW_' + ('OFF' if self.activate else 'ON')
        trans_icon = 'WIRE' if self.transparant else 'SOLID'
        shade_icon = 'LAMP_SPOT' if self.shading else 'BLANK1'

        row = layout.row(align=True)
        split = row.split()
        r = split.column()
        r.prop(self, "activate", text="Show", toggle=True, icon=view_icon)

        r = split.column()
        r.active = self.activate
        row = r.row()
        row.prop(self, "transparant", toggle=True, icon=trans_icon, icon_only=True, expand=True)
        row.prop(self, "shading", toggle=True, icon=shade_icon, icon_only=True, expand=True)

        row = layout.row(align=True)
        row.active = self.activate
        row.prop(self, "display_verts", toggle=True, icon='VERTEXSEL', text='')
        row.prop(self, "vertex_colors", text="")

        row = layout.row(align=True)
        row.active = self.activate
        row.prop(self, "display_edges", toggle=True, icon='EDGESEL', text='')
        row.prop(self, "edge_colors", text="")

        row = layout.row(align=True)
        row.active = self.activate
        row.prop(self, "display_faces", toggle=True, icon='FACESEL', text='')
        row.prop(self, "face_colors", text="")

    def draw_buttons(self, context, layout):
        self.draw_main_ui_elements(context, layout)

        if self.bakebuttonshow:
            row = layout.row()
            row.scale_y = 4.0
            opera = row.operator('node.sverchok_mesh_baker_mk2', text='B A K E')
            opera.idname = self.name
            opera.idtree = self.id_data.name

    def draw_buttons_ext(self, context, layout):

        col = layout.column(align=True)
        col.prop(self, 'vertex_size', text='vertex size')
        col.prop(self, 'edge_width', text='edge width')
        col.prop(self, 'ngon_tessellate', text='ngons tessellation', toggle=True)

        col.separator()

        col.label('Light Direction')
        col.prop(self, 'light_direction', text='')

        col.separator()

        layout.prop(self, 'bakebuttonshow', text='show bake button')

        layout.prop(self, 'callback_timings')
        self.draw_main_ui_elements(context, layout)

    # reset n_id on duplicate (shift-d)
    def copy(self, node):
        self.n_id = ''

    def update(self):
        if 'matrix' not in self.inputs:
            return

        if not (self.id_data.sv_show and self.activate):
            callback_disable(node_id(self))
            return

        self.process()

    def process(self):
        n_id = node_id(self)

        global cache_viewer_baker
        vertex_ref = n_id + 'v'
        poledg_ref = n_id + 'ep'
        matrix_ref = n_id + 'm'
        cache_viewer_baker[vertex_ref] = []
        cache_viewer_baker[poledg_ref] = []
        cache_viewer_baker[matrix_ref] = []

        callback_disable(n_id)

        # every time you hit a dot, you pay a price, so alias and benefit
        inputs = self.inputs
        vertex_links = inputs['vertices'].links
        matrix_links = inputs['matrix'].links
        edgepol_links = inputs['edg_pol'].links

        if (vertex_links or matrix_links):

            if vertex_links:
                if isinstance(vertex_links[0].from_socket, VerticesSocket):
                    propv = inputs['vertices'].sv_get()
                    if propv:
                        cache_viewer_baker[vertex_ref] = dataCorrect(propv)

            if edgepol_links:
                if isinstance(edgepol_links[0].from_socket, StringsSocket):
                    prope = inputs['edg_pol'].sv_get()
                    if prope:
                        cache_viewer_baker[poledg_ref] = dataCorrect(prope)

            if matrix_links:
                if isinstance(matrix_links[0].from_socket, MatrixSocket):
                    propm = inputs['matrix'].sv_get()
                    if propm:
                        cache_viewer_baker[matrix_ref] = dataCorrect(propm)

        if cache_viewer_baker[vertex_ref] or cache_viewer_baker[matrix_ref]:
            config_options = self.get_options().copy()
            callback_enable(n_id, cache_viewer_baker, config_options)
            self.color = (1, 1, 1)
        else:
            self.color = (0.7, 0.7, 0.7)

    def get_options(self):
        return {
            'draw_list': 0,
            'show_verts': self.display_verts,
            'show_edges': self.display_edges,
            'show_faces': self.display_faces,
            'transparent': self.transparant,
            'shading': self.shading,
            'light_direction': self.light_direction,
            'vertex_colors': self.vertex_colors,
            'face_colors': self.face_colors,
            'edge_colors': self.edge_colors,
            'vertex_size': self.vertex_size,
            'edge_width': self.edge_width,
            'forced_tessellation': self.ngon_tessellate,
            'timings': self.callback_timings
            }

    def update_socket(self, context):
        self.update()

    def free(self):
        global cache_viewer_baker
        n_id = node_id(self)
        callback_disable(n_id)
        cache_viewer_baker.pop(n_id+'v', None)
        cache_viewer_baker.pop(n_id+'ep', None)
        cache_viewer_baker.pop(n_id+'m', None)

    def bake(self):
        if self.activate and self.inputs['edg_pol'].is_linked:
            bake = bpy.ops.node.sverchok_mesh_baker_mk2
            bake(idname=self.name, idtree=self.id_data.name)


def register():
    bpy.utils.register_class(ViewerNode2)
    bpy.utils.register_class(SvObjBakeMK2)


def unregister():
    bpy.utils.unregister_class(ViewerNode2)
    bpy.utils.unregister_class(SvObjBakeMK2)


if __name__ == '__main__':
    register()
