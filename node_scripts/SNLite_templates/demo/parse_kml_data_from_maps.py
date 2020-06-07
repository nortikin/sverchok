"""
in verts v .=[[]] n=2
enum = золотое.kml серебрянное.kml
inject
include <золотое>
out  verts  v
out  names  s
"""


def ui(self, context, layout):
    layout.prop(self, 'custom_enum',expand=True)
    cb_str = 'node.scriptlite_custom_callback'
    a = layout.operator(cb_str, text='.kml>names+verts')
    a.cb_name='my_operator'

#ND = self.node_dict.get(hash(self))               #
#if ND:                                            #
#    callbacks = ND['sockets']['callbacks']        #    this will be hidden in the node eventually 
#    if not 'my_operator' in callbacks:            #
#        callbacks['my_operator'] = my_operator    #

def my_operator(self, context):
    ''' converting kml to sverchok data '''

    import bpy
    import re
    import ast
    from sverchok.utils.listutils import listinput_set_rangeI

    t = bpy.data.texts['золотое']
    tt = t.lines[0].body
    nc = re.findall(r'<name>([\d\w\-\"\.\,\s]+)</name>\S+<coordinates>(\S+)</coordinates>',tt)
    names,verts = [],[]
    for n,c in nc:
        names.append(n)
        verts.append([i for i in ast.literal_eval(c)])
    self.id_data.nodes['Scripted Node Lite'].outputs['names'].sv_set([names])
    self.id_data.nodes['Scripted Node Lite'].outputs['verts'].sv_set([verts])
    print('Парсинг городов закончился: ',names,verts)

    # all the shit with list input node
    LN = self.id_data.nodes.new('SvListInputNode')
    listinput_set_rangeI(LN,verts)
    return {'FINISHED'}

self.make_operator('my_operator')
