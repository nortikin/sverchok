import bpy
from bpy.props import (StringProperty, EnumProperty, IntProperty, FloatProperty, BoolProperty)
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

class SvMatlLinkUpdate(bpy.types.Operator):
    "Material Link Curve Sampler Update"

    bl_idname = "node.sverchok_matl_link_update"
    bl_label = "Material Link Curve Sampler Update"
    bl_options = {'REGISTER'}

    nodename = StringProperty(name='nodename')
    treename = StringProperty(name='treename')

    def execute(self, context):
        sampler_node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        sampler_node.process_node(context)

        return{'FINISHED'} 

class SvMatlLinkBuildMatl(bpy.types.Operator):
    "Material Link Curve Sampler Build Material"

    bl_idname = "node.sverchok_matl_link_build"
    bl_label = "Material Link Curve Sampler Build Material"
    bl_options = {'REGISTER'}

    nodename = StringProperty(name='nodename')
    treename = StringProperty(name='treename')
    nodetype = EnumProperty(name="New Matl. Node Type", items=(
              ('0', 'RGBCurves', 'RGBCurves'),
              ('1', 'ColorRamp', 'ColorRamp'),
    ))

    def execute(self, context):
        bpy.ops.material.new() # object needed for this!        
        nm = bpy.data.materials[-1]
        nm.use_nodes = True
        nt = nm.node_tree
        if (self.nodetype == "0"):
            cn = nt.nodes.new('ShaderNodeRGBCurve')
        else:
            cn = nt.nodes.new('ShaderNodeValToRGB')
        bpy.ops.object.material_slot_add() # add material to object 

        sampler_node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        sampler_node.name_matl = nm.name
        sampler_node.name_node = cn.name

        return{'FINISHED'} 

class SvMatlLinkSampler(bpy.types.Node, SverchCustomTreeNode):
    ''' Material Link Sampler '''
    bl_idname = 'SvMatlLinkSampler'
    bl_label = 'Material Link Curve Sampler'
    bl_icon = 'OUTLINER_OB_EMPTY'

    name_matl = StringProperty(name='name_matl', description='Name of the material with a RGB Curves or ColorRamp node', default='', update=updateNode)
    name_node = StringProperty(name='name_node', description='Node name (must be a "RGB Curves" or "ColorRamp" node)', default='RGB Curves', update=updateNode)

    count_c = IntProperty(name='C Samples', options={'ANIMATABLE'}, description='Number of samples for C channel', default=10, min=2, max=9999, update=updateNode)
    count_r = IntProperty(name='R Samples', options={'ANIMATABLE'}, description='Number of samples for R channel', default=10, min=2, max=9999, update=updateNode)
    count_g = IntProperty(name='G Samples', options={'ANIMATABLE'}, description='Number of samples for G channel', default=10, min=2, max=9999, update=updateNode)
    count_b = IntProperty(name='B Samples', options={'ANIMATABLE'}, description='Number of samples for B channel', default=10, min=2, max=9999, update=updateNode)

    nodetype = EnumProperty(name="New Matl. Node Type", items=(
              ('0', 'RGBCurves', 'RGBCurves'),
              ('1', 'ColorRamp', 'ColorRamp'),
    ))

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "C Samples").prop_name = 'count_c'
        self.inputs.new('StringsSocket', "R Samples").prop_name = 'count_r'
        self.inputs.new('StringsSocket', "G Samples").prop_name = 'count_g'
        self.inputs.new('StringsSocket', "B Samples").prop_name = 'count_b'
        self.outputs.new('StringsSocket', "C", "C")
        self.outputs.new('StringsSocket', "R", "R")
        self.outputs.new('StringsSocket', "G", "G")
        self.outputs.new('StringsSocket', "B", "B")

    def draw_buttons(self, context, layout):
        box = layout.box()
        col = box.column(align=True)
        builder = col.operator('node.sverchok_matl_link_build', text='Create New Material')	
        col.prop(self, "nodetype")
        builder.nodename = self.name
        builder.treename = self.id_data.name
        builder.nodetype = self.nodetype

        box = layout.box()
        col = box.column(align=True)
        col.prop_search(self, "name_matl", bpy.data, 'materials', text="Use Material")
        col.prop(self, "name_node", text="Use Node")

        # get node from material 
        if (self.name_matl):
            matl = bpy.data.materials[self.name_matl]
            if (matl):
                mnode = matl.node_tree.nodes[self.name_node]
                if type(mnode) is bpy.types.ShaderNodeRGBCurve:
                    col.template_curve_mapping(mnode, "mapping", type="COLOR")
                if type(mnode) is bpy.types.ShaderNodeValToRGB:
                    col.template_color_ramp(mnode, "color_ramp", expand=False)

        updater = col.operator('node.sverchok_matl_link_update', text='Refresh')	
        updater.nodename = self.name
        updater.treename = self.id_data.name


    def get_rgb_curve_values(self, mnode, output_index, input_samples, curve_index):
        output = self.outputs[output_index]
        if output.is_linked:
            data_out = []
            if (len(input_samples) == 1):
                output_count = input_samples[0]
                if (output_count > 1):
                    for i in range(0, output_count):
                        data_out.append(mnode.mapping.curves[curve_index].evaluate(i / (output_count-1)))
            else:
                for f in input_samples:
                    data_out.append(mnode.mapping.curves[curve_index].evaluate(f))

            output.sv_set([data_out])

    def get_color_ramp_values(self, mnode, output_index, input_samples, curve_index):
        output = self.outputs[output_index]
        if output.is_linked:
            data_out = []
            if (len(input_samples) == 1):
                output_count = input_samples[0]
                if (output_count > 1):                
                    for i in range(0, output_count):
                        data_out.append(mnode.color_ramp.evaluate(i / (output_count-1))[curve_index])
            else:
                for f in input_samples:
                    data_out.append(mnode.color_ramp.evaluate(f)[curve_index])

            output.sv_set([data_out])

    def process(self):

        # channel mapping (C = 3, R = 0, G = 1, B = 2)
        chan_mapping = [3, 0, 1, 2]

        # get material node
        mnode = bpy.data.materials[self.name_matl].node_tree.nodes[self.name_node]

        # RGB Curves ?
        if type(mnode) is bpy.types.ShaderNodeRGBCurve:
            # init mapping
            mnode.mapping.initialize()
            # get values            
            for i in range(0, 4):
                self.get_rgb_curve_values(mnode, i, self.inputs[i].sv_get()[0], chan_mapping[i])

        # ColorRamp ?
        if type(mnode) is bpy.types.ShaderNodeValToRGB:
            # get values
            for i in range(0, 4):
                self.get_color_ramp_values(mnode, i, self.inputs[i].sv_get()[0], chan_mapping[i])            

def register():
    bpy.utils.register_class(SvMatlLinkSampler)
    bpy.utils.register_class(SvMatlLinkBuildMatl)
    bpy.utils.register_class(SvMatlLinkUpdate)    

def unregister():
    bpy.utils.unregister_class(SvMatlLinkSampler)
    bpy.utils.unregister_class(SvMatlLinkBuildMatl)
    bpy.utils.unregister_class(SvMatlLinkUpdate)

if __name__ == '__main__':
    register() 
