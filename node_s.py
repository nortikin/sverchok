# -*- coding: utf-8 -*-
import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, FloatVectorProperty, CollectionProperty, EnumProperty
from bpy.types import NodeTree, Node, NodeSocket
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem
from mathutils import Matrix
from util import updateSlot

class SvColors(bpy.types.PropertyGroup):
    """ Class for colors CollectionProperty """
    color = bpy.props.FloatVectorProperty(
        name="svcolor", description="sverchok color", default=(0.055,0.312,0.5), min=0, max=1,
        step=1, precision=3, subtype='COLOR_GAMMA', size=3)

class MatrixSocket(NodeSocket):
    '''4x4 matrix Socket_type'''
    #ref: http://urchn.org/post/nodal-transform-experiment
    bl_idname = "MatrixSocket"
    bl_label = "Matrix Socket"
    
    MatrixProperty = StringProperty(name='MatrixProperty', update=updateSlot)
    
    
    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text + '.' + str(self.MatrixProperty)[:7])
        else:
            layout.label(text)
   
    def draw_color(self, context, node):
        '''if self.is_linked:
            return(.8,.3,.75,1.0)
        else: '''
        return(.2,.8,.8,1.0)

'''
class ObjectSocket(NodeSocket):
        'ObjectSocket'
        bl_idname = "ObjectSocket"
        bl_label = "Object Socket"
        
        ObjectProperty = StringProperty(name= "ObjectProperty", update=updateSlot)
        
        def draw(self, context, layout, node, text):
            if self.is_linked:
                layout.label(text)
            else:
                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(self, 'ObjectProperty', text=text)
                
        def draw_color(self, context, node):
            return(0.8,0.8,0.2,1.0)
'''

class VerticesSocket(NodeSocket):
        '''String Vertices - one string'''
        bl_idname = "VerticesSocket"
        bl_label = "Vertices Socket"
        
        VerticesProperty = StringProperty(name='VerticesProperty', update=updateSlot)
        #V = list()

        def draw(self, context, layout, node, text):
            if self.is_linked:
                layout.label(text + '.' + str(self.VerticesProperty)[:7])
            else:
                layout.label(text)
                
        def draw_color(self, context, node):
            return(0.9,0.6,0.2,1.0)

class StringsSocket(NodeSocket):
        '''String any type - one string'''
        bl_idname = "StringsSocket"
        bl_label = "Strings Socket"
        
        StringsProperty = StringProperty(name='StringsProperty', update=updateSlot)

        def draw(self, context, layout, node, text):
            if self.is_linked:
                layout.label(text + '.' + str(self.StringsProperty)[:7])
            else:
                layout.label(text)
                
        def draw_color(self, context, node):
            return(0.6,1.0,0.6,1.0)
        
class SverchCustomTree(NodeTree):
    ''' Sverchok - architectural node programming of geometry in low level '''
    bl_idname = 'SverchCustomTreeType'
    bl_label = 'Sverchok Node Tree'
    bl_icon = 'RNA'


class SverchCustomTreeNode:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'SverchCustomTreeType'


class SverchNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'SverchCustomTreeType'

def make_categories():
    node_categories = [
        SverchNodeCategory("SVERCHOK_B", "SVERCHOK basic", items=[
            # basic nodes
            NodeItem("ObjectsNode", label="Objects in"),
            NodeItem("ViewerNode", label="Viewer draw"),
            NodeItem("ViewerNode_text", label="Viewer text"),
            NodeItem("SvTextInNode",  label="Text Input"),
            NodeItem("WifiInNode", label="Wifi in"),
            NodeItem("WifiOutNode", label="Wifi out"),
            NodeItem("ToolsNode", label="Tools"),
            ]),
        SverchNodeCategory("SVERCHOK_L", "SVERCHOK list", items=[
            # lists nodes
            NodeItem("ListLevelsNode", label="List Levels"),
            NodeItem("ListJoinNode", label="List Join"),
            NodeItem("ZipNode", label="List Zip"),
            NodeItem("ShiftNode", label="List Shift"),
            NodeItem("ListReverseNode", label="List Reverse"),
            NodeItem("ListLengthNode", label="List Length"),
            NodeItem("ListSumNode", label="List Sum"),
            NodeItem("ListFLNode", label="List First&Last"),
            NodeItem("ListItemNode", label="List Item"),
            NodeItem("ListRepeaterNode", label="List Repeater"),
            NodeItem("ListFuncNode", label="List Math"),
            NodeItem("ConverterNode", label="SocketConvert"),
            NodeItem("ListFlipNode", label="ListFlip"),
            NodeItem("MaskListNode", label="List Mask"),
            NodeItem("ListSortNode", label="List Sort"),
            # NodeItem("Test1Node", label="test1"),
            ]),
        SverchNodeCategory("SVERCHOK_N", "SVERCHOK number", items=[
            # numbers, formula nodes
            NodeItem("GenSeriesNode", label="Series"),
            NodeItem("GenRangeNode", label="Range"),
            NodeItem("RandomNode", label="Random"),
            NodeItem("FloatNode", label="Float"),
            NodeItem("IntegerNode", label="Int"),
            NodeItem("Float2IntNode", label="Float 2 Int"),
            NodeItem("FormulaNode", label="Formula"),
            NodeItem("Formula2Node", label="Formula2"),
            NodeItem("ScalarMathNode", label="Math"),
            ]),
        SverchNodeCategory("SVERCHOK_G", "SVERCHOK generator", items=[
            # objects, new elements, line, plane
            NodeItem("LineNode", label="Line"),
            NodeItem("PlaneNode", label="Plane"),
            NodeItem("CircleNode", label="Circle"),
            NodeItem("CylinderNode", label="Cylinder"),
            NodeItem("SphereNode", label="Sphere"),
            NodeItem("HilbertNode", label="Hilbert"),
            NodeItem("HilbertImageNode", label="Hilbert image"),
            NodeItem("Voronoi2DNode", label="Voronoi"),
            NodeItem("ImageNode", label="Image"),
            ]),
        SverchNodeCategory("SVERCHOK_V", "SVERCHOK vector", items=[
            # vectors and matrixes nodes
            NodeItem("GenVectorsNode", label="Vector in"),
            NodeItem("VectorsOutNode", label="Vector out"),
            NodeItem("VectorNormalNode", label="Vector' Normal"),
            NodeItem("VectorMoveNode", label="Vector Move"),
            NodeItem("VectorMathNode", label="Vector Math"),
            NodeItem("MatrixApplyNode", label="Matrix Apply"),
            NodeItem("VectorDropNode", label="Vector Drop"),
            NodeItem("MatrixGenNode", label="Matrix in"),
            NodeItem("MatrixOutNode", label="Matrix out"),
            NodeItem("MatrixDeformNode", label="Matrix Deform"),
            NodeItem("MatrixShearNode", label="Shear Matrix"),
            NodeItem("MatrixInterpolationNode", label="Matrix Interpolation"),
            NodeItem("RandomVectorNode", label="Random Vector"),
            ]),
        SverchNodeCategory("SVERCHOK_M", "SVERCHOK modifier", items=[
            # modifiers that find data from another data
            NodeItem("EvaluateLineNode", label="Evaluate Line"),
            NodeItem("CentersPolsNode", label="Centers Polygons"),
            NodeItem("DistancePPNode", label="Distances"),
            NodeItem("AreaNode", label="Area"),
            NodeItem("AdaptivePolsNode", label="Adaptive Polygons"),
            NodeItem("CrossSectionNode", label="Cross Section"),
            NodeItem("LineConnectNode", label="Lines Connection"),
            NodeItem("DelaunayTriangulation2DNode", label="Delaunay Tri 2D "),
            NodeItem("ListBoomNode", label="Polygon Boom"),
            ]),
        ]
    return node_categories

#def Sverchok_nodes_count():
#    cats = make_categories()
#    count = []
#    for cnt in cats:
#        count.append(len(cnt.items))
#    return count

def register():
    bpy.utils.register_class(SvColors)
    bpy.utils.register_class(SverchCustomTree)
    bpy.utils.register_class(MatrixSocket)
    #bpy.utils.register_class(ObjectSocket)
    bpy.utils.register_class(StringsSocket)
    bpy.utils.register_class(VerticesSocket)
    
def unregister():
    bpy.utils.unregister_class(VerticesSocket)
    bpy.utils.unregister_class(StringsSocket)
    #bpy.utils.unregister_class(ObjectSocket)
    bpy.utils.unregister_class(MatrixSocket)
    bpy.utils.unregister_class(SverchCustomTree)
    bpy.utils.unregister_class(SvColors)

if __name__ == "__main__":
    register()
