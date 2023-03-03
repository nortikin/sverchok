import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_logging import sv_logger
from sverchok.dependencies import FreeCAD
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator

if FreeCAD is not None:
    F = FreeCAD


class SvReadFCStdOperator(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_read_fcstd_operator"
    bl_label = "read freecad file"
    bl_options = {'INTERNAL', 'REGISTER'}

    def execute(self, context):
        node = self.get_node(context)

        if not node: return {'CANCELLED'}

        if not any(socket.is_linked for socket in node.outputs):
            return {'CANCELLED'}
        if not node.inputs['File Path'].is_linked:
            return {'CANCELLED'}

        node.read_FCStd(node)
        updateNode(node,context)

        return {'FINISHED'}


class SvReadFCStdNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Read FreeCAD file
    Tooltip: import parts from a .FCStd file
    """
    bl_idname = 'SvReadFCStdNode'
    bl_label = 'Read FCStd'
    bl_icon = 'IMPORT'
    sv_category = "Solid Outputs"
    sv_dependencies = {'FreeCAD'}

    read_update : BoolProperty(name="read_update", default=True)
    read_body : BoolProperty(name="read_body", default=True, update = updateNode)
    read_part : BoolProperty(name="read_part", default=True, update = updateNode)

    tool_parts : BoolProperty(name="tool_parts", default=False, update = updateNode)
    read_features : BoolProperty(name="read_features", default=False, update = updateNode)

    inv_filter : BoolProperty(name="inv_filter", default=False, update = updateNode)

    selected_label : StringProperty( default= 'Select FC Part')
    selected_part : StringProperty( default='', update = updateNode)

    def draw_buttons(self, context, layout):

        col = layout.column(align=True)
        if self.inputs['File Path'].is_linked:
            self.wrapper_tracked_ui_draw_op(
                col, SvShowFcstdNamesOp.bl_idname,
                icon= 'TRIA_DOWN',
                text= self.selected_label )
        col.prop(self, 'read_update', text = 'global update')
        col.prop(self, 'read_body')
        col.prop(self, 'read_part')
        col.prop(self, 'tool_parts')
        if self.tool_parts:
            col.prop(self, 'read_features')
        col.prop(self, 'inv_filter')
        self.wrapper_tracked_ui_draw_op(layout, SvReadFCStdOperator.bl_idname, icon='FILE_REFRESH', text="UPDATE")

    def sv_init(self, context):

        self.inputs.new('SvFilePathSocket', "File Path")
        self.inputs.new('SvStringsSocket', "Part Filter")
        self.outputs.new('SvSolidSocket', "Solid")
        self.outputs.new('SvTextSocket', "Names")

    def ensure_name_socket_exists(self):
        if not "Names" in self.outputs:
            self.outputs.new('SvTextSocket', "Names")

    def read_FCStd(self, node):

        files = node.inputs['File Path'].sv_get()[0]

        part_filter = []
        if node.inputs['Part Filter'].is_linked:
            part_filter = node.inputs['Part Filter'].sv_get()[0]

        if node.selected_part != '' and not node.selected_part in part_filter:
            part_filter.append(node.selected_part)

        solids = []
        obj_mask = []
        names = []

        if node.read_features:
            obj_mask.append('PartDesign')
        if node.read_part:
            obj_mask.append('Part')
        if node.read_body:
            obj_mask.append('PartDesign::Body')

        for f in files:
            S = LoadSolid(f, part_filter, obj_mask, node.tool_parts, node.inv_filter)

            for s, n in S:
                solids.append(s)
                names.append(list(n))

        node.outputs['Solid'].sv_set(solids)
        self.ensure_name_socket_exists()
        node.outputs['Names'].sv_set(names)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        if not self.inputs['File Path'].is_linked:
            return

        if self.read_update:
            self.read_FCStd(self)
        else:
            return


class SvShowFcstdNamesOp(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_show_fcstd_names"
    bl_label = "Show parts list"
    bl_options = {'INTERNAL', 'REGISTER'}
    bl_property = "option"

    def LabelReader(self,context):
        labels=[('','','')]

        tree = bpy.data.node_groups[self.tree_name]
        node = tree.nodes[self.node_name]
        fc_file_list = node.inputs['File Path'].sv_get()[0]

        obj_mask = []
        if  node.read_features:
            obj_mask.append('PartDesign')
        if  node.read_part:
            obj_mask.append('Part')
        if  node.read_body:
            obj_mask.append('PartDesign::Body')

        for f in fc_file_list:
            try:
                doc = F.open(f)
                Fname = doc.Name or bpy.path.display_name_from_filepath(f)

                for obj in doc.Objects:
                    if obj.Module in obj_mask or obj.TypeId in obj_mask:
                        labels.append( (obj.Label, obj.Label, obj.Label) )

            except Exception as err:
                sv_logger.info(f'FCStd label read error: {Fname=}')
                sv_logger.info(err)
            finally:
                # del doc
                F.closeDocument(doc.Name)

        return labels

    option : EnumProperty(items=LabelReader)
    tree_name : StringProperty()
    node_name : StringProperty()

    def execute(self, context):

        tree = bpy.data.node_groups[self.tree_name]
        node = tree.nodes[self.node_name]
        node.name_filter = self.option
        node.selected_label = self.option
        node.selected_part = self.option
        bpy.context.area.tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.space_data.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


def LoadSolid(fc_file, part_filter, obj_mask, tool_parts, inv_filter):
    objs= set()
    outList = set()
    solids = set()

    try:

        doc = F.open(fc_file)
        Fname = doc.Name or bpy.path.display_name_from_filepath(fc_file)

        for obj in doc.Objects:

            if obj.Module in obj_mask or obj.TypeId in obj_mask:
                objs.add (obj)

            if not tool_parts and obj.TypeId in ( 'Part::Cut','Part::Fuse','Part::MultiCommon','Part::Section','Part::FeaturePython' ):
                if len(obj.OutList) > 0:
                    for out_obj in obj.OutList:
                        outList.add (out_obj)

        objs = objs - outList

        for obj in objs:

            if not inv_filter:
                if obj.Label in part_filter or len(part_filter)==0:
                    solids.add((obj.Shape, (obj.FullName, obj.Name, obj.Label)))

            else:
                if not obj.Label in part_filter:
                    solids.add((obj.Shape, (obj.FullName, obj.Name, obj.Label)))

    except:
        sv_logger.info('FCStd read error')
    finally:
        # del doc
        F.closeDocument(doc.Name)

    return solids


def register():
    bpy.utils.register_class(SvReadFCStdNode)
    bpy.utils.register_class(SvShowFcstdNamesOp)
    bpy.utils.register_class(SvReadFCStdOperator)


def unregister():
    bpy.utils.unregister_class(SvReadFCStdNode)
    bpy.utils.unregister_class(SvShowFcstdNamesOp)
    bpy.utils.unregister_class(SvReadFCStdOperator)
