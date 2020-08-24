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
from bpy.props import EnumProperty, BoolProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import match_long_repeat as mlr, updateNode

def draw_path_linear_mode(verts, height, scale):

    x = verts[0][0] * scale
    y = height - verts[0][1] * scale
    svg = f'd="M {x} {y}'
    for v in verts[1:]:
        x = scale * v[0]
        y = height - scale * v[1]
        svg += f' L {x} {y}'
    return svg

def get_command(cmd_idx, commands, v_idx, verts_len):
    command = commands[min(cmd_idx, len(commands)-1)]

    if v_idx+1 > verts_len-1 and not command in 'LT':
        return "T"
    if v_idx+2 > verts_len-1 and not command in 'LTQS':
        return "S"
    if not command in 'LTQSC':
        return "L"
    return command

def draw_path_user_mode(verts, height, scale, commands):

    x = verts[0][0] * scale
    y = height - verts[0][1] * scale
    svg = f'd="M {x} {y}'
    cmd_idx = 0
    i = 1
    while i < len(verts):
        command = get_command(cmd_idx, commands, i, len(verts))
        cmd_idx += 1
        if command in "LT":
            x = scale * verts[i][0]
            y = height - scale * verts[i][1]
            svg += f' {command} {x} {y}'
            i += 1
        elif command in "QS":
            x = scale * verts[i][0]
            y = height - scale * verts[i][1]
            x1 = scale * verts[i+1][0]
            y1 = height - scale * verts[i+1][1]
            svg += f' {command} {x} {y} {x1} {y1}'
            i += 2
        elif command in "C":
            x = scale * verts[i][0]
            y = height - scale * verts[i][1]
            x1 = scale * verts[i+1][0]
            y1 = height - scale * verts[i+1][1]
            x2 = scale * verts[i+2][0]
            y2 = height - scale * verts[i+2][1]
            svg += f' {command} {x} {y} {x1} {y1} {x2} {y2}'
            i += 3
        else:
            i += 1


    return svg

class SvgPath():
    def __repr__(self):
        return "<SVG Path>"
    def __init__(self, verts, commands, attributes, node):
        self.verts = verts
        self.commands = commands[0]
        self.attributes = attributes[0] if attributes else []
        self.node = node

    def draw(self, height, scale):
        verts = self.verts
        svg = '<path '
        if self.node.mode == 'LIN' or len(verts) < 3 or not self.commands:
            svg += draw_path_linear_mode(verts, height, scale)
        else:
            svg += draw_path_user_mode(verts, height, scale, self.commands)

        if self.node.cyclic:
            svg += ' Z" '
        else:
            svg += '" '

        if self.attributes:
            svg += self.attributes.draw(height, scale)
        else:
            svg += 'fill="none" '
            svg += 'stroke-width="1px"'
            svg += ' stroke="rgb(0,0,0)"'
        svg += '/>'
        return svg

class SvSvgPathNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SVG Path
    Tooltip: Generate SVG Path
    """
    bl_idname = 'SvSvgPathNode'
    bl_label = 'Path SVG'
    bl_icon = 'MESH_CIRCLE'
    sv_icon = 'SV_PATH_SVG'

    modes = [
        ('LIN', 'Linear', '', 0),
        ('USER', 'User', '', 3),
        ]
    def update_sockets(self, context):
        self.inputs["Commands"].hide_safe = self.mode == "LIN"
        updateNode(self, context)

    mode: EnumProperty(
        name='Mode',
        items=modes,
        update=update_sockets
    )
    cyclic: BoolProperty(
        name='Cyclic',
        update=updateNode
    )

    commands_description = '''
One letter per segment, the last command will be repeated to match the verts length

        L = line segment (consumes 1 vertex)
        C = Bezier Curve (consumes 3 vertex)
        S = Smooth Bezier (consumes 2 vertex)
        Q = Quadratic curve (consumes 2 vertex)
        T = Smooth Quadratic (consumes 1 vertex)

If at the beginning of the command there are not enough vertices to feed the command it will be downgraded
from C to S and from Q to T

If command Letter is not in the list [L, C, S, Q, T] it will be interpreted as L
        '''
    path_commands: StringProperty(
        name='Commands',
        description=commands_description,
        default="L",
        update=updateNode
    )
    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Commands").prop_name = 'path_commands'
        self.inputs["Commands"].hide_safe = True
        self.inputs.new('SvSvgSocket', "Fill / Stroke")

        self.outputs.new('SvSvgSocket', "SVG Objects")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=True)
        layout.prop(self, "cyclic", expand=True)

    def process(self):

        if not self.outputs[0].is_linked:
            return
        verts_in = self.inputs['Vertices'].sv_get(deepcopy=True)
        commands_in = self.inputs['Commands'].sv_get(deepcopy=True)
        shapes = []
        atts_in = self.inputs['Fill / Stroke'].sv_get(deepcopy=False, default=None)
        for verts, commands, atts in zip(*mlr([verts_in, commands_in, atts_in])):
            shapes.append(SvgPath(verts, commands, atts, self))
        self.outputs[0].sv_set(shapes)



def register():
    bpy.utils.register_class(SvSvgPathNode)


def unregister():
    bpy.utils.unregister_class(SvSvgPathNode)
