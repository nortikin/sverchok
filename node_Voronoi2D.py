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
from types import *
from voronoi import Site,computeVoronoiDiagram,computeDelaunayTriangulation

class Voronoi2DNode(Node, SverchCustomTreeNode):
    ''' Voronoi 2d line '''
    bl_idname = 'Voronoi2DNode'
    bl_label = 'Voronoi'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    clip = bpy.props.FloatProperty(name = 'clip', description='Clipping Distance', default=1.0, min=0, options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        #self.inputs.new('StringsSocket', "SizeX", "SizeX")
        #self.inputs.new('StringsSocket', "SizeY", "SizeY")
 #       self.inputs.new('StringsSocket', "Clipping", "Clipping")
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
#        self.outputs.new('StringsSocket', "Polygons", "Polygons")
# Polygon output does not work right now.
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "clip", text="Clipping")        

    def update(self):
        # inputs
        points_in = []
        if 'Vertices' in self.inputs and len(self.inputs['Vertices'].links)>0:
            if not self.inputs['Vertices'].node.socket_value_update:
                self.inputs['Vertices'].node.update()
            points_in = eval(self.inputs['Vertices'].links[0].from_socket.VerticesProperty)
        
        pts_out = []
#        polys_out = []
        edges_out = []
        for obj in points_in:
            pt_list = []
            x_max = obj[0][0]
            x_min = obj[0][0]
            y_min = obj[0][1]
            y_max = obj[0][1]
            #creates points in format for voronoi library, throwing away z
            for pt in obj:     
                x,y = pt[0],pt[1]
                x_max = max(x,x_max)
                x_min = min(x,x_min)
                y_max = max(y,y_max)
                y_min = min(x,x_min)
                pt_list.append(Site(pt[0],pt[1]))
            
            res = computeVoronoiDiagram(pt_list)
                                
            edges = res[2]
            delta = self.clip
            x_max = x_max + delta
            y_max = y_max + delta
            
            x_min = x_min - delta
            y_min = y_min - delta
            
            #clipping box to bounding box I think.
            pts_tmp = []
            for pt in res[0]:
                x,y=pt[0],pt[1]
                if x < x_min:
                    x = x_min
                if x > x_max:
                    x = x_max
                
                if y < y_min:
                    y = y_min
                if y > y_max:
                    y = y_max
                pts_tmp.append((x,y,0))
                
            pts_out.append(pts_tmp)                 
                    
            edges_out.append([ (edge[1], edge[2]) for edge in edges if -1 not in edge ])
                     

        # outputs
        if 'Vertices' in self.outputs and len(self.outputs['Vertices'].links)>0:
            if not self.outputs['Vertices'].node.socket_value_update:
                self.outputs['Vertices'].node.update()
            
            self.outputs['Vertices'].VerticesProperty = str(pts_out)
   
            
   
        if 'Edges' in self.outputs and len(self.outputs['Edges'].links)>0:
            if not self.outputs['Edges'].node.socket_value_update:
                self.outputs['Edges'].node.update()
                
            self.outputs['Edges'].StringsProperty = str(edges_out)
            
        
   
#         if 'Polygons' in self.outputs and len(self.outputs['Polygons'].links)>0:
#             if not self.outputs['Polygons'].node.socket_value_update:
#                 self.outputs['Polygons'].node.update()
#             self.outputs['Polygons'].StringsProperty=str([polys_out])
                  
    def update_socket(self, context):
        self.update()

#computeDelaunayTriangulation

class DelaunayTriangulation2DNode(Node, SverchCustomTreeNode):
    ''' DelaunayTriangulation '''
    bl_idname = 'DelaunayTriangulation2DNode'
    bl_label = 'Delaunay 2D'
    bl_icon = 'OUTLINER_OB_EMPTY'
    

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")   
 #       self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")
    

    def update(self):
        # inputs
        points_in = []
        if 'Vertices' in self.inputs and len(self.inputs['Vertices'].links)>0:
            if not self.inputs['Vertices'].node.socket_value_update:
                self.inputs['Vertices'].node.update()
            points_in = eval(self.inputs['Vertices'].links[0].from_socket.VerticesProperty)
        tris_out=[]
        edges_out=[]
        for obj in points_in:
            pt_list = []

            for pt in obj:
                pt_list.append(Site(pt[0],pt[1]))
            
          #  print("obj",obj,pt_list)     
            res = computeDelaunayTriangulation(pt_list) 
            
            tris_out.append([tri for tri in res if -1 not in tri] )

        if 'Edges' in self.outputs and len(self.outputs['Edges'].links)>0:
            if not self.outputs['Edges'].node.socket_value_update:
                self.outputs['Edges'].node.update()
                
            self.outputs['Edges'].StringsProperty = str(edges_out)
                
        if 'Polygons' in self.outputs and len(self.outputs['Polygons'].links)>0:
            if not self.outputs['Polygons'].node.socket_value_update:
                self.outputs['Polygons'].node.update()
                
            self.outputs['Polygons'].StringsProperty = str(tris_out)



    
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(Voronoi2DNode)
    bpy.utils.register_class(DelaunayTriangulation2DNode)
def unregister():
    bpy.utils.unregister_class(Voronoi2DNode)
    bpy.utils.unregister_class(DelaunayTriangulation2DNode)

if __name__ == "__main__":
    register()