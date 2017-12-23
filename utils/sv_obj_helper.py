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
from bpy.props import (BoolProperty, StringProperty, FloatProperty, IntProperty, BoolVectorProperty)

from sverchok.data_structure import updateNode

from sverchok.utils.sv_viewer_utils import (
    matrix_sanitizer, natural_plus_one, greek_alphabet)


common_ops = ['object_hide', 'object_hide_select', 'object_hide_render']
CALLBACK_OP = 'node.sv_callback_svobjects_helper'

def get_random_init_v2(node):
    objects = bpy.data.objects

    with_underscore = lambda obj: '_' in obj.name and obj.type == node.data_kind
    names_with_underscores = list(filter(with_underscore, objects))
    print(names_with_underscores)
    set_of_names_pre_underscores = set([n.name.split('_')[0] for n in names_with_underscores])
    if '' in set_of_names_pre_underscores:
        set_of_names_pre_underscores.remove('')

    n = random.choice(greek_alphabet)

    # not picked yet.
    if not n in set_of_names_pre_underscores:
        return n

    # at this point the name was already picked, we don't want to overwrite
    # existing obj/meshes and instead append digits onto the greek letter
    # if Alpha is present already a new one will be Alpha2, Alpha3 etc..
    # (not Alpha002, or Alpha.002)
    similar_names = [name for name in set_of_names_pre_underscores if n in name]
    plus_one = natural_plus_one(similar_names)
    return n + str(plus_one)



class SvObjectsHelperCallback(bpy.types.Operator):

    bl_idname = CALLBACK_OP
    bl_label = "Sverchok objects helper"
    bl_options = {'REGISTER', 'UNDO'}

    fn_name = StringProperty(default='')
    data_kind = StringProperty(default='CURVE')

    def execute(self, context):
        type_op = self.fn_name

        n = context.node
        objs = n.get_children()

        if type_op in {'object_hide', 'object_hide_render', 'object_hide_select', 'object_select'}:
            for obj in objs:
                stripped_op_name = type_op.replace("object_", '')
                setattr(obj, stripped_op_name, getattr(n, type_op))
            setattr(n, type_op, not getattr(n, type_op))

        elif type_op == 'random_basedata_name':   # random_data_name  ?
            n.basedata_name = get_random_init()

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

    def to_group(self, objs):
        groups = bpy.data.groups
        named = self.basedata_name

        # alias group, or generate new group and alias that
        group = groups.get(named)
        if not group:
            group = groups.new(named)

        for obj in objs:
            if obj.name not in group.objects:
                group.objects.link(obj)

    def ensure_parent(self):
        if self.parent_to_empty:
            self.parent_name = 'Empty_' + self.basedata_name
            scene = bpy.context.scene
            if not self.parent_name in bpy.data.objects:
                empty = bpy.data.objects.new(self.parent_name, None)
                scene.objects.link(empty)
                scene.update()        

    def to_parent(self, objs):
        for obj in objs:
            if self.parent_to_empty:
                obj.parent = bpy.data.objects[self.parent_name]
            elif obj.parent:
                obj.parent = None        

    layer_choice = BoolVectorProperty(
        subtype='LAYER', size=20, name="Layer Choice",
        update=layer_updateNode,
        description="This sets which layer objects are placed on",
        get=g, set=s)

    activate = BoolProperty(
        name='Show',
        description="When enabled this will process incoming data",
        default=True,
        update=updateNode)

    basedata_name = StringProperty(
        default='Alpha',
        description="which base name the object an data will use",
        update=updateNode
    )    

    # most importantly, what kind of base data are we making?
    data_kind = StringProperty(default='MESH')

    # to be used if the node has no material input.
    material = StringProperty(default='', update=updateNode)

    # to be used as standard toggles for object attributes of same name
    object_hide = BoolProperty(default=True)
    object_hide_render = BoolProperty(default=True)
    object_select = BoolProperty(default=True)
    object_hide_select = BoolProperty(default=False)    

    show_wire = BoolProperty(update=updateNode)
    use_smooth = BoolProperty(default=True, update=updateNode)

    parent_to_empty = BoolProperty(default=False, update=updateNode)
    parent_name = StringProperty()  # calling updateNode would recurse.    

    def __init__(self):
        ...

    def icons(self, TYPE):
        NAMED_ICON = {
            'object_hide': 'RESTRICT_VIEW',
            'object_hide_select': 'RESTRICT_RENDER',
            'object_hide_render': 'RESTRICT_SELECT'}.get(TYPE)
        if not NAMED_ICON:
            return 'WARNING'
        return NAMED_ICON + ['_ON', '_OFF'][getattr(self, TYPE)]


    def draw_object_buttons(self, context, layout):
        view_icon = 'RESTRICT_VIEW_' + ('OFF' if self.activate else 'ON')

        col = layout.column(align=True)
        row = col.row(align=True)
        row.column().prop(self, "activate", text="LIVE", toggle=True, icon=view_icon)

        for op_name in common_ops: 
            row.operator(CALLBACK_OP, text='', icon=self.icons(op_name)).fn_name = op_name

        col = layout.column(align=True)
        if col:
            row = col.row(align=True)
            row.scale_y = 1
            row.prop(self, "basedata_name", text="", icon=self.bl_icon)

            row = col.row(align=True)
            row.scale_y = 2
            row.operator(CALLBACK_OP, text='Select / Deselect').fn_name = 'object_select'

            row = col.row(align=True)
            row.scale_y = 1
            row.prop_search(
                self, 'material', bpy.data, 'materials', text='', icon='MATERIAL_DATA')
            row.operator(CALLBACK_OP, text='+Material').fn_name = 'add_material'

    def draw_ext_object_buttons(self, context, layout):
        layout.separator()
        row = layout.row(align=True)
        row.operator(CALLBACK_OP, text='Rnd Name').fn_name = 'random_basedata_name'
        row.operator(CALLBACK_OP, text='+Material').fn_name = 'add_material'        

    def set_corresponding_materials(self):
        if bpy.data.materials.get(self.material):
            for obj in self.get_children():
                obj.active_material = bpy.data.materials[self.material]

    def remove_non_updated_objects(self, obj_index):
        objs = self.get_children()
        obj_names = [obj.name for obj in objs if obj['idx'] > obj_index]
        if not obj_names:
            return

        if self.data_kind == 'MESH':
            kinds = bpy.data.meshes
        elif self.data_kind == 'CURVE':
            kinds = bpy.data.curves

        objects = bpy.data.objects
        scene = bpy.context.scene

        # remove excess objects
        for object_name in obj_names:
            obj = objects[object_name]
            obj.hide_select = False
            scene.objects.unlink(obj)
            objects.remove(obj, do_unlink=True)

        # delete associated meshes
        for object_name in obj_names:
            kinds.remove(kinds[object_name])        


    def copy(self, other):
        self.basedata_name = get_random_init_v2(self)


def register():
    bpy.utils.register_class(SvObjectsHelperCallback)


def unregister():
    bpy.utils.unregister_class(SvObjectsHelperCallback)
