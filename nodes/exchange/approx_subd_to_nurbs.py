
import bpy,bmesh
from bpy.props import BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.dependencies import FreeCAD
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator

if FreeCAD is not None:
    F = FreeCAD


class SvApproxSubdtoNurbsOperator(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.approx_subd_nurbs_operator"
    bl_label = "Approx Subd-Nurbs"
    bl_options = {'INTERNAL', 'REGISTER'}

    def execute(self, context):
        node = self.get_node(context)

        if not node:
            return {'CANCELLED'}

        if not any(socket.is_linked for socket in node.outputs):
            return {'CANCELLED'}

        try:
            node.inputs['Subd Obj'].sv_get()[0]
        except:
            return {'CANCELLED'}

        node.Approximate(node)
        updateNode(node,context)

        return {'FINISHED'}


class SvApproxSubdtoNurbsNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Approximate Subd to Nurbs
    Tooltip: Approximate Subd to Nurbs
    """
    bl_idname = 'SvApproxSubdtoNurbsNode'
    bl_label = 'Approximate Subd to Nurb'
    bl_icon = 'IMPORT'
    sv_category = "Solid Outputs"
    sv_dependencies = {'FreeCAD'}

    auto_update : BoolProperty(name="auto_update", default=True)

    def draw_buttons(self, context, layout):

        col = layout.column(align=True)
        col.prop(self, 'auto_update', text = 'global update')

        self.wrapper_tracked_ui_draw_op(layout, SvApproxSubdtoNurbsOperator.bl_idname, icon='FILE_REFRESH', text="UPDATE")

    def sv_init(self, context):

        self.inputs.new('SvObjectSocket', "Subd Obj")
        self.outputs.new('SvSolidSocket', "Solid")

    def Approximate(self,node):

        S = ApproxSubdToNurbs( node.inputs['Subd Obj'].sv_get()[0] )

        node.outputs['Solid'].sv_set(S)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        try:
            self.inputs['Subd Obj'].sv_get()[0]
        except:
            return

        if self.auto_update:
            self.Approximate(self)
        else:
            return


def ApproxSubdToNurbs(Object):

    from FreeCAD import Part
    from FreeCAD.Part import BSplineCurve
    from FreeCAD.Part import makeCompound

    F.newDocument("freecad_temp")
    F.setActiveDocument('freecad_temp')

    patches=[]

    obj = Object

    if obj.modifiers[0].levels <= 1:
        return []
    else:
        obj.modifiers[0].levels -= 1 

    obj.modifiers[0].subdivision_type = "SIMPLE"
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj = obj.evaluated_get(depsgraph)

    bm = bmesh.new()   
    bm.from_mesh(obj.data)   

    face_corners = set()

    for f in bm.faces:
        corners = []
        for l in f.loops:
            pos = (l.vert.co.x,l.vert.co.y,l.vert.co.z)
            corners.append( pos )
        face_corners.add(tuple(corners))
        
    bm.free()    

    obj = Object
    obj.modifiers[0].levels += 1
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj = obj.evaluated_get(depsgraph)

    bm = bmesh.new()   
    bm.from_mesh(obj.data)   

    borders=[]
    centers=[]

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()


    for quad_co in face_corners:
        quad = []
        for co in quad_co:
            for v in bm.verts:
                if (v.co.x,v.co.y,v.co.z) == co: quad.append(v.index)        
        edges = []
        for i in range(4): 
            j = 0 if i == 3 else i+1
            for vert in bm.verts:
                pool = set()
                for e in vert.link_edges:
                    for v in e.verts:
                        pool.add(v.index)
                edge = set((quad[i],quad[j]))
                
                    
                if edge.issubset(pool):
                    edge = ( quad[i], vert.index, quad[j] )
                    edges.append( edge )

        set1 = set()
        for e in bm.verts[edges[0][1]].link_edges:
            for v in e.verts:
                set1.add(v.index)
        
        set2 = set()
        for e in bm.verts[edges[1][1]].link_edges:
            for v in e.verts:
                set2.add(v.index)             

        borders.append(edges)
        centers.append( ((set1&set2)-set(quad)).pop() )


    obj = Object
    obj.modifiers[0].subdivision_type = "CATMULL_CLARK"
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj = obj.evaluated_get(depsgraph)
    bm = bmesh.new()   
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    v_borders=[]
    v_centers=[]

    for p in centers:
        p = bm.verts[p]
        v_centers.append( (p.co.x,p.co.y,p.co.z) )

    for b in borders:
        border=[]
        for e in b:
            edges=[]
            for p in e:
                p = bm.verts[p]
                edges.append( (p.co.x,p.co.y,p.co.z) )
            border.append( edges ) 
        v_borders.append(border)
        
    bm.free()

    for i in range(len(centers)):
        p = v_borders[i]
        cen = v_centers[i]
        curves=[]
        item=0
        
        CEN = F.ActiveDocument.addObject('Part::Feature', 'boundary_center%s'%item)
        CEN.Shape = Part.Point( F.Vector( cen ) ).toShape()
        
        for b in p:
        
            Points=[]
            
            Points.append( F.Vector( b[0]) )
            Points.append( F.Vector( b[1]) )
            Points.append( F.Vector( b[2]) )

            curve = BSplineCurve()
            curve.increaseDegree(1)
            curve.interpolate(Points)
            curves.append(curve)

        com = makeCompound([x.toShape() for x in curves]) 
        com_obj = F.ActiveDocument.addObject('Part::Feature', 'boundary_edges%s'%item)
        com_obj.Shape = com
        F.ActiveDocument.recompute()
        edge_names  = ["Edge%d"%(n+1) for n in range(len(com.Edges))]
        patch = F.ActiveDocument.addObject("Surface::Filling","Surface%s"%item)
        patch.BoundaryEdges = (com_obj, edge_names) 
        patch.Points = (CEN, "Vertex1")
        F.ActiveDocument.recompute() 
        item+=1
        
        
    F.ActiveDocument.recompute()

    SURFS= []

    for obj in F.ActiveDocument.Objects:
        if 'Surface' in obj.Name: 
            SURFS.append(obj)
                

    F.activeDocument().addObject("Part::Compound","Compound")
    COMPOUND = F.ActiveDocument.getObject("Compound")
    COMPOUND.Links = SURFS

    F.ActiveDocument.recompute()

    COMPOUND.recompute()
    SHELL = Part.Solid( Part.Shell(COMPOUND.Shape.Faces) )

    F.closeDocument("freecad_temp")   

    return [SHELL]


def register():
    bpy.utils.register_class(SvApproxSubdtoNurbsOperator)
    bpy.utils.register_class(SvApproxSubdtoNurbsNode)


def unregister():
    bpy.utils.unregister_class(SvApproxSubdtoNurbsOperator)
    bpy.utils.unregister_class(SvApproxSubdtoNurbsNode)
