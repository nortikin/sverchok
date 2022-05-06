# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import os
import json

import bpy
import bmesh
from bpy.props import (
        StringProperty,
        CollectionProperty,
        IntProperty, EnumProperty
        )
from bpy.types import (
        Operator,
        OperatorFileListElement,
        )

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.modules import sv_bmesh
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator


class SvFilePathFinder(bpy.types.Operator, SvGenericNodeLocator):
    '''Select Files from browser window'''
    bl_idname = "node.sv_file_path"
    bl_label = "Select Files/Folder"

    files: CollectionProperty(name="File Path", type=OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')

    filepath: StringProperty(
        name="File Path", description="Filepath used for writing files",
        maxlen=1024, default="", subtype='FILE_PATH')

    filename_ext: StringProperty(default="")
    filter_glob: StringProperty(default="")    


    def custom_config(self, context):
        if self.mode == "FreeCAD":
            self.filename_ext = ".FCStd"  #  ".tif"
            self.filter_glob = "*.FCStd"  # #*.tif;*.png;"  (if more than one, separate by ;)
        else:
            self.filename_ext = ''
            self.filter_glob = ''

    # mode: StringProperty(default='')
    behaviours = ["FreeCAD", "None"]
    mode: EnumProperty(items=[(i, i, '') for i in behaviours], update=custom_config)

    def sv_execute(self, context, node):
        if self.mode == "FreeCAD":
            # This is triggered after the file is selected or typed in by the user in the Text Field of path
            if self.directory and len(self.files) == 1:
                if self.files[0].name and not self.files[0].name.endswith(".FCStd"):
                    self.files[0].name = self.files[0].name + ".FCStd" 

        node.set_data(self.directory, self.files)

    def invoke(self, context, event):
        
        if self.mode: self.custom_config(context)

        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class SvFilePathNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: OS file path
    Tooltip:  get path file from OS
    """

    bl_idname = "SvFilePathNode"
    bl_label = "File Path"
    bl_icon = "FILE"

    files_num: IntProperty(name='files number ', default=0)
    files: CollectionProperty(name="File Path", type=OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH', update=updateNode)
    mode: StringProperty(default='', description="mode determines behaviour of the File Open Dialogue and Operator")

    def sv_init(self, context):

        self.outputs.new('SvFilePathSocket', "File Path")

    def draw_buttons(self, context, layout):

        op = 'node.sv_file_path'
        file_path_operator = self.wrapper_tracked_ui_draw_op(layout, op, icon='FILE', text='')
        file_path_operator.mode = self.mode

        if self.files_num == 0:
            layout.label(text=self.directory)
        elif self.files_num == 1:
            layout.label(text=self.files[0].name)
        else:
            layout.label(text="%d files at %s" % (len(self.files), self.directory))

    def set_data(self, dirname, files):

        self.files.clear()
        for file_elem in files:

            item = self.files.add()
            for k, v in file_elem.items():
                item[k] = v
        self.directory = dirname
        if len(files) == 1 and not files[0].name:
            self.files_num = 0
        else:
            self.files_num = len(files)

    def get_linked_socket_mode_and_set_operator(self):
        """
        only call this mode if the output(s) .is_linked returns true
        """
        socket = self.outputs[0]
        self.mode = ""
        if socket.is_linked:
            other_socket = socket.other
            if hasattr(other_socket, "filepath_node_mode"):
                self.mode = other_socket.filepath_node_mode

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        self.get_linked_socket_mode_and_set_operator()

        directory = self.directory
        if self.files:
            files = []
            for file_elem in self.files:
                filepath = os.path.join(directory, file_elem.name)
                files.append(filepath)
            self.outputs['File Path'].sv_set([files])
        else:
            self.outputs['File Path'].sv_set([[self.directory]])

    # iojson stuff

    def load_from_json(self, node_dict: dict, import_version: float):
        '''function to get data when importing from json''' 

        if import_version <= 0.08:
            strings_json = node_dict['string_storage']
            filenames = json.loads(strings_json)['filenames']
            directory = json.loads(strings_json)['directory']

            self.set_data(directory, filenames)


classes = [SvFilePathNode, SvFilePathFinder]
register, unregister = bpy.utils.register_classes_factory(classes)
