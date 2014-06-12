# -*- coding: utf-8 -*-
import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, FloatVectorProperty, CollectionProperty, EnumProperty, BoolProperty
from bpy.types import NodeTree, Node, NodeSocket, NodeSocketStandard
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem
from mathutils import Matrix
import util
from util import makeTreeUpdate2, speedUpdate, SvGetSocketInfo, SvGetSocket,SvSetSocket, get_update_lists, updateNode
from bpy.app.handlers import persistent


class SvColors(bpy.types.PropertyGroup):
    """ Class for colors CollectionProperty """
    color = bpy.props.FloatVectorProperty(
        name="svcolor", description="sverchok color", default=(0.055,0.312,0.5), min=0, max=1,
        step=1, precision=3, subtype='COLOR_GAMMA', size=3, update=updateNode)


class MatrixSocket(NodeSocket):
    '''4x4 matrix Socket_type'''
    #ref: http://urchn.org/post/nodal-transform-experiment
    bl_idname = "MatrixSocket"
    bl_label = "Matrix Socket"
    prop_name = StringProperty(default='')
    # beta interface only use for debug, might change
    def sv_get(self,default=None):
        if self.links and self.is_output:
            return SvGetSocket(self)
        else:
            return default
            
    def sv_set(self,data):
        SvSetSocket(self,data)

    def draw(self, context, layout, node, text):
    #    if not self.is_output and not self.is_linked and self.prop_name:
    #        layout.prop(node,self.prop_name,expand=False)
        if self.is_linked:
            layout.label(text + '. ' + SvGetSocketInfo(self))
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

class VerticesSocket(NodeSocketStandard):
    '''String Vertices - one string'''
    bl_idname = "VerticesSocket"
    bl_label = "Vertices Socket"
    prop_name = StringProperty(default='')
        
    # beta interface only use for debug, might change
    def sv_get(self,default=None):
        if self.links and self.is_output:
            return SvGetSocket(self)
        else:
            return default
            
    def sv_set(self,data):
        SvSetSocket(self,data)

    def draw(self, context, layout, node, text):
    #    if not self.is_output and not self.is_linked and self.prop_name:
    #        layout.prop(node,self.prop_name,expand=False)
        if self.is_linked:
            layout.label(text + '. '+ SvGetSocketInfo(self))
        else:
            layout.label(text)
            
    def draw_color(self, context, node):
        return(0.9,0.6,0.2,1.0)

class StringsSocket(NodeSocketStandard):
    '''String any type - one string'''
    bl_idname = "StringsSocket"
    bl_label = "Strings Socket"
            
    prop_name = StringProperty(default='')
    
    def sv_get(self,default=None):
        if self.links and not self.is_output:
            out = SvGetSocket(self)
            if out:
                return out
        if self.prop_name:
            return [[getattr(self.node,self.prop_name)]]
        return default
            
    def sv_set(self,data):
        SvSetSocket(self,data)
    
    def draw(self, context, layout, node, text):
        if self.prop_name:
            if self.is_output:
                t=text
                print('Warning output socket:',self.name,'in node:',node.name,'has property attached')
            else:    
                prop=node.rna_type.properties.get(self.prop_name,None)
                t=prop.name if prop else text
        else:
            t=text
            
        if not self.is_output and not self.is_linked and self.prop_name:
            layout.prop(node,self.prop_name)
        elif self.is_linked:
            layout.label(t + '. ' + SvGetSocketInfo(self))
        else:
            layout.label(t)
                
    def draw_color(self, context, node):
        return(0.6,1.0,0.6,1.0)
        
class SverchCustomTree(NodeTree):
    ''' Sverchok - architectural node programming of geometry in low level '''
    bl_idname = 'SverchCustomTreeType'
    bl_label = 'Sverchok Node Tree'
    bl_icon = 'RNA'
    
    def updateTree(self,context):
        speedUpdate(tree = self)
        #should turn off tree. for now it does by updating it
        
    sv_animate = BoolProperty(name="Animate", default=True)
    sv_show = BoolProperty(name="Show", default=True, update=updateTree)
    sv_bake = BoolProperty(name="Bake", default=True )
    
    # get update list for debug info, tuple (fulllist,dictofpartiallists)
    def get_update_lists(self):
        return get_update_lists(self)
        
    def update(self):
        '''
        Rebuild and update the Sverchok node tree, used at editor changes
        '''
        makeTreeUpdate2(tree = self)
        speedUpdate(tree = self)
    
    def update_ani(self):
        '''
        Updates the Sverchok node tree if animation layers show true. For animation callback
        '''
        if self.sv_animate:
            speedUpdate(tree=self)
        


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
            NodeItem("BmeshViewerNode", label="BMesh View"),
            # NodeItem("BakeryNode", label="Bake all"),
            NodeItem("ViewerNode", label="Viewer draw"),
            NodeItem("ViewerNode_text", label="Viewer text"),
            NodeItem("IndexViewerNode", label="Viewer INDX"),
            NodeItem("SvTextInNode",  label="Text in"),
            NodeItem("SvTextOutNode",  label="Text out"),
            NodeItem("WifiInNode", label="Wifi in"),
            NodeItem("WifiOutNode", label="Wifi out"),
            # NodeItem("Test1Node", label="Test1"),
            # NodeItem("Test2Node", label="Test2"),
            NodeItem("SvFrameInfoNode", label="Frame info"),
            NodeItem("NoteNode", label="Note"),
            NodeItem("GTextNode", label="GText"),
            NodeItem("ToolsNode", label="Update Button"),
            NodeItem("SvDebugPrintNode", label="Debug print"),
            ]),
        SverchNodeCategory("SVERCHOK_L", "SVERCHOK list", items=[
            # lists nodes
            NodeItem("ListLevelsNode", label="List Del Levels"),
            NodeItem("ListJoinNode", label="List Join"),
            NodeItem("ListDecomposeNode", label="List Decompose"),
            NodeItem("ZipNode", label="List Zip"),
            NodeItem("ShiftNode", label="List Shift"),
            NodeItem("ListSliceNode", label="List Slice"),
            NodeItem("SvListSplitNode", label="List Split"),
            NodeItem("ListReverseNode", label="List Reverse"),
            NodeItem("ListLengthNode", label="List Length"),
            NodeItem("ListSumNode", label="List Sum"),
            NodeItem("ListFLNode", label="List First&Last"),
            NodeItem("ListItem2Node", label="List Item"),
            NodeItem("ListRepeaterNode", label="List Repeater"),
            NodeItem("ListFuncNode", label="List Math"),
            NodeItem("ListFlipNode", label="List Flip"),
            NodeItem("MaskListNode", label="List Mask (out)"),
            NodeItem("SvMaskJoinNode", label="List Mask Join (in)"),
            NodeItem("ListSortNode", label="List Sort"),
            NodeItem("ListShuffleNode", label="List Shuffle"),
            NodeItem("ListMatchNode", label="List Match"),
            NodeItem("ConverterNode", label="SocketConvert"),
            ]),
        SverchNodeCategory("SVERCHOK_N", "SVERCHOK number", items=[
            # numbers, formula nodes
            #NodeItem("GenSeriesNode", label="Series float"),
            #NodeItem("GenRangeNode", label="Range float"),
            NodeItem("GenListRangeIntNode", label="Range Int"),
            NodeItem("SvGenFloatRange", label="Range Float"),
            NodeItem("SvListInputNode", label="List Input"),
            NodeItem("RandomNode", label="Random"),
            NodeItem("FloatNode", label="Float"),
            NodeItem("IntegerNode", label="Int"),
            NodeItem("Float2IntNode", label="Float 2 Int"),
            # NodeItem("FormulaNode", label="Formula"),
            NodeItem("Formula2Node", label="Formula"), # for newbies this is not predictable why "Formula2" renamed
            NodeItem("ScalarMathNode", label="Math"),
            NodeItem("SvMapRangeNode", label="Map Range"),
            ]),
        SverchNodeCategory("SVERCHOK_G", "SVERCHOK generator", items=[
            # objects, new elements, line, plane
            NodeItem("LineNode", label="Line"),
            NodeItem("PlaneNode", label="Plane"),
            NodeItem("SvBoxNode", label="Box"),
            NodeItem("SvCircleNode", label="Circle"),
            NodeItem("CylinderNode", label="Cylinder"),
            NodeItem("SphereNode", label="Sphere"),
            NodeItem("HilbertNode", label="Hilbert"),
            NodeItem("HilbertImageNode", label="Hilbert image"),
            NodeItem("ImageNode", label="Image"),
            NodeItem("RandomVectorNode", label="Random Vector"),
            NodeItem("SvScriptNode", label="Scripted Node")
            ]),
        SverchNodeCategory("SVERCHOK_V", "SVERCHOK vector", items=[
            # Vector nodes
            NodeItem("GenVectorsNode", label="Vector in"),
            NodeItem("VectorsOutNode", label="Vector out"),
            NodeItem("VectorMoveNode", label="Vector Move"),
            NodeItem("VectorMathNode", label="Vector Math"),
            NodeItem("VectorDropNode", label="Vector Drop"),
            NodeItem("VertsDelDoublesNode", label="Vector X Doubles"),
            NodeItem("EvaluateLineNode", label="Vector Evaluate"),
            NodeItem("SvInterpolationNode", label="Vector Interpolation"),
            NodeItem("SvVertSortNode", label="Vector Sort"),
            NodeItem("SvNoiseNode", label="Vector Noise"),
        #    ]),
        #SverchNodeCategory("SVERCHOK_Ma", "SVERCHOK matrix", items=[
        #    # Matrix nodes
            NodeItem("MatrixApplyNode", label="Matrix Apply"),
            NodeItem("MatrixGenNode", label="Matrix in"),
            NodeItem("MatrixOutNode", label="Matrix out"),
            NodeItem("SvMatrixValueIn", label="Matrix Input"),
            NodeItem("MatrixDeformNode", label="Matrix Deform"),
            NodeItem("MatrixShearNode", label="Matrix Shear"), # for uniform view renamed
            NodeItem("MatrixInterpolationNode", label="Matrix Interpolation"),
            ]),
        SverchNodeCategory("SVERCHOK_M", "SVERCHOK modifier", items=[
            # modifiers deforms and reorganize and reconstruct data
            NodeItem("AdaptivePolsNode", label="Adaptive Polygons"),
            NodeItem("SvAdaptiveEdgeNode", label="Adaptive Edges"),
            NodeItem("CrossSectionNode", label="Cross Section"),
            NodeItem("SvBisectNode", label="Bisect"),
            NodeItem("SvSolidifyNode", label="Solidify"),
            NodeItem("SvWireframeNode", label="Wireframe"),
            NodeItem("LineConnectNode", label="UV Connection"),
            NodeItem("DelaunayTriangulation2DNode", label="Delaunay 2D "),
            NodeItem("Voronoi2DNode", label="Voronoi 2D"),
            NodeItem("PolygonBoomNode", label="Polygon Boom"),
            NodeItem("Pols2EdgsNode", label="Polygons to Edges"),
            NodeItem("SvMeshJoinNode", label="Mesh Join"),
            NodeItem("SvRemoveDoublesNode", label="Remove Doubles"),
            NodeItem("SvDeleteLooseNode", label="Delete Loose"),
            NodeItem('SvSeparateMeshNode', label="Separate Loose Parts"),
            NodeItem('SvVertMaskNode', label="Mask Vertices"),
            NodeItem("SvConvexHullNode", label="Convex Hull"),
            NodeItem("SvFillsHoleNode", label="Fill Holes"),
            NodeItem("SvIntersectEdgesNode", label="Intersect Edges"),
            NodeItem("SvLatheNode", label="Lathe"),
            ]),
        SverchNodeCategory("SVERCHOK_A", "SVERCHOK analisators", items=[
            # investigate data
            NodeItem("CentersPolsNode", label="Centers Polygons"),
            NodeItem("VectorNormalNode", label="Vector' Normal"),
            NodeItem("DistancePPNode", label="Distance"),
            NodeItem("AreaNode", label="Area"),
            NodeItem("SvBBoxNode", label="Bounding box"),
            NodeItem("SvKDTreeNode", label="KDT Closest Verts"),
            NodeItem("SvKDTreeEdgesNode", label="KDT Closest Edges"), #KDTree renamed to be clear
            ]),
        ]
    return node_categories

#def Sverchok_nodes_count():
#    cats = make_categories()
#    count = []
#    for cnt in cats:
#        count.append(len(cnt.items))
#    return count

# animation update handler
@persistent
def sv_update_handler(scene):
    '''Sverchok update handler'''
    for name,tree in bpy.data.node_groups.items():
        if tree.bl_idname =='SverchCustomTreeType' and tree.nodes:
            try:
                tree.update_ani()                
            except Exception as e:
                print('Failed to update:',name,str(e))
                    
# clean up handler
@persistent
def sv_clean(scene):
    # callbacks for view nodes
    import Viewer_draw
    import Index_Viewer_draw
    Viewer_draw.callback_disable_all()
    Index_Viewer_draw.callback_disable_all()
    util.temp_handle = {}

@persistent
def sv_upgrade_nodes(scene):
    # update nodes to compact layout
    import upgrade
    for name,tree in bpy.data.node_groups.items():
        if tree.bl_idname =='SverchCustomTreeType' and tree.nodes:
            try:
                upgrade.upgrade_nodes(tree)                
            except Exception as e:
                print('Failed to upgrade:',name,str(e))
                        
def register():
    bpy.utils.register_class(SvColors)
    bpy.utils.register_class(SverchCustomTree)
    bpy.utils.register_class(MatrixSocket)
    #bpy.utils.register_class(ObjectSocket)
    bpy.utils.register_class(StringsSocket)
    bpy.utils.register_class(VerticesSocket)
    bpy.app.handlers.frame_change_post.append(sv_update_handler) 
    bpy.app.handlers.load_pre.append(sv_clean) 
    bpy.app.handlers.load_post.append(sv_upgrade_nodes) 

       
def unregister():
    bpy.utils.unregister_class(VerticesSocket)
    bpy.utils.unregister_class(StringsSocket)
    #bpy.utils.unregister_class(ObjectSocket)
    bpy.utils.unregister_class(MatrixSocket)
    bpy.utils.unregister_class(SverchCustomTree)
    bpy.utils.unregister_class(SvColors)
    bpy.app.handlers.frame_change_post.remove(sv_update_handler)
    bpy.app.handlers.load_pre.remove(sv_clean) 
    bpy.app.handlers.load_post.remove(sv_upgrade_nodes)

if __name__ == "__main__":
    register()
