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

from bpy.props import BoolProperty, EnumProperty, StringProperty, FloatProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, StringsSocket
from sverchok.data_structure import node_id, multi_socket, updateNode

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

class SvExportGcodeNnode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Export gcode from vertices position
    Tooltip: Generate a gcode file from a list of vertices
    """
    bl_idname = 'SvExportGcodeNnode'
    bl_label = 'Export Gcode'
    bl_icon = 'COPYDOWN'


    _start_code = '''
G21 ; set untis to millimeters
G90 ; use absolute coordinates
M82; set extruder to absolute positions....
G28 ; home all axe
G28 E ; home Extruder
G93 ; ingresso tubo
G92 E0 ; set position
'''

    _end_code = '''

M83

G0 E-0.5
G92 ; set position
G28 ; home all axes
G28 E; homing extruder
M84 ; disable motors
'''

    folder = StringProperty(name="File", default="", subtype='FILE_PATH')
    pull = FloatProperty(name="Pull", default=5.0, min=0, soft_max=10)
    push = FloatProperty(name="Push", default=4.0, min=0, soft_max=10)
    dz = FloatProperty(name="dz", default=2.0, min=0, soft_max=20)
    #flow_mult = FloatProperty(name="Flow Mult", default=1.0, min=0, soft_max=3)
    feed = IntProperty(name="Feed Rate (F)", default=1000, min=0, soft_max=5000)
    flow = FloatProperty(name="Flow (E/mm)", default=0.044, min=0, soft_max=1)
    start_code = StringProperty(name="Start", default=_start_code)
    end_code = StringProperty(name="End", default=_end_code)
    auto_sort = BoolProperty(name="Auto Sort", default=True)

    gcode_mode = EnumProperty(items=[
            ("CONT", "Continuous", ""),
            ("RETR", "Retraction", "")
        ], default='CONT', name="Mode")

    def sv_init(self, context):
        #self.inputs.new('StringsSocket', 'Flow', 'Flow').prop_name = 'flow'
        #self.inputs.new('StringsSocket', 'Start Code', 'Start Code').prop_name = 'start_code'
        #self.inputs.new('StringsSocket', 'End Code', 'End Code').prop_name = 'end_code'
        self.inputs.new('VerticesSocket', 'Vertices', 'Vertices')

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
        if self.gcode_mode == 'RETR':
            #col.label(text="Retraction:")
            col.prop(self, 'auto_sort')
            col.prop(self, 'pull')
            col.prop(self, 'dz')
            col.prop(self, 'push')
        col = layout.column(align=True)
        col.prop(self, 'feed')
        col.prop(self, 'flow')
        #col.prop(self, 'flow_mult')
        col = layout.column(align=True)
        col.prop_search(self, 'start_code', bpy.data, 'texts')
        col.prop_search(self, 'end_code', bpy.data, 'texts')
        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = 4.0
        row.operator(TEXT_IO_CALLBACK, text='Export Gcode').fn_name = 'process'


    def update_socket(self, context):
        self.update()

    def process(self):
        # manage data
        feed = self.feed
        flow = self.flow
        vertices = self.inputs['Vertices'].sv_get()
        #start_code = '\n'.join(self.inputs['Start Code'].sv_get()[0])
        #end_code = '\n'.join(self.inputs['End Code'].sv_get()[0])

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
        e = 0.5
        first_point = True
        count = 0
        last_vert = mathutils.Vector((0,0,0))
        maxz = 0

        # write movements
        for curve in vertices:
            #path = path[0]
            #print(curve)
            for v in curve:
                #print(v)
                new_vert = mathutils.Vector(v)
                dist = (new_vert-last_vert).length

                # record max z
                maxz = max(maxz,v[2])

                # first point of the gcode
                if first_point:
                    file.write('G1 X' + format(v[0], '.4f') + ' Y' + format(v[1], '.4f') + ' Z' + format(v[2], '.4f') + ' F' + format(feed, '.0f') + '\n')
                    file.write('G0 E0.5 \n')
                    file.write('M82 \n')
                    first_point = False
                else:
                    # start after retraction
                    if v == curve[0] and self.gcode_mode == 'RETR':
                        file.write('G1 X' + format(v[0], '.4f') + ' Y' + format(v[1], '.4f') + ' Z' + format(maxz+self.dz, '.4f') + '\n')
                        e += self.push
                        file.write('G1 X' + format(v[0], '.4f') + ' Y' + format(v[1], '.4f') + ' Z' + format(v[2], '.4f') + ' E' + format(e, '.4f') + '\n')
                    # regular extrusion
                    else:
                        e += flow*dist
                        file.write('G1 X' + format(v[0], '.4f') + ' Y' + format(v[1], '.4f') + ' Z' + format(v[2], '.4f') + ' E' + format(e, '.4f') + '\n')
                count+=1
                last_vert = new_vert
            if curve != vertices[-1] and self.gcode_mode == 'RETR': #file.write(stop_extrusion)
                e -= self.pull
                file.write('G0 E' + format(e, '.4f') + '\n')
                file.write('G1 X' + format(last_vert[0], '.4f') + ' Y' + format(last_vert[1], '.4f') + ' Z' + format(maxz+self.dz, '.4f') + '\n')

        # end code
        try:
            for line in bpy.data.texts[self.end_code].lines:
                file.write(line.body + '\n')
        except:
            pass
        #file.write(end_code)
        file.close()
        print("Saved gcode to " + path)

def register():
    bpy.utils.register_class(SvExportGcodeNnode)


def unregister():
    bpy.utils.unregister_class(SvExportGcodeNnode)
