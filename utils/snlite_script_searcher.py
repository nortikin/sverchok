# snlite_script_searcher.py

# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import os
import sverchok

loop = dict()
script_lookup = dict()

def gather_items(context):

    sv_dir = os.path.dirname(sverchok.__file__) 
    script_dir = os.path.join(sv_dir, "node_scripts","SNLite_templates")
    
    values = []
    idx = 0
    for category in os.scandir(script_dir):
        if category.is_dir():
            for script in os.scandir(category.path):
                if script.is_file():
                    script_lookup[str(idx)] = script.path
                    values.append((str(idx), f"{script.name} | {category.name}", ''))
                    idx += 1
    return values

def item_cb(self, context):
    return loop.get('results') or [("A","A", '', 0),]


class SvSnliteScriptSearch(bpy.types.Operator):
    """ SNLite Search Script Library """
    bl_idname = "node.sv_snlite_script_search"
    bl_label = "SN lite Script Search"
    bl_property = "my_enum"

    my_enum: bpy.props.EnumProperty(items=item_cb)

    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        if tree_type in {'SverchCustomTreeType', }:
            return True

    def execute(self, context):
        if self.my_enum.isnumeric():
            print(script_lookup[self.my_enum])
            pass

        return {'FINISHED'}

    def invoke(self, context, event):
        # context.space_data.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
        
        if not loop.get('results'):
            loop['results'] = gather_items(context)
        
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


classes = [SvSnliteScriptSearch]
register, unregister = bpy.utils.register_classes_factory(classes)
