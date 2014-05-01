import bpy
import os
from bpy.props import EnumProperty, StringProperty


def get_template_path():
    sv_path = os.path.dirname(os.path.realpath(__file__))
    script_dir = "node_script_templates"
    return os.path.join(sv_path, script_dir)

def get_templates():
    path = get_template_path()
    return [(t, t, "") for t in next(os.walk(path))[2]]


class SvScriptLoader(bpy.types.Operator):

    """ Load Scripts into TextEditor """
    bl_idname = "node.script_template"
    bl_label = "Sverchok script template"
    bl_options = {'REGISTER', 'UNDO'}

    # from object in
    script_path = StringProperty(name='script path')

    def execute(self, context):
        path = get_template_path()
        file_to_load = os.path.join(path, self.script_path)
        bpy.ops.text.open(filepath=file_to_load, internal=True)
        return {'FINISHED'}


class SvTextSubMenu(bpy.types.Menu):
    bl_idname = "TEXT_MT_templates_submenu"
    bl_label = "Sv NodeScripts"
    bl_options = {'REGISTER', 'UNDO'}
    
    def draw(self, context):
        layout = self.layout

        m = get_templates()
        t = "node.script_template"
        for name, p, _ in m:
            layout.operator(t, text=name).script_path = p


def menu_draw(self, context):
    self.layout.menu("TEXT_MT_templates_submenu")


def register():
    bpy.utils.register_class(SvScriptLoader)
    bpy.utils.register_class(SvTextSubMenu)
    bpy.types.TEXT_MT_templates.append(menu_draw)


def unregister():
    bpy.utils.unregister_class(SvScriptLoader)
    bpy.utils.unregister_class(SvTextSubMenu)
    bpy.types.TEXT_MT_templates.remove(menu_draw)

if __name__ == "__main__":
    register()
