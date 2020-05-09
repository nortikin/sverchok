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

import random
import string

import bmesh
import bpy
from bpy.props import (BoolProperty, StringProperty, FloatProperty, IntProperty, BoolVectorProperty)
from mathutils import Matrix

from sverchok.data_structure import updateNode
from sverchok.utils.sv_viewer_utils import (
    matrix_sanitizer, natural_plus_one, greek_alphabet)

sv_caps = set(string.ascii_uppercase)

def enum_from_list(*item_list):
    """
    usage:   var = enum_from_list('TOP_BASELINE', 'TOP')
    produces:  [('TOP_BASELINE', 'TOP_BASELINE', '', 0), ('TOP', 'TOP', '', 1)]
    """    
    return [(item, item, "", idx) for idx, item in enumerate(item_list)]

def enum_from_list_idx(*item_list):
    """
    usage:   var = enum_from_list_idx('0:TOP_BASELINE', '7:TOP')
    produces:  [('TOP_BASELINE', 'TOP_BASELINE', '', 0), ('TOP', 'TOP', '', 7)]

    """
    return [(n, n, "", int(i)) for i, n in [item.split(':') for item in item_list]]



common_ops = ['object_hide_viewport', 'object_hide_select', 'object_hide_render']
CALLBACK_OP = 'node.sv_callback_svobjects_helper'

def get_random_init_v3():
    """ it's not random """
    idx = bpy.context.scene.SvGreekAlphabet_index
    if idx <= 23:
        name = greek_alphabet[idx]
        bpy.context.scene.SvGreekAlphabet_index += 1
    else:
        name = ''.join(random.sample(sv_caps, 6))

    return name


def tracked_operator(node, layout_element, fn_name='', text='', icon=None):
    """
    this is a wrapper around the layout.operator(CALLBACK_OP....), it allows
    us to track the nodetree and nodename origins of the callback. 

    // Without treename and nodename it's not possible to tell where the button press comes from
    // and now you can just press the button, without first making a node selected or active.

    """
    operator_props = dict(text=text)
    if icon:
        operator_props['icon'] = icon

    button = layout_element.operator(CALLBACK_OP, **operator_props)
    button.fn_name = fn_name
    button.node_name = node.name
    button.tree_name = node.id_data.name    


class SvObjectsHelperCallback(bpy.types.Operator):

    bl_idname = CALLBACK_OP
    bl_label = "Sverchok objects helper"
    bl_options = {'REGISTER', 'UNDO'}

    fn_name: StringProperty(default='')

    # The imformation of "which node this button was pressed on"
    # is not communicated unless you do it explicitely.
    tree_name: StringProperty(default='')
    node_name: StringProperty(default='')

    def execute(self, context):
        type_op = self.fn_name

        if self.tree_name and self.node_name:
            n = bpy.data.node_groups[self.tree_name].nodes[self.node_name]
        else:
            n = context.node

        objs = n.get_children()

        if type_op in {'object_hide_viewport', 'object_hide_render', 'object_hide_select'}:
            for obj in objs:
                stripped_op_name = type_op.replace("object_", '')
                setattr(obj, stripped_op_name, getattr(n, type_op))
            setattr(n, type_op, not getattr(n, type_op))

        elif type_op == "object_select":
            for obj in objs:
                obj.select_set(n.object_select)
            n.object_select = not n.object_select

        elif type_op == 'random_basedata_name':   # random_data_name  ?
            n.basedata_name = get_random_init_v3()

        elif type_op == 'add_material':
            if hasattr(n, type_op):
                # some nodes will define their own add_material..
                getattr(n, type_op)()
            else:
                # this is the simplest automatic material generator.
                mat = bpy.data.materials.new('sv_material')
                mat.use_nodes = True
                n.material = mat.name

        return {'FINISHED'}


class SvObjHelper():

    # hints found at ba.org/forum/showthread.php?290106
    # - this will not allow objects on multiple layers, yet.
    def g(self):
        self['lp'] = self.get('lp', [False] * 20)
        return self['lp']

    def s(self, value):
        val = []
        for b in zip(self['lp'], value):
            val.append(b[0] != b[1])
        self['lp'] = val

    def layer_updateNode(self, context):
        '''will update in place without geometry updates'''
        for obj in self.get_children():
            obj.layers = self.layer_choice[:]

    def get_children(self):
        # criteria: basedata_name must be in object.keys and the value must be self.basedata_name
        objects = bpy.data.objects
        objs = [obj for obj in objects if obj.type == self.data_kind]
        return [o for o in objs if o.get('basedata_name') == self.basedata_name]

    def group_state_update_handler(self, context):
        """
        since this is technically a scene/admin code controlling heirarchy, pressing
        the button should result in assymetric behaviour depending on the new state of
        "self.grouping".

        + - - - + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
        | state | desired behaviour                                             |
        + ----- + --------------------------------------------------------------+
        | True  | add all objects associated with the node to the collection    |
        + ----- + --------------------------------------------------------------+
        | False | remove collection, if present, and association with object    |
        + - - - + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
        """
        if self.grouping:
            updateNode(self, context)
        else:
            with self.sv_throttle_tree_update():
                self.clear_collection()

    def to_collection(self, objs):
        collections = bpy.data.collections
        named = self.custom_collection_name or self.basedata_name

        # alias collection, or generate new collection and alias that
        collection = collections.get(named)
        if not collection:
            collection = collections.new(named)
            bpy.context.scene.collection.children.link(collection)

        for obj in objs:
            if obj.name not in collection.objects:
                collection.objects.link(obj)
            if obj.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(obj)

    def clear_collection(self):
        collections = bpy.data.collections
        named = self.custom_collection_name or self.basedata_name

        # alias collection, or generate new collection and alias that
        collection = collections.get(named)
        if not collection:
            """ seems the collection is already gone, this is a no op """
            return
        else:
            for obj in collection.objects:
                bpy.context.scene.collection.objects.link(obj)
            collections.remove(collection)

    def ensure_parent(self):
        if self.parent_to_empty:
            self.parent_name = 'Empty_' + self.basedata_name
            collection = bpy.context.scene.collection
            scene = bpy.context.scene
            if not self.parent_name in bpy.data.objects:
                empty = bpy.data.objects.new(self.parent_name, None)
                collection.objects.link(empty)
                scene.update()        

    def to_parent(self, objs):
        for obj in objs:
            if self.parent_to_empty:
                obj.parent = bpy.data.objects[self.parent_name]
            elif obj.parent:
                obj.parent = None        

    layer_choice: BoolVectorProperty(
        subtype='LAYER', size=20, name="Layer Choice",
        update=layer_updateNode,
        description="This sets which layer objects are placed on",
        get=g, set=s)

    activate: BoolProperty(
        name='activate',
        description="When enabled this will process incoming data",
        default=True,
        update=updateNode)

    basedata_name: StringProperty(
        name='basedata name',
        default='Alpha',
        description="which base name the object and data will use",
        update=updateNode
    )    

    # most importantly, what kind of base data are we making?
    data_kind: StringProperty(name='data kind', default='MESH')

    # to be used if the node has no material input.
    material: StringProperty(name='material', default='')
    material_pointer: bpy.props.PointerProperty(type=bpy.types.Material, poll=lambda s, o: True, update=updateNode)

    # to be used as standard toggles for object attributes of same name
    object_hide_viewport: BoolProperty(name='object hide viewport', default=True)
    object_hide_render: BoolProperty(name='object hide render', default=True)
    object_hide_select: BoolProperty(name='object hide select', default=False)

    object_select: BoolProperty(name='object select', default=True)

    show_wire: BoolProperty(name='show wire', update=updateNode)
    use_smooth: BoolProperty(name='use smooth', default=True, update=updateNode)

    parent_to_empty: BoolProperty(name='parent to empty', default=False, update=updateNode)
    parent_name: StringProperty(name='parent name')  # calling updateNode would recurse.    
    
    custom_collection_name: StringProperty(
        name='collection name', update=updateNode,
        description='custom collection name, will default to the basename of the node first')

    def sv_init_helper_basedata_name(self):
        """ 
        this is to be used in sv_init, at the top
        """
        dname = get_random_init_v3()
        self.basedata_name = dname
        self.use_custom_color = True        


    def icons(self, TYPE):
        NAMED_ICON = {
            'object_hide_viewport': 'RESTRICT_VIEW',
            'object_hide_render': 'RESTRICT_RENDER',
            'object_hide_select': 'RESTRICT_SELECT'}.get(TYPE)
        if not NAMED_ICON:
            return 'ERROR'
        return NAMED_ICON + ['_ON', '_OFF'][getattr(self, TYPE)]

    def draw_live_and_outliner(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.column().prop(self, "activate", text="LIVE", toggle=True)

        for op_name in common_ops: 
            tracked_operator(self, row, fn_name=op_name, icon=self.icons(op_name))

    def draw_object_buttons(self, context, layout):

        col = layout.column(align=True)
        if col:
            row = col.row(align=True)
            row.scale_y = 1
            row.prop(self, "basedata_name", text="", icon=self.bl_icon)

            row = col.row(align=True)
            row.scale_y = 2
            tracked_operator(self, row, fn_name='object_select', text='Select / Deselect')

            row = col.row(align=True)
            row.scale_y = 1
            row.prop_search(self, 'material', bpy.data, 'materials', text='', icon='MATERIAL_DATA')
            tracked_operator(self, row, fn_name='add_material', icon="ZOOM_IN")

    def draw_ext_object_buttons(self, context, layout):
        layout.separator()
        row = layout.row(align=True)
        tracked_operator(self, row, fn_name='random_basedata_name', text='Rnd Name')
        tracked_operator(self, row, fn_name='add_material', text='+Material', icon="ZOOM_IN")

    def set_corresponding_materials(self):
        if bpy.data.materials.get(self.material.strip()):
            for obj in self.get_children():
                obj.active_material = bpy.data.materials[self.material.strip()]

    def remove_non_updated_objects(self, obj_index):
        objs = self.get_children()
        obj_names = [obj.name for obj in objs if obj['idx'] > obj_index]
        if not obj_names:
            return

        if self.data_kind == 'MESH':
            kinds = bpy.data.meshes
        elif self.data_kind == 'CURVE':
            kinds = bpy.data.curves
        elif self.data_kind == 'META':
            kinds = bpy.data.metaballs

        objects = bpy.data.objects
        collection = bpy.context.scene.collection

        if hasattr(self, "grouping") and self.grouping:
            # if a node employs "grouping" it must also provide
            # - self.custom_collection_name (even if not directly used)
            # - self.basedata_name
            named = self.custom_collection_name or self.basedata_name
            collection = bpy.data.collections.get(named)

        # remove excess objects
        for object_name in obj_names:
            obj = objects[object_name]
            obj.hide_select = False
            collection.objects.unlink(obj)
            objects.remove(obj, do_unlink=True)

        # delete associated meshes/curves etc
        for object_name in obj_names:
            kinds.remove(kinds[object_name])        

    def create_object(self, object_name, obj_index, data):
        """
        Create a new object and link it into collection.
        """
        obj = bpy.data.objects.new(object_name, data)
        obj['basedata_name'] = self.basedata_name
        obj['madeby'] = self.name
        obj['idx'] = obj_index
        bpy.context.scene.collection.objects.link(obj)
        return obj

    def get_or_create_object(self, object_name, obj_index, data):
        """
        Return existing Object or create new one.
        : if object reference exists, pick it up else make a new one
        """
        obj = bpy.data.objects.get(object_name)
        if not obj:
            obj = self.create_object(object_name, obj_index, data)
        return obj

    def get_obj_curve(self, obj_index):
        curves = bpy.data.curves
        objects = bpy.data.objects
        collection = bpy.context.scene.collection

        curve_name = f'{self.basedata_name}.{obj_index:04d}'

        # if curve data exists, pick it up else make new curve
        cu = curves.get(curve_name)
        if not cu:
            cu = curves.new(name=curve_name, type='CURVE')
        obj = self.get_or_create_object(curve_name, obj_index, cu)

        # break down existing splines entirely.
        if cu.splines:
            cu.splines.clear()

        return obj, cu


    def clear_current_mesh(self, data):
        bm = bmesh.new()
        bm.to_mesh(data)
        bm.free()
        data.update()

    def get_alphabet(self):
        return greek_alphabet


    def push_custom_matrix_if_present(self, sv_object, matrix):
        if matrix:
            # matrix = matrix_sanitizer(matrix)    
            sv_object.matrix_local = matrix
        else:
            sv_object.matrix_local = Matrix.Identity(4)    


def register():
    bpy.utils.register_class(SvObjectsHelperCallback)


def unregister():
    bpy.utils.unregister_class(SvObjectsHelperCallback)
