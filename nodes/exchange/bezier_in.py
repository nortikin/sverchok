# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, StringProperty, IntProperty
from datetime import datetime

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.data_structure import updateNode, zip_long_repeat, split_by_count
from sverchok.utils.curve.algorithms import concatenate_curves
from sverchok.utils.curve.bezier import SvCubicBezierCurve

from sverchok.ui.sv_object_names_utils import SvNodeInDataMK4, SV_PT_ViewportDisplayPropertiesDialogMK4, ReadingObjectDataError, get_objects_from_item

def get_object_data_spline_info(object_pointer):
    '''Is object exists, has spline and bezier info?'''
    object_exists       = None
    curve_object        = None
    splines_bezier      = None
    splines_non_bezier  = None
    chars               = []

    if object_pointer:
        object_exists=True
        if object_pointer.type=='CURVE':
            curve_object        = True
            splines_bezier      = False
            splines_non_bezier  = False
            if object_pointer.data.splines:
                splines = object_pointer.data.splines
                if splines:
                    for spline in splines:
                        if spline.type=='BEZIER':
                            splines_bezier = True
                            chars.append(f"{len(spline.bezier_points)-1+(1 if spline.use_cyclic_u else 0)}{'c' if spline.use_cyclic_u else 'o'}")
                        else:
                            splines_non_bezier = True
                            chars.append(f"{spline.type[0]}{'c' if spline.use_cyclic_u else 'o'}")
                        pass
                else:
                    chars.append("[empty]")
                pass
            else:
                splines_bezier = False
                splines_non_bezier = False
                chars.append("")
                pass
            pass
        else:
            curve_object = False
            splines_bezier = False
            splines_non_bezier = False
            chars.append("")
            pass

    return object_exists, curve_object, splines_bezier, splines_non_bezier, chars

class SvBezierInCallbackOpMK2(bpy.types.Operator, SvGenericNodeLocator):
    '''Select objects from scene into this node. Objects selected erlier will be removed'''
    bl_idname = "node.sv_bezier_in_callback_mk2"
    bl_label = "Bezier In Callback mk2"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):
        """
        passes the operator's 'self' too to allow calling self.report()
        """
        node.get_objects_from_scene(self)
        pass

class SvBezierInNodeMK2(Show3DProperties, SvNodeInDataMK4, bpy.types.Node):
    """
    Triggers: Input Bezier
    Tooltip: Get Bezier Curve objects from scene
    """
    bl_idname = 'SvBezierInNodeMK2'
    bl_label = 'Bezier Input'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECTS_IN'

    @property
    def is_scene_dependent(self):
        return self.object_names

    @property
    def is_animation_dependent(self):
        return self.object_names

    source_curves_join_modes = [
            #('SPLIT', "Split", "Split/Separate the object curves into individual curves", 'MOD_OFFSET', 0),
            ('KEEP' , "Keep", "Keep curves as in source objects", 'SYNTAX_ON', 1),
            #('MERGE', "Merge", "Join all curves into a single object", 'STICKY_UVS_LOC', 2)
        ]

    source_curves_join_mode : EnumProperty(
        name = "",
        items = source_curves_join_modes,
        default = 'KEEP',
        update = updateNode) # type: ignore

    legacy_mode: BoolProperty(
        name='Legacy Mode',
        description='Flats output lists (affects all sockets)',
        default=False,
        update=updateNode
        )

    sort: BoolProperty(
        name='Sort',
        description='Sorting inserted objects by names',
        default=True, update=updateNode)

    apply_matrix: BoolProperty(
        name = "Apply matrices",
        description = "Apply object matrices to control points",
        default = True,
        update = updateNode)
    
    concat_segments : BoolProperty(
        name = "Concatenate segments",
        description = "If checked, join Bezier segments of the curve into a single Curve object; otherwise, output a separate Curve object for each segment. Recommended for experienced users.",
        default = True,
        update = updateNode)
    
    def draw_curves_out_socket(self, socket, context, layout):
        layout.alignment = 'RIGHT'
        flags = socket.get_mode_flags()
        s_flags = " [" + ",".join(flags) + "]" if flags else ''
        if socket.is_linked:
            layout.label(text=f"{socket.label}. {socket.objects_number or ''}"+s_flags)
        else:
            layout.label(text=f'{socket.label}')
        pass
    
    def sv_init(self, context):
        self.width = 300
        self.outputs.new('SvCurveSocket'   , 'curves')
        self.outputs.new('SvStringsSocket' , 'use_cyclic_u').label='Cyclic U'
        self.outputs.new('SvVerticesSocket', 'control_points_c0')
        self.outputs.new('SvVerticesSocket', 'control_points_c1')
        self.outputs.new('SvVerticesSocket', 'control_points_c2')
        self.outputs.new('SvVerticesSocket', 'control_points_c3')
        self.outputs.new('SvStringsSocket' , 'tilts')
        self.outputs.new('SvStringsSocket' , 'radiuses')
        self.outputs.new('SvStringsSocket' , 'material_idx')
        self.outputs.new('SvStringsSocket' , 'material_names')
        self.outputs.new('SvMatrixSocket'  , 'matrices')
        self.outputs.new('SvObjectSocket'  , "objects")
        self.outputs.new('SvStringsSocket' , 'object_names')

        self.outputs["curves"].label = 'Curves'
        self.outputs["curves"].custom_draw = 'draw_curves_out_socket'

        self.outputs['control_points_c0'].label = 'Controls Points c0'
        self.outputs['control_points_c1'].label = 'Controls Points handle c1'
        self.outputs['control_points_c2'].label = 'Controls Points handle c2'
        self.outputs['control_points_c3'].label = 'Controls Points c3'
        self.outputs['tilts']            .label = 'Tilts'
        self.outputs['radiuses']         .label = 'Radiuses'
        self.outputs['material_idx']     .label = 'Material Idx'
        self.outputs['material_names']   .label = 'Material Names'
        self.outputs['matrices']         .label = 'Matrices'
        self.outputs['objects']          .label = 'Objects'
        self.outputs['object_names']     .label = 'Object names'

        self.inputs.new('SvObjectSocket'   , "objects")
        self.inputs ['objects'].label = "Objects"
        return

    def draw_buttons_3dpanel(self, layout):
        row = layout.row(align=True)
        row.label(text=self.label if self.label else self.name)
        self.wrapper_tracked_ui_draw_op(row, SvBezierInCallbackOpMK2.bl_idname, text='GET')
        self.wrapper_tracked_ui_draw_op(row, "node.sv_nodeview_zoom_border", text="", icon="TRACKER_DATA")

    @property
    def by_input(self):
        return self.inputs['objects'].object_ref_pointer is not None or self.inputs['objects'].is_linked

    def sv_draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.alignment='EXPAND'

        op_text = "Get selection"  # fallback

        if self.prefs_over_sized_buttons:
            row.scale_y = 4.0
            op_text = "G E T"

        self.wrapper_tracked_ui_draw_op(row, SvBezierInCallbackOpMK2.bl_idname, text=op_text, icon='IMPORT')
        
        grid = layout.grid_flow(row_major=False, columns=2, align=True)
        grid.column(align=True).prop(self, 'sort')
        grid.column(align=True).prop(self, 'apply_matrix')
        grid.column(align=True).prop(self, 'legacy_mode')
        row0 = grid.row(align=True)
        row0.column(align=True).operator(SV_PT_ViewportDisplayPropertiesDialogMK4.bl_idname, icon='TOOL_SETTINGS', text="", emboss=True)
        row0.column(align=True).popover(panel="SV_PT_ViewportDisplayPropertiesMK4", icon='DOWNARROW_HLT', text="")
        
        if not self.by_input:
            if self.object_names:
                col = layout.column(align=True)
                elem = col.row(align=True)
                self.draw_controls(elem)
                self.draw_object_names(col.row(align=True))
            else:
                layout.label(text='--None--')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "concat_segments")
        self.draw_buttons(context, layout)

    def get_curve(self, spline, matrix):
        segments = []
        pairs = list(zip(spline.bezier_points, spline.bezier_points[1:]))
        if spline.use_cyclic_u:
            pairs = pairs + [(spline.bezier_points[-1], spline.bezier_points[0])]
        points = []
        for p1, p2 in pairs:
            c0 = p1.co
            c1 = p1.handle_right
            c2 = p2.handle_left
            c3 = p2.co
            if self.apply_matrix:
                c0, c1, c2, c3 = [tuple(matrix @ c) for c in [c0, c1, c2, c3]]
            else:
                c0, c1, c2, c3 = [tuple(c) for c in [c0, c1, c2, c3]]
            points.append([c0, c1, c2, c3])
            segment = SvCubicBezierCurve(c0, c1, c2, c3)
            segments.append(segment)

        tilt_values = []
        radius_values = []
        if self.concat_segments:
            tilt_values = [p.tilt for p in spline.bezier_points]
            radius_values = [p.radius for p in spline.bezier_points]
            return points, tilt_values, radius_values, concatenate_curves(segments), spline.use_cyclic_u
        else:
            for p1, p2 in pairs:
                tilt_values.append([p1.tilt, p2.tilt])
                radius_values.append([p1.radius, p2.radius])
            points_by_segments = [[[p] for p in cp] for cp in points]
            return points_by_segments, tilt_values, radius_values, segments, spline.use_cyclic_u
        
    def check_object_allowed(self, layout, item):
        objs = get_objects_from_item(item)
        for obj in objs:
            object_exists, curve_object, bezier_object, non_bezier_object, chars = get_object_data_spline_info(obj)
            if object_exists:
                if curve_object:
                    layout.alert=False
                else:
                    layout.alert=True
                    break
                pass
            pass
        pass

    def process(self):
        #self.update_display_type(None)

        if not any([sock.is_linked for sock in self.outputs]):
            return

        objs = self.inputs['objects'].sv_get(default=[[]])
        if not self.object_names and not objs[0]:
            return
        # if not self.object_names:
        #     return

        curves_out              = []
        use_cyclic_u_out        = []
        object_names_out        = []
        controls_out            = []
        control_points_c0_out   = []
        control_points_c1_out   = []
        control_points_c2_out   = []
        control_points_c3_out   = []
        tilt_out                = []
        radius_out              = []
        objects_out             = []
        material_idx_out        = []
        material_names_out      = []
        matrices_out            = []

        if isinstance(objs[0], list):
            objs = objs[0]
            
        if not objs:
            objs = []
            for o in self.object_names:
                if o.exclude==False:
                    _obj = get_objects_from_item(o)
                    objs.extend(_obj)
                pass
            pass

        #for item in self.object_names:
        l_material_idx   = []
        l_material_names = []

        for I, obj in enumerate(objs):
            object_exists, curve_object, bezier_object, non_bezier_object, chars = get_object_data_spline_info(obj)

            splines_curves       = []
            splines_use_cyclic_u = []
            splines_controls_c0  = []
            splines_controls_c1  = []
            splines_controls_c2  = []
            splines_controls_c3  = []
            splines_tilt         = []
            splines_radius       = []
            objects              = []
            matrix = obj.matrix_world

            if curve_object==False:
                # time-consumer. More objects, more time
                self.warning(f"{obj.type}, {obj.name}: do not support spline.")
                pass
            else:
                if obj.data.splines:
                    material_indexes = []
                    for spline in obj.data.splines:
                        if spline.type != 'BEZIER':
                            self.warning(f"{obj.name}.{spline}: not supported spline type: {spline.type}")
                            continue
                        controls, tilt_values, radius_values, curve, use_cyclic_u = self.get_curve(spline, matrix)
                        material_indexes.append(spline.material_index)
                        splines_curves.append(curve)
                        splines_use_cyclic_u.append(use_cyclic_u)
                        spline_controls_c0  = []
                        spline_controls_c1  = []
                        spline_controls_c2  = []
                        spline_controls_c3  = []
                        for segments_c in controls:
                            spline_controls_c0.append(segments_c[0])
                            spline_controls_c1.append(segments_c[1])
                            spline_controls_c2.append(segments_c[2])
                            spline_controls_c3.append(segments_c[3])
                        
                        splines_controls_c0.append([spline_controls_c0])
                        splines_controls_c1.append([spline_controls_c1])
                        splines_controls_c2.append([spline_controls_c2])
                        splines_controls_c3.append([spline_controls_c3])
                        splines_tilt  .append(tilt_values)
                        splines_radius.append(radius_values)
                        pass
                    pass
                    if obj.material_slots:
                        material_socket_ids = set(material_indexes)
                        # save all sockets materials in materials sockets of object (materials name if it is not null and info about faces)
                        materials_info = dict([(id, dict(material_name=(None if obj.material_slots[id].material is None else obj.material_slots[id].material.name), is_faces=id in material_socket_ids )) for id in range(len(obj.material_slots))])
                    else:
                        if splines_curves:
                            material_indexes = [0]*len(splines_curves)
                            materials_info = dict( [(0,dict(material_name=None, is_faces=True))] )
                        else:
                            material_indexes = []
                            materials_info = dict()
                    pass
                else:
                    # if splines are empty
                    splines_curves.append([])
                    splines_use_cyclic_u.append([])
                    splines_controls_c0.append([])
                    splines_controls_c1.append([])
                    splines_controls_c2.append([])
                    splines_controls_c3.append([])

                    splines_tilt.append([])
                    splines_radius.append([])

                    material_indexes = []
                    materials_info = dict()

                    pass
            objects.append(obj)
            l_material_idx.append( material_indexes )
            l_material_names.append(materials_info)


            if self.concat_segments==True:
                curves_out           .append(splines_curves)
                use_cyclic_u_out     .append(splines_use_cyclic_u)
                object_names_out     .append([obj.name] * max(len(splines_curves), 1) )  # if no splines then return 1 for object name
                control_points_c0_out.append([co for lst in splines_controls_c0 for co in lst])
                control_points_c1_out.append([co for lst in splines_controls_c1 for co in lst])
                control_points_c2_out.append([co for lst in splines_controls_c2 for co in lst])
                control_points_c3_out.append([co for lst in splines_controls_c3 for co in lst])
                tilt_out             .append(splines_tilt)
                radius_out           .append(splines_radius)
                objects_out          .append(objects )
                matrices_out         .append([matrix] * max(len(splines_curves), 1) ) # if no splines then return 1 matrix of object
                pass
            else:
                curves_out           .append(splines_curves)
                use_cyclic_u_out     .append(splines_use_cyclic_u)
                object_names_out     .append([obj.name]*len(splines_curves))
                spline_c0 = []
                spline_c1 = []
                spline_c2 = []
                spline_c3 = []
                for I in range(len(splines_controls_c0)):
                    splines_controls_c0_I = splines_controls_c0[I]
                    splines_controls_c1_I = splines_controls_c1[I]
                    splines_controls_c2_I = splines_controls_c2[I]
                    splines_controls_c3_I = splines_controls_c3[I]
                    spline_c0.append([co for controls in splines_controls_c0_I for co in controls])
                    spline_c1.append([co for controls in splines_controls_c1_I for co in controls])
                    spline_c2.append([co for controls in splines_controls_c2_I for co in controls])
                    spline_c3.append([co for controls in splines_controls_c3_I for co in controls])
                    pass
                control_points_c0_out.append(spline_c0)
                control_points_c1_out.append(spline_c1)
                control_points_c2_out.append(spline_c2)
                control_points_c3_out.append(spline_c3)
                tilt_out             .append(splines_tilt)
                radius_out           .append(splines_radius)
                objects_out          .append(objects )
                matrices_out         .append([matrix]*len(splines_curves))
                pass
            pass

        if self.legacy_mode==True:
            # Обработка материалов для legacy
            # Create dict of unique materials before join polygons
            _materials_ids = []
            _l_materials_names_unique = set()  # Unique materials names before sorting: {'Material.002.Red', None, 'Material.005.Green', 'Material.001.Blue'}
            for l_material in l_material_names:
                for K in l_material:
                    # do not use material if it has no faces
                    if l_material[K]['is_faces']==True:
                        _l_materials_names_unique.update( [l_material[K]['material_name']] )
                    pass
                pass
            _l_materials_names_unique_sorted = sorted(_l_materials_names_unique, key=lambda x: (x is None, x)) # # sorted unique names, None is a last element (for convinience reading, has no influence for mesh join): ['Material.001.Blue', 'Material.002.Red', 'Material.005.Green', None]
            _l_materials_names_uniques = dict( zip( _l_materials_names_unique_sorted, list(range(len(_l_materials_names_unique))))) # Global materials idx: {'Material.001.Blue': 0, 'Material.002.Red': 1, 'Material.005.Green': 2, None: 3}
            for idx, obj in enumerate(objs):
                # material changes in mesh join:
                l_material_idx_I   = l_material_idx[idx]    # what sockets idx: [2, 1, 0, 3, 1, 1]
                l_material_info_I  = l_material_names[idx]  # what materials info of sockets: {0: {'material_name': 'Material.006', 'is_faces': False}, 1: {'material_name': 'Material.005.Green', 'is_faces': True}, 2: {'material_name': 'Material.007_Object', 'is_faces': False}}
                l_material_names_I = dict([(K, l_material_info_I[K]['material_name']) for K in l_material_info_I if l_material_info_I[K]['is_faces']==True]) # What used materials info: {0: None, 1: 'Material.001.Blue', 2: 'Material.002.Red', 3: 'Material.005.Green'}

                l_materials_I_repack_materials = dict([(k, _l_materials_names_uniques[l_material_names_I[k]]) for k in l_material_names_I])   # repack info of materials for global materials indexes: {0: 3, 1: 0, 2: 1, 3: 2}
                l_material_idx_I_repack        = [l_materials_I_repack_materials[s] for s in l_material_idx_I]                                # replace local sockets idx for global materials idx: [1, 0, 3, 2, 0, 0] This idx may do not equals Mesh Join in reality, but algorithm does equals results
                _materials_ids.extend(l_material_idx_I_repack)
                pass
            l_material_idx = [_materials_ids]
            l_material_names = [ list(_l_materials_names_uniques.keys())]
            pass
        else:
            _t = []
            for materials_of_object in l_material_names:
                _to = []
                for material_socket in sorted(materials_of_object.keys()):
                    _to.append(materials_of_object[material_socket]['material_name'])
                _t.append(_to)
            l_material_names = _t
            pass

        _curves_out = curves_out
        _use_cyclic_u_out = use_cyclic_u_out
        _control_points_c0_out = control_points_c0_out
        _control_points_c1_out = control_points_c1_out
        _control_points_c2_out = control_points_c2_out
        _control_points_c3_out = control_points_c3_out
        _object_names_out = object_names_out
        _tilt_out = tilt_out
        _radius_out = radius_out
        _objects_out = objects_out
        _matrices_out = matrices_out

        if self.legacy_mode == True:
            _curves_out            = [c for curves in _curves_out            for c in curves]
            _use_cyclic_u_out      = [c for curves in _use_cyclic_u_out      for c in curves]
            _control_points_c0_out = [c for curves in _control_points_c0_out for c in curves]
            _control_points_c1_out = [c for curves in _control_points_c1_out for c in curves]
            _control_points_c2_out = [c for curves in _control_points_c2_out for c in curves]
            _control_points_c3_out = [c for curves in _control_points_c3_out for c in curves]
            _object_names_out      = [c for curves in _object_names_out      for c in curves]
            _tilt_out              = [c for curves in _tilt_out              for c in curves]
            _radius_out            = [c for curves in _radius_out            for c in curves]
            _objects_out           = [c for objs   in _objects_out           for c in objs  ]
            _matrices_out          = [c for curves in _matrices_out          for c in curves]
            

        

        self.outputs['curves']           .sv_set(_curves_out)
        self.outputs['use_cyclic_u']     .sv_set(_use_cyclic_u_out)
        self.outputs['control_points_c0'].sv_set(_control_points_c0_out)
        self.outputs['control_points_c1'].sv_set(_control_points_c1_out)
        self.outputs['control_points_c2'].sv_set(_control_points_c2_out)
        self.outputs['control_points_c3'].sv_set(_control_points_c3_out)
        self.outputs['tilts']            .sv_set(_tilt_out)
        self.outputs['radiuses']         .sv_set(_radius_out)
        if 'material_idx' in self.outputs:
            self.outputs['material_idx'] .sv_set(l_material_idx)
        if 'material_names' in self.outputs:
            self.outputs['material_names'].sv_set(l_material_names)
        self.outputs['matrices']         .sv_set(_matrices_out)
        self.outputs['objects']          .sv_set(_objects_out)
        self.outputs['object_names']     .sv_set(_object_names_out)

    def migrate_links_from(self, old_node, operator):
        '''replace socket names to lowercase'''
        # copy of "ui\nodes_replacement.py"

        tree = self.id_data
        # Copy incoming / outgoing links
        old_in_links = [link for link in tree.links if link.to_node == old_node]
        old_out_links = [link for link in tree.links if link.from_node == old_node]

        for old_link in old_in_links:
            new_target_socket_name = operator.get_new_input_name(old_link.to_socket.name)
            new_target_socket_name = new_target_socket_name.lower()
            if new_target_socket_name in self.inputs:
                new_target_socket = self.inputs[new_target_socket_name]
                new_link = tree.links.new(old_link.from_socket, new_target_socket)
            else:
                self.debug("New node %s has no input named %s, skipping", self.name, new_target_socket_name)
            tree.links.remove(old_link)

        for old_link in old_out_links:
            new_source_socket_name = operator.get_new_output_name(old_link.from_socket.name)
            new_source_socket_name = new_source_socket_name.lower()
            if new_source_socket_name=='object':
                new_source_socket_name='objects'
            elif new_source_socket_name=='matrix':
                new_source_socket_name='matrixes'
            elif new_source_socket_name=='tilt':
                new_source_socket_name='tilts'
            elif new_source_socket_name=='radius':
                new_source_socket_name='radiuses'
            # We have to remove old link before creating new one
            # Blender would not allow two links pointing to the same target socket
            old_target_socket = old_link.to_socket
            tree.links.remove(old_link)
            if new_source_socket_name in self.outputs:
                new_source_socket = self.outputs[new_source_socket_name]
                new_link = tree.links.new(new_source_socket, old_target_socket)
            else:
                self.debug("New node %s has no output named %s, skipping", self.name, new_source_socket_name)
            pass

        # recreate hide property of socket:
        for s in old_node.outputs:
            if s.name in self.outputs:
                self.outputs[s.name].hide = old_node.outputs[s.name].hide
            pass
        pass

    def migrate_from(self, old_node):
        if hasattr(self, 'location_absolute'):
            # Blender 3.0 has no this attribute
            self.location_absolute = old_node.location_absolute

        #copy old objects to new object_names table (old table has only names of objects, no pointers):
        for I, item in enumerate(old_node.object_names):
            if I<=len(self.object_names)-1:
                if hasattr(item, 'pointer_type')==False:
                    if hasattr(item, 'name')==True:
                        if item.name in bpy.data.objects:
                            self.object_names[I].object_pointer = bpy.data.objects[item.name]
                        pass
                    pass
                pass
            pass

        if hasattr(old_node, 'legacy_mode'):
            self.legacy_mode = old_node.legacy_mode
        else:
            self.legacy_mode = True
        pass

classes = [
        SvBezierInCallbackOpMK2,
        SvBezierInNodeMK2
    ]
register, unregister = bpy.utils.register_classes_factory(classes)