def group_state_update_handler(node, context):
    """
    since this is technically a scene/admin code controlling heirarchy, pressing
    the button should result in assymetric behaviour depending on the new state of
    "self.grouping".



    + - - - + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
    | state | desired behaviour                                             |
    + ----- + --------------------------------------------------------------+
    | True  | add all objects associated with the node to the collection    |
    + ----- + --------------------------------------------------------------+
    | False | remove collection, if present, and association with object    |
    + - - - + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
    
    the node you add this to must implement " self.get_collection_name() "
    something like

        def get_collection_name(self):
            reutnr self.custom_collection_name or self.basedata_name

    """
    if node.grouping:
        updateNode(node, context)
    else:
        with node.sv_throttle_tree_update():
            node.clear_collection()

def to_collection(self, objs):
    collections = bpy.data.collections
    named = self.get_collection_name()

    # alias collection, or generate new collection and alias that
    collection = collections.get(named)
    if not collection:
        collection = collections.new(named)
        bpy.context.scene.collection.children.link(collection)

    for obj in objs:
        if obj.name not in collection.objects:
            collection.objects.link(obj)

def clear_collection(self, named):
    collections = bpy.data.collections

    named = self.get_collection_name()
    
    # alias collection, or generate new collection and alias that
    collection = collections.get(named)
    if not collection:
        """ seems the collection is already gone, this is a no op """
        return
    else:
        collections.remove(collection)