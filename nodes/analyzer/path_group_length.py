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
from bpy.props import BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, ensure_nesting_level
import numpy as np
from collections import defaultdict

def edges_aux(vertices):
    '''create auxiliary edges array '''
    v_len = [len(v) for v in vertices]
    v_len_max = max(v_len)
    np_edges = np.add.outer(np.arange(v_len_max - 1), [0, 1])

    return [np_edges]

def edges_length(meshes, need_total=False, need_cumsum=False, need_cumsum1=False, as_numpy=False):
    '''calculate edges length '''

    segments_lengths_out = []
    segments_groups_out = []
    cumsum_out = []
    cumsum_1_out = []
    summary_lengths_out = []
    summary_lengths_groups_out = []

    for vertices, edges, edges_groups in zip(*meshes):
        np_verts = np.array(vertices)
        if type(edges[0]) in (list, tuple):
            np_edges = np.array(edges)
        else:
            np_edges = edges[:len(vertices)-1, :]

        general_vect = np_verts[np_edges[:, 0], :] - np_verts[np_edges[:, 1], :]
        vect_groups = group_values_np(general_vect, edges_groups)

        lengths_out1                = np.linalg.norm(general_vect, axis=1).tolist()
        summary_lengths_out1        = []
        summary_lengths_groups_out1 = []
        segments_groups_out1        = edges_groups
        cumsum_out1                 = []
        cumsum_1_out1               = []


        for id in vect_groups:
            vect_groups_id = vect_groups[id]
            lengths_groups_id = np.linalg.norm(vect_groups_id, axis=1)
            if need_cumsum or need_cumsum1 or need_total:
                total_length = np.sum(lengths_groups_id)[np.newaxis]
            else:
                total_length = None

            if need_cumsum or need_cumsum1:
                cumsum = np.cumsum(np.insert(lengths_groups_id, 0, 0))
            else:
                cumsum = None

            if need_cumsum1 and total_length is not None and cumsum is not None:
                cumsum_1 = cumsum / total_length
            else:
                cumsum_1 = None

            if not as_numpy:
                if cumsum is not None:
                    cumsum = cumsum.tolist()
                if cumsum_1 is not None:
                    cumsum_1 = cumsum_1.tolist()
                if total_length is not None:
                    total_length = total_length.tolist()
                pass

            if cumsum is None:
                cumsum = []

            if cumsum_1 is None:
                cumsum_1 = []

            if total_length is None:
                total_length = []


            summary_lengths_out1        .extend(total_length)
            summary_lengths_groups_out1 .extend([id.tolist()])
            cumsum_out1                 .extend(cumsum)
            cumsum_1_out1               .extend(cumsum_1)
            pass

        l, s = zip(*sorted(zip(segments_groups_out1, lengths_out1)))
        segments_lengths_out.append(lengths_out1)
        segments_groups_out.append(segments_groups_out1)
        summary_lengths_out.append(summary_lengths_out1)
        summary_lengths_groups_out.append(summary_lengths_groups_out1)
        cumsum_out.append(cumsum_out1)
        cumsum_1_out.append(cumsum_1_out1)

    return segments_lengths_out, segments_groups_out, summary_lengths_out, summary_lengths_groups_out, cumsum_out, cumsum_1_out

def group_values_np(values, groups):
    values = np.array(values)
    groups = np.array(groups)
    
    result = {}
    for g in np.unique(groups):
        result[g] = values[groups == g]
    return result

class SvPathGroupLength(SverchCustomTreeNode, bpy.types.Node):
    '''
    Triggers: Path / Edges length
    Tooltip: Measures the length of a path or the length of its segments
    '''
    bl_idname = 'SvPathGroupLength'
    bl_label = 'Path Group Length'
    bl_icon = 'DRIVER_DISTANCE'

    output_numpy : BoolProperty(
        name='Output NumPy', description='output NumPy arrays',
        default=False, update=updateNode)
    
    def sv_draw_buttons(self, context, layout):
        """Override to display node properties, text, operators etc. Read more in
        [Blender docs](https://docs.blender.org/api/3.3/bpy.types.UILayout.html)."""
        pass

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, "output_numpy", toggle=False)
        #layout.prop(self, "width")

    def sv_init(self, context):
        '''create sockets'''
        self.width = 220
        self.inputs.new('SvVerticesSocket', 'vertices'      ).label = 'Vertices'
        self.inputs.new('SvStringsSocket' , 'edges'         ).label = 'Edges'
        self.inputs.new('SvStringsSocket' , 'groups'     ).label = 'Groups'

        self.outputs.new('SvStringsSocket', 'segments_lengths_out'      ).label = 'Segments'
        self.outputs.new('SvStringsSocket', 'segments_groups_out'       ).label = 'Groups of Segments'
        self.outputs.new('SvStringsSocket', 'summary_lengths_out'       ).label = 'Lengths'
        self.outputs.new('SvStringsSocket', 'summary_lengths_groups_out').label = 'Groups of Lengths'
        self.outputs.new('SvStringsSocket', 'merged_lengths_out'        ).label = 'Merged Lengths'
        self.outputs.new('SvStringsSocket', 'merged_lengths_groups_out' ).label = 'Groupes of Merged Lengths'
        # self.outputs.new('SvStringsSocket', 'cumulativeSum'             ).label = 'CumulativeSum'
        # self.outputs.new('SvStringsSocket', 'cumulativeSum1'            ).label = 'CumulativeSum1'

        # self.outputs['segments_lengths_out'].description = 'Length of segments'

    def process(self):
        '''main node function called every update'''
        if not any(socket.is_linked for socket in self.outputs):
            return
        
        if (self.inputs['vertices'].is_linked==True and self.inputs['edges'].is_linked==True)==False:
            raise Exception("001. Vertices and Edges are Required!")
        
        _vertices  = self.inputs['vertices'].sv_get(default=None, deepcopy=False)
        vertices3  = ensure_nesting_level(_vertices, 3)
        _edges     = self.inputs['edges'].sv_get(default=None, deepcopy=False)
        edges3     = ensure_nesting_level(_edges, 3)


        si = self.inputs

        #vertices = si['vertices'].sv_get()

        edges_in = edges3

        groups_has_not_number = False # Признак того, что среди ключей есть нечисловой ключ. В таком случае все ключи надо заменить на числа, а потом выполнить обратное преобразование
        groups_new_id = dict()
        groups_src_id = dict()
        if si['groups'].is_linked:
            _objects = si['groups'].sv_get()
            objects = ensure_nesting_level(_objects, 2)
            groups_set = set()
            # Собрать все ключи вместе и сделать из них set
            for I, group_I in enumerate(objects):
                groups_set.update(group_I)

            # Преобразовать его в перечисляемый список
            lst_groups = list(sorted(groups_set))
            for s in lst_groups:
                if isinstance(s, (int, float) )==False:
                    groups_has_not_number = True
                    break
                pass
        
            if groups_has_not_number==True:
                # конвертер от ключей в числовую последовательность взамен старых ключей
                groups_new_id = {v: k for k,v in zip(list(range(len(lst_groups))), lst_groups)}
                groups_src_id = {k: v for k,v in zip(list(range(len(lst_groups))), lst_groups)}

                # Конвертировать ключи в числа:
                groups_converted = []
                for I, group_I in enumerate(objects):
                    group_I_converted = [groups_new_id[id] for id in group_I]
                    len_group_I_converted = len(group_I_converted)
                    len_edges_in_I = len(edges_in[I])
                    if len_group_I_converted<len_edges_in_I:
                        group_I_converted.extend([group_I_converted[-1]]*(len_edges_in_I - len_group_I_converted))
                    elif len_group_I_converted>len_edges_in_I:
                        group_I_converted = group_I_converted[:len_edges_in_I]
                    groups_converted.append(group_I_converted)
                pass
            else:
                groups_converted = objects
                pass
            groups_id = groups_converted
        else:
            groups_id = [[0]*len(e) for e in edges_in]

        meshes = match_long_repeat([vertices3, edges_in, groups_id])

        segments_lengths_out, segments_groups_out, summary_lengths_out, summary_lengths_groups_out, cumsum_out, cumsum_1_out = edges_length(meshes,
                        need_total   = True, # self.outputs['summary_lengths_out' ].is_linked,
                        need_cumsum  = False, # self.outputs['cumulativeSum' ].is_linked,
                        need_cumsum1 = False, # self.outputs['cumulativeSum1'].is_linked,
                        as_numpy     = self.output_numpy
                    )
        if groups_has_not_number==True:
            # Если ключи были заменены на цифровые, то восстановить ключи обратно на исходные значения:
            segments_groups_out = [
                                    [groups_src_id[x] for x in sublist]
                                    for sublist in segments_groups_out
                                ]
            summary_lengths_groups_out = [
                                    [groups_src_id[x] for x in sublist]
                                    for sublist in summary_lengths_groups_out
                                ]
            pass

        # смержить группы и посчитать суммы
        total_lengths_groups_merged_out = defaultdict(list)
        for group, val in sorted(zip(summary_lengths_groups_out, summary_lengths_out)):
            for g, v in zip(group, val):
                total_lengths_groups_merged_out[g].append(v)
            pass
        for g in total_lengths_groups_merged_out:
            total_lengths_groups_merged_out[g] = np.sum(total_lengths_groups_merged_out[g]).tolist()

        merged_lengths_out = []
        merged_lengths_groups_out = []

        for k in sorted(total_lengths_groups_merged_out):
            merged_lengths_out.append( [total_lengths_groups_merged_out[k]] )
            merged_lengths_groups_out.append( [k] )

        # merged_lengths_out              = [[v] for v in total_lengths_groups_merged_out.values()]
        # merged_lengths_groups_out       = [[k] for k in total_lengths_groups_merged_out.keys()]
        


        self.outputs['segments_lengths_out'         ].sv_set(segments_lengths_out)
        self.outputs['segments_groups_out'          ].sv_set(segments_groups_out)
        self.outputs['summary_lengths_out'          ].sv_set(summary_lengths_out)
        self.outputs['summary_lengths_groups_out'   ].sv_set(summary_lengths_groups_out)
        self.outputs['merged_lengths_out'           ].sv_set(merged_lengths_out)
        self.outputs['merged_lengths_groups_out'    ].sv_set(merged_lengths_groups_out)
        # self.outputs['cumulativeSum'                ].sv_set(cumsum_out)
        # self.outputs['cumulativeSum1'               ].sv_set(cumsum_1_out)
        return

classes = [SvPathGroupLength]
register, unregister = bpy.utils.register_classes_factory(classes)