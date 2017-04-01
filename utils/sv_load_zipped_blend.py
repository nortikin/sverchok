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

import os
import urllib
import urllib.request
from zipfile import ZipFile

import bpy
import tempfile

class SvLoadZippedBlendURL(bpy.types.Operator):

    bl_idname = "node.sv_load_zipped_blend_url"
    bl_label = "Load URL (zipped blend)"

    # "https://github.com/nortikin/sverchok/files/647412/scipy_voroi_2016_12_12_22_27.zip"
    download_url = bpy.props.StringProperty()
    os_temp_path = tempfile.gettempdir()

    def execute(self, context):

        wm = bpy.data.window_managers[0]
        wm.progress_begin(0, 100)
        wm.progress_update(20)

        if not self.download_url:
            clipboard = context.window_manager.clipboard
            if not clipboard:
                self.report({'ERROR'}, "Clipboard empty")
                return {'CANCELLED'}
            else:
                self.download_url = clipboard

        try:
            file_and_ext = os.path.basename(self.download_url)
            to_path = os.path.join(self.os_temp_path, file_and_ext)
            file = urllib.request.urlretrieve(self.download_url, to_path)
            wm.progress_update(50)
        except Exception as fullerr:
            print(repr(fullerr))
            self.report({'ERROR'}, "Cannot get archive from Internet")
            wm.progress_end()
            return {'CANCELLED'}

        try:
            err = 0
            with ZipFile(to_path) as zf:
                inner_files = zf.namelist()
                if len(inner_files) == 1:
                    blendfile = inner_files[0]
                else:
                    print('cancelled, not a github zipped .blend')
                    return {'CANCELLED'}

            ZipFile(file[0]).extractall(path=self.os_temp_path, members=None, pwd=None)

            wm.progress_update(90)
            err = 1
            os.remove(file[0])
            err = 2
            wm.progress_update(100)
            wm.progress_end()
            
            fp = os.path.join(self.os_temp_path, blendfile)
            bpy.ops.wm.open_mainfile(filepath=fp)
            
        except:
            self.report({'ERROR'}, "Cannot extract files errno {0}".format(str(err)))
            wm.progress_end()
            os.remove(file[0])
            return {'CANCELLED'}

        return {'FINISHED'}


class SvLoadZippedBlendDialog(bpy.types.Operator):
    bl_idname = "node.sv_load_zipped_blend_dialog"
    bl_label = "Load Zipped (Sverchok Dialog)"

    def draw(self, context):
        row = self.layout.row()
        row.label(context.window_manager.clipboard or "No url in clipboard")

    def execute(self, context):
        return bpy.ops.node.sv_load_zipped_blend_url(download_url=context.window_manager.clipboard)
 
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


classes = [
    SvLoadZippedBlendURL,
    SvLoadZippedBlendDialog
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes[::-1]:
        bpy.utils.unregister_class(cls)
