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
        IntProperty,
        )
from bpy.types import (
        Operator,
        OperatorFileListElement,
        )

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.modules import sv_bmesh

class SvFilePathFinder(bpy.types.Operator):
    '''Select Files from browser window'''
    bl_idname = "node.sv_file_path"
    bl_label = "Select Files/Folder"

    idtree: StringProperty(default='')
    idname: StringProperty(default='')
    files: CollectionProperty(
            name="File Path",
            type=OperatorFileListElement,
            )
    directory: StringProperty(
            subtype='DIR_PATH',
            )
    filepath: bpy.props.StringProperty(
        name="File Path", description="Filepath used for writing waveform files",
        maxlen=1024, default="", subtype='FILE_PATH')

    def execute(self, context):
        node = bpy.data.node_groups[self.idtree].nodes[self.idname]
        node.set_data(self.directory, self.files)
        return {'FINISHED'}

    def invoke(self, context, event):
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

    files_num: bpy.props.IntProperty(name='files number ', default=0)

    files: CollectionProperty(
        name="File Path",
        type=OperatorFileListElement,
        )
    directory: StringProperty(
        subtype='DIR_PATH',
        update=updateNode)

    properties_to_skip_iojson = ['files'] 

    def sv_init(self, context):

        self.outputs.new('SvFilePathSocket', "File Path")

    def draw_buttons(self, context, layout):

        op = 'node.sv_file_path'
        self.wrapper_tracked_ui_draw_op(layout, op, icon='FILE', text='')
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

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return
        directory = self.directory
        files = []
        for file_elem in self.files:
            filepath = os.path.join(directory, file_elem.name)
            files.append(filepath)
        self.outputs['File Path'].sv_set([files])

    # iojson stuff

    def storage_set_data(self, storage):
        '''function to get data when importing from json''' 

        strings_json = storage['string_storage']
        filenames = json.loads(strings_json)['filenames']
        directory = json.loads(strings_json)['directory']
        
        self.id_data.freeze(hard=True)
        self.set_data(directory, filenames)
        self.id_data.unfreeze(hard=True)

    def storage_get_data(self, node_dict):
        '''function to set data for exporting json''' 

        local_storage = {
            'filenames': [{"name": file_elem.name} for file_elem in self.files], 
            'directory': self.directory
        }
        node_dict['string_storage'] = json.dumps(local_storage)


classes = [SvFilePathNode, SvFilePathFinder]
register, unregister = bpy.utils.register_classes_factory(classes)
