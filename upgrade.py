
# dict for nodes be upgraded to
# compact node layout. Format
# bl_idname : [[socket_name0, prop_name0],
#              [socket_name1, prop_name1]],

upgrade_dict = { 
    'SphereNode': 
        [['Radius', 'rad_'],
         ['U', 'U_'],
         ['V', 'V_']],
    'CylinderNode': 
        [['RadTop','radTop_'],
         ['RadBot','radBot_'],
         ['Vertices','vert_'],
         ['Height', 'height_'],
         ['Subdivisions', 'subd_']],
    'RandomNode':
        [['Count','count_inner'],
         ['Seed','seed']],   
    'PlaneNode':
        [["Nº Vertices X",'int_X'],
         ["Nº Vertices Y",'int_Y'],
         ["Step X","step_X"],
         ["Step Y","step_Y"]],
    'ListSliceNode' :  
        [['Start','start'],
         ['Stop', 'stop']],
    'LineNode': 
        [["Nº Vertices",'int_'],
         ["Step",'step_']],
    'FloatNode':
        [['Float','float_']],
    'IntegerNode':
        [['Integer','int_']],
    'HilbertNode':
        [["Level",'level_'],
         ["Size",'size_']],
    'HilbertImageNode':
        [["Level",'level_'],
         ["Size",'size_'],
         ["Sensitivity",'sensitivity_']],
    'VectorMoveNode':
        [["multiplier",'mult_']],
    'EvaluateLine':
        [["Factor",'factor_']],
    'SvBoxNode':
        [["Size",'Size'],
         ["Divx",'Divx'],
         ["Divy",'Divy'],
         ["Divz",'Divz']],
    'ImageNode':
        [["vecs X",'Xvecs'],
         ["vecs Y",'Yvecs'],
         ["Step X",'Xstep'],
         ["Step Y",'Ystep']],
    'GenVectorsNode':
        [['X','x_'],
         ['Y','y_'],
         ['Z','z_']],
    'MatrixInterpolationNode':
        [['Factor','factor_']],
    'MatrixShearNode':
        [['Factor1','factor1_'],
         ['Factor2','factor2_']],
    'RandomVectorNode':
        [["Count",'count_inner'],
         ["Seed", "seed"]],
    'ListRepeaterNode':
        [["Number", "number"]],
    'ListItem2Node':
        [["Item","item"]],
    'SvWireframeNode':
        [['thickness','thickness'],
         ['Offset','offset']],
    'SvSolidifyNode':
        [['thickness','thickness']],
    'SvRemoveDoublesNode':
        [['Distance','distance']],
    }

# new sockets
# format
# bl_idname : [[new_socket0],[newsocket1]],
# new_socket [inputs/outputs,type,name,position]

new_socket_dict = {
    'SvWireframeNode':
        [['inputs','StringsSocket','thickness',0],
         ['inputs','StringsSocket','Offset',1]],
    'SvSolidifyNode':
        [['inputs','StringsSocket','thickness',0]],
    'SvRemoveDoublesNode':
        [['inputs','StringsSocket','Distance',0]],
    'MaskListNode':
        [['outputs','StringsSocket','ind_true',1],
         ['outputs','StringsSocket','ind_false',2]],
    }
        
def upgrade_nodes(ng):
    ''' Apply prop_name for nodes in the node group ng for 
        upgrade to compact ui ''' 
    for node in [n for n in ng.nodes if n.bl_idname in new_socket_dict]:
        for in_out, s_type, name, pos in new_socket_dict[node.bl_idname]:
            s_list = getattr(node,in_out)
            if s_list:
                if not name in s_list:
                    s_list.new(s_type,name)
                    s_list.move(len(s_list)-1,pos)
                
    for node in [node for node in ng.nodes if node.bl_idname in upgrade_dict]:
        for s_name,p_name in upgrade_dict[node.bl_idname]:
            if s_name in node.inputs and not node.inputs[s_name].prop_name:
                node.inputs[s_name].prop_name = p_name
