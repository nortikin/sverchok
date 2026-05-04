# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import StringProperty, EnumProperty, FloatProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.utils.sv_logging import sv_logger
from sverchok.utils.ifc import IFC_export
import os
import uuid
from datetime import datetime
import math
import numpy as np


class SvExportIFCOperator(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_export_ifc"
    bl_label = "Export IFC"
    bl_options = {'INTERNAL', 'REGISTER'}

    def execute(self, context):
        node = self.get_node(context)

        if not node: 
            self.report({'ERROR'}, "Node not found")
            return {'CANCELLED'}
        mode = node.mode
        base_name = node.base_name
        max_faces = node.max_faces
        area_threshold = node.area_threshold

        if not node.inputs['File_Path'].is_linked:
            self.report({'WARNING'}, "Folder path is not specified")
            return {'FINISHED'}
        if not node.inputs['Vertices'].is_linked and not node.inputs['Polygons'].is_linked:
            self.report({'WARNING'}, "Object to be exported is not specified")
            return {'FINISHED'}
        try:
            vers = node.inputs['Vertices'].sv_get()
            pols = node.inputs['Polygons'].sv_get()
            file_path = node.inputs['File_Path'].sv_get()[0][0]
            ifc = IFC_export(vers, pols, node, mode, file_path, base_name, max_faces, area_threshold)
            ifc.prepare(context)

            self.report({'INFO'}, f"Saved objects to {file_path}")

            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            sv_logger.error(f"IFC export error: {e}")
            return {'CANCELLED'}


class SvExportIfcNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Export IFC
    Tooltip: Export IFC file
    """
    bl_idname = 'SvExportIfcNode'
    bl_label = 'Export IFC'
    bl_icon = 'EXPORT'
    sv_category = "Solid Outputs"

    file_types = [
            ("BREP", "BREP", "", 0),
            ("MESH", "MESH", "", 1),
        ]

    mode: EnumProperty(
        name="File Type",
        description="Choose file type",
        items=file_types,
        default="BREP",
        )

    base_name: StringProperty(
        name="Base Name",
        description="Name of file",
        default='Sverchok_object'
        )

    area_threshold: FloatProperty(
        name="Area Threshold",
        description="Too small polygons will not pass",
        default=0.00001
        )

    max_faces: IntProperty(
        name="Max Faces Count",
        description="Maximum faces and vertices in output file",
        default=2000000
        )

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")
        layout.prop(self, "base_name")
        #print(SvExportIFCOperator.bl_idname)
        row = layout.row()
        if self.prefs_over_sized_buttons:
            row.scale_y = 4.0
        self.wrapper_tracked_ui_draw_op(row, "node.sv_export_ifc", icon='EXPORT', text="EXPORT") #SvExportIFCOperator.bl_idname

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "max_faces")
        layout.prop(self, "area_threshold")

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Polygons')
        self.inputs.new('SvFilePathSocket', "File_Path")

    def process(self):
        pass


def register():
    bpy.utils.register_class(SvExportIFCOperator)
    bpy.utils.register_class(SvExportIfcNode)


def unregister():
    bpy.utils.unregister_class(SvExportIfcNode)
    bpy.utils.unregister_class(SvExportIFCOperator)
