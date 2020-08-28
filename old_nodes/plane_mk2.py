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
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList, match_long_repeat
from sverchok.utils.nodes_mixins.draft_mode import DraftMode

directionItems = [("XY", "XY", ""), ("YZ", "YZ", ""), ("ZX", "ZX", "")]


def make_plane(stepsx, stepsy, center, direction, separate):
    if direction == "XY":
        v = lambda l, k: (l, k, 0.0)
    elif direction == "YZ":
        v = lambda l, k: (0.0, l, k)
    elif direction == "ZX":
        v = lambda l, k: (k, 0.0, l)
    cx = -sum(stepsx) / 2 if center else 0
    verts = []
    y = -sum(stepsy) / 2 if center else 0
    for sy in [0.0] + stepsy:
        y = y + sy
        x = cx
        vertList = []
        for sx in [0.0] + stepsx:
            x = x + sx
            vertList.append(v(x, y))
        if separate:
            verts.append(vertList)
        else:
            verts.extend(vertList)
    edges = []
    nx = len(stepsx) + 1  # number of vertices along X
    ny = len(stepsy) + 1  # number of vertices along Y
    if separate:  # edges along X
        edges = [[[i, i + 1] for i in range(nx - 1)]] * ny
    else:
        ex = [[i + j * nx, i + 1 + j * nx] for j in range(ny) for i in range(nx - 1)]
        ey = [[i + j * nx, i + (j + 1) * nx] for i in range(nx) for j in range(ny - 1)]
        edges.extend(ex)  # edges along X
        edges.extend(ey)  # edges along Y
    if separate:
        polys = []  # why this? can we separate polygons instead ?
    else:
        polys = [[i + j * nx, i + j * nx + 1, i + (j + 1) * nx + 1, i + (j + 1) * nx]
                 for i in range(nx - 1) for j in range(ny - 1)]
    return verts, edges, polys


class SvPlaneNodeMK2(DraftMode, bpy.types.Node, SverchCustomTreeNode):
    ''' Plane MK2 '''
    bl_idname = 'SvPlaneNodeMK2'
    bl_label = 'Plane MK2'
    bl_icon = 'MESH_PLANE'

    replacement_nodes = [('SvPlaneNodeMk3', None, None)]

    def update_size_link(self, context):
        self.sizeRatio = self.sizex / self.sizey

    def update_size(self, context, sizeID):
        if self.syncing:
            return
        if self.linkSizes:
            self.syncing = True
            if sizeID == "X":  # updating X => sync Y
                self.sizey = self.sizex / self.sizeRatio
            else:  # updating Y => sync X
                self.sizex = self.sizey * self.sizeRatio
            self.syncing = False
        updateNode(self, context)

    def update_sizex(self, context):
        self.update_size(context, "X")

    def update_sizey(self, context):
        self.update_size(context, "Y")

    direction: EnumProperty(
        name="Direction", items=directionItems,
        default="XY", update=updateNode)

    numx: IntProperty(
        name='N Verts X', description='Number of vertices along X',
        default=2, min=2, update=updateNode)

    numy: IntProperty(
        name='N Verts Y', description='Number of vertices along Y',
        default=2, min=2, update=updateNode)

    numx_draft: IntProperty(
        name='[D] N Verts X', description='Number of vertices along X (draft mode)',
        default=2, min=2, update=updateNode)

    numy_draft: IntProperty(
        name='[D] N Verts Y', description='Number of vertices along Y (draft mode)',
        default=2, min=2, update=updateNode)

    stepx: FloatProperty(
        name='Step X', description='Step length X',
        default=1.0, update=updateNode)

    stepy: FloatProperty(
        name='Step Y', description='Step length Y',
        default=1.0, update=updateNode)

    stepx_draft: FloatProperty(
        name='[D] Step X', description='Step length X (draft mode)',
        default=1.0, update=updateNode)

    stepy_draft: FloatProperty(
        name='[D] Step Y', description='Step length Y (draft mode)',
        default=1.0, update=updateNode)

    separate: BoolProperty(
        name='Separate', description='Separate UV coords',
        default=False, update=updateNode)

    center: BoolProperty(
        name='Center', description='Center the plane around origin',
        default=False, update=updateNode)

    normalize: BoolProperty(
        name='Normalize', description='Normalize the plane sizes',
        default=False, update=updateNode)

    sizex: FloatProperty(
        name='Size X', description='Plane size along X',
        default=10.0, min=0.01, update=update_sizex)

    sizey: FloatProperty(
        name='Size Y', description='Plane size along Y',
        default=10.0, min=0.01, update=update_sizey)

    sizeRatio: FloatProperty(
        name="Size Ratio", default=1.0)

    linkSizes: BoolProperty(
        name='Link', description='Link the normalize sizes',
        default=False, update=update_size_link)

    syncing: BoolProperty(
        name='Syncing', description='Syncing flag', default=False)

    draft_properties_mapping = dict(
            numx = 'numx_draft',
            numy = 'numy_draft',
            stepx = 'stepx_draft',
            stepy = 'stepy_draft'
        )

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Num X").prop_name = 'numx'
        self.inputs.new('SvStringsSocket', "Num Y").prop_name = 'numy'
        self.inputs.new('SvStringsSocket', "Step X").prop_name = 'stepx'
        self.inputs.new('SvStringsSocket', "Step Y").prop_name = 'stepy'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polygons")

    def draw_buttons(self, context, layout):
        layout.prop(self, "separate")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "direction", expand=True)
        row = col.row(align=True)
        row.prop(self, "center", toggle=True)
        row.prop(self, "normalize", toggle=True)
        if self.normalize:
            row = col.row(align=True)
            row.prop(self, "sizex")
            if self.linkSizes:
                row.prop(self, "linkSizes", icon="LINKED", text="")
            else:
                row.prop(self, "linkSizes", icon="UNLINKED", text="")
            row.prop(self, "sizey")

    def draw_label(self):
        label = self.label or self.name
        if self.id_data.sv_draft:
            label = "[D] " + label
        return label

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return
        inputs = self.inputs
        outputs = self.outputs
        input_numx = inputs["Num X"].sv_get()
        input_numy = inputs["Num Y"].sv_get()
        input_stepx = inputs["Step X"].sv_get()
        input_stepy = inputs["Step Y"].sv_get()
        params = match_long_repeat([input_numx, input_numy, input_stepx, input_stepy])
        verts, edges, polys, stex, stey = [],[],[],[],[]
        c, d, s = self.center, self.direction, self.separate
        for nx, ny, sx, sy in zip(*params):
            for nxn, nyn in zip(nx,ny):
                numx, numy = [max(2, nxn), max(2, nyn)]  # sanitize the input
                stepsx, stepsy = [sx[:(numx - 1)], sy[:(numy - 1)]]  # shorten if needed
                fullList(stepsx, numx - 1)  # extend if needed
                fullList(stepsy, numy - 1)
                if self.normalize:
                    sizex, sizey = [self.sizex / sum(stepsx), self.sizey / sum(stepsy)]
                    stex.append([sx * sizex for sx in stepsx])
                    stey.append([sy * sizey for sy in stepsy])
                else:
                    stex.append(stepsx)
                    stey.append(stepsy)
        for sx, sy in zip(stex, stey):
            V,E,P = make_plane(sx, sy, c, d, s)
            verts.append(V)
            edges.append(E)
            polys.append(P)
        if outputs['Vertices'].is_linked:
            outputs['Vertices'].sv_set(verts)
        if outputs['Edges'].is_linked:
            outputs['Edges'].sv_set(edges)
        if outputs['Polygons'].is_linked:
            outputs['Polygons'].sv_set(polys)

    def does_support_draft_mode(self):
        return True

def register():
    bpy.utils.register_class(SvPlaneNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvPlaneNodeMK2)
