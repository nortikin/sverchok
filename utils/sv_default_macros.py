import bpy

macros = {
    "> obj vd": {
        'display_name': "active_obj into objlite + vdmk2", 
        'file': 'macro', 
        'ident': ['verbose_macro_handler', 'obj vd']},
    "> objs vd": {
        'display_name': "multi obj in + vdmk2",
        'file':'macro', 
        'ident': ['verbose_macro_handler', 'objs vd']}
}

sv_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}

class DefaultMacros():

    @classmethod
    def ensure_nodetree(cls, operator, context):
        '''
        if no active nodetree
        add new empty node tree, set fakeuser immediately
        '''
        if not context.space_data.tree_type in sv_types:
            print('not running from a sv nodetree')
            return

        if not hasattr(context.space_data.edit_tree, 'nodes'):
            msg_one = 'going to add a new empty node tree'
            msg_two = 'added new node tree'
            print(msg_one)
            operator.report({"WARNING"}, msg_one)
            ng_params = {'name': 'unnamed_tree', 'type': 'SverchCustomTreeType'}
            ng = bpy.data.node_groups.new(**ng_params)
            ng.use_fake_user = True
            context.space_data.node_tree = ng
            operator.report({"WARNING"}, msg_two)        

    @classmethod
    def verbose_macro_handler(cls, operator, context, term):

        cls.ensure_nodetree(operator, context)

        tree = context.space_data.edit_tree
        nodes, links = tree.nodes, tree.links

        if term == 'obj vd':
            obj_in_node = nodes.new('SvObjInLite')
            obj_in_node.dget()
            vd_node = nodes.new('ViewerNode2')
            vd_node.location = obj_in_node.location.x + 180, obj_in_node.location.y
            
            links.new(obj_in_node.outputs[0], vd_node.inputs[0])
            links.new(obj_in_node.outputs[2], vd_node.inputs[1])
            links.new(obj_in_node.outputs[3], vd_node.inputs[2])
        elif term == 'objs vd':
            obj_in_node = nodes.new('SvObjectsNodeMK3')
            obj_in_node.get_objects_from_scene(operator)
            vd_node = nodes.new('ViewerNode2')
            vd_node.location = obj_in_node.location.x + 180, obj_in_node.location.y
            
            links.new(obj_in_node.outputs[0], vd_node.inputs[0])
            links.new(obj_in_node.outputs[2], vd_node.inputs[1])
            links.new(obj_in_node.outputs[3], vd_node.inputs[2])            
