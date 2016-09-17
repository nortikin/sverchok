try:
    import pyaudio
    netw = [
        'udp_client',
        'pyaudio_client',
    ]
except:
    netw = [
        'udp_client',
    ]
nodes_dict = {
    'analyzer': [
        'area',
        'normals',
        'volume',
        'bbox',
        'mesh_filter',
        'edge_angles',
        'distance_pp',
        'polygons_centers',
        'polygons_centers_mk3',
        'neuro_elman',
        'image_components',
        'kd_tree',
        'kd_tree_edges',
        'weights',
        'object_raycast',
        'scene_raycast',
        'bmesh_props',
        'closest_point_on_mesh',
        'colors',
        'colors2',
        # 'bvh_raycast',
        # 'bvh_overlap',
        # 'bvh_nearest'
    ],

    'basic_view': [
        'viewer_bmesh_mk2',
        'viewer_indices',
        'viewer_curves',
        'viewer_curves_2d',
        'viewer_polyline',
        'viewer_skin',
        'viewer_text',
        'viewer_mk2',
        'viewer_typography',
        'empty_out',
    ],

    'basic_data': [
        'objects',
        'text',
        'wifi_in',
        'wifi_out',
        'switch',
        'obj_remote',
        'dupli_instances',
        'instancer',  # this is the mesh instancer (can I rename it? 'mesh_instances')
        'group', # old group
        'monad',
        'cache',
        'getsetprop',
        'node_remote',
        'get_blenddata',
        'set_blenddata',
        'sort_blenddata',
        'filter_blenddata',
        'blenddata_to_svdata',
        'BMOperators',
        'bmesh_in',
        'bmesh_out',
        # 'create_bvh_tree',
        'bmesh_to_element'
    ],

    'basic_debug': [
        'debug_print',
        'frame_info',
        'gtext',
        'note',
        '3dview_props',
        'stethoscope'
    ],

    'generator': [
        'box',
        'box_rounded',
        'circle',
        'ngon',
        'cylinder',
        'hilbert_image',
        'hilbert',
        'hilbert3d',
        'image',
        'line',
        'plane',
        'bricks',
        'random_vector',
        'script',
        'script_mk2',
        'formula',
        'sphere',
        'basic_spline',
        'basic_3pt_arc',
        'profile',
        'generative_art',
        'script3',
    ],

    'list_basic': [
        'converter',
        'decompose',
        'func',
        'join',
        'length',
        'levels',
        'mask_join',
        'mask',
        'match',
        'sum_mk2',
        'zip'
    ],

    'list_interfere': [
        'shift_mk2',
        'repeater',
        'slice',
        'split',
        'start_end',
        'item',
        'reverse',
        'shuffle',
        'sort_mk2',
        'flip',
        'numpy_array'
    ],

    'matrix': [
        'apply',
        'apply_and_join',
        'deform',
        'destructor',
        'generator',
        'input',
        'interpolation',
        'shear',
        'euler'
    ],

    'modifier_change': [
        'delete_loose',
        'edges_intersect',
        'holes_fill',
        'mesh_join',
        'mesh_separate',
        'mirror',
        'polygons_boom',
        'polygons_to_edges',
        'triangulate',
        'triangulate_heavy',
        'remove_doubles',
        'recalc_normals',
        'rotation',
        'scale',
        'vertices_mask',
        'bevel',
        'objects_along_edge',
        'randomize',
        'limited_dissolve',
        'extrude_separate',
        'extrude_edges',
        'offset',
        'iterate',
    ],

    'modifier_make': [
        'bisect',
        'convex_hull',
        'cross_section',
        'edges_adaptative',
        'join_tris',
        'lathe',
        'uv_connect',
        'inset_special',
        'polygons_adaptative',
        'solidify',
        'voronoi_2d',
        'wireframe',
        'wafel',
        'csg_boolean',
        'pipe_tubes',
        'matrix_tube',
    ],  #

    'number': [
        'float_to_int',
        'float',
        'integer',
        'random',
        'formula2',
        'scalar',
        'list_input',
        'range_map',
        'range_float',
        'range_int',
        'fibonacci',
        'exponential',
        'easing',
        'logic'
    ],

    'vector': [
        'drop',
        'interpolation',
        'interpolation_mk2',
        'interpolation_mk3',
        'line_evaluate',
        'math',
        'move',
        'noise',
        'normal',
        'vector_polar_in',
        'vector_polar_out',
        'vector_in',
        'vector_out',
        'vertices_delete_doubles',
        'vertices_sort',
        'axis_input'
    ],


    'network': netw

}
