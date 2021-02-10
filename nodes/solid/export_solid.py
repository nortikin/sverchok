
import bpy
from bpy.props import StringProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import flatten_data, map_recursive
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.logging import debug
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvExportSolidNode', 'Export Solid', 'FreeCAD')
else:

    from FreeCAD import Part

    from sverchok.utils.solid import to_solid

    class SvExportSolidOperator(bpy.types.Operator):

        bl_idname = "node.sv_export_solid_mk2"
        bl_label = "Export Solid"
        bl_options = {'INTERNAL', 'REGISTER'}

        idtree: StringProperty(default='')
        idname: StringProperty(default='')

        def execute(self, context):
            tree = bpy.data.node_groups[self.idtree]
            node = bpy.data.node_groups[self.idtree].nodes[self.idname]

            if not node.inputs['Folder Path'].is_linked:
                self.report({'WARNING'}, "Folder path is not specified")
                return {'FINISHED'}
            if not node.inputs['Solids'].is_linked:
                self.report({'WARNING'}, "Object to be exported is not specified")
                return {'FINISHED'}

            folder_path = node.inputs[0].sv_get()[0][0]
            objects = node.inputs['Solids'].sv_get()
            #objects = flatten_data(objects, data_types=(Part.Shape, SvCurve, SvSurface))
            base_name = node.base_name
            if not base_name:
                base_name = "sv_solid"
            for i, shape in enumerate(objects):
                #shape = map_recursive(to_solid, object, data_types=(Part.Shape, SvCurve, SvSurface))
                debug("Exporting", shape)
                if isinstance(shape, (list, tuple)):
                    shape = flatten_data(shape, data_types=(Part.Shape,))
                if isinstance(shape, (list,tuple)):
                    debug("Make compound:", shape)
                    shape = Part.Compound(shape)
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

