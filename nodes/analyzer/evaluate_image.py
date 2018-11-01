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
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList
from math import floor


class EvaluateImageNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Evaluate Image '''
    bl_idname = 'EvaluateImageNode'
    bl_label = 'Evaluate Image'
    bl_icon = 'FILE_IMAGE'

    image_name = StringProperty(name='image_name', description='image name', default='', update=updateNode)

    boundary_modes = [
        ("CLIP", "Clip", "", 0),
        ("CYCLIC", "Repeat", "", 1),
        ("MIRROR", "Mirror", "", 2)]

    shift_modes = [
        ("NONE", "None", "", 0),
        ("ALTERNATE", "Alternate", "", 1),
        ("CONSTANT", "Constant", "", 2)]

    shift_mode_U = EnumProperty(
        name="U Shift",
        description="U Shift",
        default="NONE", items=shift_modes,
        update=updateNode)

    shift_mode_V = EnumProperty(
        name="V Shift",
        description="V Shift",
        default="NONE", items=shift_modes,
        update=updateNode)

    boundU = EnumProperty(
        name="U Bounds",
        description="U Boundaries",
        default="CYCLIC", items=boundary_modes,
        update=updateNode)

    boundV = EnumProperty(
        name="V Bounds",
        description="V Boundaries",
        default="CYCLIC", items=boundary_modes,
        update=updateNode)

    domU = FloatProperty(
        name='U domain', description='U domain', default=1, min=0.00001,
        options={'ANIMATABLE'}, update=updateNode)

    domV = FloatProperty(
        name='V domain', description='V domain', default=1, min=0.00001,
        options={'ANIMATABLE'}, update=updateNode)

    shiftU = FloatProperty(
        name='U shift', description='U shift', default=0.5, soft_min=-1, soft_max=1,
        options={'ANIMATABLE'}, update=updateNode)

    shiftV = FloatProperty(
        name='V shift', description='V shift', default=0, soft_min=-1, soft_max=1,
        options={'ANIMATABLE'}, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Verts UV")
        self.inputs.new('StringsSocket', "U domain").prop_name = 'domU'
        self.inputs.new('StringsSocket', "V domain").prop_name = 'domV'
        #if self.shift_mode_U not 'NONE':
        #self.inputs.new('StringsSocket', "U shift").prop_name = 'shiftU'
        #if self.shift_mode_V not 'NONE':
        #self.inputs.new('StringsSocket', "V shift").prop_name = 'shiftV'
        self.outputs.new('StringsSocket', "R")
        self.outputs.new('StringsSocket', "G")
        self.outputs.new('StringsSocket', "B")

    def draw_buttons(self, context, layout):
        layout.label(text="Image:")
        layout.prop_search(self, "image_name", bpy.data, 'images', text="")

        row = layout.row(align=True)
        col = row.column(align=True)
        col.label(text="Tile U:")
        col.prop(self, "boundU", text="")
        col.label(text="Shift U:")
        col.prop(self, "shift_mode_U", text="")
        if self.shift_mode_U != 'NONE':
            col.prop(self, "shiftU", text="")

        col = row.column(align=True)
        col.label(text="Tile V:")
        col.prop(self, "boundV", text="")
        col.label(text="Shift V:")
        col.prop(self, "shift_mode_V", text="")
        if self.shift_mode_V != 'NONE':
            col.prop(self, "shiftV", text="")


    def process(self):
        verts = self.inputs['Verts UV'].sv_get()

        inputs, outputs = self.inputs, self.outputs

        # inputs
        if inputs['Verts UV'].is_linked:
            verts = inputs['Verts UV'].sv_get()[0]
        else:
            verts = [(0,0,0),(0,1,0),(1,0,0),(1,1,0)]

        if inputs['U domain'].is_linked:
            domU = inputs['U domain'].sv_get()[0][0]
        else: domU = self.domU

        if inputs['V domain'].is_linked:
            domV = inputs['V domain'].sv_get()[0][0]
        else: domV = self.domV

        # outputs
        red = [[]]
        green = [[]]
        blue = [[]]

        if outputs['R'].is_linked or outputs['G'].is_linked or outputs['B'].is_linked:
            # copy images data, pixels is created on every access with [i], extreme speedup.
            # http://blender.stackexchange.com/questions/3673/why-is-accessing-image-data-so-slow
            imag = bpy.data.images[self.image_name].pixels[:]
            sizeU = bpy.data.images[self.image_name].size[0]
            sizeV = bpy.data.images[self.image_name].size[1]
            for vert in verts:
                vx = vert[0]*(sizeU-1)/domU
                vy = vert[1]*sizeV/domV
                u = floor(vx)
                v = floor(vy)
                u0 = u

                if self.shift_mode_U == 'ALTERNATE':
                    if (v//sizeV)%2: u += floor(sizeU*self.shiftU)
                if self.shift_mode_U == 'CONSTANT':
                    u += floor(sizeU*self.shiftU*(v//sizeV))
                if self.boundU == 'CLIP':
                    u = max(0,min(u,sizeU-1))
                elif self.boundU == 'CYCLIC':
                    u = u%sizeU
                elif self.boundU == 'MIRROR':
                    if (u//sizeU)%2: u = sizeU - 1 - u%(sizeU)
                    else: u = u%(sizeU)


                if self.shift_mode_V == 'ALTERNATE':
                    if (u0//sizeU)%2: v += floor(sizeV*self.shiftV)
                if self.shift_mode_V == 'CONSTANT':
                    v += floor(sizeV*self.shiftV*(u0//sizeU))
                if self.boundV == 'CLIP':
                    v = max(0,min(v,sizeV-1))
                elif self.boundV == 'CYCLIC':
                    v = v%sizeV
                elif self.boundV == 'MIRROR':
                    if (v//sizeV)%2: v = sizeV - 1 - v%(sizeV)
                    else: v = v%(sizeV)

                index = int(u*4 + v*4*sizeU)
                red[0].append(imag[index])
                green[0].append(imag[index+1])
                blue[0].append(imag[index+2])
        outputs['R'].sv_set(red)
        outputs['G'].sv_set(green)
        outputs['B'].sv_set(blue)


def register():
    bpy.utils.register_class(EvaluateImageNode)


def unregister():
    bpy.utils.unregister_class(EvaluateImageNode)
