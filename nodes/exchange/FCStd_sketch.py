from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy


if FreeCAD is None:
    add_dummy('SvReadFCStdSketchNode', 'SvReadFCStdSketchNode', 'FreeCAD')

else:
    F = FreeCAD
    import bpy
    from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode
    from sverchok.utils.logging import info

    class SvReadFCStdSketchNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Read FreeCAD file
        Tooltip: import parts from a .FCStd file 
        """
        bl_idname = 'SvReadFCStdSketchNode'
        bl_label = 'Read FCStd Sketches'
        bl_icon = 'IMPORT'
        solid_catergory = "Outputs"
        
        max_points : IntProperty(name="max_points", default=50, update = updateNode) 
        read_update : BoolProperty(name="read_update", default=True)
        inv_filter : BoolProperty(name="inv_filter", default=False, update = updateNode)
        selected_label : StringProperty(default='Select FC Part')
        selected_part : StringProperty(default='',update = updateNode) 

        def draw_buttons(self, context, layout):

            col = layout.column(align=True)
            if self.inputs['File Path'].is_linked:
                self.wrapper_tracked_ui_draw_op(
                    col, SvShowFcstdSketchNamesOp.bl_idname, 
                    icon= 'TRIA_DOWN',
                    text= self.selected_label )
                    
            col.prop(self, 'max_points')   
            col.prop(self, 'read_update')   
            col.prop(self, 'inv_filter')

        def sv_init(self, context):
            self.inputs.new('SvFilePathSocket', "File Path")
            self.inputs.new('SvStringsSocket', "Part Filter")   

            self.outputs.new('SvVerticesSocket', "Verts")
            self.outputs.new('SvVerticesSocket', "Edges")

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

                Verts = []
                Edges = []
                for f in files:
                    S = LoadSketch(f,part_filter,self.max_points,self.inv_filter)
                    for v_set in S[0]:
                        Verts.append(v_set)
                    for e_set in S[1]:
                        Edges.append(e_set)
                
                self.outputs['Verts'].sv_set(Verts)
                self.outputs['Edges'].sv_set(Edges)
            
            else:
                return



    class SvShowFcstdSketchNamesOp(bpy.types.Operator):
        bl_idname = "node.sv_show_fcstd_sketch_names"
        bl_label = "Show parts list"
        bl_options = {'INTERNAL', 'REGISTER'}
        bl_property = "option"

        def LabelReader(self,context):
            labels=[('','','')]

            tree = bpy.data.node_groups[self.idtree]
            node = tree.nodes[self.idname]
            fc_file_list = node.inputs['File Path'].sv_get()[0]

            try:

                for f in fc_file_list:
                    F.open(f) 
                    Fname = bpy.path.display_name_from_filepath(f)
                    F.setActiveDocument(Fname)

                    for obj in F.ActiveDocument.Objects:

                        if obj.Module == 'Sketcher':
                            labels.append( (obj.Label, obj.Label, obj.Label) )
                    F.closeDocument(Fname)

            except:
                info('FCStd read error')  
            
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
   

def LoadSketch(fc_file,part_filter,max_points,inv_filter):
    import Part
    sketches = []
    Verts = []
    Edges = []

    try:
        F.open(fc_file) 
        Fname = bpy.path.display_name_from_filepath(fc_file)
        F.setActiveDocument(Fname)
        print (Fname)
        for obj in F.ActiveDocument.Objects:

            if obj.Module == 'Sketcher':
                
                if not inv_filter:

                    if obj.Label in part_filter or len(part_filter)==0:
                        sketches.append(obj)

                else:
                    if not obj.Label in part_filter:
                        sketches.append(obj)

        
        #max_len = max([ g.length() for s in sketches for g in s.Geometry ])
        max_len=set()
        for s in sketches:
            for g in s.Geometry:
                if not isinstance(g, Part.Point ) :
                    max_len.add( g.length() )
        
        max_len=max(max_len)

        for s in sketches:
            
            #get sketch plane
            s_placement = s.Placement

            for geo in s.Geometry:
                v_set=[]
                e_set=[]
                if isinstance(geo, Part.LineSegment ):
                    geo_points = 2

                elif isinstance(geo, Part.Point ):
                    geo_points = 1

                else:
                    geo_points = int (max_points * geo.length() / max_len) + 1
            
                    if geo_points < 2:
                        geo_points = 2

                if geo_points!=1:
                    verts = geo.discretize(Number= geo_points )
                else:
                    verts = [ (geo.X,geo.Y,geo.Z) ]

                for v in verts:
                    v_co = F.Vector( ( v[0], v[1], v[2] ) )
                    
                    v_placement = F.Placement()
                    v_placement.Base = v_co

                    abs_co = s_placement.multiply(v_placement)
                    v_set.append ( ( abs_co.Base.x, abs_co.Base.y, abs_co.Base.z) )
                
                for i in range ( len(v_set)-1 ):
                    e_set.append ( (i,i+1) )

                Verts.append (v_set)
                Edges.append (e_set)


    except:
        info('FCStd read error')

    finally:
        F.closeDocument(Fname)

    return (Verts,Edges)
    
def register():
    bpy.utils.register_class(SvReadFCStdSketchNode)
    bpy.utils.register_class(SvShowFcstdSketchNamesOp)

def unregister():
    bpy.utils.unregister_class(SvReadFCStdSketchNode)
    bpy.utils.register_class(SvShowFcstdSketchNamesOp)