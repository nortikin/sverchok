old_bl_idnames = {
    'BakeryNode' : "bakery",
    'CircleNode' : "circle",
    'ListItemNode' : "list_item",
    'GenRangeNode' : "range",
    'GenSeriesNode' : "series",
    'Test1Node' : "test",
    'Test2Node' : "test",
    'ToolsNode' : "tools",
}
# we should add some functions to load things there
import importlib
import inspect
from sverchok.node_tree import SverchCustomTreeNode
import bpy
imported_cls = []

def register_old(bl_id):
    if bl_id in old_bl_idnames:
        mod = importlib.import_module(".{}".format(old_bl_idnames[bl_id]), __name__)
        print(mod)
        res = inspect.getmembers(mod)
        for name, cls in res:
            if inspect.isclass(cls):
                if issubclass(cls, bpy.types.Node) and cls.bl_idname == bl_id:
                    bpy.utils.register_class(cls)
                    imported_cls.append(cls)
                    print("Loaded old node type {}".format(bl_id)) 
                    return
                    
    print("Cannot find {} among old nodes".format(bl_id))
         
def unregister():
    for cls in imported_cls:
        bpy.utils.unregister_class(cls)
