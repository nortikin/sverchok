import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.logging import info
from sverchok.dependencies import FreeCAD
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator

if FreeCAD is not None:
    # june '22
    # modified version of FCStd_read includes changes by rastart, zeffii, et al
    # please feed changes back to the Sverchok issue tracker.
    F = FreeCAD


class SvReadFCStdModOperator(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_read_fcstd_operator_mod"
    bl_label = "read freecad file"
    bl_options = {'INTERNAL', 'REGISTER'}

    def sv_execute(self, context, node):

        if not any(socket.is_linked for socket in node.outputs):
            return {'CANCELLED'}
        if not node.inputs['File Path'].is_linked:
            return {'CANCELLED'}

        node.read_FCStd(node)
        updateNode(node, context)
        return {'FINISHED'}


def LabelReader(operator):
    tree = bpy.data.node_groups[operator.tree_name]
    node = tree.nodes[operator.node_name]

    module_filter = []

    # \/ does not appear to be available from the items= func
    # node = self.get_node(context)
    #
    if node.read_features: module_filter.append('PartDesign')
    if node.read_part: module_filter.append('Part')
    if node.read_body: module_filter.append('PartDesign::Body')
    if node.merge_linked: module_filter.append('App::Link')

    labels = [('', '', '')]

    fc_file_list = node.inputs['File Path'].sv_get()[0]
    for fc_file in fc_file_list:
        try:
            doc = F.open(fc_file)
            for obj in doc.Objects:
                if obj.Module in module_filter or obj.TypeId in module_filter:
                    labels.append( (obj.Label, obj.Label, obj.Label) )
        except:
            info('FCStd label read error')
        finally:
            #del doc
            F.closeDocument(doc.Name)

    return labels


class SvShowFcstdNamesModOp(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_show_fcstd_names_mod"
    bl_label = "Show parts list"
    bl_options = {'INTERNAL', 'REGISTER'}
    bl_property = "option"

    option: EnumProperty(items=lambda s, c: LabelReader(s))

    def sv_execute(self, context, node):
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


class SvReadFCStdModNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Read FreeCAD file mod
    Tooltip: import parts from a .FCStd file
    """
    bl_idname = 'SvReadFCStdModNode'
    bl_label = 'Read FCStd MOD'
    bl_icon = 'IMPORT'
    sv_category = "Solid Outputs"
    sv_dependencies = {'FreeCAD'}

    read_update : BoolProperty(name="read_update", default=True)
    read_body : BoolProperty(name="read_body", default=True, update=updateNode)
    read_part : BoolProperty(name="read_part", default=True, update=updateNode)

    tool_parts : BoolProperty(name="tool_parts", default=False, update=updateNode)
    read_features : BoolProperty(name="read_features", default=False, update=updateNode)
    inv_filter : BoolProperty(name="inv_filter", default=False, update=updateNode)
    scale_factor : FloatProperty(name="unit factor", default=1, update=updateNode)
    selected_label : StringProperty( default= 'Select FC Part')
    selected_part : StringProperty( default='', update=updateNode)
    merge_linked : BoolProperty(name="merge_linked", default=False, update=updateNode)
    READ_ALL : BoolProperty(name="read all", default=False, update=updateNode)

    def draw_buttons(self, context, layout):

        col = layout.column(align=True)
        if self.inputs['File Path'].is_linked:
            self.wrapper_tracked_ui_draw_op(
                col, "node.sv_show_fcstd_names_mod",
                icon= 'TRIA_DOWN',
                text= self.selected_label )

        col.prop(self, 'read_update', text='global update')
        col.prop(self, 'read_body')
        col.prop(self, 'read_part')
        col.prop(self, 'tool_parts')
        if self.tool_parts:
            col.prop(self, 'read_features')
        col.prop(self, 'inv_filter')
        col.prop(self, 'merge_linked')
        col.prop(self,'READ_ALL')
        col.prop(self, 'scale_factor')
        self.wrapper_tracked_ui_draw_op(layout, "node.sv_read_fcstd_operator_mod", icon='FILE_REFRESH', text="UPDATE")

    def sv_init(self, context):

        self.inputs.new('SvFilePathSocket', "File Path")
        self.inputs.new('SvStringsSocket', "Label1 Filter")
        self.inputs.new('SvStringsSocket', "Label2 Filter")
        self.outputs.new('SvSolidSocket', "Solid")
        self.outputs.new('SvTextSocket', "Names")

    def read_FCStd(self, node):

        files = node.inputs['File Path'].sv_get()[0]

        label_1_filter = []
        label_2_filter = []
        label_1_tags = []
        label_2_tags = []

        if (L1_Filter := node.inputs['Label1 Filter']).is_linked:
            raw_filter = L1_Filter.sv_get()[0]

            if len(raw_filter) == 1 and ',' in raw_filter[0]:
                raw_filter = raw_filter[0].split(',')

            for i in raw_filter:
                label_1_tags.append(i) if '#' in i else label_1_filter.append(i)

        if (L2_Filter := node.inputs['Label2 Filter']).is_linked:
            raw_filter = L2_Filter.sv_get()[0]

            if len(raw_filter) == 1 and ',' in raw_filter[0]:
                raw_filter = raw_filter[0].split(',')

            for i in raw_filter:
                label_2_tags.append(i) if '#' in i else label_2_filter.append(i)

        #ADD TO LABEL 1 FILTER THE DROPDOWN ENTRY IF SELECTED
        if node.selected_part != '' and not node.selected_part in label_1_filter:
            label_1_filter.append(node.selected_part)

        solids = []
        identifiers = []
        module_filter = []

        if node.read_features: module_filter.append('PartDesign')
        if node.read_part: module_filter.append('Part')
        if node.read_body: module_filter.append('PartDesign::Body')

        for fname in files:
            S = LoadSolid(
                self.scale_factor, fname,
                label_1_filter, label_1_tags, label_2_filter, label_2_tags,
                module_filter, node.tool_parts,
                node.inv_filter, self.READ_ALL, self.merge_linked )

            for s, ident in S:
                solids.append(s)
                identifiers.append(ident)

        node.outputs['Solid'].sv_set(solids)
        node.outputs['Names'].sv_set(identifiers)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        if not self.inputs['File Path'].is_linked:
            return

        if self.read_update:
            self.read_FCStd(self)
        else:
            return


def LoadSolid(
    scale_factor, fc_file,
    label_1_filter, label_1_tags, label_2_filter, label_2_tags,
    module_filter, tool_parts,
    inv_filter, READ_ALL, merge_linked):

    objs = set()
    sel_objs = set()
    outList = set()
    solids = set()

    try:

        doc = F.open(fc_file)

        #PRE-FILTER FREECAD ENTITY BY TYPE_ID

        #AVOID REIMPORT COMPOUND CHILDS
        #for obj in F.ActiveDocument.Objects:
            #if obj.TypeId == 'Part::Compound':
                #for child in obj.Links:
                    #outList.add(child)

        if merge_linked: module_filter.append('App::Link')

        for obj in doc.Objects:
            #print ('START',obj)
            '''
            if merge_linked and obj.TypeId == 'App::Link':

                if obj.LinkedObject.Module in ('Part', 'PartDesign'):
                    if len(obj.LinkedObject.Shape.Solids)>0:
                        try:
                            shapeobj = F.ActiveDocument.addObject(obj.LinkedObject.TypeId, obj.LinkedObject.Name + '_' + obj.Name )
                            M=F.Matrix();M.scale(1, 1, 1)#M.scale(scale_factor, scale_factor, scale_factor)
                            new_shape = obj.LinkedObject.Shape.transformGeometry(M)
                            new_shape.Placement = obj.Placement
                            shapeobj.Shape = new_shape
                            obj = shapeobj
                        except:
                            print ('ERROR',obj)
            '''
            if obj.Module in module_filter or obj.TypeId in module_filter:
                objs.add (obj)


            elif not tool_parts and obj.TypeId in ( 'Part::Cut','Part::Fuse','Part::MultiCommon','Part::Section','Part::FeaturePython' ):  
                if len(obj.OutList) > 0:
                    for out_obj in obj.OutList:
                        outList.add (out_obj)

        objs = objs - outList
        #SEARCH FOR TAGGED ITEM
        if len(label_1_tags)>0:
            for tag in label_1_tags:
                for obj in objs:
                    if tag[1:] in obj.Label:
                        label_1_filter.append(obj.Label)

        if len(label_2_tags)>0:
            for tag in label_2_tags:
                for obj in objs:
                    if tag[1:] in obj.Label2:
                        label_2_filter.append(obj.Label2)


        for obj in objs:

            if READ_ALL: 
                sel_objs.add( obj )

            elif len(label_1_filter)>0:
                if obj.Label in label_1_filter:

                    if len(label_2_filter)>0:
                        if obj.Label2 in label_2_filter:
                            sel_objs.add(obj)

                    else:
                        sel_objs.add(obj)

            elif len(label_1_filter)==0 and len(label_2_filter)>0:
                if obj.Label2 in label_2_filter: sel_objs.add(obj)



        if inv_filter:
            sel_objs = objs - sel_objs

        for obj in sel_objs:
            '''
            if obj.TypeId == 'App::Link':
                M=F.Matrix(); M.scale(scale_factor, scale_factor, scale_factor)
                new_shape = obj.LinkedObject.Shape.transformGeometry(M)
                new_shape.Placement = obj.Placement
                solids.add( new_shape ) 
            ''' 
            obj_info = obj.FullName, obj.Name, obj.Label
            if scale_factor != 1:
                if len(obj.Shape.Solids) > 0:
                    M = F.Matrix()
                    M.scale(scale_factor, scale_factor, scale_factor)
                    solids.add(( obj.Shape.transformGeometry(M), obj_info ))
            else:
                solids.add(( obj.Shape, obj_info ))

    except Exception as err:
        info(f"FCStd read error {err}")

    finally:
        #del doc
        F.closeDocument(doc.Name)

    return solids

def unitCheck(solid, scale_factor):
    if len(solid.Solids) > 0:
        M = F.Matrix()
        M.scale(scale_factor, scale_factor, scale_factor)
        return solid.transformGeometry(M)
    else:
        return solid


def register():
    bpy.utils.register_class(SvReadFCStdModNode)
    bpy.utils.register_class(SvShowFcstdNamesModOp)
    bpy.utils.register_class(SvReadFCStdModOperator)


def unregister():
    bpy.utils.unregister_class(SvReadFCStdModOperator)
    bpy.utils.unregister_class(SvShowFcstdNamesModOp)
    bpy.utils.unregister_class(SvReadFCStdModNode)
