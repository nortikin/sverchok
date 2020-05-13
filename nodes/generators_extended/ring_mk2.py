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

from math import sin, cos, pi, radians

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.sv_transform_helper import AngleUnits, SvAngleHelper


def ring_verts(separate, u, r1, r2, N1, N2, a1, a2, p):
    """
    separate : separate vertices into radial section lists
    u  : circular section subdivisions
    r1 : major radius
    r2 : minor radius
    N1 : RADIAL sections - number of sections around the center
    N2 : CIRCULAR sections - number of sections away from center
    a1 : starting angle
    a2 : ending angle
    p  : radial section phase
    """

    # use an extra section if the ring is open (start & end angles differ)
    i = open_ring = abs((a2-a1) % (2*pi)) > 1e-5

    # angle increment (cached outside of the loop for performance)
    da = (a2 - a1) / (N1*(1+u))

    s2 = 2 / (N2 - 1)  # caching outside the loop

    list_verts = []

    for n1 in range(N1*(1+u) + i):  # for each RADIAL section around the center
        theta = a1 + n1 * da + p  # RADIAL section angle
        sin_theta = sin(theta)    # caching
        cos_theta = cos(theta)    # caching

        verts = []
        for n2 in range(N2):  # for each CIRCULAR section away from center
            t = n2*s2 - 1  # interpolation factor : [-1, +1]
            r = r1 + t*r2  # radius range : [r1-r2, r1+r2]
            x = r * cos_theta
            y = r * sin_theta

            # append vertex at this (radial, circular) index to the list
            verts.append([x, y, 0.0])

        if separate:
            list_verts.append(verts)
        else:
            list_verts.extend(verts)

    return list_verts


def ring_edges(N1, N2, a1, a2, u):
    """
    N1 : RADIAL sections - number of sections around the center
    N2 : CIRCULAR sections - number of sections away from center
    a1 : starting angle
    a2 : ending angle
    u  : circular section subdivisions
    """

    # use an extra section if the ring is open (start & end angles differ)
    i = open_ring = abs((a2-a1) % (2*pi)) > 1e-5

    list_edges = []

    # radial EDGES (away from center)
    for n1 in range(N1 + i):  # for each RADIAL section around the center
        for n2 in range(N2 - 1):  # for each CIRCULAR section away from center
            list_edges.append([N2 * n1*(1+u) + n2, N2 * n1*(1+u) + n2 + 1])

    # circular EDGES (around the center) : edges are ordered radially
    for n1 in range(N1*(1+u) - 1 + i):  # for each RADIAL section around the center
        for n2 in range(N2):  # for each CIRCULAR section away from center
            list_edges.append([N2 * n1 + n2, N2 * (n1 + 1) + n2])

    # close the ring ? => use the start vertices to close the last edges in the ring
    if not open_ring:
        for n2 in range(N2):
            list_edges.append([N2 * (N1*(1+u) - 1) + n2, n2])

    return list_edges


def ring_polygons(N1, N2, a1, a2, u):
    """
    N1 : RADIAL sections - number of sections around the center
    N2 : CIRCULAR sections - number of sections away from center
    a1 : starting angle
    a2 : ending angle
    u  : circular section subdivisions

    Note: the vertex order is consistent with face normal along pozitive Z
    """

    # use an extra section if the ring is open (start & end angles differ)
    i = open_ring = abs((a2-a1) % (2*pi)) > 1e-5

    list_polys = []

    for n1 in range(N1 - 1 + i):  # RADIAL (around the center)
        for n2 in range(N2 - 1):  # CIRCULAR (away from center)
            arc1 = [N2*(n1*(1+u) + iu) + n2 for iu in reversed(range(2+u))]
            arc2 = [N2*(n1*(1+u) + iu) + n2 + 1 for iu in range(2+u)]
            face = arc2 + arc1
            list_polys.append(face)

    # close the ring ? => use the start vertices to close the last faces in the ring
    if not open_ring:
        for n2 in range(N2 - 1):  # CIRCULAR (away from center)
            arc1 = [N2*((N1-1)*(1+u) + iu) + n2 for iu in reversed(range(1+u))]
            arc2 = [N2*((N1-1)*(1+u) + iu) + n2 + 1 for iu in range(1+u)]
            face = arc2 + [n2+1, n2] + arc1
            list_polys.append(face)

    return list_polys


class SvRingNodeMK2(bpy.types.Node, SverchCustomTreeNode, SvAngleHelper):
    """
    Triggers: Ring
    Tooltip: Generate ring meshes
    """
    bl_idname = 'SvRingNodeMK2'
    bl_label = 'Ring'
    bl_icon = 'PROP_CON'

    def update_mode(self, context):
        # switch radii input sockets (R,r) <=> (eR,iR)
        if self.mode == 'EXT_INT':
            self.inputs['R'].prop_name = "ring_er"
            self.inputs['r'].prop_name = "ring_ir"
        else:
            self.inputs['R'].prop_name = "ring_r1"
            self.inputs['r'].prop_name = "ring_r2"
        updateNode(self, context)

    # keep the equivalent radii pair in sync (eR,iR) => (R,r)
    def external_internal_radii_changed(self, context):
        if self.mode == "EXT_INT":
            self.ring_r1 = (self.ring_er + self.ring_ir) * 0.5
            self.ring_r2 = (self.ring_er - self.ring_ir) * 0.5
            updateNode(self, context)

    # keep the equivalent radii pair in sync (R,r) => (eR,iR)
    def major_minor_radii_changed(self, context):
        if self.mode == "MAJOR_MINOR":
            self.ring_er = self.ring_r1 + self.ring_r2
            self.ring_ir = self.ring_r1 - self.ring_r2
            updateNode(self, context)

    def update_angles(self, context, au):
        ''' Update all the angles to preserve their values in the new units '''
        self.ring_p = self.ring_p * au
        self.ring_a1 = self.ring_a1 * au
        self.ring_a2 = self.ring_a2 * au

    # Ring DIMENSIONS options
    mode: EnumProperty(
        name="Ring Dimensions",
        items=(("MAJOR_MINOR", "R : r",
                "Use the Major/Minor radii for ring dimensions."),
               ("EXT_INT", "eR : iR",
                "Use the Exterior/Interior radii for ring dimensions.")),
        update=update_mode)

    ring_r1: FloatProperty(
        name="Major Radius",
        description="Radius from the ring center to the middle of ring band",
        default=1.0, min=0.0,
        update=major_minor_radii_changed)

    ring_r2: FloatProperty(
        name="Minor Radius",
        description="Width of the ring band",
        default=.25, min=0.0,
        update=major_minor_radii_changed)

    ring_ir: FloatProperty(
        name="Interior Radius",
        description="Interior radius of the ring (closest to the ring center)",
        default=.75, min=0.0,
        update=external_internal_radii_changed)

    ring_er: FloatProperty(
        name="Exterior Radius",
        description="Exterior radius of the ring (farthest from the ring center)",
        default=1.25, min=0.0,
        update=external_internal_radii_changed)

    # Ring RESOLUTION options
    ring_n1: IntProperty(
        name="Radial Sections", description="Number of radial sections",
        default=32, min=3, soft_min=3,
        update=updateNode)

    ring_n2: IntProperty(
        name="Circular Sections", description="Number of circular sections",
        default=3, min=2, soft_min=2,
        update=updateNode)

    # Ring ANGLE options
    ring_a1: FloatProperty(
        name="Start Angle", description="Starting angle of the ring",
        default=0.0,
        update=updateNode)

    ring_a2: FloatProperty(
        name="End Angle", description="Ending angle of the ring",
        default=360.0,
        update=updateNode)

    ring_p: FloatProperty(
        name="Phase", description="Phase of the radial sections",
        default=0.0,
        update=updateNode)

    # OTHER options
    ring_u: IntProperty(
        name="Subdivide Circular", description="Number of subdivisions in the circular sections",
        default=0, min=0, soft_min=0,
        update=updateNode)

    Separate: BoolProperty(
        name='Separate', description='Separate UV coords',
        default=False,
        update=updateNode)

    def migrate_from(self, old_node):
        ''' Migration from old nodes '''
        if old_node.bl_idname == "SvRingNode":
            self.angle_units = AngleUnits.RADIANS
            self.last_angle_units = AngleUnits.RADIANS
            self.ring_p = old_node.ring_rP
            self.ring_r1 = old_node.ring_R
            self.ring_r2 = old_node.ring_r
            self.ring_ir = old_node.ring_iR
            self.ring_er = old_node.ring_eR

    def sv_init(self, context):
        self.width = 160
        self.inputs.new('SvStringsSocket', "R").prop_name = 'ring_r1'
        self.inputs.new('SvStringsSocket', "r").prop_name = 'ring_r2'
        self.inputs.new('SvStringsSocket', "n1").prop_name = 'ring_n1'
        self.inputs.new('SvStringsSocket', "n2").prop_name = 'ring_n2'
        self.inputs.new('SvStringsSocket', "a1").prop_name = 'ring_a1'
        self.inputs.new('SvStringsSocket', "a2").prop_name = 'ring_a2'
        self.inputs.new('SvStringsSocket', "p").prop_name = 'ring_p'

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket',  "Edges")
        self.outputs.new('SvStringsSocket',  "Polygons")

    def draw_buttons(self, context, layout):
        layout.prop(self, "Separate", text="Separate")
        layout.prop(self, 'mode', expand=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_angle_units_buttons(context, layout)
        layout.prop(self, 'ring_u')

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # list of MAJOR or EXTERIOR radii
        input_r1 = self.inputs["R"].sv_get()[0]
        # list of MINOR or INTERIOR radii
        input_r2 = self.inputs["r"].sv_get()[0]
        # list of number of MAJOR sections : RADIAL
        input_n1 = self.inputs["n1"].sv_get()[0]
        # list of number of MINOR sections : CIRCULAR
        input_n2 = self.inputs["n2"].sv_get()[0]
        # list of START angles
        input_a1 = self.inputs["a1"].sv_get()[0]
        # list of END angles
        input_a2 = self.inputs["a2"].sv_get()[0]
        # list of radial PHASES
        input_p = self.inputs["p"].sv_get()[0]

        # sanitize the input values
        input_r1 = list(map(lambda x: max(0, x), input_r1))
        input_r2 = list(map(lambda x: max(0, x), input_r2))
        input_n1 = list(map(lambda x: max(3, int(x)), input_n1))
        input_n2 = list(map(lambda x: max(2, int(x)), input_n2))

        # conversion factor from the current angle units to radians
        au = self.radians_conversion_factor()

        input_a1 = list(map(lambda x: x * au, input_a1))
        input_a2 = list(map(lambda x: x * au, input_a2))
        input_p = list(map(lambda x: x * au, input_p))

        # convert input radii values to MAJOR/MINOR, based on selected mode
        if self.mode == 'EXT_INT':
            # convert radii from EXTERIOR/INTERIOR to MAJOR/MINOR
            # (extend radii lists to a matching length before conversion)
            input_a, input_b = match_long_repeat([input_r1, input_r2])
            input_r1 = list(map(lambda a, b: (a + b) * 0.5, input_a, input_b))
            input_r2 = list(map(lambda a, b: (a - b) * 0.5, input_a, input_b))

        params = match_long_repeat([input_r1, input_r2,
                                    input_n1, input_n2,
                                    input_a1, input_a2,
                                    input_p])

        V, E, P = self.outputs[:]
        for s, f in [(V, ring_verts), (E, ring_edges), (P, ring_polygons)]:
            if not s.is_linked:
                continue
            if s == V:
                s.sv_set([f(self.Separate, self.ring_u, *args) for args in zip(*params)])
            else:
                s.sv_set([f(n1, n2, a1, a2, self.ring_u) for _, _, n1, n2, a1, a2, _ in zip(*params)])


def register():
    bpy.utils.register_class(SvRingNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvRingNodeMK2)
