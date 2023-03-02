import bpy
import numpy as np
import mathutils
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_logging import sv_logger
from sverchok.dependencies import FreeCAD
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator

if FreeCAD is not None:
    F = FreeCAD


class SvReadFCStdSketchOperator(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_read_fcstd_sketch_operator"
    bl_label = "read freecad sketch"
    bl_options = {'INTERNAL', 'REGISTER'}

    def execute(self, context):
        node = self.get_node(context)

        if not node: return {'CANCELLED'}

        node.read_sketch(node)
        updateNode(node,context)

        return {'FINISHED'}


class SvReadFCStdSketchNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Read FreeCAD file
    Tooltip: import parts from a .FCStd file
    """
    bl_idname = 'SvReadFCStdSketchNode'
    bl_label = 'Read FCStd Sketches'
    bl_icon = 'IMPORT'
    sv_category = "Solid Outputs"
    sv_dependencies = {'FreeCAD'}

    max_points : IntProperty(name="max_points", default=50, update = updateNode)
    read_update : BoolProperty(name="read_update", default=True)
    inv_filter : BoolProperty(name="inv_filter", default=False, update = updateNode)
    selected_label : StringProperty(default='Select FC Part')
    selected_part : StringProperty(default='',update = updateNode)

    read_mode : EnumProperty(
                name='mode',
                description='read geometry / construction',
                items=[
                ('geometry', 'geometry', 'geometry'),
                ('construction', 'construction', 'construction'),
                ('BOTH', 'BOTH', 'BOTH')],
                default='geometry',
                update = updateNode )

    def draw_buttons(self, context, layout):

        col = layout.column(align=True)
        col.prop(self, 'read_mode')

        if self.inputs['File Path'].is_linked:
            self.wrapper_tracked_ui_draw_op(
                col, SvShowFcstdSketchNamesOp.bl_idname,
                icon= 'TRIA_DOWN',
                text= self.selected_label )

        col.prop(self, 'max_points')
        col.prop(self, 'read_update')
        col.prop(self, 'inv_filter')
        self.wrapper_tracked_ui_draw_op(layout, SvReadFCStdSketchOperator.bl_idname, icon='FILE_REFRESH', text="UPDATE")

    def sv_init(self, context):
        self.inputs.new('SvFilePathSocket', "File Path")
        self.inputs.new('SvStringsSocket', "Sketch Filter")

        self.outputs.new('SvVerticesSocket', "Verts")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvCurveSocket', "Curve")

    def read_sketch(self,node):

        if not any(socket.is_linked for socket in node.outputs):
            return

        if not node.inputs['File Path'].is_linked:
            return

        if node.read_update:

            files = node.inputs['File Path'].sv_get()[0]

            sketch_filter = []
            if node.inputs['Sketch Filter'].is_linked:
                sketch_filter = node.inputs['Sketch Filter'].sv_get()[0]

            if node.selected_part != '' and not node.selected_part in sketch_filter:
                sketch_filter.append(node.selected_part)

            Verts = []
            Edges = []
            curves_out = []
            for f in files:
                S = LoadSketch(f, sketch_filter, node.max_points, node.inv_filter, node.read_mode)
                for i in S[0]:
                    Verts.append(i)
                for i in S[1]:
                    Edges.append(i)
                for i in S[2]:
                    curves_out.append(i)
            node.outputs['Verts'].sv_set([Verts])
            node.outputs['Edges'].sv_set([Edges])
            node.outputs['Curve'].sv_set(curves_out)

        else:
            return

    def process(self):
        self.read_sketch(self)


class SvShowFcstdSketchNamesOp(bpy.types.Operator):
    bl_idname = "node.sv_show_fcstd_sketch_names"
    bl_label = "Show parts list"
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

                    if obj.Module == 'Sketcher':
                        labels.append( (obj.Label, obj.Label, obj.Label) )
                F.closeDocument(Fname)

        except:
            sv_logger.info('FCStd read error')

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
   

def LoadSketch(fc_file, sketch_filter, max_points, inv_filter, read_mode):
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
        sv_logger.info('FCStd read error')
        return (Verts,Edges,Curves)
    
    #___________________SEARCH FOR SKETCHES

    for obj in F.ActiveDocument.Objects:

        if obj.Module == 'Sketcher':
            
            if not inv_filter:

                if obj.Label in sketch_filter or len(sketch_filter)==0:
                    sketches.append(obj)

            else:
                if not obj.Label in sketch_filter:
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


        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> EVALUATE CURVE START
        for i,geo in enumerate(s.Geometry):

            if read_mode == 'geometry':
                if s.getConstruction(i) : continue
                #FREECAD 0.18 #if geo.Construction : continue

            elif read_mode == 'construction':
                if not s.getConstruction(i) : continue
                #FREECAD 0.18 #if not geo.Construction : continue

            v_set=[]
            e_set=[]
            
            #LINE CASE
            if isinstance(geo, Part.LineSegment ):
                geo_points = 2

            #POINT CASE
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
            #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< EVALUATE CURVE END
            #-------------------------------------------------------------
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> FC CURVE TO SV CURVE
            #LINE
            if isinstance(geo, Part.LineSegment ):
                from sverchok.utils.curve import SvLine
                point1 = np.array(v_set[0])
                direction = np.array(v_set[1]) - point1
                line = SvLine(point1, direction)
                line.u_bounds = (0, 1)
                Curves.append(line)

            #CIRCLE
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

            elif geo_points!=1:
                geo = geo.toNurbs()
                from sverchok.utils.nurbs_common import SvNurbsMaths
                from sverchok.utils.curve import SvNurbsCurve

                abs_poles = []

                for vec in geo.getPoles():
                    abs_co = FreeCAD_abs_placement(s_placement,vec).Base
                    abs_poles.append ( (abs_co.x, abs_co.y, abs_co.z) )

                new_curve = SvNurbsCurve.build( SvNurbsMaths.FREECAD, geo.Degree, geo.KnotSequence, abs_poles, geo.getWeights() )

                Curves.append(new_curve)

    F.closeDocument(Fname)
    return (Verts,Edges,Curves)

def FC_matrix_to_mathutils_format(fc_matrix):
    row=0
    col=0
    b_matrix = mathutils.Matrix()
    for i in fc_matrix.A:
        if col == 4: 
            row += 1; col = 0
        b_matrix[row][col] = i
        col += 1
    return b_matrix

def FreeCAD_abs_placement(sketch_placement,p_co):
    p_co = F.Vector( ( p_co[0], p_co[1], p_co[2] ) )
    local_placement = F.Placement()
    local_placement.Base = p_co
    return sketch_placement.multiply(local_placement)


def register():
    bpy.utils.register_class(SvReadFCStdSketchNode)
    bpy.utils.register_class(SvShowFcstdSketchNamesOp)
    bpy.utils.register_class(SvReadFCStdSketchOperator)


def unregister():
    bpy.utils.unregister_class(SvReadFCStdSketchNode)
    bpy.utils.unregister_class(SvShowFcstdSketchNamesOp)
    bpy.utils.unregister_class(SvReadFCStdSketchOperator)
