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
from bpy.props import IntProperty, BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, fullList, multi_socket, levelsOflist)
from sverchok.utils.nodes_mixins.sockets_config import ModifierNode


class LineConnectNodeMK3(ModifierNode, SverchCustomTreeNode, bpy.types.Node):
    """
    UV Connection Node for Sverchok
    Creates edges or polygons by connecting vertices in U or V direction
    Useful for creating surfaces from grid-like vertex arrangements
    """
    bl_idname = 'LineConnectNodeMK3'
    bl_label = 'UV Connection MK3'
    bl_icon = 'GRID'

    base_name = 'vertices '
    multi_socket_type = 'SvVerticesSocket'

    # Direction options
    direction_options = [('U_dir', 'U', 'U direction'), ('V_dir', 'V', 'V direction')]
    
    # Output type options
    output_type_options = [('Pols', 'Pols', 'Polygons'), ('Edges', 'Edges', 'Edges')]

    # Node properties
    join_level: IntProperty(
        name='Join Level', 
        description='Choose connect level of data (see help)',
        default=1, min=1, max=2, update=updateNode)

    output_type: EnumProperty(
        name='Output Type', 
        items=output_type_options, 
        update=updateNode)
    
    direction: EnumProperty(
        name='Direction', 
        items=direction_options, 
        update=updateNode)

    # Cyclic and capping options
    cyclic_u: BoolProperty(
        name='Cycle U', 
        description='Cycle in U direction', 
        default=False, 
        update=updateNode)
        
    cyclic_v: BoolProperty(
        name='Cycle V', 
        description='Cycle in V direction', 
        default=False, 
        update=updateNode)
        
    cap_u: BoolProperty(
        name='Cap U', 
        description='Cap ends in U direction', 
        default=False, 
        update=updateNode)
        
    cap_v: BoolProperty(
        name='Cap V', 
        description='Cap ends in V direction', 
        default=False, 
        update=updateNode)
        
    slice_polygons: BoolProperty(
        name='Slice', 
        description='Slice polygon', 
        default=True, 
        update=updateNode)

    def sv_init(self, context):
        """Initialize node sockets"""
        self.inputs.new('SvVerticesSocket', 'vertices')
        self.outputs.new('SvVerticesSocket', 'vertices')
        self.outputs.new('SvStringsSocket', 'edges')
        self.outputs.new('SvStringsSocket', 'polygons')

    def sv_internal_links(self):
        """Define internal connections between sockets"""
        return [self.inputs[0], self.outputs[0]]

    def draw_buttons(self, context, layout):
        """Draw node UI elements"""
        col = layout.column(align=True)
        
        # Direction selection
        row = col.row(align=True)
        row.label(text='Direction')
        row.prop(self, "direction", expand=True)

        # Cyclic options
        row = col.row(align=True)
        row.label(text='Cycle')
        row.prop(self, "cyclic_u", text="U", toggle=True)
        row.prop(self, "cyclic_v", text="V", toggle=True)
       
        # Capping options
        row = col.row(align=True)
        row.label(text='Cap')
        row.prop(self, "cap_u", text="U", toggle=True)
        row.prop(self, "cap_v", text="V", toggle=True)

        # Output type and slicing
        row = col.row(align=True)
        row.label(text='Make')
        row.prop(self, "output_type", text="polygons", expand=True)
        
        # Show slice option only for polygons
        if self.output_type == "Pols":
            row = col.row(align=True)
            row.label(text='Slice')
            row.prop(self, "slice_polygons", text="Slice", toggle=True)
            row.label(text=' ')

    def create_end_caps(self, object_count, vertices_per_object, flip=False):
        """
        Create end caps for the geometry
        
        Args:
            object_count (int): Number of objects/rows
            vertices_per_object (int): Number of vertices per object
            flip (bool): Whether to flip the cap orientation
            
        Returns:
            list: List of cap polygons
        """
        if not flip:
            # Standard end caps
            caps = [
                [j * vertices_per_object for j in reversed(range(object_count))],
                [j * vertices_per_object + vertices_per_object - 1 for j in range(object_count)]
            ]
        else:
            # Flipped end caps
            caps = [
                [j for j in reversed(range(object_count))],
                [j + object_count * (vertices_per_object - 1) for j in range(object_count)]
            ]
        return caps

    def join_vertices(self, vertices_list, target_length):
        """
        Join vertices from multiple objects into a single list
        
        Args:
            vertices_list (list): List of vertex lists
            target_length (int): Target length for padding
            
        Returns:
            list: Joined and padded vertex list
        """
        joined_vertices = []
        for vertex_group in vertices_list:
            # Pad vertex groups to have consistent length
            fullList(list(vertex_group), target_length)
            joined_vertices.extend(vertex_group)
        return joined_vertices

    def connect_vertices(self, vertices_data, direction, cyclic_u, cyclic_v, join_level, output_type, slice_polygons, cap_u, cap_v):
        """
        Main connection logic - creates edges or polygons from vertices
        
        Args:
            vertices_data (list): Input vertex data
            direction (str): Connection direction ('U_dir' or 'V_dir')
            cyclic_u (bool): Whether to cycle in U direction
            cyclic_v (bool): Whether to cycle in V direction
            join_level (int): Data join level
            output_type (str): Output type ('Pols' or 'Edges')
            slice_polygons (bool): Whether to slice polygons
            cap_u (bool): Whether to cap U ends
            cap_v (bool): Whether to cap V ends
            
        Returns:
            tuple: (processed_vertices, edge/polygon_data)
        """
        processed_vertices = []
        vertex_counts = []
        connection_edges = []
        connection_polygons = []

        # Flatten vertex data and count vertices
        for vertex_group in vertices_data:
            for vertex_list in vertex_group:
                processed_vertices.append(vertex_list)
                vertex_counts.append(len(vertex_list))

        object_count = len(processed_vertices)  # Number of objects/rows
        max_vertices_per_object = max(vertex_counts)  # Max vertices in any object

        if direction == 'U_dir':
            if output_type == "Pols":
                # Polygon generation in U direction
                all_vertices = []
                polygons = []
                
                # Join all vertices into a single list
                for vertex_list in processed_vertices:
                    all_vertices.extend(vertex_list)

                current_index = 0
                previous_indices = []
                
                if slice_polygons:
                    # Create polygons by slicing across objects
                    polygon_indices = [
                        [j * max_vertices_per_object + i for j in range(object_count)] 
                        for i in range(max_vertices_per_object)
                    ]
                    polygons = [list(polygon) for polygon in zip(*polygon_indices)]
                else:
                    # Create polygons by connecting adjacent objects
                    first_row_indices = []
                    
                    for i, vertex_count in enumerate(vertex_counts):
                        current_indices = []
                        for w in range(vertex_count):
                            current_indices.append(current_index)
                            current_index += 1
                            
                        if i > 0:
                            # Create quads between current and previous row
                            combined_indices = current_indices + previous_indices[::-1]
                            quads = [
                                (combined_indices[k], combined_indices[k+1], 
                                 combined_indices[-(k+2)], combined_indices[-(k+1)])
                                for k in range((len(combined_indices) - 1) // 2)
                            ]
                            polygons.extend(quads)
                            
                            # Handle cyclic connections
                            if i == len(vertex_counts) - 1 and cyclic_u:
                                combined_indices = first_row_indices + current_indices[::-1]
                                quads = [
                                    (combined_indices[k], combined_indices[k+1], 
                                     combined_indices[-(k+2)], combined_indices[-(k+1)])
                                    for k in range((len(combined_indices) - 1) // 2)
                                ]
                                polygons.extend(quads)

                            if i == len(vertex_counts) - 1 and cyclic_v:
                                quads = [
                                    [(k-1) * max_vertices_per_object, k * max_vertices_per_object - 1, 
                                     (k+1) * max_vertices_per_object - 1, k * max_vertices_per_object]
                                    for k in range(object_count) if k > 0
                                ]
                                polygons.extend(quads)
                                
                        if i == 0 and cyclic_u:
                            first_row_indices = current_indices
                            if cyclic_v:
                                polygons.append([
                                    0, (object_count - 1) * max_vertices_per_object, 
                                    object_count * max_vertices_per_object - 1, max_vertices_per_object - 1
                                ])
                                
                        previous_indices = current_indices
                    
                    # Add end caps if requested
                    if cap_u:
                        polygons.extend(self.create_end_caps(object_count, max_vertices_per_object))
                    if cap_v:
                        polygons.extend(self.create_end_caps(max_vertices_per_object, object_count, flip=True))
                        
                processed_vertices = [all_vertices]
                connection_polygons = [polygons]
                connection_edges = [[]]
                
            elif output_type == "Edges":
                # Edge generation in U direction
                for k, vertex_list in enumerate(processed_vertices):
                    edges = []
                    for i in range(len(vertex_list) - 1):
                        edges.append([i, i + 1])
                    if cyclic_u:
                        edges.append([0, len(vertex_list) - 1])
                    connection_edges.append(edges)
                #connection_polygons = [[] for i in range(len(connection_edges))]
                connection_polygons = [[]]

        elif direction == 'V_dir':
            polygons = []
            
            if output_type == "Pols":
                if slice_polygons:
                    # Join vertices and create polygons by slicing
                    joined_vertices = self.join_vertices(processed_vertices, max_vertices_per_object)
                    for i in range(len(processed_vertices[0])):
                        polygon_indices = [j * max_vertices_per_object + i for j in range(object_count)]
                        polygons.append(polygon_indices)
                else:
                    # Transpose the vertex matrix and create polygons
                    transposed_vertices = [list(column) for column in zip(*processed_vertices)]
                    processed_vertices = transposed_vertices
                    
                    joined_vertices = self.join_vertices(processed_vertices, object_count)
                    
                    # Create quads from the transposed vertices
                    for i in range(len(processed_vertices) - 1):
                        for k in range(len(processed_vertices[i]) - 1):
                            polygons.append([
                                i * object_count + k,
                                (i + 1) * object_count + k,
                                (i + 1) * object_count + k + 1,
                                i * object_count + k + 1
                            ])
                            
                            # Handle cyclic connections
                            if i == 0 and cyclic_v:
                                polygons.append([
                                    k + 1,
                                    (len(processed_vertices) - 1) * object_count + k + 1,
                                    (len(processed_vertices) - 1) * object_count + k,
                                    k
                                ])
                                
                        if i == 0 and cyclic_u and cyclic_v:
                            polygons.append([
                                0,
                                (len(processed_vertices) - 1) * object_count,
                                len(processed_vertices) * object_count - 1,
                                object_count - 1
                            ])
                            
                        if i == 0 and cyclic_u:
                            quads = [
                                [(k - 1) * object_count, k * object_count - 1, 
                                 (k + 1) * object_count - 1, k * object_count]
                                for k in range(len(processed_vertices)) if k > 0
                            ]
                            polygons.extend(quads)

                    # Add end caps if requested
                    if cap_v:
                        polygons.extend(self.create_end_caps(len(processed_vertices), object_count))
                    if cap_u:
                        polygons.extend(self.create_end_caps(object_count, len(processed_vertices), flip=True))
                processed_vertices = [joined_vertices]
                connection_polygons.append(polygons)
                connection_edges = [[]]
                        
            elif output_type == "Edges":
                # Edge generation in V direction
                joined_vertices = self.join_vertices(processed_vertices, max_vertices_per_object)
                vertices_out = []
                for i in range(len(processed_vertices[0])):
                    edge_indices = [j * max_vertices_per_object + i for j in range(object_count)]
                    edge_indices_local = [i for i in range(object_count)]
                    vertices_out.append([joined_vertices[i] for i in edge_indices])
                    polygons_ = []
                    for j, vertex_index in enumerate(edge_indices_local):
                        if j == 0 and cyclic_v:
                            polygons_.append([edge_indices_local[0], edge_indices_local[-1]])
                        elif j == 0:
                            continue
                        else:
                            polygons_.append([vertex_index, edge_indices_local[j - 1]])
                    polygons.append(polygons_)
                processed_vertices = vertices_out
                connection_edges.extend(polygons)
                #connection_polygons = [[] for i in range(len(connection_edges))]
                connection_polygons = [[]]
            
        return processed_vertices, connection_edges, connection_polygons

    def sv_update(self):
        """Update node sockets based on connections"""
        multi_socket(self, min=1)

    def process(self):
        """Main processing function"""
        if not self.inputs[0].is_linked:
            return
            
        # Get input data
        input_slots = [socket.sv_get() for socket in self.inputs if socket.is_linked]
        data_depth = levelsOflist(input_slots)
        
        output_vertices = []
        output_edges = []
        output_polygons = []
        
        if data_depth == 4:
            # Single level processing
            output_vertices, output_edges, output_polygons = self.connect_vertices(
                input_slots, self.direction, self.cyclic_u, self.cyclic_v, 
                data_depth, self.output_type, self.slice_polygons, self.cap_u, self.cap_v
            )
        elif data_depth == 5:
            # Nested level processing
            for slot in input_slots:
                for sub_slot in slot:
                    result_vertices, result_edges, result_polygons = self.connect_vertices(
                        [sub_slot], self.direction, self.cyclic_u, self.cyclic_v, 
                        data_depth, self.output_type, self.slice_polygons, self.cap_u, self.cap_v
                    )
                    output_vertices.extend(result_vertices)
                    output_edges.extend(result_edges)
                    output_polygons.extend(result_polygons)
        else:
            return

        # Set outputs
        if self.outputs['vertices'].is_linked:
            self.outputs['vertices'].sv_set(output_vertices)
        if self.outputs['edges'].is_linked:
            self.outputs['edges'].sv_set(output_edges)
        if self.outputs['polygons'].is_linked:
            self.outputs['polygons'].sv_set(output_polygons)


def register():
    """Register the node"""
    bpy.utils.register_class(LineConnectNodeMK3)


def unregister():
    """Unregister the node"""
    bpy.utils.unregister_class(LineConnectNodeMK3)

if __name__ == '__main__': register()
