import importlib
import logging
import sys
import sverchok
import bpy
import types
import inspect
from pathlib import Path
from sverchok.utils.development import get_version_string
from sverchok.utils.sv_logging import add_file_handler, remove_console_handler

root_modules = [
    "dependencies",
    "data_structure",
    "node_tree",
    "core",  # already imported but should be added to use register function
    "utils",  # already imported but should be added to use register function
    "ui", "nodes", "old_nodes"
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


def imported_utils_modules():
    return [m for n, m in sys.modules.items() if 'sverchok.utils' in n]

def iter_modules(module, visited=None):
    if visited is None:
        visited = set()

    if module in visited:
        return
    visited.add(module)

    yield module

    for obj in module.__dict__.values():
        if isinstance(obj, types.ModuleType)  and obj.__name__.startswith("sverchok.nodes"):
            yield from iter_modules(obj, visited)
    pass


sverchok_help_prefix = "https://nortikin.github.io/sverchok/docs/nodes/"
sverchok_nodes_map = tuple()
sverchok_help_nodes_map_was_registered = False
def sverchok_help_nodes_map():
    return sverchok_help_prefix, sverchok_nodes_map


def sv_register_modules(modules):
    global sverchok_help_prefix, sverchok_nodes_map, sverchok_help_nodes_map_was_registered
    for m in modules:
        if hasattr(m, "register"):
            # print("Registering module: {}".format(m.__name__))
            m.register()
    _sverchok_nodes = [m for m in modules if m.__name__ == 'sverchok.nodes']
    if _sverchok_nodes:
        sverchok_nodes = _sverchok_nodes[0]
        result = []
        for mod in iter_modules(sverchok_nodes):
            for _, cls in inspect.getmembers(mod, inspect.isclass):
                if not cls.__module__.startswith(mod.__name__):
                    continue

                try:
                    if issubclass(cls, bpy.types.Node):
                        if hasattr(cls, 'bl_idname'):
                            p = Path(mod.__file__)
                            mod_filename = p.stem
                            mod_parentdir_name = p.parent.name
                            d = dict(c=cls, filename = mod_filename, parentdir = mod_parentdir_name)
                            help_mapping = (f'bpy.types.{cls.bl_idname}'.lower(), f'{mod_parentdir_name}/{mod_filename}.html',)
                            result.append(help_mapping)
                        pass
                    pass
                except TypeError:
                    pass
                pass
            pass
        
        if result:
            try:
                sverchok_nodes_map = tuple(result)
                bpy.utils.register_manual_map(sverchok_help_nodes_map)
                sverchok_help_nodes_map_was_registered = True
            except RuntimeError as e:
                print("Error registering bpy.utils.register_manual_map")
                pass
            pass

    pass

def sv_unregister_modules(modules):
    global sverchok_help_prefix, sverchok_nodes_map, sverchok_help_nodes_map_was_registered
    for m in reversed(modules):
        if hasattr(m, "unregister"):
            try:
                m.unregister()
            except RuntimeError as e:
                print("Error unregistering module: {}".format(m.__name__))
                print(str(e))
    try:
        if sverchok_help_nodes_map_was_registered==True:
            bpy.utils.unregister_manual_map(sverchok_help_nodes_map)
        sverchok_help_nodes_map_was_registered = False
    except RuntimeError as e:
        print("Error unregistering bpy.utils.unregister_manual_map")
    pass


def import_nodes():
    from sverchok import nodes
    node_modules = []
    base_name = "sverchok.nodes"
    for category, names in nodes.nodes_dict.items():
        importlib.import_module('.{}'.format(category), base_name)
        import_modules(names, '{}.{}'.format(base_name, category), node_modules)
    return node_modules


def import_modules(modules, base, im_list):
    for m in modules:
        # print(base, '.{}'.format(m))
        im = importlib.import_module('.{}'.format(m), base)
        im_list.append(im)


def handle_reload_event(imported_modules):
    node_modules = import_nodes()

    # reload base modules
    for module in imported_modules:
        importlib.reload(module)

    # reload util modules
    for module in imported_utils_modules():
        importlib.reload(module)

    # reload nodes
    for node in node_modules:
        importlib.reload(node)
    return node_modules


def import_settings(imported_modules):
    """Useful have the function to be sure that we do not import half of
    Sverchok modules wia settings"""
    settings = importlib.import_module(".settings", "sverchok")
    imported_modules.append(settings)


def import_logging(imported_modules):
    """Should be registered second after add-on settings"""
    module = importlib.import_module(".sv_logging", "sverchok.utils")
    # the module will be in imported_utils_modules - move sv_logging to core?
    # imported_modules.append(module)


def import_all_modules(imported_modules, mods_bases):
    for mods, base in mods_bases:
        import_modules(mods, base, imported_modules)
    # register context help
    _sverchok_nodes = [m for m in imported_modules if m.__name__ == 'sverchok.nodes']
    if _sverchok_nodes:
        sverchok_nodes = _sverchok_nodes[0]
        nodes_dict = sverchok_nodes.nodes_dict
        for category_name in nodes_dict:
            category = sverchok_nodes.nodes_dict[category_name]
            for node_name in category:
                node_help_map = ((f'bpy.types.{node_name}', f'{category_name}/{node_name}.html'))
                pass

    pass


def init_architecture():
    """There is no too much sense to init settings module first. It just useful
    to make sure that we do not init half of Sverchok via the module.
    Settings (preferences) are only available when add-on is imported (during
    registration).

    Import core modules here like Sverchok node tree, sockets, settings,
    update system, user interface etc.
    Utils modules are imported only via core modules. If you need your module
    to be imported you either add import in some core module or convert it into
    a core module (for example by moving into the ui folder).
    List of core modules is used for calling their register function.
    """
    import sverchok.ui as ui

    imported_modules = []
    mods_bases = [
        (root_modules, "sverchok"),
        (core_modules, "sverchok.core"),
        (ui.module_names(), "sverchok.ui")
    ]
    # print('sv: import settings')
    import_settings(imported_modules)
    # print('sv: import all modules')
    import_logging(imported_modules)
    import_all_modules(imported_modules, mods_bases)
    return imported_modules


def enable_logging():
    """Should be called after registration the add-on settings.
    Adds additional handlers according the add-on settings and set logging level"""
    if sverchok.reload_event:
        return

    addon = bpy.context.preferences.addons.get(sverchok.__name__)
    prefs = addon.preferences

    sv_logger = logging.getLogger('sverchok')
    level = getattr(logging, prefs.log_level)
    sv_logger.setLevel(level)
    if prefs.log_to_file:
        add_file_handler(prefs.log_file_name)
    if not prefs.log_to_console:
        remove_console_handler()

    logging.captureWarnings(True)
    sv_logger.info(f'Initializing Sverchok logging (level={prefs.log_level}). '
                   f'Blender version={bpy.app.version_string},'
                   f' Sverchok version={get_version_string()}')


def disable_logging():
    sv_logger = logging.getLogger('sverchok')
    for handler in sv_logger.handlers[:]:
        handler.close()
        sv_logger.removeHandler(handler)


def interupted_activation_detected():
    activation_message = """\n
    ** Sverchok needs a couple of seconds to become activated when you enable it for the first time. **
    ** Please restart Blender and enable it by pressing the tick box only once -- be patient!        ** 
    """
    return NameError(activation_message)


undo_handler_node_count = {}
undo_handler_node_count['sv_groups'] = 0
