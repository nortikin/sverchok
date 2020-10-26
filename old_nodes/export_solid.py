
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvExportSolidNode', 'Export Solid', 'FreeCAD')
else:
    import bpy
    from bpy.props import StringProperty, EnumProperty
    from sverchok.node_tree import SverchCustomTreeNode

    class SvExportSolidOperator(bpy.types.Operator):

        bl_idname = "node.sv_export_solid"
        bl_label = "Export Solid"

        idtree: bpy.props.StringProperty(default='')
        idname: bpy.props.StringProperty(default='')

        def execute(self, context):
            tree = bpy.data.node_groups[self.idtree]
            node = bpy.data.node_groups[self.idtree].nodes[self.idname]

            if not all(s.is_linked for s in node.inputs):
                return {'FINISHED'}
            folder_path = node.inputs[0].sv_get()[0][0]
            solids = node.inputs[1].sv_get()
            base_name = node.base_name
            if not base_name:
                base_name = "sv_solid"
            for i, solid in enumerate(solids):
                file_path = folder_path + base_name + "_"  + "%05d" % i
                if node.mode == "BREP":
                    solid.exportBrep(file_path + ".brp")

                elif node.mode == "IGES":
                    solid.exportIges(file_path + ".igs")
                else:
                    solid.exportStep(file_path + ".stp")

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
        mode_items = [
        ("BREP", "BREP", "", 0),
        ("IGES", "IGES", "", 1),
        ("STEP", "STEP", "", 2),
        ]
        mode: EnumProperty(
            name="Mode",
            description="Choose file type",
            items=mode_items,
            default="BREP",
            )
        base_name: StringProperty(
            name="Base Name",
            description="Name of file",
            )

        def draw_buttons(self, context, layout):
            layout.prop(self, "mode")
            layout.prop(self, "base_name")
            self.wrapper_tracked_ui_draw_op(layout, "node.sv_export_solid", icon='EXPORT', text="EXPORT")


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
