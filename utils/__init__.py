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

def auto_gather_node_classes():
    """ 
    this produces a dict with mapping from bl_idname to class reference at runtime 
    f.ex   
          node_classes = {SvBMeshViewerMk2: <class svechok.nodes.viz ......> , .... }
    """

    import inspect

    node_cats = inspect.getmembers(sverchok.nodes, inspect.ismodule)
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

    # this will also return a Nonetype if the ref isn't found, and the class ref if found
    return node_classes.get(bl_idname)