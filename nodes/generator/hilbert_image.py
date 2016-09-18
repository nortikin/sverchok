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
from bpy.props import EnumProperty, IntProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, SvSetSocketAnyType, SvGetSocketAnyType


class HilbertImageNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Hilbert Image '''
    bl_idname = 'HilbertImageNode'
    bl_label = 'Hilbert image'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def images(self, context):
        return [tuple(3 * [im.name]) for im in bpy.data.images]
    name_image = EnumProperty(items=images, name='images')
    level_ = IntProperty(name='level', description='Level',
                         default=2, min=1, max=20,
                         options={'ANIMATABLE'}, update=updateNode)
    size_ = FloatProperty(name='size', description='Size',
                          default=1.0, min=0.1,
                          options={'ANIMATABLE'}, update=updateNode)
    #name_image = bpy.props.StringProperty(name='image_name', description='image name', default='', update=updateNode)
    sensitivity_ = FloatProperty(name='sensitivity', description='sensitivity',
                                 default=1, min=0.1, max=1.0,
                                 options={'ANIMATABLE'}, update=updateNode)
    R = FloatProperty(name='R', description='R',
                      default=0.30, min=0, max=1,
                      options={'ANIMATABLE'}, update=updateNode)
    G = FloatProperty(name='G', description='G',
                      default=0.59, min=0, max=1,
                      options={'ANIMATABLE'}, update=updateNode)
    B = FloatProperty(name='B', description='B',
                      default=0.11, min=0, max=1,
                      options={'ANIMATABLE'}, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Level", "Level").prop_name = 'level_'
        self.inputs.new('StringsSocket', "Size", "Size").prop_name = 'size_'
        self.inputs.new('StringsSocket', "Sensitivity", "Sensitivity").prop_name = 'sensitivity_'
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")

    def draw_buttons(self, context, layout):
        layout.prop(self, "name_image", text="image name")
        row = layout.row(align=True)
        row.scale_x = 10.0
        row.prop(self, "R", text="R")
        row.prop(self, "G", text="G")
        row.prop(self, "B", text="B")

    def process(self):
        # inputs
        if self.outputs['Edges'].links or self.outputs['Vertices'].links:
            if 'Level' in self.inputs and self.inputs['Level'].links:
                Integer = int(SvGetSocketAnyType(self, self.inputs['Level'])[0][0])
            else:
                Integer = self.level_

            if 'Size' in self.inputs and self.inputs['Size'].links:
                Step = SvGetSocketAnyType(self, self.inputs['Size'])[0][0]
            else:
                Step = self.size_

            if 'Sensitivity'in self.inputs and self.inputs['Sensitivity'].links:
                Sensitivity = SvGetSocketAnyType(self, self.inputs['Sensitivity'])[0][0]
            else:
                Sensitivity = self.sensitivity_

        # outputs
        if 'Vertices' in self.outputs and self.outputs['Vertices'].links and self.name_image:
            img = bpy.data.images[self.name_image]
            pixels = list(img.pixels)
            verts = self.hilbert(0.0, 0.0, 1.0, 0.0, 0.0, 1.0, Integer, img, pixels, Sensitivity)
            for iv, v in enumerate(verts):
                for ip, p in enumerate(v):
                    verts[iv][ip] *= Step

            self.outputs['Vertices'].sv_set(verts)

            if 'Edges' in self.outputs and len(self.outputs['Edges'].links) > 0:

                listEdg = []
                r = len(verts)-1
                for i in range(r):
                    listEdg.append((i, i+1))

                edg = list(listEdg)
                self.outputs['Edges'].sv_set([edg])
        else:
            pass
            #self.outputs['Vertices'].VerticesProperty = str([[]])
            #self.outputs['Edges'].StringsProperty = str([[]])

    def hilbert(self, x0, y0, xi, xj, yi, yj, n, img, pixels, Sensitivity):
        w = img.size[0]-1
        h = img.size[1]-1
        px = x0+(xi+yi)/2
        py = y0+(xj+yj)/2
        xy = int(int(px*w)+int(py*h)*(w+1))*4
        p = (pixels[xy]*self.R+pixels[xy+1]*self.G+pixels[xy+2]*self.B)#*pixels[xy+3]
        if p > 0:
            n = n-p**(1/Sensitivity)
        out = []
        if n <= 0:
            X = x0 + (xi + yi)/2
            Y = y0 + (xj + yj)/2
            out.append(X)
            out.append(Y)
            out.append(0)
            return [out]
        else:
            out.extend(self.hilbert(x0,               y0,               yi/2, yj/2, xi/2, xj/2, n - 1, img, pixels, Sensitivity))
            out.extend(self.hilbert(x0 + xi/2,        y0 + xj/2,        xi/2, xj/2, yi/2, yj/2, n - 1, img, pixels, Sensitivity))
            out.extend(self.hilbert(x0 + xi/2 + yi/2, y0 + xj/2 + yj/2, xi/2, xj/2, yi/2, yj/2, n - 1, img, pixels, Sensitivity))
            out.extend(self.hilbert(x0 + xi/2 + yi,   y0 + xj/2 + yj,  -yi/2,-yj/2,-xi/2,-xj/2, n - 1, img, pixels, Sensitivity))
            return out


def register():
    bpy.utils.register_class(HilbertImageNode)


def unregister():
    bpy.utils.unregister_class(HilbertImageNode)

if __name__ == '__main__':
    register()
