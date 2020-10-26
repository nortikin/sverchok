
import bpy
from bpy.props import StringProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.surface.core import SvSurface
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvExportSolidMk2Node', 'Export Solid', 'FreeCAD')
else:

    from FreeCAD import Part

    from sverchok.utils.curve.freecad import curve_to_freecad
    from sverchok.utils.surface.freecad import surface_to_freecad

    def make_solid(ob):
        if isinstance(ob, Part.Shape):
            return ob
        elif isinstance(ob, SvCurve):
            return curve_to_freecad(ob).curve
        elif isinstance(ob, SvSurface):
            return surface_to_freecad(ob, make_face=True).face
        else:
            raise Exception(f"Unknown data type in input: {ob}")

    class SvExportSolidMk2Operator(bpy.types.Operator):

        bl_idname = "node.sv_export_solid_mk2"
        bl_label = "Export Solid"
        bl_options = {'INTERNAL', 'REGISTER'}

        idtree: StringProperty(default='')
        idname: StringProperty(default='')
        input_name : StringProperty(default='')

        def execute(self, context):
            tree = bpy.data.node_groups[self.idtree]
            node = bpy.data.node_groups[self.idtree].nodes[self.idname]

            if not node.inputs['Folder Path'].is_linked:
                self.report({'WARNING'}, "Folder path is not specified")
                return {'FINISHED'}
            if not node.inputs[self.input_name].is_linked:
                self.report({'WARNING'}, "Object to be exported is not specified")
                return {'FINISHED'}

            folder_path = node.inputs[0].sv_get()[0][0]
            objects = node.inputs[self.input_name].sv_get()
            base_name = node.base_name
            if not base_name:
                base_name = "sv_solid"
            for i, object in enumerate(objects):
                solid = make_solid(object)
                file_path = folder_path + base_name + "_"  + "%05d" % i
                if node.mode == "BREP":
                    solid.exportBrep(file_path + ".brp")

                elif node.mode == "IGES":
                    solid.exportIges(file_path + ".igs")
                else:
                    solid.exportStep(file_path + ".stp")

            return {'FINISHED'}

    class SvExportSolidMk2Node(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Export Solid
        Tooltip: Export Solid to BREP, IGES or STEP
        """
        bl_idname = 'SvExportSolidMk2Node'
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

        input_types = [
                ('Solids', "Solids", "Solid objects", 0),
                ('Curves', "Curves", "NURBS-like curves", 1),
                ('Surfaces', "Surfaces", "NURBS-like surfaces", 2)
            ]

        @throttled
        def update_sockets(self, context):
            self.inputs['Solids'].hide_safe = self.input_type != 'Solids'
            self.inputs['Curves'].hide_safe = self.input_type != 'Curves'
            self.inputs['Surfaces'].hide_safe = self.input_type != 'Surfaces'

        input_type : EnumProperty(
                name = "Input type",
                description = "Type of objects to export",
                items = input_types,
                default = input_types[0][0],
                update = update_sockets)

        def draw_buttons(self, context, layout):
            layout.prop(self, "input_type")
            layout.prop(self, "mode")
            layout.prop(self, "base_name")
            op = self.wrapper_tracked_ui_draw_op(layout, SvExportSolidMk2Operator.bl_idname, icon='EXPORT', text="EXPORT")
            op.input_name = self.input_type

        def sv_init(self, context):
            self.inputs.new('SvFilePathSocket', "Folder Path")
            self.inputs.new('SvSolidSocket', "Solids")
            self.inputs.new('SvCurveSocket', "Curves")
            self.inputs.new('SvSurfaceSocket', "Surfaces")
            self.update_sockets(context)

        def process(self):
            pass

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvExportSolidMk2Operator)
        bpy.utils.register_class(SvExportSolidMk2Node)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvExportSolidMk2Node)
        bpy.utils.unregister_class(SvExportSolidMk2Operator)

