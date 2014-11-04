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
from bpy.props import StringProperty, CollectionProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode


# global variables in tools
from sverchok.utils import sv_panels_tools 

class Sv3DPanel(bpy.types.Panel):
    ''' Panel to manipuplate parameters in sverchok layouts '''

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Sverchok " + sv_panels_tools.sv_version_local
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = 'SV'

    def draw(self, context):
        layout = self.layout
        little_width = 0.12
        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = 2.0
        row.operator('node.sv_scan_propertyes', text='Scan for props')
        row.operator("node.sverchok_update_all", text="Update all")
        row = col.row(align=True)
        row.prop(context.scene, 'sv_do_clear', text='hard clean', toggle=True)
        delley = row.operator(
            'node.sv_delete_nodelayouts',
            text='Clean layouts').do_clear = context.scene.sv_do_clear

        for tree in bpy.data.node_groups:
            if tree.bl_idname == 'SverchCustomTreeType':
                box = layout.box()
                col = box.column(align=True)
                row = col.row(align=True)

                split = row.column(align=True)
                split.scale_x = little_width
                icoco = 'DOWNARROW_HLT' if tree.SvShowIn3D else 'RIGHTARROW'
                split.prop(tree, 'SvShowIn3D', icon=icoco, emboss=False, text=' ')

                split = row.column(align=True)
                split.label(text=tree.name)

                # bakery
                split = row.column(align=True)
                split.scale_x = little_width
                baka = split.operator('node.sverchok_bake_all', text='B')
                baka.node_tree_name = tree.name

                #eye
                split = row.column(align=True)
                split.scale_x = little_width
                if tree.sv_show:
                    split.prop(tree, 'sv_show', icon='RESTRICT_VIEW_OFF', text=' ')
                else:
                    split.prop(tree, 'sv_show', icon='RESTRICT_VIEW_ON', text=' ')
                split = row.column(align=True)
                split.scale_x = little_width
                #if tree.sv_animate:
                split.prop(tree, 'sv_animate', icon='ANIM', text=' ')
                #else:
                #    split.prop(tree, 'sv_animate', icon='LOCKED', text=' ')
                
                split = row.column(align=True)
                split.scale_x = little_width
                split.prop(tree, "sv_process", toggle=True, text="P")
                
                split = row.column(align=True)
                split.scale_x = little_width
                split.prop(tree, 'use_fake_user', toggle=True, text='F')

                # veriables
                if tree.SvShowIn3D:
                    for item in tree.Sv3DProps:
                        no = item.node_name
                        ver = item.prop_name
                        node = tree.nodes[no]
                        if node.label:
                            tex = node.label
                        else:
                            tex = no
                        if node.bl_idname == "ObjectsNode":
                            row = col.row(align=True)
                            row.label(text=node.label if node.label else no)
                            colo = row.row(align=True)
                            colo.scale_x = little_width*5
                            op = colo.operator("node.sverchok_object_insertion", text="Get")
                            op.node_name = node.name
                            op.tree_name = tree.name
                            op.grup_name = node.groupname
                            op.sort = node.sort
                        elif node.bl_idname in {"IntegerNode", "FloatNode"}:
                            row = col.row(align=True)
                            row.prop(node, ver, text=tex)
                            colo = row.row(align=True)
                            colo.scale_x = little_width*2.5
                            colo.prop(node, 'minim', text='', slider=True, emboss=False)
                            colo.prop(node, 'maxim', text='', slider=True, emboss=False)


class SverchokToolsMenu(bpy.types.Panel):
    bl_idname = "Sverchok_tools_menu"
    bl_label = "SV "+sv_panels_tools.sv_version_local
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'
    use_pin = True

    @classmethod
    def poll(cls, context):
        try:
            return context.space_data.node_tree.bl_idname == 'SverchCustomTreeType'
        except:
            return False

    def draw(self, context):
        ng_name = context.space_data.node_tree.name
        layout = self.layout
        #layout.scale_y=1.1
        layout.active = True
        row = layout.row(align=True)
        col = row.column(align=True)
        col.scale_y = 3.0
        col.scale_x = 0.5
        u = "Update all"
        col.operator("node.sverchok_update_all", text=u)
        col = row.column(align=True)
        col.scale_y = 3.0
        u = "Update {0}".format(ng_name)
        op = col.operator("node.sverchok_update_current", text=u)
        op.node_group = ng_name
        box = layout.box()
        little_width = 0.12
        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text='Layout')
        col0 = row.column(align=True)
        col0.scale_x = little_width
        col0.label(text='B')
        col1 = row.column(align=True)
        col1.scale_x = little_width
        col1.label(icon='RESTRICT_VIEW_OFF', text=' ')
        col2 = row.column(align=True)
        col2.scale_x = little_width
        col2.label(icon='ANIM', text=' ')
        
        col3 = row.column(align=True)
        col3.scale_x = little_width
        col3.label(text='P')
        
        col3 = row.column(align=True)
        col3.scale_x = little_width
        col3.label(text='F')
            

        for name, tree in bpy.data.node_groups.items():
            if tree.bl_idname == 'SverchCustomTreeType':

                row = col.row(align=True)
                # tree name
                if name == ng_name:
                    row.label(text=name)
                else:
                    row.operator('node.sv_switch_layout', text=name).layout_name = name

                # bakery
                split = row.column(align=True)
                split.scale_x = little_width
                baka = split.operator('node.sverchok_bake_all', text='B')
                baka.node_tree_name = name

                # eye
                split = row.column(align=True)
                split.scale_x = little_width
                view_icon = 'RESTRICT_VIEW_' + ('OFF' if tree.sv_show else 'ON')
                split.prop(tree, 'sv_show', icon=view_icon, text=' ')

                split = row.column(align=True)
                split.scale_x = little_width
                #animate_icon = ('UN' if tree.sv_animate else '') + 'LOCKED'
                split.prop(tree, 'sv_animate', icon='ANIM', text=' ')

                split = row.column(align=True)
                split.scale_x = little_width
                split.prop(tree, "sv_process", toggle=True, text="P")

                split = row.column(align=True)
                split.scale_x = little_width
                split.prop(tree, 'use_fake_user', toggle=True, text='F')

        if context.scene.sv_new_version:
            row = layout.row()
            row.alert = True
            row.operator(
                "node.sverchok_update_addon", text='Upgrade Sverchok addon')
        else:
            layout.row().operator(
                "node.sverchok_check_for_upgrades", text='Check for new version')
        #       row.prop(tree, 'sv_bake',text=' ')
            
        
sv_tools_classes = [
    SverchokToolsMenu,
    Sv3DPanel,
]


def register():
    bpy.types.SverchCustomTreeType.SvShowIn3D = BoolProperty(name='show in panel',default=True, \
            description='Show properties in 3d panel or not')
    for class_name in sv_tools_classes:
        bpy.utils.register_class(class_name)

def unregister():
    # cargo cult to unregister in reverse order? I don't think this is needed.
    # maybe it was handy at some point?
    for class_name in reversed(sv_tools_classes):
        bpy.utils.unregister_class(class_name)

if __name__ == '__main__':
    register()
