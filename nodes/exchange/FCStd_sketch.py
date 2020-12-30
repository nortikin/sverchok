from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy


if FreeCAD is None:
    add_dummy('SvReadFCStdSketchNode', 'SvReadFCStdSketchNode', 'FreeCAD')

else:
    F = FreeCAD
    import bpy
    import numpy as np
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
            self.outputs.new('SvCurveSocket', "Curve")

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
                curves_out = []
                for f in files:
                    S = LoadSketch(f,part_filter,self.max_points,self.inv_filter)
                    for i in S[0]:
                        Verts.append(i)
                    for i in S[1]:
                        Edges.append(i)
                    for i in S[2]:
                        curves_out.append(i)                
                self.outputs['Verts'].sv_set([Verts])
                self.outputs['Edges'].sv_set([Edges])
                self.outputs['Curve'].sv_set(curves_out)
            
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
    Curves = []

    #___________________GET FC FILE
    try:
        F.open(fc_file) 
        Fname = bpy.path.display_name_from_filepath(fc_file)
        F.setActiveDocument(Fname)

    except:
        info('FCStd read error')
        return (Verts,Edges,Curves)
    
    #___________________SEARCH FOR SKETCHES

    for obj in F.ActiveDocument.Objects:

        if obj.Module == 'Sketcher':
            
            if not inv_filter:

                if obj.Label in part_filter or len(part_filter)==0:
                    sketches.append(obj)

            else:
                if not obj.Label in part_filter:
                    sketches.append(obj)

    if len(sketches)==0: 
        return (Verts,Edges)

    #__ search for max single perimeter in sketches geometry
    #__ (to use as resampling reference)

    max_len=set()
    for s in sketches:
        for g in s.Geometry:
            if not isinstance(g, Part.Point ) :
                max_len.add( g.length() )
    
    max_len=max(max_len)

    #___________________CONVERT SKETCHES GEOMETRY

    for s in sketches:
        
        #get sketch plane placement to local - global conversion
        s_placement = s.Placement
        if len(s.InList) > 0:
            s_placement = s.InList[0].Placement.multiply( s_placement )

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
                verts = geo.discretize(Number = geo_points )
            else:
                verts = [ (geo.X,geo.Y,geo.Z) ]

            for v in verts:
                v_co = F.Vector( ( v[0], v[1], v[2] ) )

                abs_co = FreeCAD_abs_placement(s_placement,v_co).Base
                v_set.append ( (abs_co.x, abs_co.y, abs_co.z) )

            for i in range ( len(v_set)-1 ):
                v_count = len(Verts)
                e_set.append ( (v_count+i,v_count+i+1) )

            Verts.extend (v_set)
            Edges.extend (e_set)

            if isinstance(geo, Part.LineSegment ):
                from sverchok.utils.curve import SvLine
                point1 = np.array(v_set[0])
                direction = np.array(v_set[1]) - point1
                line = SvLine(point1, direction)
                line.u_bounds = (0, 1)
                Curves.append(line)

            elif isinstance(geo, Part.Circle ) or isinstance(geo, Part.ArcOfCircle ):
                from sverchok.utils.curve import SvCircle
                from mathutils import Matrix
                
                center = F.Vector( (geo.Location.x,geo.Location.y,geo.Location.z) )

                c_placement = FreeCAD_abs_placement(s_placement,center)

                placement_mat = c_placement.toMatrix() 
                b_mat = Matrix()
                
                r=0; c=0
                for i in placement_mat.A:
                    if c == 4: 
                        r+=1; c=0
                        
                    b_mat[r][c]=i
                    c+=1

                curve = SvCircle(matrix=b_mat, radius=geo.Radius)
                if isinstance(geo, Part.ArcOfCircle ):
                    curve.u_bounds = (geo.FirstParameter, geo.LastParameter)

                Curves.append(curve)


    F.closeDocument(Fname)
    return (Verts,Edges,Curves)

def FreeCAD_abs_placement(sketch_placement,p_co):
    p_co = F.Vector( ( p_co[0], p_co[1], p_co[2] ) )
    local_placement = F.Placement()
    local_placement.Base = p_co
    return sketch_placement.multiply(local_placement)

def register():
    bpy.utils.register_class(SvReadFCStdSketchNode)
    bpy.utils.register_class(SvShowFcstdSketchNamesOp)

def unregister():
    bpy.utils.unregister_class(SvReadFCStdSketchNode)
    bpy.utils.register_class(SvShowFcstdSketchNamesOp)
