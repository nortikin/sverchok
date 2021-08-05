# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import StringProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import flatten_data, map_recursive
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.logging import debug
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvExportSolidNode', 'Export Solid', 'FreeCAD')
else:

    from FreeCAD import Part
    try:
        import Part as PartModule
    except ImportError:
        PartModule = Part

    from sverchok.utils.solid import to_solid

    class SvExportSolidOperator(bpy.types.Operator, SvGenericNodeLocator):

        bl_idname = "node.sv_export_solid_mk2"
        bl_label = "Export Solid"
        bl_options = {'INTERNAL', 'REGISTER'}

        def execute(self, context):
            node = self.get_node(context)
            if not node: return {'CANCELLED'}

            if not node.inputs['Folder Path'].is_linked:
                self.report({'WARNING'}, "Folder path is not specified")
                return {'FINISHED'}
            if not node.inputs['Solids'].is_linked:
                self.report({'WARNING'}, "Object to be exported is not specified")
                return {'FINISHED'}

            folder_path = node.inputs[0].sv_get()[0][0]
            objects = node.inputs['Solids'].sv_get()
            #objects = flatten_data(objects, data_types=(PartModule.Shape, SvCurve, SvSurface))
            base_name = node.base_name
            if not base_name:
                base_name = "sv_solid"
            for i, shape in enumerate(objects):
                #shape = map_recursive(to_solid, object, data_types=(PartModule.Shape, SvCurve, SvSurface))
                debug("Exporting", shape)
                if isinstance(shape, (list, tuple)):
                    shape = flatten_data(shape, data_types=(PartModule.Shape,))
                if isinstance(shape, (list,tuple)):
                    debug("Make compound:", shape)
                    shape = PartModule.Compound(shape)
                file_path = folder_path + base_name + "_"  + "%05d" % i

                if node.mode == "BREP":
                    file_path += ".brp"
                    shape.exportBrep(file_path)
                elif node.mode == "IGES":
                    file_path += ".igs"
                    shape.exportIges(file_path)
                else:
                    file_path += ".stp"
                    shape.exportStep(file_path)
                self.report({'INFO'}, f"Saved object #{i} to {file_path}")

            return {'FINISHED'}

    class SvExportSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Export Solid
        Tooltip: Export Solid to BREP, IGES or STEP
        """
        bl_idname = 'SvExportSolidNode'
        bl_label = 'Export Solid'
        bl_icon = 'EXPORT'
        solid_catergory = "Outputs"
        # sv_icon = 'SV_VORONOI'

        file_types = [
                ("BREP", "BREP", "", 0),
                ("IGES", "IGES", "", 1),
                ("STEP", "STEP", "", 2),
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
            )

        def draw_buttons(self, context, layout):
            layout.prop(self, "mode")
            layout.prop(self, "base_name")
            self.wrapper_tracked_ui_draw_op(layout, SvExportSolidOperator.bl_idname, icon='EXPORT', text="EXPORT")

        def sv_init(self, context):
            self.inputs.new('SvFilePathSocket', "Folder Path")
            self.inputs.new('SvSolidSocket', "Solids")

        def process(self):
            pass

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvExportSolidOperator)
        bpy.utils.register_class(SvExportSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvExportSolidNode)
        bpy.utils.unregister_class(SvExportSolidOperator)

