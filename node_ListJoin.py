import bpy
from node_s import *
from functools import reduce



class ListJoinNode(Node, SverchCustomTreeNode):
    ''' ListJoin node '''
    bl_idname = 'ListJoinNode'
    bl_label = 'List Join Node'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    Separate = bpy.props.BoolProperty(name='Separate', description='Show or not vertices', default=True)
    def init(self, context):
        self.inputs.new('StringsSocket', 'slot1', 'slot1')
        self.inputs.new('StringsSocket', 'slot2', 'slot2')
        self.inputs.new('StringsSocket', 'slot3', 'slot3')
        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'data', 'data')
        self.outputs.new('MatrixSocket', 'matrix', 'matrix')
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "Separate", text="Separate lists")
    
    def update(self):
        typ = ''
        slot1 = []
        slot2 = []
        slot3 = []
        if self.inputs['slot1'].links and len(self.inputs['slot1'].links)>0:
            if not self.inputs['slot1'].node.socket_value_update:
                self.inputs['slot1'].node.update()
            if self.inputs['slot1'].links and len(self.inputs['slot1'].links)>0:
                if type(self.inputs['slot1'].links[0].from_socket) == bpy.types.VerticesSocket:
                    slot1 = eval(self.inputs['slot1'].links[0].from_socket.VerticesProperty)
                    typ = 'v'
                elif type(self.inputs['slot1'].links[0].from_socket) == bpy.types.StringsSocket:
                    slot1 = eval(self.inputs['slot1'].links[0].from_socket.StringsProperty)
                    typ = 's'
                elif type(self.inputs['slot1'].links[0].from_socket) == bpy.types.MatrixSocket:
                    slot1 = eval(self.inputs['slot1'].links[0].from_socket.MatrixProperty)
                    typ = 'm'
                    
        if self.inputs['slot2'].links and len(self.inputs['slot2'].links)>0:
            if not self.inputs['slot2'].node.socket_value_update:
                self.inputs['slot2'].node.update()
            if self.inputs['slot2'].links and len(self.inputs['slot2'].links)>0:
                if type(self.inputs['slot2'].links[0].from_socket) == bpy.types.VerticesSocket:
                    slot2 = eval(self.inputs['slot2'].links[0].from_socket.VerticesProperty)
                elif type(self.inputs['slot2'].links[0].from_socket) == bpy.types.StringsSocket:
                    slot2 = eval(self.inputs['slot2'].links[0].from_socket.StringsProperty)
                elif type(self.inputs['slot2'].links[0].from_socket) == bpy.types.MatrixSocket:
                    slot2 = eval(self.inputs['slot2'].links[0].from_socket.MatrixProperty)
                    
        if self.inputs['slot3'].links and len(self.inputs['slot3'].links)>0:
            if not self.inputs['slot3'].node.socket_value_update:
                self.inputs['slot3'].node.update()
            if self.inputs['slot3'].links and len(self.inputs['slot3'].links)>0:
                if type(self.inputs['slot3'].links[0].from_socket) == bpy.types.VerticesSocket:
                    slot3 = eval(self.inputs['slot3'].links[0].from_socket.VerticesProperty)
                elif type(self.inputs['slot3'].links[0].from_socket) == bpy.types.StringsSocket:
                    slot3 = eval(self.inputs['slot3'].links[0].from_socket.StringsProperty)
                elif type(self.inputs['slot3'].links[0].from_socket) == bpy.types.MatrixSocket:
                    slot3 = eval(self.inputs['slot3'].links[0].from_socket.MatrixProperty)
        
        if self.outputs['vertices'].links or self.outputs['data'].links or self.outputs['matrix'].links:
            
            if self.Separate:
                tempob = []
                for i in range(3):
                    ob = []
                    if slot1:
                        ob.extend([a for a in slot1])
                    if slot2:
                        ob.extend([a for a in slot2])
                    if slot3:
                        ob.extend([a for a in slot3])
                
            elif not self.Separate:
                if typ == 'v':
                    all = self.LISTlenV([slot1, slot2, slot3])
                if typ == 's':
                    all = self.LISTlenS([slot1, slot2, slot3])
                if typ == 'm':
                    all = self.LISTlenM([slot1, slot2, slot3])
                tempob = []
                #print (all)
                len0 = len(all[0])
                len1 = len(all[1])
                len2 = len(all[2])
                for i in range(len2):
                    tempob.append(all[2][i])
                    if len1:
                        tempob.append(all[1][i])
                        if len0:
                            tempob.append(all[0][i])
                    len1 -= 1
                    len0 -= 1
                print (tempob)
            if len(self.outputs['vertices'].links)>0 and typ == 'v':
                if not self.outputs['vertices'].node.socket_value_update:
                    self.outputs['vertices'].node.update()
                self.outputs['vertices'].links[0].from_socket.VerticesProperty =  str([tempob])
            if len(self.outputs['data'].links)>0 and typ == 's':
                if not self.outputs['data'].node.socket_value_update:
                    self.outputs['data'].node.update()
                self.outputs['data'].links[0].from_socket.StringsProperty =  str([tempob])
            if len(self.outputs['matrix'].links)>0 and typ == 'm':
                if not self.outputs['matrix'].node.socket_value_update:
                    self.outputs['matrix'].node.update()
                self.outputs['matrix'].links[0].from_socket.MatrixProperty = str([tempob])
                
    def LISTlenV(self, lists):
        #print (lists)
        dicti = {}
        for k, l in enumerate(lists):
            dicti[str(len(l)) + '_' + str(k)] = tuple(l)
        #print(dicti)
        rewrite = []
        for i in sorted(dicti):
            rewrite.append(dicti[i])
        #print (rewrite)
        return rewrite
    
    def LISTlenS(self, lists):
        #print (lists)
        dicti = {}
        for k, l in enumerate(lists):
            dicti[str(len(l)) + '_' + str(k)] = list(l)
        #print(dicti)
        rewrite = []
        for i in sorted(dicti):
            rewrite.append(dicti[i])
        #print (rewrite)
        return rewrite
    
    def LISTlenM(self, lists):
        #print (lists)
        dicti = {}
        for k, l in enumerate(lists):
            dicti[str(len(l)) + '_' + str(k)] = tuple(l)
        #print(dicti)
        rewrite = []
        for i in sorted(dicti):
            rewrite.append(dicti[i])
        #print (rewrite)
        return rewrite

    def update_socket(self, context):
        self.update()



def register():
    bpy.utils.register_class(ListJoinNode)
    
def unregister():
    bpy.utils.unregister_class(ListJoinNode)

if __name__ == "__main__":
    register()



#   Памятка по данным, используемым в сверчке:
#   What is data in Svrchok:
#
#   [[(x0,y0,z0),(x1,y1,z1),(x2,y2,z2)][...     ]...]  that is how it looks ABCD
# 0 [                                               ]  parameter from socket
# 1  [object 0                        ][object 1]...   objects, matrixes
# 2   [vert 0  ],[vert 1  ],[vert 2  ]  [...   ]       vertices, edges, polygons, tuples
# 3    x0,y0,z0   x1,y1,z1   x2,y2,z2                  coordinates, vert_indexes, matrix floats
# ... in future will be flaxiable levels
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