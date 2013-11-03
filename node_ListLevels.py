import bpy
from node_s import *
from functools import reduce
from util import *



class ListLevelsNode(Node, SverchCustomTreeNode):
    ''' Lists Levels node '''
    bl_idname = 'ListLevelsNode'
    bl_label = 'List Levels Node'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    Sverch_LisLevA = bpy.props.StringProperty(name='Sverch_LisLevA', description='User defined nesty levels. (i.e. 1,2)', default='1,2,3', update=updateNode)
    Sverch_LisLevB = bpy.props.StringProperty(name='Sverch_LisLevB', description='User defined nesty levels. (i.e. 1,2)', default='1,2,3', update=updateNode)
    Sverch_LisLevC = bpy.props.StringProperty(name='Sverch_LisLevC', description='User defined nesty levels. (i.e. 1,2)', default='1,2,3', update=updateNode)
    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edg_pol', 'edg_pol')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')
        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'edg_pol', 'edg_pol')
        self.outputs.new('MatrixSocket', 'matrix', 'matrix')
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "Sverch_LisLevA", text="List A levels")
        layout.prop(self, "Sverch_LisLevB", text="List B levels")
        layout.prop(self, "Sverch_LisLevC", text="List C levels")
    
    
    def update(self):
        
        if 'vertices' in self.inputs and self.inputs['vertices'].links and len(self.inputs['vertices'].links)>0:
            if not self.inputs['vertices'].node.socket_value_update:
                self.inputs['vertices'].node.update()
            if self.inputs['vertices'].links[0].from_socket.VerticesProperty:
                list_a = eval(self.inputs['vertices'].links[0].from_socket.VerticesProperty)
                if self.outputs['vertices'].links and len(self.outputs['vertices'].links)>0:
                    userlevela = eval('['+self.Sverch_LisLevA+']')
                    self.outputs['vertices'].links[0].from_socket.VerticesProperty = str(preobrazovatel(list_a, userlevela))
                        
        if 'edg_pol' in self.inputs and self.inputs['edg_pol'].links and len(self.inputs['edg_pol'].links)>0:
            if not self.inputs['edg_pol'].node.socket_value_update:
                self.inputs['edg_pol'].node.update()
            if self.inputs['edg_pol'].links[0].from_socket.StringsProperty:
                list_b = eval(self.inputs['edg_pol'].links[0].from_socket.StringsProperty)
                if self.outputs['edg_pol'].links and len(self.outputs['edg_pol'].links)>0:
                    userlevelb = eval('['+self.Sverch_LisLevB+']')
                    self.outputs['edg_pol'].links[0].from_socket.StringsProperty = str(preobrazovatel(list_b, userlevelb))
                    #print (self.outputs['edg_pol'].links[0].from_socket.StringsProperty)
                
        if 'matrix' in self.inputs and self.inputs['matrix'].links and len(self.inputs['matrix'].links)>0:
            if not self.inputs['matrix'].node.socket_value_update:
                self.inputs['matrix'].node.update()
            if self.inputs['matrix'].links[0].from_socket.MatrixProperty:
                list_c = eval(self.inputs['matrix'].links[0].from_socket.MatrixProperty)
                if self.outputs['matrix'].links and len(self.outputs['matrix'].links)>0:
                    userlevelc = eval('['+self.Sverch_LisLevC+']')
                    self.outputs['matrix'].links[0].from_socket.MatrixProperty = str(preobrazovatel(list_c, userlevelc))
                    #print (self.outputs['matrix'].links[0].from_socket.MatrixProperty)
    
        
    

    def update_socket(self, context):
        self.update()



def register():
    bpy.utils.register_class(ListLevelsNode)
    
def unregister():
    bpy.utils.unregister_class(ListLevelsNode)

if __name__ == "__main__":
    register()



#   Памятка по данным, используемым в сверчке:
#   What is data in Svrchok:
#
#   [[(x0,y0,z0),(x1,y1,z1),(x2,y2,z2)][...     ]...]  that is how it looks ABCD
# 0 [                                               ]  parameter from socket
# 1  [object 0                        ][object 1]...   objects, matrixes
#                                                      here can be added levels for making poligons or smth
# 2   (vert 0  ),(vert 1  ),(vert 2  )  (...   )       vertices, edges, polygons, tuples
# 3    x0,y0,z0   x1,y1,z1   x2,y2,z2                  coordinates, vert_indexes, matrix floats
# ... in future will be flaxiable levels
#
#
# For dummies:
# Edges/polygons tree:
#
# [ object ]
# object = [i,i,i,i,i ]
# i = [n,n,n,n,n]
# n = integer
#
#
# Matrixes tree:
#
# [ matrix ]
# matrix = (a,b,c,d)
# a,b,c,d = (x,y,z,w)...
# x,y,z,w = float
#
#
# Vertices tree:
#
# [ object,... ]
# obect = [ v... ]
# v = (x,y,z)
# x,y,z = float,float,float
#
#
#
#
#   Памятка по уровням структуры данных
#   Data structures:
#
# 0123 [1, [2,3], [4,[5],[6,[7]]], [8]]
# 0    [                              ]
# 1     1, [   ], [             ]  [ ]
# 2         2,3    4 [ ] [     ]    8
# 3                         [ ]
# 4                   5   6  7
# 12    1  [2 3]  [4 [5] [6  7 ]]  [8]
# 13    1  [2 3]  [4  5   6 [7] ]  [8]
# 2     1   2 3    4 [5] [6  7]     8
# 3     1   2 3    4  5   6 [7]     8
# 23    1   2 3    4 [5] [6 [7]]    8
#
#
#
# ListLevel working principle:
#
# *** level=  0 ***
# listA= [1, [2, 3], [4, [5], [6, [7]]], [8]]
# list result  [1, 2, 3, 4, 5, 6, 7, 8]
# 
# *** level=  1 ***
# listA= [1, [2, 3], [4, [5], [6, [7]]], [8]]
# list result  [1, [2, 3], [4, 5, 6, 7], [8]]
#  
# *** level=  2 ***
# listA= [1, [2, 3], [4, [5], [6, [7]]], [8]]
# list result  [1, 2, 3, 4, [5], [6, 7], 8]
#  
# *** level=  3 ***
# listA= [1, [2, 3], [4, [5], [6, [7]]], [8]]
# list result  [1, 2, 3, 4, 5, 6, [7], 8]
#  
# *** level=  4 ***
# listA= [1, [2, 3], [4, [5], [6, [7]]], [8]]
# list result  [1, 2, 3, 4, 5, 6, 7, 8]
#  
# *** level= [1, 3] ***
# list result  [1, [2, 3], [4, 5, 6, [7]], [8]]
# 