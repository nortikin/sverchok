import importlib
import sverchok
from sverchok.utils.logging import debug, exception
from sverchok.core.update_system import clear_system_cache

reload_event = False

root_modules = [
    "menu", "node_tree", "data_structure", "core",
    "utils", "ui", "nodes", "old_nodes"
]

core_modules = [
    "sv_custom_exceptions",
    "sockets",
    "handlers", "update_system", "main_tree_handler",
    "events", "node_group", "group_handlers"
]

def sv_register_modules(modules):
    for m in modules:
        if m.__name__ != "sverchok.menu":
            if hasattr(m, "register"):
                # print("Registering module: {}".format(m.__name__))
                m.register()

def sv_unregister_modules(modules):
    clear_system_cache()
    for m in reversed(modules):
        if hasattr(m, "unregister"):
            try:
                m.unregister()
            except RuntimeError as e:
                print("Error unregistering module: {}".format(m.__name__))
                print(str(e))


def sv_registration_utils():
    """ this is a faux module for syntactic sugar on the imports in __init__ """
    pass


sv_registration_utils.register_all = sv_register_modules
sv_registration_utils.unregister_all = sv_unregister_modules


def reload_all(imported_modules, node_list):
    # reload base modules
    _ = [importlib.reload(im) for im in imported_modules]

    # reload nodes
    _ = [importlib.reload(node) for node in node_list]


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
    reload_all(imported_modules, node_list)
    return node_list


def import_settings(imported_modules, sv_dir_name):
    # "settings" treated separately in case the sverchok dir isn't named "sverchok"
    settings = importlib.import_module(".settings", sv_dir_name)
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
    import_settings(imported_modules, sv_name)
    print('sv: import all modules')
    import_all_modules(imported_modules, mods_bases)
    return imported_modules


def init_bookkeeping(sv_name):

    from sverchok.utils import ascii_print, auto_gather_node_classes

    sverchok.data_structure.SVERCHOK_NAME = sv_name
    ascii_print.show_welcome()
    auto_gather_node_classes()



undo_handler_node_count = {}
undo_handler_node_count['sv_groups'] = 0
