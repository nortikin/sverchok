# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.data_structure import updateNode, zip_long_repeat, split_by_count
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.surface.nurbs import SvNurbsSurface
from sverchok.dependencies import geomdl

from sverchok.ui.sv_object_names_utils import SvNodeInDataMK4, ReadingObjectDataError, get_objects_from_item

if geomdl is not None:
    from geomdl import NURBS

def get_object_data_curve_info(object_pointer):
    '''Is object exists, has NURBS info?'''
    object_exists        = None
    SURFACE_CURVE_object = None
    Nurbs_SURFACE        = None
    Nurbs_CURVE          = None

    if object_pointer:
        object_exists=True
        #if hasattr(object_pointer.data, 'splines'):
        if object_pointer.type in ['SURFACE', 'CURVE']:
            SURFACE_CURVE_object = True
            Nurbs_SURFACE        = False
            Nurbs_CURVE          = False
            if object_pointer.data.splines:
                splines = object_pointer.data.splines
                if splines:
                    for spline in splines:
                        if spline.type=='NURBS':
                            if object_pointer.type=='SURFACE':
                                Nurbs_SURFACE = True
                            elif object_pointer.type=='CURVE':
                                Nurbs_CURVE   = True
                            else:
                                pass
                        else:
                            pass
                        pass
                    pass
                pass
            else:
                SURFACE_CURVE_object = True
                Nurbs_SURFACE        = False
                Nurbs_CURVE          = False
                pass
            pass
        else:
            SURFACE_CURVE_object = False
            Nurbs_SURFACE        = False
            Nurbs_CURVE          = False
            pass
    else:
        object_exists=False

    return object_exists, SURFACE_CURVE_object, Nurbs_SURFACE, Nurbs_CURVE

class SvExNurbsInCallbackOpMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_ex_nurbs_in_callback_mk2"
    bl_label = "Nurbs In Callback"
    bl_options = {'INTERNAL'}

    fn_name: bpy.props.StringProperty(default='')

    def sv_execute(self, context, node):
        """
        returns the operator's 'self' too to allow the code being called to
        print from self.report.
        """
        getattr(node, self.fn_name)(self)

class SvExNurbsInNodeMK2(Show3DProperties, SvNodeInDataMK4, bpy.types.Node):
    """
    Triggers: Input NURBS
    Tooltip: Get NURBS curve or surface objects from scene
    """
    bl_idname = 'SvExNurbsInNodeMK2'
    bl_label = 'NURBS Input'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECTS_IN'
    is_scene_dependent = True
    is_animation_dependent = True

    
    legacy_mode: bpy.props.BoolProperty(
        name='Legacy Mode',
        description='Flats output lists (affects all sockets)',
        default=False,
        update=updateNode
        )
    
    # object_names: bpy.props.CollectionProperty(type=SvExNurbsInDataCollectionMK2)
    # active_obj_index: bpy.props.IntProperty()
    # object_names_ui_minimal: bpy.props.BoolProperty(default=False, description='Minimize table view')

    sort: bpy.props.BoolProperty(
        name='Sort',
        description='Sorting inserted objects by names',
        default=True, update=updateNode)

    apply_matrix : bpy.props.BoolProperty(
        name = "Apply matrices",
        description = "Apply object matrices to control points",
        default = True,
        update = updateNode)

    def sv_init(self, context):
        self.outputs.new('SvCurveSocket'  , 'curves')
        self.outputs.new('SvSurfaceSocket', 'surfaces')
        self.outputs.new('SvStringsSocket', 'object_names')
        self.outputs.new('SvMatrixSocket' , 'matrices')
        self.outputs.new('SvObjectSocket' , 'objects')

        self.outputs['curves'      ].label = 'Curves'
        self.outputs['surfaces'    ].label = 'Surfaces'
        self.outputs['object_names'].label = 'Object Names'
        self.outputs['matrices'    ].label = 'Matrices'
        self.outputs['objects'     ].label = 'Objects'

        self.inputs.new('SvObjectSocket'   , 'objects')
        self.inputs['objects'].label = 'Objects'

    def draw_obj_names(self, layout):
        if self.object_names:
            col = layout.column(align=True)
            elem = col.row(align=True)
            self.draw_controls(elem)
            self.draw_object_names(col.row(align=True))
        else:
            layout.label(text='--None--')
        
        pass

    implementations = []
    if geomdl is not None:
        implementations.append( (SvNurbsCurve.GEOMDL, "Geomdl", "Geomdl (NURBS-Python) package implementation", 0) )
    implementations.append( (SvNurbsCurve.NATIVE, "Sverchok", "Sverchok built-in implementation", 1) )

    implementation : bpy.props.EnumProperty(
            name = "Implementation",
            items=implementations,
            update = updateNode)
    
    @property
    def by_input(self):
        return self.inputs['objects'].object_ref_pointer is not None or self.inputs['objects'].is_linked

    def sv_draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.alignment='RIGHT'
        row = col.row(align=True)
        row.alignment = 'RIGHT'
        if self.prefs_over_sized_buttons:
            row.alignment='CENTER'

        op_text = "Get selection"  # fallback
        if self.prefs_over_sized_buttons:
            row.scale_y = 4.0
            op_text = "G E T"

        callback = SvExNurbsInCallbackOpMK2.bl_idname
        self.wrapper_tracked_ui_draw_op(row, callback, text=op_text, icon='IMPORT').fn_name = 'get_objects_from_scene'

        # r = layout.row(align=True)
        # r.alignment='LEFT'
        # grid = r.grid_flow(row_major=True, columns=0, align=True)
        grid = layout.grid_flow(row_major=False, columns=2, align=False)
        #grid.alignment='RIGHT'
        # c0 = grid.column()
        # c0.alignment = 'RIGHT'
        # c0.label(text='Sort:')
        # grid.column().prop(self, 'sort', text='')
        # c1 = grid.column()
        # c1.alignment = 'RIGHT'
        # c1.label(text='Implementation:')
        # grid.column().prop(self, 'implementation', text='')
        # c2 = grid.column()
        # c2.alignment = 'RIGHT'
        # c2.label(text='Apply matrixes:')
        # grid.column().prop(self, 'apply_matrix', text='')
        # c3 = grid.column()
        # c3.alignment = 'RIGHT'
        # c3.label(text='Legacy Mode:')
        # grid.column().prop(self, 'legacy_mode', text='')
        # c4 = grid.column()
        # c4.alignment = 'RIGHT'
        # c4.label(text='Display Mode:')
        # row0 = grid.row(align=True)
        # row0.column(align=True).popover(panel="SV_PT_ViewportDisplayPropertiesMK4", icon='DOWNARROW_HLT', text="")
        # row0.row().prop(self, 'display_type', expand=True, text='')

        # grid.prop(self, 'sort')
        # elem = grid.row(align=True)
        # elem.alignment='LEFT'
        # elem.prop(self, 'implementation', expand=True)
        # grid.prop(self, 'apply_matrix')
        # grid.prop(self, 'legacy_mode')
        # row0 = grid.row(align=True)
        # row0.column(align=True).popover(panel="SV_PT_ViewportDisplayPropertiesMK4", icon='DOWNARROW_HLT', text="")
        # row0.row().prop(self, 'display_type', expand=True, text='')

        grid.column(align=True).prop(self, 'sort')
        grid.column(align=True).prop(self, 'apply_matrix')
        grid.column(align=True).prop(self, 'legacy_mode')
        row = grid.row(align=True)
        row.alignment = 'LEFT'
        row.prop(self, 'implementation', expand=True)
        row0 = grid.column(align=True).row(align=True)
        row0.alignment='LEFT'
        row0.column(align=True).popover(panel="SV_PT_ViewportDisplayPropertiesMK4", icon='DOWNARROW_HLT', text="")
        row0.row().prop(self, 'display_type', expand=True, text='')

        if not self.by_input:
            if self.object_names:
                col = layout.column(align=True)
                elem = col.row(align=True)
                self.draw_controls(elem)
                self.draw_object_names(col.row(align=True))
            else:
                layout.label(text='--None--')
            pass
        pass

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "draw_3dpanel", icon="PLUGIN")
        self.draw_buttons(context, layout)

    def draw_buttons_3dpanel(self, layout):
        row = layout.row(align=True)
        row.label(text=self.label if self.label else self.name)
        callback = SvExNurbsInCallbackOpMK2.bl_idname
        row.prop(self, 'implementation', text='')
        self.wrapper_tracked_ui_draw_op(row, callback, text='GET').fn_name = 'get_objects_from_scene'
        self.wrapper_tracked_ui_draw_op(row, "node.sv_nodeview_zoom_border", text="", icon="TRACKER_DATA")

    def get_surface(self, spline, matrix):
        surface_degree_u = spline.order_u - 1
        surface_degree_v = spline.order_v - 1

        spline_points = split_by_count(spline.points, spline.point_count_u)
        if self.apply_matrix:
            control_points = [[list(matrix @ Vector(p.co[:3])) for p in row] for row in spline_points]
        else:
            control_points = [[tuple(p.co) for p in row] for row in spline_points]
        surface_weights = [[p.co[3] for p in row] for row in spline_points]
        if spline.use_cyclic_v:
            for row_idx in range(len(control_points)):
                control_points[row_idx].extend(control_points[row_idx][:spline.order_v])
        if spline.use_cyclic_u:
            control_points.extend(control_points[:spline.order_u])

        # Control points
        n_u_total = len(control_points)
        n_v_total= len(control_points[0])
        if spline.use_cyclic_u:
            knots_u = list(range(n_u_total + spline.order_u))
        else:
            knots_u = sv_knotvector.generate(surface_degree_u, n_u_total, clamped=spline.use_endpoint_u)
        self.debug("Auto knots U: %s", knots_u)

        if spline.use_cyclic_v:
            knots_v = list(range(n_v_total + spline.order_v))
        else:
            knots_v = sv_knotvector.generate(surface_degree_v, n_v_total, clamped=spline.use_endpoint_v)
        self.debug("Auto knots V: %s", knots_v)

        surface_knotvector_u = knots_u
        surface_knotvector_v = knots_v

        new_surf = SvNurbsSurface.build(self.implementation,
                        surface_degree_u, surface_degree_v,
                        surface_knotvector_u, surface_knotvector_v,
                        control_points, surface_weights,
                        normalize_knots = True)

        if spline.use_cyclic_u:
            u_min = surface_knotvector_u[surface_degree_u]
            u_max = surface_knotvector_u[-surface_degree_u - 2]
        else:
            if spline.use_endpoint_u:
                u_min = min(surface_knotvector_u)
                u_max = max(surface_knotvector_u)
            else:
                u_min = surface_knotvector_u[surface_degree_u]
                u_max = surface_knotvector_u[-surface_degree_u - 1]
        if spline.use_cyclic_v:
            v_min = surface_knotvector_v[surface_degree_v]
            v_max = surface_knotvector_v[-surface_degree_v - 2]
        else:
            if spline.use_endpoint_v:
                v_min = min(surface_knotvector_v)
                v_max = max(surface_knotvector_v)
            else:
                v_min = surface_knotvector_v[surface_degree_v]
                v_max = surface_knotvector_v[-surface_degree_v - 1]

        new_surf.u_bounds = u_min, u_max
        new_surf.v_bounds = v_min, v_max

        return new_surf

    def get_curve(self, spline, matrix):
        curve_degree = spline.order_u - 1
        if self.apply_matrix:
            vertices = [tuple(matrix @ Vector(p.co[:3])) for p in spline.points]
        else:
            vertices = [tuple(p.co)[:3] for p in spline.points]
        weights = [tuple(p.co)[3] for p in spline.points]
        if spline.use_cyclic_u:
            vertices = vertices + vertices[:curve_degree+1]
            weights = weights + weights[:curve_degree+1]
        n_total = len(vertices)
        curve_ctrlpts = vertices
        curve_weights = weights
        if spline.use_cyclic_u:
            knots = list(range(n_total + curve_degree + 1))
        else:
            knots = sv_knotvector.generate(curve_degree, n_total, clamped=spline.use_endpoint_u)
        self.debug('Auto knots: %s', knots)
        curve_knotvector = knots

        new_curve = SvNurbsCurve.build(self.implementation,
                        curve_degree, curve_knotvector,
                        curve_ctrlpts, curve_weights)
        if spline.use_cyclic_u:
            u_min = curve_knotvector[curve_degree]
            u_max = curve_knotvector[-curve_degree-2]
            new_curve = new_curve.cut_segment(u_min, u_max)
            #new_curve.u_bounds = u_min, u_max
        else:
            if spline.use_endpoint_u:
                u_min = min(curve_knotvector)
                u_max = max(curve_knotvector)
            else:
                u_min = curve_knotvector[curve_degree]
                u_max = curve_knotvector[-curve_degree-1]
            new_curve.u_bounds = (u_min, u_max)

        return new_curve
    
    def check_object_allowed(self, layout, item):
        objs = get_objects_from_item(item)
        for obj in objs:
            object_exists, SURFACE_CURVE_object, Nurbs_SURFACE, Nurbs_CURVE = get_object_data_curve_info(obj)
            if object_exists:
                if SURFACE_CURVE_object:
                    layout.alert=False
                else:
                    layout.alert=True
                    break
                pass
            pass
        pass

    def process(self):

        if not any([sock.is_linked for sock in self.outputs]):
            return

        objs = self.inputs['objects'].sv_get(default=[[]])
        if not self.object_names and not objs[0]:
            return        

        curves_out = []
        surfaces_out = []
        object_names_out = []
        objects_out = []
        matrices_out = []

        if isinstance(objs[0], list):
            objs = objs[0]
            
        if not objs:
            objs = []
            collection_names=[]
            for o in self.object_names:
                if o.exclude==False:
                    if o.pointer_type=='OBJECT':
                        if o.object_pointer:
                            objs.append(o.object_pointer)
                            collection_names.append("")
                    elif o.pointer_type=='COLLECTION':
                        if o.collection_pointer:
                            obj_coll = list(o.collection_pointer.objects)
                            for child in o.collection_pointer.children_recursive:
                                obj_coll.update(child.objects)
                            collection_names.extend( [o.collection_pointer.name]*len(objs) )
                            objs.extend(list(obj_coll))
                    else:
                        raise Exception(f"Unknown pointer type: {o.pointer_type}.")
                pass
            pass
        else:
            collection_names = [""]*len(objs)

        #for item in self.object_names:
        for I, obj in enumerate(objs):
            object_exists, SURFACE_CURVE_object, Nurbs_SURFACE, Nurbs_CURVE = get_object_data_curve_info(obj)
            objects_out.append([obj])
            if SURFACE_CURVE_object==False:
                curves_out.append([])
                surfaces_out.append([])
                object_names_out.append([obj.name])
                matrices_out.append([obj.matrix_world])
                # time-consumer. More objects, more time
                self.warning(f"{obj.type}, {obj.name}: do not support NURBS.")
                pass
            else:
                object_curves = []
                object_surfaces = []
                object_matrices = []
                matrix = obj.matrix_world
                names_count=0
                for spline in obj.data.splines:
                    if spline.type != 'NURBS':
                        self.warning("%s: not supported spline type: %s", spline, spline.type)
                        continue
                    if obj.type == 'SURFACE':
                        surface = self.get_surface(spline, matrix)
                        object_surfaces.append(surface)
                        object_matrices.append(matrix)
                        names_count+=1
                    elif obj.type == 'CURVE':
                        curve = self.get_curve(spline, matrix)
                        object_curves.append(curve)
                        object_matrices.append(matrix)
                        names_count+=1
                    pass
                pass
                curves_out.append(object_curves)
                surfaces_out.append(object_surfaces)
                object_names_out.append([obj.name] * max(names_count, 1) )  # if no splines then return 1 for object name
                matrices_out.append(object_matrices)
                pass
            pass            
        pass

        _curves_out = curves_out
        _surfaces_out = surfaces_out
        _object_names_out = object_names_out
        _objects_out = objects_out
        _matrices_out = matrices_out
        if self.legacy_mode == True:
            _curves_out            = [c for   curves in _curves_out   for c in curves]
            _surfaces_out          = [s for surfaces in _surfaces_out for s in surfaces]
            _object_names_out      = [name for objs in _object_names_out for name in objs]
            _objects_out           = [o for objs in _objects_out for o in objs]
            _matrices_out          = [m for matrices in _matrices_out for m in matrices]

        self.outputs[  'curves'].sv_set(_curves_out)
        self.outputs['curfaces'].sv_set(_surfaces_out)
        self.outputs['object_names'].sv_set(_object_names_out)
        self.outputs['objects'].sv_set(_objects_out)
        self.outputs['matrices'].sv_set(_matrices_out)

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
            # We have to remove old link before creating new one
            # Blender would not allow two links pointing to the same target socket
            old_target_socket = old_link.to_socket
            tree.links.remove(old_link)
            if new_source_socket_name in self.outputs:
                new_source_socket = self.outputs[new_source_socket_name]
                new_link = tree.links.new(new_source_socket, old_target_socket)
            else:
                self.debug("New node %s has no output named %s, skipping", self.name, new_source_socket_name)

    def migrate_from(self, old_node):
        if hasattr(self, 'location_absolute'):
            # Blender 3.0 has no this attribute
            self.location_absolute = old_node.location_absolute
        if hasattr(old_node, 'legacy_mode'):
            self.legacy_mode = old_node.legacy_mode
        else:
            self.legacy_mode = True
        pass

classes = [
    SvExNurbsInCallbackOpMK2,
    SvExNurbsInNodeMK2
]
register, unregister = bpy.utils.register_classes_factory(classes)