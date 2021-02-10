
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy


if FreeCAD is None:
    add_dummy('SvReadFCStdNode', 'SvReadFCStdNode', 'FreeCAD')

else:
    F = FreeCAD
    import bpy
    from bpy.props import StringProperty, BoolProperty, EnumProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode
    from sverchok.utils.logging import info

    class SvReadFCStdNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Read FreeCAD file
        Tooltip: import parts from a .FCStd file 
        """
        bl_idname = 'SvReadFCStdNode'
        bl_label = 'Read FCStd'
        bl_icon = 'IMPORT'
        solid_catergory = "Outputs"

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

            col.prop(self, 'read_update')
            col.prop(self, 'read_body')
            col.prop(self, 'read_part')
            col.prop(self, 'tool_parts')
            if self.tool_parts:
                col.prop(self, 'read_features')
            col.prop(self, 'inv_filter')

        def sv_init(self, context):
            self.inputs.new('SvFilePathSocket', "File Path")
            self.inputs.new('SvStringsSocket', "Part Filter")   


            self.outputs.new('SvSolidSocket', "Solid")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            if not self.inputs['File Path'].is_linked:
                return            

            if self.read_update:
                
                files = self.inputs['File Path'].sv_get()[0]

                part_filter = []
                if self.inputs['Part Filter'].is_linked:
                    part_filter = self.inputs['Part Filter'].sv_get()[0]
                
                if self.selected_part != '' and not self.selected_part in part_filter:
                    part_filter.append(self.selected_part)

                solids = []
                obj_mask = []

                if self.read_features:
                    obj_mask.append('PartDesign')
                if self.read_part:
                    obj_mask.append('Part')
                if self.read_body: 
                    obj_mask.append('PartDesign::Body')

                for f in files:
                    S = LoadSolid(f, part_filter, obj_mask, self.tool_parts, self.inv_filter)

                    for s in S:
                        solids.append(s)
                
                self.outputs['Solid'].sv_set(solids)
            
            else:
                return


    class SvShowFcstdNamesOp(bpy.types.Operator):
        bl_idname = "node.sv_show_fcstd_names"
        bl_label = "Show parts list"
        bl_options = {'INTERNAL', 'REGISTER'}
        bl_property = "option"

        def LabelReader(self,context):
            labels=[('','','')]

            tree = bpy.data.node_groups[self.idtree]
            node = tree.nodes[self.idname]
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
                    F.open(f) 
                    Fname = bpy.path.display_name_from_filepath(f)
                    F.setActiveDocument(Fname)

                    for obj in F.ActiveDocument.Objects:
                        if obj.Module in obj_mask or obj.TypeId in obj_mask:
                            labels.append( (obj.Label, obj.Label, obj.Label) )
                    
                except:
                    info('FCStd label read error')
                finally:
                    F.closeDocument(Fname)

            return labels
            
            
        option : EnumProperty(items=LabelReader)
        idtree : StringProperty()
        idname : StringProperty() 


        def execute(self, context):

            tree = bpy.data.node_groups[self.idtree]
            node = tree.nodes[self.idname]
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
   

def LoadSolid(fc_file,part_filter,obj_mask,tool_parts, inv_filter):
    objs= set()
    outList = set()
    solids = set()
    
    try:    

        F.open(fc_file) 
        Fname = bpy.path.display_name_from_filepath(fc_file)
        F.setActiveDocument(Fname)

        for obj in F.ActiveDocument.Objects:

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
                    solids.add(obj.Shape)

            else:
                if not obj.Label in part_filter:
                    solids.add(obj.Shape)  
                        
    except:
        info('FCStd read error')

    finally:
        F.closeDocument(Fname)

    return solids

def open_fc_file(fc_file):
    F.open(fc_file) 
    Fname = bpy.path.display_name_from_filepath(fc_file)
    F.setActiveDocument(Fname)  

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvReadFCStdNode)
        bpy.utils.register_class(SvShowFcstdNamesOp)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvReadFCStdNode)
        bpy.utils.register_class(SvShowFcstdNamesOp)
