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

# pylint: disable=E1121


import bpy
from bpy.props import (
    BoolProperty,
    StringProperty,
    BoolVectorProperty,
    FloatProperty,
    IntProperty,
    PointerProperty
)

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect, fullList, updateNode
from sverchok.utils.sv_obj_helper import SvObjHelper, enum_from_list

mode_options_x = enum_from_list('LEFT', 'CENTER', 'RIGHT', 'JUSTIFY', 'FLUSH')
mode_options_y = enum_from_list('TOP_BASELINE', 'TOP', 'CENTER', 'BOTTOM')

def get_font(node):
    fonts = bpy.data.fonts
    default = fonts.get('Bfont')

    if node.font_pointer:
        return node.font_pointer
    else:
        return fonts.get(node.fontname, default)

def font_set_props(f, node, txt):

    f.body = txt
    f.size = node.fsize
    f.font = get_font(node)

    f.space_character = node.space_character
    f.space_word = node.space_word
    f.space_line = node.space_line
    f.offset_x = node.xoffset
    f.offset_y = node.yoffset
    f.offset = node.offset
    f.extrude = node.extrude
    f.bevel_depth = node.bevel_depth
    f.bevel_resolution = node.bevel_resolution

    f.align_x = node.align_x
    f.align_y = node.align_y

def get_obj_and_fontcurve(context, name):
    collection = context.collection
    curves = bpy.data.curves
    objects = bpy.data.objects

    # CURVES
    if not name in curves:
        f = curves.new(name, 'FONT')
    else:
        f = curves[name]

    # CONTAINER OBJECTS
    if name in objects:
        sv_object = objects[name]
    else:
        sv_object = objects.new(name, f)
        collection.objects.link(sv_object)

    return sv_object, f


def make_text_object(node, idx, context, data):
    txt, matrix = data
    name = f'{node.basedata_name}.{idx:04d}'

    sv_object, f = get_obj_and_fontcurve(context, name)
    font_set_props(f, node, txt)
    sv_object['idx'] = idx
    sv_object['madeby'] = node.name
    sv_object['basedata_name'] = node.basedata_name
    sv_object.hide_select = False
    node.push_custom_matrix_if_present(sv_object, matrix)


class SvFontFileImporterOpV28(bpy.types.Operator):

    bl_idname = "node.sv_fontfile_importer_mk1"
    bl_label = "sv FontFile Importer"

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing the font file",
        maxlen=1024, default="", subtype='FILE_PATH')

    def execute(self, context):
        n = self.node
        t = bpy.data.fonts.load(self.filepath)
        n.fontname = t.name
        return {'FINISHED'}

    def invoke(self, context, event):
        self.node = context.node
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class SvTypeViewerNodeV28(bpy.types.Node, SverchCustomTreeNode, SvObjHelper):

    bl_idname = 'SvTypeViewerNodeV28'
    bl_label = 'Typography Viewer'
    bl_icon = 'OUTLINER_OB_FONT'
    sv_icon = 'SV_TYPOGRAPHY_VIEWER'

    def captured_updateNode(self, context):
        if not self.updating_name_from_pointer:
            font_datablock = self.get_bpy_data_from_name(self.fontname, bpy.data.fonts)
            if font_datablock:
                self.font_pointer = font_datablock
                updateNode(self, context)    

    def pointer_update(self, context):
        self.updating_name_from_pointer = True

        try:
            self.fontname = self.font_pointer.name if self.font_pointer else ""
        except Exception as err:
            self.info(err)

        self.updating_name_from_pointer = False
        updateNode(self, context)

    
    grouping: BoolProperty(default=False, update=SvObjHelper.group_state_update_handler)
    data_kind: StringProperty(name='data kind', default='FONT')

    show_options: BoolProperty(default=0)

    properties_to_skip_iojson = ["font_pointer"]
    updating_name_from_pointer: BoolProperty(name="updating name")
    fontname: StringProperty(default='', update=captured_updateNode)
    font_pointer: PointerProperty(type=bpy.types.VectorFont, poll=lambda s, o: True, update=pointer_update)
    fsize: FloatProperty(default=1.0, update=updateNode)

    # space
    space_character: FloatProperty(default=1.0, update=updateNode)
    space_word: FloatProperty(default=1.0, update=updateNode)
    space_line: FloatProperty(default=1.0, update=updateNode)
    yoffset: FloatProperty(default=0.0, update=updateNode)
    xoffset: FloatProperty(default=0.0, update=updateNode)

    # modifications
    offset: FloatProperty(default=0.0, update=updateNode)
    extrude: FloatProperty(default=0.0, update=updateNode)

    # bevel
    bevel_depth: FloatProperty(default=0.0, update=updateNode)
    bevel_resolution: IntProperty(default=0, update=updateNode)

    # orientation x | y 
    align_x: bpy.props.EnumProperty(
        items=mode_options_x, description="Horizontal Alignment",
        default="LEFT", update=updateNode)

    align_y: bpy.props.EnumProperty(
        items=mode_options_y, description="Vertical Alignment",
        default="TOP_BASELINE", update=updateNode)
    

    def sv_init(self, context):
        self.sv_init_helper_basedata_name()
        self.inputs.new('SvStringsSocket', 'text')
        self.inputs.new('SvMatrixSocket', 'matrix')

    def draw_buttons(self, context, layout):
        self.draw_live_and_outliner(context, layout)
        self.draw_object_buttons(context, layout)

        col = layout.column(align=True)
        if col:
            row = col.row(align=True)
            row.prop(self, "grouping", text="Group", toggle=True)

            col = layout.column(align=True)
            col.prop(self, 'fsize')
            col.prop(self, 'show_options', toggle=True)
            if self.show_options:
                col.label(text='position')
                row = col.row(align=True)
                if row:
                    row.prop(self, 'xoffset', text='XOFF')
                    row.prop(self, 'yoffset', text='YOFF')
                split = col.split()
                col1 = split.column()
                col1.prop(self, 'space_character', text='CH')
                col1.prop(self, 'space_word', text='W')
                col1.prop(self, 'space_line', text='L')

                col.label(text='modifications')
                col.prop(self, 'offset')
                col.prop(self, 'extrude')
                col.label(text='bevel')
                col.prop(self, 'bevel_depth')
                col.prop(self, 'bevel_resolution')

                col.label(text="alignment")
                row = col.row(align=True)
                row.prop(self, 'align_x', text="")
                row.prop(self, 'align_y', text="")
                col.separator()


    def draw_buttons_ext(self, context, layout):
        shf = 'node.sv_fontfile_importer_mk1'

        self.draw_buttons(context, layout)
        self.draw_ext_object_buttons(context, layout)

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop_search(self, 'font_pointer', bpy.data, 'fonts', text='', icon='FONT_DATA')
        row.operator(shf, text='', icon='ZOOM_IN')

        box = col.box()
        if box:
            box.label(text="Beta options")
            box.prop(self, 'layer_choice', text='layer')

        row = layout.row()
        row.prop(self, 'parent_to_empty', text='parented')
        if self.parent_to_empty:
            row.label(self.parent_name)

    def process(self):

        if (not self.activate) or (not self.inputs['text'].is_linked):
            return

        # no autorepeat yet.
        text = self.inputs['text'].sv_get(default=[['sv_text']])[0]
        matrices = self.inputs['matrix'].sv_get(default=[[]])

        with self.sv_throttle_tree_update():
            if self.parent_to_empty:
                mtname = 'Empty_' + self.basedata_name
                self.parent_name = mtname
                
                scene = bpy.context.scene
                collection = scene.collection

                if not mtname in bpy.data.objects:
                    empty = bpy.data.objects.new(mtname, None)
                    collection.objects.link(empty)
                    scene.update()

            last_index = 0
            for obj_index, txt_content in enumerate(text):
                matrix = matrices[obj_index]
                if isinstance(txt_content, list) and (len(txt_content) == 1):
                    txt_content = txt_content[0]
                else:
                    txt_content = str(txt_content)

                make_text_object(self, obj_index, bpy.context, (txt_content, matrix))
                last_index = obj_index

            self.remove_non_updated_objects(last_index)
            objs = self.get_children()

            if self.grouping:
                self.to_collection(objs)

            self.set_corresponding_materials()

            for obj in objs:
                if self.parent_to_empty:
                    obj.parent = bpy.data.objects[mtname]
                elif obj.parent:
                    obj.parent = None

    def draw_label(self):
        return f"TV {self.basedata_name}"


classes = [SvTypeViewerNodeV28, SvFontFileImporterOpV28]
register, unregister = bpy.utils.register_classes_factory(classes)