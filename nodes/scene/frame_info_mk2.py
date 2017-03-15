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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


def get_int(self):
    return bpy.context.scene.frame_current

def set_int(self, value):
    bpy.context.scene.frame_current = value


class SvFrameInfoNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Frame Info '''
    bl_idname = 'SvFrameInfoNodeMK2'
    bl_label = 'Frame infoMK2'
    bl_icon = 'OUTLINER_OB_EMPTY'


    def wrapUpdate(self, context):
        updateNode(self, context)

    curr_frame = bpy.props.IntProperty(get=get_int, set=set_int, update=wrapUpdate)

    def sv_init(self, context):
        # self.curr_frame = context.scene.frame_current
        outputs = self.outputs
        outputs.new('StringsSocket', "Current Frame")
        outputs.new('StringsSocket', "Start Frame")
        outputs.new('StringsSocket', "End Frame")
        outputs.new('StringsSocket', "Evaluate")

    def draw_buttons(self, context, layout):
        # almost verbatim copy of space_time.py time controls.
        scene = context.scene
        screen = context.screen

        row = layout.row(align=True)
        if not scene.use_preview_range:
            row.prop(scene, "frame_start", text="Start")
            row.prop(scene, "frame_end", text="End")
        else:
            row.prop(scene, "frame_preview_start", text="Start")
            row.prop(scene, "frame_preview_end", text="End")

        row = layout.row(align=True)
        row.operator('node.sv_push_current_frame', text='-1').direction=-1
        row.operator('node.sv_push_current_frame', text='+1').direction=1

        row = layout.row(align=True)
        row.operator("screen.frame_jump", text="", icon='REW').end = False
        # row.operator("screen.keyframe_jump", text="", icon='PREV_KEYFRAME').next = False
        if not screen.is_animation_playing:
            row.operator("screen.animation_play", text="", icon='PLAY_REVERSE').reverse = True
            row.operator("screen.animation_play", text="", icon='PLAY')
        else:
            sub = row.row(align=True)
            sub.scale_x = 2.0
            sub.operator("screen.animation_play", text="", icon='PAUSE')
        # row.operator("screen.keyframe_jump", text="", icon='NEXT_KEYFRAME').next = True
        row.operator("screen.frame_jump", text="", icon='FF').end = True
        row.prop(self, "curr_frame", text="Current Frame")

    def process(self):
        scene = bpy.context.scene
        outputs = self.outputs

        frame_current = scene.frame_current
        frame_end = scene.frame_end
        frame_start = scene.frame_start
        num_frames = max(1, frame_end - frame_start)


        outputs['Current Frame'].sv_set([[frame_current]])
        outputs['Start Frame'].sv_set([[frame_start]])
        outputs['End Frame'].sv_set([[frame_end]])
        outputs['Evaluate'].sv_set([[frame_current / num_frames]])


def register():
    bpy.utils.register_class(SvFrameInfoNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvFrameInfoNodeMK2)
