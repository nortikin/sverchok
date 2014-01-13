import bpy, bmesh, mathutils
from mathutils import Matrix
from util import *
from node_s import *
import webbrowser

class SverchokUpdateAll(bpy.types.Operator):
    """Sverchok update all"""
    bl_idname = "node.sverchok_update_all"
    bl_label = "Sverchok update all"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        makeTreeUpdate()
        speedUpdate()
        return {'FINISHED'}

class SverchokPurgeCache(bpy.types.Operator):
    """Sverchok purge cache"""
    bl_idname = "node.sverchok_purge_cache"
    bl_label = "Sverchok purge cache"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print(bpy.context.space_data.node_tree.name)
        return {'FINISHED'}
    
class SverchokHome(bpy.types.Operator):
    """Sverchok Home"""
    bl_idname = "node.sverchok_home"
    bl_label = "Sverchok go home"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        page = 'http://nikitron.cc.ua/blend_scripts.html'
        if context.scene.use_webbrowser:
            try:
                webbrowser.open_new_tab(page)
            except:
                self.report({'WARNING'}, "Error in opening the page %s." % (page))
        return {'FINISHED'}

class SverchokToolsMenu(bpy.types.Panel):
    bl_idname = "Sverchok_tools_menu"
    bl_label = "Sverchok Tools"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        #layout.scale_y=1.1
        layout.active = True
        box = layout.box()
        box.scale_y=3.0
        
        box.operator(SverchokUpdateAll.bl_idname, text="UPDATE")
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Sverchok v_0.2.7")
        col.label(text='layout: '+bpy.context.space_data.node_tree.name)
        row = col.row(align=True)
        row.operator('wm.url_open', text='Help!').url = 'http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Sverchok'
        row.operator('wm.url_open', text='Home!').url = 'http://nikitron.cc.ua/blend_scripts.html'
        #layout.operator(SverchokHome.bl_idname, text="WWW: Go home")
        row = col.row(align=True)
        row.operator('wm.url_open', text='FBack').url = 'http://www.blenderartists.org/forum/showthread.php?272679-Addon-WIP-Sverchok-parametric-tool-for-architects/'
        row.operator('wm.url_open', text='Bugtr').url = 'https://docs.google.com/forms/d/1L2BIpDhjMgQEbVAc7pEq93432Qanu8UPbINhzJ5SryI/viewform'
        
        


class ToolsNode(Node, SverchCustomTreeNode):
    ''' Tools for different purposes '''
    bl_idname = 'ToolsNode'
    bl_label = 'Tools node'
    bl_icon = 'OUTLINER_OB_EMPTY'
    #bl_height_default = 110
    #bl_width_min = 20
    #color = (1,1,1)
    color_ = bpy.types.ColorRamp
    
    def init(self, context):
        pass
        
    def draw_buttons(self, context, layout):
        col = layout.column()
        col.scale_y=15
        col.template_color_picker
        col.operator(SverchokUpdateAll.bl_idname, text="UPDATE")
        #box = layout.box()
        
        #col = box.column(align=True)
        #col.template_node_socket(color=(0.0, 0.9, 0.7, 1.0))
        #col.operator('wm.url_open', text='Help!').url = 'http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Sverchok'
        #col.operator('wm.url_open', text='Home!').url = 'http://nikitron.cc.ua/blend_scripts.html'
        #layout.operator(SverchokHome.bl_idname, text="WWW: Go home")
        #col.operator('wm.url_open', text='FBack').url = 'http://www.blenderartists.org/forum/showthread.php?272679-Addon-WIP-Sverchok-parametric-tool-for-architects/'
        #col.operator('wm.url_open', text='Bugtr').url = 'https://docs.google.com/forms/d/1L2BIpDhjMgQEbVAc7pEq93432Qanu8UPbINhzJ5SryI/viewform'
        
        lennon = len(bpy.data.node_groups[self.id_data.name].nodes)
        group = self.id_data.name
        tex = str(lennon) + ' | ' + str(group)
        layout.label(text=tex)
        #layout.template_color_ramp(self, 'color_', expand=True)
    
    def update(self):
        self.use_custom_color = True
        self.color = (1.0,0.0,0.0)
        
                
    def update_socket(self, context):
        pass

def register():
    bpy.utils.register_class(SverchokUpdateAll)
    bpy.utils.register_class(SverchokPurgeCache)
    bpy.utils.register_class(SverchokHome)
    bpy.utils.register_class(SverchokToolsMenu)
    bpy.utils.register_class(ToolsNode)
    
def unregister():
    bpy.utils.unregister_class(ToolsNode)
    bpy.utils.unregister_class(SverchokToolsMenu)
    bpy.utils.unregister_class(SverchokHome)
    bpy.utils.unregister_class(SverchokPurgeCache)
    bpy.utils.unregister_class(SverchokUpdateAll)

if __name__ == "__main__":
    register()