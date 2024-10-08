# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from concurrent.futures import ThreadPoolExecutor

import collections
import itertools
import numpy as np
import bpy, math, bmesh
from bpy.props import FloatProperty, BoolProperty, IntProperty
from mathutils import Vector, Matrix
from more_itertools import sort_together

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.geom_2d.merge_mesh import merge_mesh
from sverchok.utils.nodes_mixins.sockets_config import ModifierLiteNode
from sverchok.data_structure import dataCorrect, updateNode, zip_long_repeat, ensure_nesting_level, flatten_data
#from sverchok.utils.mesh.separate_loose_mesh import separate_loose_mesh
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.nodes.analyzer.mesh_filter import Edges
from sverchok.nodes.vector.vertices_sort import sort_vertices_by_connexions
from sverchok.utils.modules.polygon_utils import areas_from_polygons
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator

from pySVCGAL.pySVCGAL import pySVCGAL_extrude_skeleton

def vertices_sort_by_edges(verts_in, edges_in):
    edges_indexes = list(itertools.chain(*edges_in))
    verts_out = []
    if len(edges_indexes)==0:
        pass
    else:
        edges_indexes_0 = edges_indexes[ ::2]
        edges_indexes_1 = edges_indexes[1::2]

        chain = []
        pos = 0
        v0_idx = edges_indexes_0[pos]
        chain.append(v0_idx)
        
        while True:
            v1_idx = edges_indexes_1[pos]
            if v1_idx in chain:
                # цикл прервать, кольцо
                break
            chain.append(v1_idx)
            if v1_idx in edges_indexes_0:
                pos = edges_indexes_0.index(v1_idx)
                #v0_idx = edges_indexes_0[pos]
            else:
                # конец цепочки
                break

        # Попробовать построить цепочку в обратном направлении (тут не в курсе, вышли из-за кольца
        # или что достигнут конец цепочки:	
        
        v1_idx = chain[0]
        if v1_idx not in edges_indexes_1:
            pass
        else:
            pos = edges_indexes_1.index( v1_idx )
            while True:
                v0_idx = edges_indexes_0[pos]
                if v0_idx in chain:
                    # цикл прервать, кольцо
                    break
                chain.append(v0_idx)
                if v0_idx in edges_indexes_1:
                    pos = edges_indexes_1.index(v0_idx)
                    #v1_idx = edges_indexes_1[pos]
                else:
                    # конец цепочки
                    break
        
        np_verts = np.array(verts_in)
        verts_out = np_verts[chain].tolist()
    return verts_out
    pass

def separate_loose_mesh(verts_in, poly_edge_in):
        ''' separate a mesh by loose parts.
        input:
          1. list of verts
          2. list of edges/polygons
        output: list of
          1. separated list of verts
          2. separated list of edges/polygons with new indices of separated elements
          3. separated list of edges/polygons (like 2) with old indices
        '''
        verts_out = []
        poly_edge_out = []
        poly_edge_old_indexes_out = []  # faces with old indices 

        # build links
        node_links = {}
        for edge_face in poly_edge_in:
            for i in edge_face:
                if i not in node_links:
                    node_links[i] = set()
                node_links[i].update(edge_face)

        nodes = set(node_links.keys())
        n = nodes.pop()
        node_set_list = [set([n])]
        node_stack = collections.deque()
        node_stack_append = node_stack.append
        node_stack_pop = node_stack.pop
        node_set = node_set_list[-1]
        # find separate sets
        while nodes:
            for node in node_links[n]:
                if node not in node_set:
                    node_stack_append(node)
            if not node_stack:  # new mesh part
                n = nodes.pop()
                node_set_list.append(set([n]))
                node_set = node_set_list[-1]
            else:
                while node_stack and n in node_set:
                    n = node_stack_pop()
                nodes.discard(n)
                node_set.add(n)
        # create new meshes from sets, new_pe is the slow line.
        if len(node_set_list) >= 1:
            for node_set in node_set_list:
                mesh_index = sorted(node_set)
                vert_dict = {j: i for i, j in enumerate(mesh_index)}
                new_vert = [verts_in[i] for i in mesh_index]
                new_pe = [[vert_dict[n] for n in fe]
                            for fe in poly_edge_in
                            if fe[0] in node_set]
                old_pe = [fe for fe in poly_edge_in
                             if fe[0] in node_set]
                verts_out.append(new_vert)
                poly_edge_out.append(new_pe)
                poly_edge_old_indexes_out.append(old_pe)
        elif node_set_list:  # no reprocessing needed
            verts_out.append(verts_in)
            poly_edge_out.append(poly_edge_in)
            poly_edge_old_indexes_out.append(poly_edge_in)

        return verts_out, poly_edge_out, poly_edge_old_indexes_out

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


class SvSaveCGALDatFile(bpy.types.Operator, SvGenericNodeLocator):
    ''' Save coords and angles to the file .dat for CGAL '''
    bl_idname = "node.sverchok_save_cgal_dat_file"
    bl_label = "Save coords and angles to the file .dat for CGAL"
    
    def sv_execute(self, context, node):
        if hasattr(node, 'saveCGALDatFile')==True:
            node.saveCGALDatFile()
            #text = node.dataAsString()
            #context.window_manager.clipboard = text
            ShowMessageBox("File saved")
        pass


class SvStraightSkeleton2D(ModifierLiteNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Merge two 2d meshes

    Each mesh can have disjoint parts
    Only X and Y coordinate takes in account
    """
    bl_idname = 'SvStraightSkeleton2D'
    bl_label = 'Straight Skeleton 2D'
    bl_icon = 'MOD_OUTLINE'

    def wrapper_tracked_ui_draw_op(self, layout_element, operator_idname, **keywords):
        """
        this wrapper allows you to track the origin of a clicked operator, by automatically passing
        the node_name and tree_name to the operator.

        example usage:

            row.separator()
            self.wrapper_tracked_ui_draw_op(row, "node.view3d_align_from", icon='CURSOR', text='')

        """
        op = layout_element.operator(operator_idname, **keywords)
        op.node_name = self.name
        op.tree_name = self.id_data.name
        return op

    ss_angle: FloatProperty(
        default=0.785398, name="a float", update=updateNode,
        description = "Angle of cliff",
        subtype='ANGLE',
    ) # type: ignore

    ss_height: FloatProperty(
        default=1.0, name="a float", update=updateNode,
        description = "Max height",
        #subtype='ANGLE',
    ) # type: ignore

    merge_meshes: BoolProperty(
        name='Merge',
        description='Apply modifier geometry to import (original untouched)',
        default=True, update=updateNode) # type: ignore

    verbose_messages_while_process: BoolProperty(
        name='Verbose',
        description='Show additional debug info in console',
        default=True, update=updateNode) # type: ignore


    def draw_failed_contours_vertices_out_socket(self, socket, context, layout):
        #layout.prop(self, 'enable_verts_attribute_sockets', icon='STICKY_UVS_DISABLE', text='', toggle=True)
        if socket.objects_number>0:
            layout.label(text=f'', icon='ERROR')
        layout.label(text=f'{socket.label} ')
        if socket.is_linked:  # linked INPUT or OUTPUT
            layout.label(text=f". {socket.objects_number or ''}")
        elif socket.is_output:  # unlinked OUTPUT
            layout.separator()


    def draw_buttons(self, context, layout):
        col = layout.column()
        col.prop(self, 'ss_angle')
        #col.prop(self, 'ss_height')
        col.prop(self, 'merge_meshes')
        col.prop(self, 'verbose_messages_while_process')
        ui_file_save_dat = col.row()
        self.wrapper_tracked_ui_draw_op(ui_file_save_dat, SvSaveCGALDatFile.bl_idname, text='', icon='DISK_DRIVE')

        
        pass

    def draw_buttons_ext(self, context, layout):
        col = layout.column(align=True)
        pass

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvStringsSocket' , 'edges')
        self.inputs.new('SvStringsSocket' , 'polygons')
        self.inputs.new('SvStringsSocket' , 'ssangles').prop_name = 'ss_angle'
        self.inputs.new('SvStringsSocket' , 'ssheight').prop_name = 'ss_height'
        self.inputs.new('SvTextSocket'    , 'file_name')
        #self.inputs.new('SvMatrixSocket'  , "matrixes")

        self.inputs['vertices'].label = 'Vertices'
        self.inputs['edges'].label = 'Edges'
        self.inputs['polygons'].label = 'Polygons'
        self.inputs['ssangles'].label = 'Angles'
        self.inputs['ssheight'].label = 'Height'
        self.inputs['file_name'].label = 'File Name'
        #self.inputs['matrixes'].label = 'Matrixes'

        self.outputs.new('SvVerticesSocket', 'vertices')
        self.outputs.new('SvStringsSocket' , 'edges')
        self.outputs.new('SvStringsSocket' , 'polygons')
        self.outputs.new('SvVerticesSocket', 'boundaries')
        self.outputs.new('SvVerticesSocket', 'objects_boundaries_vertices')
        self.outputs.new('SvVerticesSocket', 'failed_contours_vertices')

        self.outputs['vertices'].label = 'Vertices'
        self.outputs['edges'].label = 'Edges'
        self.outputs['polygons'].label = 'Polygons'
        self.outputs['boundaries'].label = 'Boundaries'
        self.outputs['objects_boundaries_vertices'].label = 'Object Boud.Verts.'
        self.outputs['failed_contours_vertices'].label = 'Wrong contours verts'
        self.outputs['failed_contours_vertices'].custom_draw = 'draw_failed_contours_vertices_out_socket'

    def process(self):
        if not all([sock.is_linked for sock in self.inputs if sock.name in ['vertices', 'edges', 'polygons'] ]):
            return
        if not any([sock.is_linked for sock in self.outputs]):
            return
        
        #print(f"== stright skeleton node start ===============================")
        inputs = self.inputs
        _Vertices  = inputs['vertices'].sv_get(default=[[]], deepcopy=False)
        Vertices3  = ensure_nesting_level(_Vertices, 3)
        _Edges     = inputs['edges'].sv_get(default=[[]], deepcopy=False)
        Edges3     = ensure_nesting_level(_Edges, 3)
        _Faces     = inputs['polygons'].sv_get(default=[[]], deepcopy=False)
        Faces3     = ensure_nesting_level(_Faces, 3)
        _ssangles  = inputs['ssangles'].sv_get(default=[[self.ss_angle]], deepcopy=False)
        ssangles3  = ensure_nesting_level(_ssangles, 3)
        _ssheights  = inputs['ssheight'].sv_get(default=[[self.ss_height]], deepcopy=False)
        ssheights3  = ensure_nesting_level(_ssheights, 3)
        
        _file_names = inputs['file_name'].sv_get(default=[[]], deepcopy=False)
        file_names3 = ensure_nesting_level(_file_names, 3)
        file_name_dat = None
        if len(file_names3)>0 and len(file_names3[0])>0 and len(file_names3[0][0])>0:
            file_name_dat = file_names3[0][0][0]

        res_verts = []
        res_boundaries_verts = []
        res_edges = []
        res_faces = []

        objects_boundaries = []
        objects_heights = []
        objects_angles_of_boundaries = []
        objects_area_boundaries = []

        contours_failed_at_all = []

        for verts_i, edges_i, faces_i, ssangle3, ssheight3 in zip_long_repeat(Vertices3, Edges3, Faces3, ssangles3, ssheights3):
            ssheight = ssheight3[0][0]
            # separate objects of loose parts (objects can has islands. Every island have to be separated)
            verts_i_separated, faces_i_separated, _ = separate_loose_mesh(verts_i, faces_i)

            for I in range(len(verts_i_separated)):
                verts_i_separated_I, faces_i_separated_I = verts_i_separated[I], faces_i_separated[I]

                try:
                    bm = bmesh_from_pydata(verts_i_separated_I, None, faces_i_separated_I, normal_update=True)
                    bm.edges.ensure_lookup_table()
                    edges = [[e.verts[0].index, e.verts[1].index] for e in bm.edges]
                    BoundaryEdges, NonBoundaryEdges, MaskBoundaryEdges = Edges.process(bm, "Boundary", edges)
                    # BoundaryVerticesIndexes = []
                    # for e in BoundaryEdges:
                    #     BoundaryVerticesIndexes.extend(e)
                    # BoundaryVerticesIndexes = set(BoundaryVerticesIndexes)
                    # verts_i_separated_I = [verts_i_separated_I[I] for I in BoundaryVerticesIndexes]
                    bm.free()
                except Exception as ex:
                    # Keep shape to show as errors in the future
                    contours_failed_at_all.append(verts_i_separated_I)
                    continue

                # separate contours of every island
                verts_boundaries, edges_boundaries, _ = separate_loose_mesh(verts_i_separated_I, BoundaryEdges)

                object_boundaries = []
                object_area_boundaries = []
                objects_angles_of_boundary = []
                failed_contours_vertices = []
                areas = []
                for I in range(len(verts_boundaries)):
                    verts_boundaries_I, edges_boundaries_I = verts_boundaries[len(verts_boundaries)-1-I], edges_boundaries[len(verts_boundaries)-1-I]
                    #vect_boundaries_I_sorted, pol_edge_new, index_new = sort_vertices_by_connexions(verts_boundaries_I, edges_boundaries_I, True)
                    vect_boundaries_I_sorted = vertices_sort_by_edges(verts_boundaries_I, edges_boundaries_I)
                    res_boundaries_verts.append(vect_boundaries_I_sorted)
                    area = areas_from_polygons(vect_boundaries_I_sorted, [list(range(len(vect_boundaries_I_sorted)))], )
                    areas.append(area[0])
                    object_boundaries.append(vect_boundaries_I_sorted)
                    object_area_boundaries.append({"area":area, "object_boundaries":vect_boundaries_I_sorted})
                    objects_angles_of_boundary.append( [self.ss_angle*180/math.pi,]*len(verts_boundaries_I) )
                    pass
                srt = sort_together([areas, object_boundaries, objects_angles_of_boundary])
                object_boundaries_sorted, objects_angles_of_boundary_sorted = list(reversed(srt[1])), list(reversed(srt[2]))
                objects_boundaries.append(object_boundaries_sorted)
                objects_heights.append(ssheight)
                objects_angles_of_boundaries.append( objects_angles_of_boundary_sorted )
                objects_area_boundaries.append(object_area_boundaries)
                pass
            pass

        
        if not file_name_dat:
            lst_errors = []
            def parallel_extrude_skeleton(data1):
                #new_mesh = pySVCGAL_extrude_skeleton(self.ss_height/1.0, objects_boundaries_I, objects_angles_of_boundaries_I, True)
                new_mesh = pySVCGAL_extrude_skeleton( *data1 )
                return new_mesh
            with ThreadPoolExecutor() as executor:
                data = []
                data_copy = []
                for I in range(len(objects_boundaries)):
                    objects_boundaries_I = objects_boundaries[I]
                    objects_heights_I = objects_heights[I]
                    objects_angles_of_boundaries_I = objects_angles_of_boundaries[I]
                    data     .append( [I, objects_heights_I/1.0, objects_boundaries_I, objects_angles_of_boundaries_I, self.verbose_messages_while_process] )
                    data_copy.append( {'polygon_id':I, 'height':objects_heights_I/1.0, 'boundaries' : objects_boundaries_I, 'angles' : objects_angles_of_boundaries_I, 'verbose' : self.verbose_messages_while_process} )

                # run all skeletons
                data_processed = list( executor.map(parallel_extrude_skeleton, data))
                faces_delta = 0
                object_verts = []
                object_faces = []
                lst_errors1 = []
                for data1 in data_processed:
                    polygon_id = data1['polygon_id']
                    if data1['has_error']==True:
                        if 'ftcs_count' in data1 and data1['ftcs_count']>0:
                            lst_errors1.append(f"Failed polygon_id: {polygon_id}. ")
                            if data1['str_error']:
                                lst_errors1[-1] = lst_errors1[-1] + (data1['str_error'])
                            for s in data1['ftcs_vertices_description']:
                                if s:
                                    lst_errors1.append(f'{s}')
                            failed_contours_vertices.extend(data1['ftcs_vertices_list'])
                        pass
                    else:
                        #print(f"\nPolygon_id: {polygon_id} is good. It has no errors")
                        if self.merge_meshes==True:
                            object_verts.extend(data1['vertices'])
                            object_faces.extend( [ list(map(lambda n: n+faces_delta, face)) for face in data1['faces'] ] )
                            faces_delta+=len(data1['vertices'])
                        else:
                            res_verts.append( data1['vertices'] )
                            res_faces.append( data1['faces']    )
                    pass
                lst_errors.extend(lst_errors1)

                if self.merge_meshes==True:
                    res_verts.append(object_verts)
                    res_faces.append(object_faces)
                # else:
                #     res_verts.extend(object_verts)
                #     res_faces.extend(object_faces)
                if len(contours_failed_at_all)>0:
                    failed_contours_vertices.extend(contours_failed_at_all)
                pass

            print("")
            print("Node Skeleton Finished.")
            if lst_errors:
                for s in lst_errors:
                    print(s)
                if self.verbose_messages_while_process==False:
                    print("")
                    print("for more info turn on verbose mode in node")


        else: # file_name_dat:
            # faces_delta = 0
            # object_verts = []
            # object_faces = []
            # for I in range(len(objects_boundaries)):
            #     #print(f"== stright skeleton {I} ===============================")
            #     objects_boundaries_I = objects_boundaries[I]
            #     objects_angles_of_boundaries_I = objects_angles_of_boundaries[I]
            #     new_mesh = pySVCGAL_extrude_skeleton(self.ss_height/1.0, objects_boundaries_I, objects_angles_of_boundaries_I, True)
            #     object_verts.extend(new_mesh['vertices'])
            #     object_faces.extend( [ list(map(lambda n: n+faces_delta, face)) for face in new_mesh['faces'] ] )
            #     faces_delta+=len(new_mesh['vertices'])
            #     # res_verts.append(new_mesh['vertices'])
            #     # res_faces.append(new_mesh['faces'])
            #     pass
            # res_verts.append(object_verts)
            # res_faces.append(object_faces)

            lines_verts = []
            lines_angles = []
            # Записывать вершины только первого объекта, т.к. только один объект и может быть рассчитал в CGAL
            # Когда сделаю компонент, то тогда передам все объекты по очереди.
            objects_boundaries_0 = objects_boundaries[0]
            for I in range(len(objects_boundaries_0)):
                objects_boundaries_0_I = objects_boundaries_0[I]
                lines_verts .append(str(len(objects_boundaries_0_I)),)
                if len(objects_boundaries_0_I)>0:
                    # Если контур только один, внешний, то добавление количества углов приводит к сбою.
                    # При обном контуре не добавлять количество углов в первую строку
                    lines_angles.append(str(len(objects_boundaries_0_I)),)
                
                for J, vert in enumerate(objects_boundaries_0_I):
                    v_str = [str(v) for v in vert[:2] ]
                    v_line = " ".join(v_str)
                    lines_verts.append(v_line)
                    lines_angles.append( str(self.ss_angle*180/math.pi) )
            txt_verts  = "\n".join(lines_verts)
            txt_angles = "\n".join(lines_angles)

            print(f"stright skeleton node write to file")
            with open(file_name_dat, "w") as file:
                file.write(txt_verts)
                print(f'Записаны вершины {len(lines_verts)-1}: {file_name_dat}')
            with open(file_name_dat+'.angles', "w") as file:
                file.write(txt_angles)
                print(f'Записаны углы: {len(lines_angles)-1}: {file_name_dat}.angles')

        self.outputs['vertices'].sv_set(res_verts)
        self.outputs['edges'].sv_set(res_edges)
        self.outputs['polygons'].sv_set(res_faces)
        self.outputs['boundaries'].sv_set(res_boundaries_verts)
        self.outputs['objects_boundaries_vertices'].sv_set(objects_boundaries)
        self.outputs['failed_contours_vertices'].sv_set(failed_contours_vertices)

        pass
    
    def saveCGALDatFile(self):
        if not all([sock.is_linked for sock in self.inputs if sock.name not in ['ssangles', 'file_name'] ]):
            return 'Не подключены сокеты Vertices и Faces. Файлы не записаны.'

        print("file .dat saved")
        pass

classes = [SvSaveCGALDatFile, SvStraightSkeleton2D,]
register, unregister = bpy.utils.register_classes_factory(classes)