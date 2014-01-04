# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from node_s import *
from util import *


class SortCircleNode(Node, SverchCustomTreeNode):
    ''' SortCircleNode '''
    bl_idname = 'SortCircleNode'
    bl_label = 'Sort Circle'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    is_circle = bpy.props.BoolProperty(name='is_circle', default=True, update=updateNode)
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "is_circle", text="Circle?")
    
    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edges', "edges")
        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'edges', 'edges')
    

    def update(self):
        edge_list, vert_list = [],[]
        if 'vertices' in self.inputs and self.inputs['vertices'].links and \
            type(self.inputs['vertices'].links[0].from_socket) == VerticesSocket:
            if not self.inputs['vertices'].node.socket_value_update:
                self.inputs['vertices'].node.update()  
            vert_list = eval(self.inputs['vertices'].links[0].from_socket.VerticesProperty)
            
        if 'edges' in self.inputs and self.inputs['edges'].links and \
            type(self.inputs['edges'].links[0].from_socket) == StringsSocket:
            if not self.inputs['edges'].node.socket_value_update:
                self.inputs['edges'].node.update()  
            edge_list = eval(self.inputs['edges'].links[0].from_socket.StringsProperty)
               
        if 'vertices' in self.outputs and len(self.outputs['vertices'].links)>0:
            if not self.outputs['vertices'].node.socket_value_update:
                self.outputs['vertices'].node.update()
            vert_res=[]      
            if len(vert_list) and len(edge_list):
                for i in range(len(vert_list)):
                    vert_res.append(self.topologySort( vert_list[i], edge_list[i]))
            #print(len(vert_res)!=len(vert_list[i]))        
            self.outputs['vertices'].VerticesProperty = str(vert_res)
                
            
        if 'edges' in self.outputs and len(self.outputs['edges'].links)>0:
            if not self.outputs['edges'].node.socket_value_update:
                self.outputs['edges'].node.update()
            edge_res = []
            for v_l in vert_list:    
                l=len(v_l)
                if l:
                    if self.is_circle:
                        edge_res.append( [[i,(i+1)%l] for i in range(l)] )
                    else:
                        edge_res.append( [[i,i+1] for i in range(l - 1)])
            self.outputs['edges'].StringsProperty = str(edge_res)



# take a list of verts and edges and sorts them according according to the visual order
# makes order of the geometry follow the topology of the edges
# vert_list, edge_list                             
# [(0, 1),(0, 2),(2, 3),(3, 4),(4, 5),(5, 6),(6, 7)]
# feels like there should be a simpler way... this a bit brute force.

    def topologySort(self, v_l , e_l):  
        if len(v_l) != len(e_l):
            print(len(v_l),len(e_l))
            return self.topologySort2(v_l,e_l)  
        l,l1 = e_l[0]
        res = [l]
        for j in range(len(v_l)-1):
            tmp=[e_l[i] for i in range(len(e_l)) if l in e_l[i] and not l1 in e_l[i] ]
            if len(tmp) == 0:
                break
            if tmp[0][0] in res:
                res.append(tmp[0][1])
                l1,l = l, tmp[0][1]
            else:
                res.append(tmp[0][0])
                l1,l = l, tmp[0][0]
               
        v_res = [v_l[i] for i in res]
        return v_res        
        
    def topologySort2(self, v_l , e_l):    
        l,l1 = e_l[0]
        res = [l,l1]
        
        for j in range(len(v_l)):
            tmp=[e_l[i] for i in range(len(e_l)) if l in e_l[i] and not l1 in e_l[i] ]
            if not len(tmp):
                break
            if tmp[0][0] in res:
                res.append(tmp[0][1])
                l1,l = l, tmp[0][1]
            else:
                res.append(tmp[0][0])
                l1,l = l, tmp[0][0]
        print("res:",len(res),":", len(v_l),":", res ,":",e_l ) 
        if len(res) != len(v_l):
            #unsorted = [i for i in range(len(v_l)) if not i in res]
            print("kanske")           
            l = res[0]
            
            while len(res) < len(v_l): #non cyclic
                tmp=[e_l[i] for i in range(len(e_l)) if l in e_l[i]] 
                print(tmp)
                for i in tmp:
                    if not (i[0] in res and i[1] in res):
                        if l == i[0]:
                            l = i[1]
                        else:
                            l = i[0]
                res.insert(0,l)

        print("res:",len(res),":", len(v_l),":", res) 
           
        v_res = [v_l[i] for i in res]
        return v_res        
        
 

def register():
    bpy.utils.register_class(SortCircleNode)
    
def unregister():
    bpy.utils.unregister_class(SortCircleNode)

if __name__ == "__main__":
    register()
