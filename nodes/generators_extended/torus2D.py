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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from math import sin, cos, pi

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat


def torus_verts(R, r, N1, N2, p, Separate):
    '''
        R   : major radius
        r   : minor radius
        N1  : major sections - number of RADIAL sections
        N2  : minor sections - number of CIRCULAR sections
        p   : radial section phase
    '''
    listVerts = []

    # angle increments (cached outside of the loop for performance)
    da = 2*pi/N1

    for n1 in range(N1):
        theta = n1 * da + p     # radial section angle
        sin_theta = sin(theta)  # caching
        cos_theta = cos(theta)  # caching

        loopVerts = []
        s = 2 / (N2-1)  # caching
        for n2 in range(N2):
            rr = R + (n2*s - 1) * r
            x = rr * cos_theta
            y = rr * sin_theta

            # append vertex to loop
            loopVerts.append([x, y, 0.0])

        if Separate:
            listVerts.append(loopVerts)
        else:
            listVerts.extend(loopVerts)

    return listVerts


def torus_edges(N1, N2):
    '''
        N1 : major sections - number of RADIAL sections
        N2 : minor sections - number of CIRCULAR sections
    '''
    listEdges = []

    # radial EDGES
    for n1 in range(N1):
        for n2 in range(N2-1):
            listEdges.append([N2*n1 + n2, N2*n1 + n2+1])

    # circular EDGES
    for n1 in range(N1-1):
        for n2 in range(N2):
            listEdges.append([N2*n1 + n2, N2*(n1+1) + n2])
    for n2 in range(N2):
        listEdges.append([N2*(N1-1) + n2, N2*0 + n2])

    return listEdges


def torus_polygons(N1, N2):
    '''
        N1 : major sections - number of RADIAL sections
        N2 : minor sections - number of CIRCULAR sections
    '''
    listPolys = []
    for n1 in range(N1-1):
        for n2 in range(N2-1):
            listPolys.append(
                [N2*n1 + n2, N2*(n1+1) + n2, N2*(n1+1) + n2+1, N2*n1 + n2+1])

    for n2 in range(N2-1):
        listPolys.append([N2*(N1-1) + n2, N2*0 + n2, N2*0 + n2+1, N2*(N1-1) + n2+1])
    listPolys.append([N2*(N1-1) + N2-1, N2*0 + N2-1, N2*0 + 0, N2*(N1-1) + 0])

    return listPolys


class SvTorus2DNode(bpy.types.Node, SverchCustomTreeNode):

    ''' Torus 2D '''
    bl_idname = 'SvTorus2DNode'
    bl_label = 'Torus 2D'
    bl_icon = 'PROP_CON'

    def update_mode(self, context):
        # switch radii input sockets (R,r) <=> (eR,iR)
        if self.mode == 'EXT_INT':
            self.inputs['R'].prop_name = "torus_eR"
            self.inputs['r'].prop_name = "torus_iR"
        else:
            self.inputs['R'].prop_name = "torus_R"
            self.inputs['r'].prop_name = "torus_r"
        updateNode(self, context)

    # keep the equivalent radii pair in sync (eR,iR) => (R,r)
    def external_internal_radii_changed(self, context):
        if self.mode == "EXT_INT":
            self.torus_R = (self.torus_eR + self.torus_iR)*0.5
            self.torus_r = (self.torus_eR - self.torus_iR)*0.5
            updateNode(self, context)

    # keep the equivalent radii pair in sync (R,r) => (eR,iR)
    def major_minor_radii_changed(self, context):
        if self.mode == "MAJOR_MINOR":
            self.torus_eR = self.torus_R + self.torus_r
            self.torus_iR = self.torus_R - self.torus_r
            updateNode(self, context)

    # TORUS DIMENSIONS options
    mode = EnumProperty(
        name="Torus Dimensions",
        items=(("MAJOR_MINOR", "Major/Minor",
                "Use the Major/Minor radii for torus dimensions."),
               ("EXT_INT", "Exterior/Interior",
                "Use the Exterior/Interior radii for torus dimensions.")),
        update=update_mode)

    torus_R = FloatProperty(
        name="Major Radius",
        description="Radius from the torus origin to the center of the cross section",
        default=1.0, min=0.00, max=100.0,
        update=major_minor_radii_changed)

    torus_r = FloatProperty(
        name="Minor Radius",
        description="Radius of the torus' cross section",
        default=.25, min=0.00, max=100.0,
        update=major_minor_radii_changed)

    torus_iR = FloatProperty(
        name="Interior Radius",
        description="Interior radius of the torus (closest to the torus center)",
        default=.75, min=0.00, max=100.0,
        update=external_internal_radii_changed)

    torus_eR = FloatProperty(
        name="Exterior Radius",
        description="Exterior radius of the torus (farthest from the torus center)",
        default=1.25, min=0.00, max=100.0,
        update=external_internal_radii_changed)

    # TORUS RESOLUTION options
    torus_n1 = IntProperty(
        name="Radial Sections", description="Number of radial sections",
        default=32, min=3, soft_min=3,
        update=updateNode)

    torus_n2 = IntProperty(
        name="Circular Sections", description="Number of circular sections",
        default=3, min=2, soft_min=2,
        update=updateNode)

    # TORUS Phase Options
    torus_rP = FloatProperty(
        name="Phase", description="Phase of the radial sections (in radians)",
        default=0.0, min=0.0, soft_min=0.0,
        update=updateNode)

    # OTHER options
    Separate = BoolProperty(
        name='Separate', description='Separate UV coords',
        default=False,
        update=updateNode)

    def sv_init(self, context):
        self.width = 180
        self.inputs.new('StringsSocket', "R").prop_name = 'torus_R'
        self.inputs.new('StringsSocket', "r").prop_name = 'torus_r'
        self.inputs.new('StringsSocket', "n1").prop_name = 'torus_n1'
        self.inputs.new('StringsSocket', "n2").prop_name = 'torus_n2'
        self.inputs.new('StringsSocket', "rP").prop_name = 'torus_rP'

        self.outputs.new('VerticesSocket', "Vertices")
        self.outputs.new('StringsSocket',  "Edges")
        self.outputs.new('StringsSocket',  "Polygons")

    def draw_buttons(self, context, layout):
        layout.prop(self, "Separate", text="Separate")
        layout.prop(self, 'mode', expand=True)

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # input values lists (single or multi value)
        # list of MAJOR or EXTERIOR radii
        input_RR = self.inputs["R"].sv_get()[0]
        # list of MINOR or INTERIOR radii
        input_rr = self.inputs["r"].sv_get()[0]
        # list of number of MAJOR sections : RADIAL
        input_n1 = self.inputs["n1"].sv_get()[0]
        # list of number of MINOR sections : CIRCULAR
        input_n2 = self.inputs["n2"].sv_get()[0]
        # list of RADIAL phases
        input_rp = self.inputs["rP"].sv_get()[0]

        # sanitize the input values
        input_RR = list(map(lambda x: max(0, x), input_RR))
        input_rr = list(map(lambda x: max(0, x), input_rr))
        input_n1 = list(map(lambda x: max(3, int(x)), input_n1))
        input_n2 = list(map(lambda x: max(2, int(x)), input_n2))

        # convert input radii values to MAJOR/MINOR, based on selected mode
        if self.mode == 'EXT_INT':
            # convert radii from EXTERIOR/INTERIOR to MAJOR/MINOR
            # (extend radii lists to a matching length before conversion)
            input_RR, input_rr = match_long_repeat([input_RR, input_rr])
            input_R = list(map(lambda x, y: (x+y)*0.5, input_RR, input_rr))
            input_r = list(map(lambda x, y: (x-y)*0.5, input_RR, input_rr))
        else:  # values already given as MAJOR/MINOR radii
            input_R = input_RR
            input_r = input_rr

        parameters = match_long_repeat([input_R, input_r, input_n1, input_n2, input_rp])

        if self.outputs['Vertices'].is_linked:
            vertList = []
            for R, r, n1, n2, p in zip(*parameters):
                verts = torus_verts(R, r, n1, n2, p, self.Separate)
                vertList.append(verts)
            self.outputs['Vertices'].sv_set(vertList)

        if self.outputs['Edges'].is_linked:
            edgeList = []
            for R, r, n1, n2, _ in zip(*parameters):
                edges = torus_edges(n1, n2)
                edgeList.append(edges)
            self.outputs['Edges'].sv_set(edgeList)

        if self.outputs['Polygons'].is_linked:
            polyList = []
            for R, r, n1, n2, _ in zip(*parameters):
                polys = torus_polygons(n1, n2)
                polyList.append(polys)
            self.outputs['Polygons'].sv_set(polyList)


def register():
    bpy.utils.register_class(SvTorus2DNode)


def unregister():
    bpy.utils.unregister_class(SvTorus2DNode)

if __name__ == '__main__':
    register()
