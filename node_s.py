# -*- coding: utf-8 -*-
import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, FloatVectorProperty, CollectionProperty, EnumProperty
from bpy.types import NodeTree, Node, NodeSocket
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem
from mathutils import Matrix


class MatrixSocket(NodeSocket):
    '''4x4 matrix Socket_type'''
    #ref: http://urchn.org/post/nodal-transform-experiment
    bl_idname = "MatrixSocket"
    bl_label = "Matrix Socket"
    
    MatrixProperty = StringProperty(name='MatrixProperty') 
    
    
    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text)
        else:
            col = layout.column(align=True)
            col.label(text)
   
    def draw_color(self, context, node):
        '''if self.is_linked:
            return(.8,.3,.75,1.0)
        else: '''
        return(.2,.8,.8,1.0)

class ObjectSocket(NodeSocket):
        '''ObjectSocket'''
        bl_idname = "ObjectSocket"
        bl_label = "Object Socket"
        
        ObjectProperty = StringProperty(name= "ObjectProperty")
        
        def draw(self, context, layout, node, text):
            if self.is_linked:
                layout.label(text)
            else:
                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(self, 'ObjectProperty', text=text)
                
        def draw_color(self, context, node):
            return(0.8,0.8,0.2,1.0)

class VerticesSocket(NodeSocket):
        '''String Vertices - one string'''
        bl_idname = "VerticesSocket"
        bl_label = "Vertices Socket"
        
        VerticesProperty = StringProperty(name='VerticesProperty')

        def draw(self, context, layout, node, text):
            if self.is_linked:
                layout.label(text + str(self.VerticesProperty))
            else:
                col = layout.column(align=True)
                row = col.row(align=True)
                row.label(text)
                #row.prop(self, 'VerticesProperty', text=text)
                
        def draw_color(self, context, node):
            return(0.9,0.6,0.2,1.0)

class StringsSocket(NodeSocket):
        '''String any type - one string'''
        bl_idname = "StringsSocket"
        bl_label = "Strings Socket"
        
        StringsProperty = StringProperty(name='StringsProperty')

        def draw(self, context, layout, node, text):
            if self.is_linked:
                layout.label(text + str(self.StringsProperty))
            else:
                col = layout.column(align=True)
                row = col.row(align=True)
                row.label(text)
                #row.prop(self, 'StringsProperty', text=text)
                
        def draw_color(self, context, node):
            return(0.6,1.0,0.6,1.0)
        
class SverchCustomTree(NodeTree):
    '''A Sverchok node tree type that will show up in the node editor header'''
    bl_idname = 'SverchCustomTreeType'
    bl_label = 'Sverchok Node Tree'
    bl_icon = 'NODETREE'


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
        SverchNodeCategory("SVERCHOK", "SVERCHOK Nodes", items=[
            # our basic nodes
            NodeItem("CentersPolsNode", label="Centers Polygons"),
            NodeItem("ObjectsNode", label="Objects in"),
            NodeItem("ObjectsNodeOut", label="Objects out"),
            NodeItem("ViewerNode", label="Viewer draw"),
            NodeItem("ViewerNode_text", label="Viewer text"),
            NodeItem("ListLevelsNode", label="List Levels"),
            NodeItem("ListJoinNode", label="List Join"),
            NodeItem("ZipNode", label="List Zip"),
            NodeItem("ShiftNode", label="List Shift"),
            NodeItem("DistancePPNode", label="Distances"),
            NodeItem("GenSeriesNode", label="Series"),
            NodeItem("GenVectorsNode", label="Vector in"),
            NodeItem("FloatNode", label="Float"),
            NodeItem("IntegerNode", label="Int"),
            NodeItem("NumberNode", label="Float 2 Int"),
            NodeItem("MoveNode", label="Move Vector"),
            NodeItem("MatrixDeformNode", label="Deform Matrix"),
            NodeItem("MatrixGenNode", label="Matrix in"),
            NodeItem("FormulaNode", label="Formula"),
            NodeItem("ToolsNode", label="Tools"),
            ]),
        ]
    return node_categories

def register():
    bpy.utils.register_class(SverchCustomTree)
    bpy.utils.register_class(MatrixSocket)
    bpy.utils.register_class(ObjectSocket)
    bpy.utils.register_class(StringsSocket)
    bpy.utils.register_class(VerticesSocket)
    
def unregister():
    bpy.utils.unregister_class(VerticesSocket)
    bpy.utils.register_class(StringsSocket)
    bpy.utils.register_class(ObjectSocket)
    bpy.utils.register_class(MatrixSocket)
    bpy.utils.register_class(SverchCustomTree)

if __name__ == "__main__":
    register()