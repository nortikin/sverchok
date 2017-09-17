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

def auto_gather_node_classes():
    items_to_drop = [
        'automatic_collection', 'basename', 'defaultdict', 
        'directory', 'dirname', 'nodes_dict', 'os']

    def track_me(item_name):
        return not item_name.startswith("__") or item_name in items_to_drop

    def filter_module(_mod):
        return (getattr(_mod, item) for item in dir(_mod) if track_me(item))
    
    for i in filter_module(sverchok.nodes):
        for j in filter_module(i):
            for cls in filter_module(j):
                try:
                    if cls.bl_rna.base.name == "Node":
                        node_classes[cls.bl_idname] = cls
                except:
                    ...


def get_node_class_reference(bl_idname):
    # formerly stuff like:
    #   cls = getattr(bpy.types, self.cls_bl_idname, None)

    # this will also return a Nonetype if the ref isn't found, and the class ref if found
    return node_classes.get(bl_idname)