# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import EnumProperty, PointerProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import (updateNode, no_space, enum_item as e)

def frame_from_available(idx, layer):
    keys = {}
    for frame in layer.frames:
        keys[frame.frame_number] = frame.strokes
    return keys

def frame_from_available2(current_frame, layer):
    scene = bpy.context.scene
    rng = [scene.frame_start, scene.frame_end]
    inp = [frame.frame_number for frame in layer.frames]
    inp_to_index = {val: idx for idx, val in enumerate(inp)}

    # this can be cached if inp and rng unchanged. there are several redundancies here
    # but i don't care

    remaps = []  # you fill this
    last_valid = None
    for i in range(rng[0], rng[1]+1):
        if i < inp[0]:
            last_valid = inp[0]
        elif i in set(inp):
            last_valid = i
        elif i >= inp[-1]:
            last_valid = inp[-1]
        else:
            for j in range(len(inp)-1):
                begin, end = inp[j], inp[j+1]
                if begin < i < end:
                    last_valid = begin
                    
        remaps.append(last_valid)

    mdict = {idx: remaps[idx-1] for idx in range(1, len(remaps)+1)}
    tval = mdict.get(current_frame, 0)
    return inp_to_index.get(tval, 0)


class SvGetAssetPropertiesMK2(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    ''' Get Asset Props '''
    bl_idname = 'SvGetAssetPropertiesMK2'
    bl_label = 'Object ID Selector+'
    bl_icon = 'SELECT_SET'
    sv_icon = 'SV_OBJECT_ID_SELECTOR'

    def type_filter(self, object):
        return object.type == self.Type

    def frame_updateNode(self, context):
        ''' must rebuild for each update'''
        self.frame_collection_name.clear()
        
        if not (self.gp_pointer and self.gp_layer_pointer):
           return 

        for idx, f in enumerate(gp_layer_pointer.frames):
            self.frame_collection_name.add().name = str(idx) + ' | ' + str(f.frame_number)

        # updateNode(self, context)
        if self.gp_selected_frame_mode == 'active_frame':
            if len(self.inputs) == 0:
                self.inputs.new("SvStringsSocket", 'frame#')
        else:
            if len(self.inputs) > 0:
                self.inputs.remove(self.inputs[-1])

        self.process()

    type_collection_name: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    frame_collection_name: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    M = ['actions', 'brushes', 'filepath', 'grease_pencils', 'groups',
         'images', 'libraries', 'linestyles', 'masks', 'materials',
         'movieclips', 'node_groups', 'particles', 'scenes', 'screens', 'shape_keys',
         'sounds', 'speakers', 'texts', 'textures', 'worlds', 'objects']


    T = ['MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'ARMATURE', 'GPENCIL',
         'LATTICE', 'EMPTY', 'CAMERA', 'LIGHT', 'SPEAKER']

    Mode: EnumProperty(name="get modes", default="objects", items=e(M), update=updateNode)
    Type: EnumProperty(name="get types", default="MESH", items=e(T), update=updateNode)

    properties_to_skip_iojson: ["object_pointer", "image_pointer", "text_pointer"]

    text_pointer: PointerProperty(type=bpy.types.Text, poll=lambda s, o: True, update=updateNode)
    object_pointer: PointerProperty(type=bpy.types.Object, poll=type_filter, update=updateNode)
    image_pointer: PointerProperty(type=bpy.types.Image, poll=lambda s, o: True, update=updateNode)
    pass_pixels: bpy.props.BoolProperty(update=updateNode)

    # GP props
    gp_pointer: PointerProperty(type=bpy.types.GreasePencil, poll=lambda s, o: True, update=updateNode)
    gp_layer_pointer: PointerProperty(type=bpy.types.GreasePencilLayers, poll=lambda s, o: True, update=updateNode) # <---- no?
    gp_frame_current: bpy.props.BoolProperty(default=True, update=updateNode)
    gp_frame_override: bpy.props.IntProperty(default=1, update=updateNode)
    gp_stroke_idx: bpy.props.IntProperty(update=updateNode)

    gp_frame_mode_options = [(no_space(k), k, '', i) for i, k in enumerate(["pick frame", "active frame"])]
    gp_selected_frame_mode: bpy.props.EnumProperty(
        items=gp_frame_mode_options, description="offers choice between current frame or available frames",
        default="pick_frame", update=frame_updateNode
    )
    gp_frame_pick: bpy.props.StringProperty(update=frame_updateNode)
    gp_pass_points: bpy.props.BoolProperty(default=True, update=updateNode)

    def draw_gp_options(self, context, layout):
        layout.prop_search(self, 'gp_pointer', bpy.data, 'grease_pencils', text='name')
        if not self.gp_pointer:
            return
        
        layout.prop_search(self, 'gp_layer_pointer', self.gp_pointer, 'layers', text='layer')
        if not self.gp_layer_pointer:
            return

        layout.prop(self, 'gp_selected_frame_mode', expand=True)
        frame_data = None
        if self.gp_selected_frame_mode == 'active_frame':
            frame_data = gp_layer_pointer.active_frame
        else:
            # maybe display uilist with frame_index and frame_nmber.
            layout.prop_search(self, 'gp_frame_pick', self, 'frame_collection_name')
        layout.prop(self, 'gp_pass_points', text='pass points')

    def process_mode_grease_pencils(self):
        data_list = bpy.data.grease_pencils
        if not (self.gp_pointer and self.gp_layer_pointer):
            return data_list[:]

        if self.gp_selected_frame_mode == 'active_frame':
            if len(self.inputs) > 0 and self.inputs[0].is_linked:

                frame_number = self.inputs[0].sv_get()[0][0]
                key = frame_from_available2(frame_number, self.gp_layer_pointer)
                strokes = self.gp_layer_pointer.frames[key].strokes
            else:
                strokes = self.gp_layer_pointer.active_frame.strokes

            if not strokes:
                return []

            if self.gp_pass_points:
                return [[p.co[:] for p in s.points] for s in strokes]
            else:
                return strokes
        else:
            if self.gp_frame_pick:
                idx_from_frame_pick = int(self.gp_frame_pick.split(' | ')[0])
                frame_data = self.gp_layer_pointer.frames[idx_from_frame_pick]
                if frame_data:
                    if self.gp_pass_points:
                        return [[p.co[:] for p in s.points] for s in frame_data.strokes]
                    else:
                        return strokes

    def process_mode_objects(self):
        data_list = bpy.data.objects
        if self.object_pointer:
            return [self.object_pointer]
        else:
            return [i for i in data_list if i.type == self.Type]

    def process_mode_texts(self):
        data_list = bpy.data.texts
        if self.text_pointer:
            return [[self.text_pointer.as_string()]]
        else:
            return data_list[:]

    def process_mode_images(self):
        data_list = bpy.data.images
        if self.image_pointer:
            if self.pass_pixels:
                return [[self.image_pointer.pixels[:]], self.image_pointer.size[:]]
            else:
                return [self.image_pointer]
        else:
            return data_list[:]

    def draw_buttons(self, context, layout):
        # layout.operator('node.'   ,text='refresh from scene')
        self.draw_animatable_buttons(layout, icon_only=True)
        layout.row().prop(self, "Mode", text="data")

        if self.Mode == 'objects':
            layout.prop(self, "Type", text="type")
            layout.prop_search(self, 'object_pointer', bpy.data, 'objects', text='name', icon='OBJECT_DATA')
        elif self.Mode == 'texts':
            layout.prop_search(self, 'text_pointer', bpy.data, 'texts', text='name')
        elif self.Mode == 'images':
            layout.prop_search(self, 'image_pointer', bpy.data, 'images', text='name')
            if self.image_pointer and self.image_pointer.name:
                layout.prop(self, 'pass_pixels', text='pixels')
                layout.label(text=f"dimensions: {self.image_pointer.size[:]}")
        elif self.Mode == 'grease_pencils':
            self.draw_gp_options(context, layout)
        else:
            col = layout.column()
            col.alert = True
            col.label(text=f"This node is not yet programmed to do")
            col.label(text=f"anything sensible with bpy.data.{self.Mode}")

    def sv_init(self, context):
        self.outputs.new('SvStringsSocket', "Objects")
        self.width = 210

    def process(self):
        output_socket = self.outputs['Objects']
        if not output_socket.is_linked:
            return

        if self.Mode in {'objects', 'texts', 'images', 'grease_pencils'}:
            data_output = getattr(self, f"process_mode_{self.Mode}")()
        else:
            data_list = getattr(bpy.data, self.Mode)
            data_output = data_list[:]

        output_socket.sv_set(data_output)



def register():
    bpy.utils.register_class(SvGetAssetPropertiesMK2)


def unregister():
    bpy.utils.unregister_class(SvGetAssetPropertiesMK2)
