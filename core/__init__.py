root_modules = [
    "menu", "node_tree", "data_structure", "core",
    "utils", "ui", "nodes", "old_nodes", "sockets",
]

core_modules = [
    "monad_properties", "sv_custom_exceptions",
    "handlers", "update_system", "upgrade_nodes", "upgrade_group",
    "monad", "node_defaults"
]

def sv_register_module(m):
    if m.__name__ != "sverchok.menu":
        if hasattr(m, "register"):
            # print("Registering module: {}".format(m.__name__))
            m.register()

def sv_unregister_module(m):
    if hasattr(m, "unregister"):
        # print("Unregistering module: {}".format(m.__name__))
        m.unregister()
