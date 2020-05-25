# GPL3
import bpy
import sverchok

node_classes = {}


def register_node_class(class_ref):
    node_classes[class_ref.bl_idname] = class_ref
    bpy.utils.register_class(class_ref)

def unregister_node_class(class_ref):
    del node_classes[class_ref.bl_idname]
    bpy.utils.unregister_class(class_ref)


def register_node_classes_factory(node_class_references, ops_class_references=None):
    """

    
    !!!! Unless you are testing/developing a node, you do not need to use this. ever. !!!!


    Utility function to create register and unregister functions
    which registers and unregisters a sequence of classes

    "node_class_references":
        : are tracked by Sverchok, for later lookup by bl_idname.
    "ops_class_references":
        : are registered with the normal bpy.utils.register / unregister

    This factory is implemented verbose for now.
    """
    if not ops_class_references:

        def register():
            for cls in node_class_references:
                register_node_class(cls)

        def unregister():
            for cls in reversed(node_class_references):
                unregister_node_class(cls)

        return register, unregister

    else:

        def register():
            for cls in node_class_references:
                register_node_class(cls)
            for cls in ops_class_references:
                bpy.utils.register_class(cls)

        def unregister():
            for cls in reversed(ops_class_references):
                bpy.utils.unregister_class(cls)            
            for cls in reversed(node_class_references):
                unregister_node_class(cls)

        return register, unregister

def auto_gather_node_classes(start_module = None):
    """ 
    this produces a dict with mapping from bl_idname to class reference at runtime 
    f.ex   
          node_classes = {SvBMeshViewerMk2: <class svechok.nodes.viz ......> , .... }
    """

    import inspect
    if start_module is None:
        start_module = sverchok.nodes

    node_cats = inspect.getmembers(start_module, inspect.ismodule)
    for catname, nodecat in node_cats:
        node_files = inspect.getmembers(nodecat, inspect.ismodule)
        for filename, fileref in node_files:
            classes = inspect.getmembers(fileref, inspect.isclass)
            for clsname, cls in classes:
                try:
                    if cls.bl_rna.base.name == "Node":
                        node_classes[cls.bl_idname] = cls
                except:
                    ...


def get_node_class_reference(bl_idname):
    # formerly stuff like:
    #   cls = getattr(bpy.types, self.cls_bl_idname, None)

    if bl_idname == "NodeReroute":
        return getattr(bpy.types, bl_idname)
    # this will also return a Nonetype if the ref isn't found, and the class ref if found
    return node_classes.get(bl_idname)


def clear_node_classes():
    node_classes.clear()


def register_multiple_classes(classes):
    _ = [bpy.utils.register_class(cls) for cls in classes]

def unregister_multiple_classes(classes):
    _ = [bpy.utils.unregister_class(cls) for cls in reversed(classes)]

def app_handler_ops(append=None, remove=None):
    """ append or remove multiple items to specific bpy.app.handlers """

    (operation, handler_dict) = ('append', append) if append else ('remove', remove)
    for handler_name, handler_function in handler_dict.items():
        handler = getattr(bpy.app.handlers, handler_name)
        
        # bpy.app.handlers.<handler>.<append or remove>(function_name)
        getattr(handler, operation)(handler_function)

    # try:
    #     names = lambda d: [f"    {k} -> {v.__name__}" for k, v in d.items()] 
    #     listed = "\n".join(names(handler_dict))
    # except Exception as err:
    #     print('error while listing event handlers', err)
    #     listed = ""

    print(f'sv: {operation} app.handlers')
    # print(f'{listed}')


utils_modules = [
    # non UI tools
    "cad_module_class", "sv_bmesh_utils", "sv_stethoscope_helper", "sv_viewer_utils",
    "sv_curve_utils", "voronoi", "sv_script", "sv_itertools", "script_importhelper", "sv_oldnodes_parser",
    "csg_core", "csg_geom", "geom", "sv_easing_functions", "sv_text_io_common", "sv_obj_baker",
    "snlite_utils", "snlite_importhelper", "context_managers", "sv_node_utils", "sv_noise_utils",
    "profile", "logging", "testing", "sv_requests", "sv_examples_utils", "sv_shader_sources",
    "avl_tree", "sv_nodeview_draw_helper", "sv_font_xml_parser", "exception_drawing_with_bgl",
    # UI text editor ui
    "text_editor_submenu", "text_editor_plugins",
    # UI operators and tools
    "sv_IO_pointer_helpers",
    "sv_IO_monad_helpers", "sv_operator_utils", "sv_IO_panel_properties", "sv_IO_panel_operators",
    "sv_panels_tools", "sv_gist_tools", "sv_IO_panel_tools", "sv_load_archived_blend",
    "monad", "sv_help", "sv_default_macros", "sv_macro_utils", "sv_extra_search", "sv_3dview_tools",
    "sv_update_utils", "sv_obj_helper", "sv_batch_primitives", "sv_idx_viewer28_draw",
    # geom 2d tools
    "geom_2d.lin_alg", "geom_2d.dcel", "geom_2d.dissolve_mesh", "geom_2d.merge_mesh", "geom_2d.intersections",
    "geom_2d.make_monotone", "geom_2d.sort_mesh", "geom_2d.dcel_debugger"
]
