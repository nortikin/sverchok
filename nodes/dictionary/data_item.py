# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from collections import defaultdict

import bpy
from bpy.types import Operator, Node, PropertyGroup
from bpy.props import StringProperty, EnumProperty, IntProperty, BoolProperty, FloatProperty, CollectionProperty, PointerProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode
from sverchok.utils.dictionary import SvDict
from sverchok.utils.logging import info, debug

ANY = '__SV_ANY_KEY__'

class SvStringItem(bpy.types.PropertyGroup):
    string : StringProperty()

class SvDictKeyEntry(bpy.types.PropertyGroup):
    def update_key(self, context):
        if hasattr(context, 'node'):
            context.node.update_sockets_throttled(context)
            #updateNode(context.node, context)
        else:
            info("Node is not defined in this context, so will not update the node.")
    
    def get_items(self, context):
        items = []
        for k in self.known_keys:
            if k.string == ANY:
                item = (ANY, "All keys", "Any key")
            else:
                item = (k.string, k.string, k.string)
            items.append(item)
        return items

    def set_known_keys(self, keys):
        self.known_keys.clear()
        for k in keys:
            item = self.known_keys.add()
            item.string = k

    known_keys : CollectionProperty(type=SvStringItem)

    key : EnumProperty(name = "Key",
            items = get_items,
            update = update_key)

class UI_UL_SvDictKeyList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        row = layout.row(align=True)
        row.prop(item, 'key', text='')

class SvDataItemNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: data dictionary item
    Tooltip: Select data items from nested dictionary
    """

    bl_idname = 'SvDataItemNode'
    bl_label = "Data Items"
    bl_icon = 'MATERIAL'

    keys : CollectionProperty(type=SvDictKeyEntry)
    selected : IntProperty()

    def draw_buttons(self, context, layout):
        #layout.template_list("UI_UL_SvDictKeyList", "keys", self, "keys", self, "selected")
        for i in range(len(self.keys)):
            layout.prop(self.keys[i], 'key', text='')

    def get_data(self):
        ds = self.inputs['Data'].sv_get()
        result = []
        for d in ds:
            if not isinstance(d, SvDict):
                d = SvDict(d)
            result.append(d)
        return result

    def update_keys(self, context):
        if not self.inputs['Data'].links:
            return
        d = self.get_data()[0]
        count = d.get_max_nesting_level() + 1
        existing = len(self.keys)
        dc = count - existing
        print("C", count, existing, dc)
        if dc > 0:
            for i in range(dc):
                k = self.keys.add()
        else:
            for i in range(-dc):
                n = len(self.keys)
                self.keys.remove(n-1)

        for i, k in enumerate(self.keys):
            keys = [ANY] + list(d.get_nested_keys_at(i))
            k.set_known_keys(keys)

    def sv_update(self):
        self.update_keys(None)
        self.update_sockets(None)
    
    @throttled
    def update_sockets_throttled(self, context):
        self.update_sockets(context)

    def update_sockets(self, context):
        if not self.inputs['Data'].links:
            return

        dict_keys = [k.key for k in self.keys]
        print("D", dict_keys)
        empty = [i for i, k in enumerate(self.keys) if k.key == ANY]
        if len(empty) == 0:
            show_item = True
        elif len(empty) == 1:
            show_item = False
        else:
            raise Exception("Not more than one key can be unset")
        
        d = self.get_data()[0]
        #n_existing = len(self.outputs)
        links = {sock.name: [link.to_socket for link in sock.links] for sock in self.outputs}
        self.outputs.clear()

        new_socks = []
        if show_item:
            sock = self.outputs.new('SvStringsSocket', "Item")
            new_socks.append(sock)

        if len(empty) == 1:
            for key, data in d.get_nested_inputs_at(empty[0]).items():
                sock = self.outputs.new(data['type'], data['name'])
                new_socks.append(sock)

        [self.id_data.links.new(sock, other_socket) for sock in new_socks if sock.name in links
                                                    for other_socket in links[sock.name]]

    def sv_init(self, context):
        self.inputs.new('SvDictionarySocket', 'Data')
        #self.outputs.new('SvDictionarySocket', "Data")
        #self.outputs.new('SvStringsSocket', "Item")

    def get_item(self, data, keys):
        key = keys[0]
        value = data[key]
        if len(keys) == 1:
            return value
        elif len(keys) > 1 and not isinstance(value, dict):
            return None
        else:
            sub_keys = keys[1:]
            return self.get_item(value, sub_keys)

    def get_dict(self, data, keys, level):
        possible_keys = data.get_nested_keys_at(level)
        print("P", possible_keys)
        result = {}
        for key in possible_keys:
            keys_option = [str(k) for k in keys]
            keys_option[level] = key
            value = self.get_item(data, keys_option)
            print("Option", keys_option, value)
            result[key] = value
        return result

    def process(self):
        if not self.inputs['Data'].links:
            return

        self.update_keys(None)
        if not self.keys:
            return
        #self.update_sockets(None)

        data = self.get_data()
        outputs = defaultdict(list)
        for data_dict in data:
            dict_keys = [k.key for k in self.keys]
            empty = [i for i, key in enumerate(dict_keys) if key == ANY]
            if not empty:
                value = self.get_item(data_dict, dict_keys)
                outputs[0].append(value)
            elif len(empty) == 1:
                values = self.get_dict(data_dict, dict_keys, empty[0])
                for key, value in values.items():
                    outputs[key].append(value)

        for i, values in outputs.items():
            self.outputs[i].sv_set([values])

classes = [SvStringItem, SvDictKeyEntry, UI_UL_SvDictKeyList, SvDataItemNode]

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in classes: bpy.utils.unregister_class(cls)

