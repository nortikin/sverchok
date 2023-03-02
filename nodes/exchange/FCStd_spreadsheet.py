import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_logging import sv_logger
from sverchok.dependencies import FreeCAD
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator

if FreeCAD is not None:
    F = FreeCAD


class SvFCStdSpreadsheetOperator(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_fcstd_spreadsheet_operator"
    bl_label = "read/write freecad spreadsheet"
    bl_options = {'INTERNAL', 'REGISTER'}

    def execute(self, context):
        node = self.get_node(context)

        if not node: return {'CANCELLED'}

        node.edit_spreadsheet(node)
        updateNode(node,context)

        return {'FINISHED'}


class SvFCStdSpreadsheetNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Read FreeCAD file
    Tooltip: Read/write FCStd Spreadsheets from a .FCStd file
    """
    bl_idname = 'SvFCStdSpreadsheetNode'
    bl_label = 'Read/write Spreadsheets'
    bl_icon = 'IMPORT'
    sv_category = "Solid Outputs"
    sv_dependencies = {'FreeCAD'}

    auto_update : BoolProperty(name="auto_update", default=True)
    write_update : BoolProperty(name="read_update", default=True)
    write_parameter : BoolProperty(name="write_parameter", default=False)

    selected_label : StringProperty(default='Spreadsheet')
    selected_sheet : StringProperty(default='',update = updateNode)

    selected_par_label : StringProperty(default='Parameter')
    selected_par : StringProperty(default='',update = updateNode)

    cell_in : FloatProperty( name="cell_in", description='cell_in', default=0.0 )

    def draw_buttons(self, context, layout):

        col = layout.column(align=True)
        if self.inputs['File Path'].is_linked:
            self.wrapper_tracked_ui_draw_op(
                col, SvShowFcstdSpreadsheetsOp.bl_idname,
                icon= 'TRIA_DOWN',
                text= self.selected_label )


        if self.inputs['File Path'].is_linked:
            self.wrapper_tracked_ui_draw_op(
                col, SvShowFcstdParNamesOp.bl_idname,
                icon= 'TRIA_DOWN',
                text= self.selected_par_label )

        col.prop(self, 'auto_update')
        col.prop(self, 'write_parameter')
        self.wrapper_tracked_ui_draw_op(layout, SvFCStdSpreadsheetOperator.bl_idname, icon='FILE_REFRESH', text="UPDATE")

    def sv_init(self, context):
        self.inputs.new('SvFilePathSocket', "File Path")
        self.inputs.new('SvStringsSocket', "cell_in").prop_name = 'cell_in'

        self.outputs.new('SvStringsSocket', "cell_out")

    def edit_spreadsheet(self,node):

        if not node.inputs['File Path'].is_linked:
            return

        if node.selected_par != '' :

            files = node.inputs['File Path'].sv_get()[0]

            cell_out=None

            for f in files:
                cell_out = WriteParameter(
                    f,
                    node.selected_sheet,
                    node.selected_par,
                    node.inputs['cell_in'].sv_get()[0][0],
                    node.write_parameter)

            if cell_out != None:

                node.outputs['cell_out'].sv_set( [[cell_out]] )

        else:
            node.outputs['cell_out'].sv_set( [ ] )
            return

    def process(self):
        if self.auto_update:
            self.edit_spreadsheet(self)


class SvShowFcstdSpreadsheetsOp(bpy.types.Operator, SvGenericNodeLocator):
    bl_idname = "node.sv_show_fcstd_spreadsheets"
    bl_label = "Show spreadsheet list"
    bl_options = {'INTERNAL', 'REGISTER'}
    bl_property = "option"

    def LabelReader(self,context):
        labels=[('','','')]

        tree = bpy.data.node_groups[self.tree_name]
        node = tree.nodes[self.node_name]
        fc_file_list = node.inputs['File Path'].sv_get()[0]

        try:
            for f in fc_file_list:
                F.open(f)
                Fname = bpy.path.display_name_from_filepath(f)
                F.setActiveDocument(Fname)

                for obj in F.ActiveDocument.Objects:
                    if obj.Module == 'Spreadsheet':
                        labels.append( (obj.Label, obj.Label, obj.Label) )

        except:
            sv_logger.info('LabelReader Spreadsheet error')
        finally:
            F.closeDocument(Fname)

        return labels

    option : EnumProperty(items=LabelReader)
    tree_name : StringProperty()
    node_name : StringProperty()

    def execute(self, context):

        tree = bpy.data.node_groups[self.tree_name]
        node = tree.nodes[self.node_name]
        node.name_filter = self.option
        node.selected_label = self.option
        node.selected_sheet = self.option
        bpy.context.area.tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.space_data.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


class SvShowFcstdParNamesOp(bpy.types.Operator, SvGenericNodeLocator):
    bl_idname = "node.sv_show_fcstd_par_names"
    bl_label = "Show parameter list"
    bl_options = {'INTERNAL', 'REGISTER'}
    bl_property = "option"

    def LabelReader(self,context):
        labels=[('','','')]

        tree = bpy.data.node_groups[self.tree_name]
        node = tree.nodes[self.node_name]
        fc_file_list = node.inputs['File Path'].sv_get()[0]

        try:

            for f in fc_file_list:
                F.open(f)
                Fname = bpy.path.display_name_from_filepath(f)
                F.setActiveDocument(Fname)

                for obj in F.ActiveDocument.Objects:

                    if obj.Label == node.selected_sheet:
                        props = obj.PropertiesList
                        for label in props:
                            alias = obj.getCellFromAlias(label)
                            if alias:
                                labels.append( (label, label, label) )

        except:
            sv_logger.info('Label reader read cell error')

        finally:
            F.closeDocument(Fname)

        return labels

    option : EnumProperty(items=LabelReader)
    tree_name : StringProperty()
    node_name : StringProperty()

    def execute(self, context):

        tree = bpy.data.node_groups[self.tree_name]
        node = tree.nodes[self.node_name]
        node.name_filter = self.option
        node.selected_par_label = self.option
        node.selected_par = self.option
        bpy.context.area.tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.space_data.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


def WriteParameter(fc_file,spreadsheet,alias,par_write,write):

    #___________________GET FC FILE

    try:
        F.open(fc_file) 
        Fname = bpy.path.display_name_from_filepath(fc_file)
        F.setActiveDocument(Fname)
        
        #___________________SEARCH FOR SKETCHES
        cell_out = None

        for obj in F.ActiveDocument.Objects:

            if obj.Label == spreadsheet:

                if alias in obj.PropertiesList:
                    cell = obj.getCellFromAlias(alias)
                    if write:
                        obj.set(cell,str(par_write))
                        F.ActiveDocument.recompute()
                        F.getDocument(Fname).save()
                    
                    cell_out = obj.get(cell)
                    break
    
    except:
        sv_logger.info('WriteParameter error')

    finally:
        F.closeDocument(Fname)

    return cell_out


def register():
    bpy.utils.register_class(SvFCStdSpreadsheetNode)
    bpy.utils.register_class(SvShowFcstdSpreadsheetsOp)
    bpy.utils.register_class(SvShowFcstdParNamesOp)
    bpy.utils.register_class(SvFCStdSpreadsheetOperator)


def unregister():
    bpy.utils.unregister_class(SvFCStdSpreadsheetNode)
    bpy.utils.unregister_class(SvShowFcstdSpreadsheetsOp)
    bpy.utils.unregister_class(SvShowFcstdParNamesOp)
    bpy.utils.unregister_class(SvFCStdSpreadsheetOperator)
