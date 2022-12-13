import importlib


root_modules = [
    "node_tree", "data_structure", "core",
    "utils", "ui", "nodes", "old_nodes"
]

core_modules = [
    "sv_custom_exceptions", "update_system",
    "sockets", "socket_data",
    "handlers",
    "events", "node_group",
    "tasks",
    "group_update_system",
    "event_system",
]


def sv_register_modules(modules):
    for m in modules:
        if hasattr(m, "register"):
            # print("Registering module: {}".format(m.__name__))
            m.register()


def sv_unregister_modules(modules):
    for m in reversed(modules):
        if hasattr(m, "unregister"):
            try:
                m.unregister()
            except RuntimeError as e:
                print("Error unregistering module: {}".format(m.__name__))
                print(str(e))


def make_node_list(nodes):
    node_list = []
    base_name = "sverchok.nodes"
    for category, names in nodes.nodes_dict.items():
        importlib.import_module('.{}'.format(category), base_name)
        import_modules(names, '{}.{}'.format(base_name, category), node_list)
    return node_list


def import_modules(modules, base, im_list):
    for m in modules:
        im = importlib.import_module('.{}'.format(m), base)
        im_list.append(im)


def handle_reload_event(nodes, imported_modules):
    node_list = make_node_list(nodes)

    # reload base modules
    for module in imported_modules:
        importlib.reload(module)

    # reload nodes
    for node in node_list:
        importlib.reload(node)
    return node_list


def import_settings(imported_modules):
    """Useful have the function to be sure that we do not import half of
    Sverchok modules wia settings"""
    settings = importlib.import_module(".settings", "sverchok")
    imported_modules.append(settings)


def import_all_modules(imported_modules, mods_bases):
    for mods, base in mods_bases:
        import_modules(mods, base, imported_modules)


def init_architecture(sv_name, utils_modules, ui_modules):

    imported_modules = []
    mods_bases = [
        (root_modules, "sverchok"),
        (core_modules, "sverchok.core"),
        (utils_modules, "sverchok.utils"),
        (ui_modules, "sverchok.ui")
    ]
    print('sv: import settings')
    import_settings(imported_modules)
    print('sv: import all modules')
    import_all_modules(imported_modules, mods_bases)
    return imported_modules


def init_bookkeeping(sv_name):

    from sverchok.utils import ascii_print, auto_gather_node_classes
    from sverchok import data_structure, nodes

    data_structure.SVERCHOK_NAME = sv_name
    ascii_print.show_welcome()
    auto_gather_node_classes(nodes)


def interupted_activation_detected():
    activation_message = """\n
    ** Sverchok needs a couple of seconds to become activated when you enable it for the first time. **
    ** Please restart Blender and enable it by pressing the tick box only once -- be patient!        ** 
    """
    return NameError(activation_message)


undo_handler_node_count = {}
undo_handler_node_count['sv_groups'] = 0
