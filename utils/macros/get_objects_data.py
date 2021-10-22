

def objdata_macro_one(context, operator, term, nodes, links):

    A = context.active_node
    if not A: 
      	# operator.report({'WARNING'}, "A Node that outputs Objects must be selected before running this macro")
      	return

    idx = -1
    for socket in A.outputs:
    	if socket.bl_idname == "SvObjectSocket":
    		idx = socket.index
    		break

    # end early if we couldn't find an Objects socket.
    if idx < 0: return

    B = nodes.new('SvGetObjectsData')
    B.location = A.absolute_location[0] + 30 + A.width, A.absolute_location[1]

    links.new(A.outputs[idx], B.inputs[0])