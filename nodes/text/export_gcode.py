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

# made by: Alessandro Zomparelli
# url: www.alessandrozomparelli.com

import io
import itertools
import pprint
import sverchok

import bpy, os, mathutils
from numpy import mean
import operator
from math import pi

from bpy.props import BoolProperty, EnumProperty, StringProperty, FloatProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, StringsSocket
from sverchok.data_structure import node_id, multi_socket, updateNode
from sverchok.utils.sv_itertools import sv_zip_longest2, flatten, list_of_lists, recurse_verts_fxy, match_longest_lists

from sverchok.utils.sv_text_io_common import (
    FAIL_COLOR, READY_COLOR, TEXT_IO_CALLBACK,
    get_socket_type,
    new_output_socket,
    name_dict,
    text_modes
)

def convert_to_text(list):
    while True:
        if type(list) is str: break
        elif type(list) in (tuple, list):
            try:
                list = '\n'.join(list)
                break
            except: list = list[0]
        else: break
    return list

class SvExportGcodeNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Export gcode from vertices position
    Tooltip: Generate a gcode file from a list of vertices
    """
    bl_idname = 'SvExportGcodeNode'
    bl_label = 'Export Gcode'
    bl_icon = 'COPYDOWN'

    last_e = FloatProperty(name="Pull", default=5.0, min=0, soft_max=10)
    path_length = FloatProperty(name="Pull", default=5.0, min=0, soft_max=10)

    folder = StringProperty(name="File", default="", subtype='FILE_PATH')
    pull = FloatProperty(name="Pull", default=5.0, min=0, soft_max=10)
    push = FloatProperty(name="Push", default=5.0, min=0, soft_max=10)
    dz = FloatProperty(name="dz", default=2.0, min=0, soft_max=20)
    flow_mult = FloatProperty(name="Flow Mult", default=1.0, min=0, soft_max=3)
    feed = IntProperty(name="Feed Rate (F)", default=1000, min=0, soft_max=20000)
    feed_horizontal = IntProperty(name="Feed Horizontal", default=2000, min=0, soft_max=20000)
    feed_vertical = IntProperty(name="Feed Vertical", default=500, min=0, soft_max=20000)
    feed = IntProperty(name="Feed Rate (F)", default=1000, min=0, soft_max=20000)
    esteps = FloatProperty(name="E Steps/Unit", default=5, min=0, soft_max=100)
    start_code = StringProperty(name="Start", default='')
    end_code = StringProperty(name="End", default='')
    auto_sort = BoolProperty(name="Auto Sort", default=True)
    close_all = BoolProperty(name="Close Shapes", default=False)
    nozzle = FloatProperty(name="Nozzle", default=0.4, min=0, soft_max=10)
    layer_height = FloatProperty(name="Layer Height", default=0.1, min=0, soft_max=10)
    filament = FloatProperty(name="Filament (\u03A6)", default=1.75, min=0, soft_max=120)

    gcode_mode = EnumProperty(items=[
            ("CONT", "Continuous", ""),
            ("RETR", "Retraction", "")
        ], default='CONT', name="Mode")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'Layer Height',).prop_name = 'layer_height'
        self.inputs.new('StringsSocket', 'Flow Mult',).prop_name = 'flow_mult'
        self.inputs.new('VerticesSocket', 'Vertices',)

        self.outputs.new('StringsSocket', 'Info',)
        self.outputs.new('VerticesSocket', 'Vertices',)
        self.outputs.new('StringsSocket', 'Printed Edges',)
        self.outputs.new('StringsSocket', 'Travel Edges',)

    def draw_buttons(self, context, layout):

        addon = context.user_preferences.addons.get(sverchok.__name__)
        over_sized_buttons = addon.preferences.over_sized_buttons

        col = layout.column(align=True)
        row = col.row()
        row.prop(self, 'folder', toggle=True, text='')
        col = layout.column(align=True)
        row = col.row()
        row.prop(self, 'gcode_mode', expand=True, toggle=True)
        #col = layout.column(align=True)
        col = layout.column(align=True)
        col.label(text="Extrusion:", icon='MOD_FLUIDSIM')
        #col.prop(self, 'esteps')
        col.prop(self, 'filament')
        col.prop(self, 'nozzle')
        col.separator()
        col.label(text="Speed (Feed Rate F):", icon='DRIVER')
        col.prop(self, 'feed', text='Print')
        if self.gcode_mode == 'RETR':
            col.prop(self, 'feed_vertical', text='Z Lift')
            col.prop(self, 'feed_horizontal', text='Travel')
        col.separator()
        if self.gcode_mode == 'RETR':
            col.label(text="Retraction:", icon='NOCURVE')
            col.prop(self, 'pull', text='Retraction')
            col.prop(self, 'dz', text='Z Hop')
            col.prop(self, 'push', text='Preload')
            col.prop(self, 'auto_sort', text="Sort Layers (z)")
            col.prop(self, 'close_all')
            col.separator()
        col.label(text='Custom Code:', icon='SCRIPT')
        col.prop_search(self, 'start_code', bpy.data, 'texts')
        col.prop_search(self, 'end_code', bpy.data, 'texts')
        col.separator()
        row = col.row(align=True)
        row.scale_y = 4.0
        row.operator(TEXT_IO_CALLBACK, text='Export Gcode').fn_name = 'process'

    def update_socket(self, context):
        self.update()

    def process(self):
        # manage data
        feed = self.feed
        feed_v = self.feed_vertical
        feed_h = self.feed_horizontal
        layer = self.layer_height
        layer = self.inputs['Layer Height'].sv_get()
        vertices = self.inputs['Vertices'].sv_get()
        flow_mult = self.inputs['Flow Mult'].sv_get()

        # data matching
        vertices = list_of_lists(vertices)
        flow_mult = list_of_lists(flow_mult)
        layer = list_of_lists(layer)
        vertices, flow_mult, layer = match_longest_lists([vertices, flow_mult, layer])
        print(vertices)
        print(layer)

        # open file
        if self.folder == '':
            folder = '//' + os.path.splitext(bpy.path.basename(bpy.context.blend_data.filepath))[0]
        else:
            folder = self.folder
        if '.gcode' not in folder: folder += '.gcode'
        path = bpy.path.abspath(folder)
        file = open(path, 'w')
        try:
            for line in bpy.data.texts[self.start_code].lines:
                file.write(line.body + '\n')
        except:
            pass

        # sort vertices
        if self.auto_sort and self.gcode_mode == 'RETR':
            sorted_verts = []
            for curve in vertices:
                # mean z
                listz = [v[2] for v in curve]
                meanz = mean(listz)
                # store curve and meanz
                sorted_verts.append((curve, meanz))
            vertices = [data[0] for data in sorted(sorted_verts, key=lambda height: height[1])]

        # initialize variables
        e = 0
        last_vert = mathutils.Vector((0,0,0))
        maxz = 0
        path_length = 0

        printed_verts = []
        printed_edges = []
        travel_verts = []
        travel_edges = []

        # write movements
        for i in range(len(vertices)):
            curve = vertices[i]
            first_id = len(printed_verts)
            for j in range(len(curve)):
                v = curve[j]
                v_flow_mult = flow_mult[i][j]
                v_layer = layer[i][j]

                # record max z
                maxz = max(maxz,v[2])

                # first point of the gcode
                if i ==  j == 0:
                    printed_verts.append(v)
                    file.write('G92 E0 \n')
                    params = v[:3] + (feed,)
                    to_write = 'G1 X{0:.4f} Y{1:.4f} Z{2:.4f} F{3:.0f}\n'.format(*params)
                    file.write(to_write)
                else:
                    # start after retraction
                    if j == 0 and self.gcode_mode == 'RETR':
                        params = v[:2] + (maxz+self.dz,) + (feed_h,)
                        to_write = 'G1 X{0:.4f} Y{1:.4f} Z{2:.4f} F{3:.0f}\n'.format(*params)
                        file.write(to_write)
                        e += self.push
                        params = v[:3] + (feed_v,)
                        to_write = 'G1 X{0:.4f} Y{1:.4f} Z{2:.4f} F{3:.0f}\n'.format(*params)
                        file.write(to_write)
                        file.write( 'G1 E' + format(e, '.4f') + '\n')
                        printed_verts.append((v[0], v[1], maxz+self.dz))
                        travel_edges.append((len(printed_verts)-1, len(printed_verts)-2))
                        printed_verts.append(v)
                        travel_edges.append((len(printed_verts)-1, len(printed_verts)-2))
                    # regular extrusion
                    else:
                        printed_verts.append(v)
                        v1 = mathutils.Vector(v)
                        v0 = mathutils.Vector(curve[j-1])
                        dist = (v1-v0).length
                        print(dist)
                        area = v_layer * self.nozzle + pi*(v_layer/2)**2 # rectangle + circle
                        cylinder = pi*(self.filament/2)**2
                        flow = area / cylinder
                        e += dist * v_flow_mult * flow
                        params = v[:3] + (e,)
                        to_write = 'G1 X{0:.4f} Y{1:.4f} Z{2:.4f} E{3:.4f}\n'.format(*params)
                        file.write(to_write)
                        path_length += dist
                        printed_edges.append([len(printed_verts)-1, len(printed_verts)-2])
            if self.gcode_mode == 'RETR':
                v0 = mathutils.Vector(curve[-1])
                if self.close_all:
                    #printed_verts.append(v0)
                    printed_edges.append([len(printed_verts)-1, first_id])

                    v1 = mathutils.Vector(curve[0])
                    dist = (v0-v1).length
                    area = v_layer * self.nozzle + pi*(v_layer/2)**2 # rectangle + circle
                    cylinder = pi*(self.filament/2)**2
                    flow = area / cylinder
                    e += dist * v_flow_mult * flow
                    params = v1[:3] + (e,)
                    to_write = 'G1 X{0:.4f} Y{1:.4f} Z{2:.4f} E{3:.4f}\n'.format(*params)
                    file.write(to_write)
                    path_length += dist
                    v0 = v1
                if i < len(vertices)-1:
                    e -= self.pull
                    file.write('G0 E' + format(e, '.4f') + '\n')
                    params = v0[:2] + (maxz+self.dz,) + (feed_v,)
                    to_write = 'G1 X{0:.4f} Y{1:.4f} Z{2:.4f} F{3:.0f}\n'.format(*params)
                    file.write(to_write)
                    printed_verts.append(v0.to_tuple())
                    printed_verts.append((v0.x, v0.y, maxz+self.dz))
                    travel_edges.append((len(printed_verts)-1, len(printed_verts)-2))

        # end code
        try:
            for line in bpy.data.texts[self.end_code].lines:
                file.write(line.body + '\n')
        except:
            pass
        file.close()
        print("Saved gcode to " + path)
        info = "Extruded Filament: " + format(e, '.2f') + '\n'
        info += "Extruded Volume: " + format(e*pi*(self.filament/2)**2, '.2f') + '\n'
        info += "Printed Path: " + format(path_length, '.2f')
        self.outputs[0].sv_set(info)
        self.outputs[1].sv_set(printed_verts)
        self.outputs[2].sv_set(printed_edges)
        self.outputs[3].sv_set(travel_edges)

def register():
    bpy.utils.register_class(SvExportGcodeNode)


def unregister():
    bpy.utils.unregister_class(SvExportGcodeNode)
