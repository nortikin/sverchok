# GPL3
import bpy

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
