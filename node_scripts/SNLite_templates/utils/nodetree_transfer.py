"""
in nodetree_name   s  d=''  n=2
in node_name   s  d=''  n=2
in input_name  s  d=''  n=2
out data      s
"""
#transfer data from another Sverchok Nodetree.
#names can be passed from Note nodes
#a Socket Converter node may be needed after this node for the data to be accepted by the next nodes
if nodetree_name and node_name and input_name:
    data = bpy.data.node_groups[nodetree_name].nodes[node_name].inputs[input_name].sv_get()
